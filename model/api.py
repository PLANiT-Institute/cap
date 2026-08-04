"""CAP 계산기 API — 파일을 건드리지 않는 순수 계산 진입점 (향후 MCP 시임).

    from model.api import compute
    compute({"pricing": {"lambda": 0.6},
             "sigmas": {"carbon_diffusion": 0.5},
             "carbon_scenarios_kr": [
                 {"scenario": "SQ", "level_usd": 12, "prob": 0.5, "binds": 0},
                 {"scenario": "REFORM", "level_usd": 60, "prob": 0.5, "binds": 1}],
             "interventions": ["h2_cfd", "carbon_reform"]},
            mode="full_counterfactual")

두 계산 모드:
- fixed_exposure: 최근 artifact의 τ*를 고정한 빠른 가격·위험 민감도.
- full_counterfactual: LSM τ*와 condition gap까지 메모리에서 다시 계산.

오버라이드는 config·outputs를 수정하지 않는다. p_bind는 시나리오에서 파생된다
(Option A) — 직접 오버라이드할 수 없다.
"""
from __future__ import annotations

import sys
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.interventions import apply_interventions, carbon_regime  # noqa: E402
from model.lib.gap_pricing import price_alignment_gap  # noqa: E402
from model.lib.pathways import condition_gap, firm_pathway  # noqa: E402
from model.lib.result_contract import (  # noqa: E402
    ALIGNMENT_GAP_LOSS_BASIS,
    ALIGNMENT_GAP_LOSS_METRIC,
    ALIGNMENT_GAP_RISK_CHARGE_METRIC,
    ENTERPRISE_FIXED_RISK_BASIS,
    ENTERPRISE_RISK_BASIS,
    RISK_CHARGE_METRIC,
    result_descriptor,
)
from model.lib.underwriting import annual_charge_usd_m, dominant_driver  # noqa: E402
from model.lib.transactions import DealTerms, screen_project  # noqa: E402
from model.s02_calibrate import load_calibration  # noqa: E402
from model.s03_lsm import solve_tau_map  # noqa: E402
from model.s04_anatomy import anatomy_for, firm_exposures, firm_frame  # noqa: E402
from model.s09_deal_screening import risk_for_project  # noqa: E402

OUT = ROOT / "outputs"
COUNTRIES = ("KR", "JP")
CALCULATION_MODES = ("fixed_exposure", "full_counterfactual")
OVERRIDE_KEYS = {
    "sigmas",
    "pricing",
    "carbon_scenarios_kr",
    "carbon_scenarios_jp",
    "interventions",
}


def _replace_scenarios(cal, country: str, rows: list[dict]) -> None:
    """국가 탄소 시나리오를 메모리에서 교체한다."""
    scen = pd.DataFrame(rows).copy()
    required = {"scenario", "level_usd", "prob", "binds"}
    missing = sorted(required - set(scen.columns))
    if missing:
        raise ValueError(f"carbon_scenarios_{country.lower()} missing columns: {missing}")
    if scen.empty or (scen["level_usd"].astype(float) <= 0).any():
        raise ValueError(f"carbon_scenarios_{country.lower()} level_usd는 양수여야 함")
    probs = scen["prob"].astype(float)
    if (probs < 0).any() or (probs > 1).any() or abs(probs.sum() - 1.0) > 1e-9:
        raise ValueError(f"carbon_scenarios_{country.lower()} prob 합 ≠ 1 또는 범위 오류")
    binds = scen["binds"].astype(int)
    if not binds.isin([0, 1]).all() or not binds.astype(bool).any():
        raise ValueError(f"carbon_scenarios_{country.lower()} binds 오류")
    driver = f"carbon_{country.lower()}"
    scen["driver"] = driver
    if "factor" not in scen:
        scen["factor"] = "domestic"
    if "anchor_note" not in scen:
        scen["anchor_note"] = "in-memory API override"
    scen = scen[cal.scenarios.columns]
    cal.scenarios = pd.concat(
        [cal.scenarios[cal.scenarios["driver"] != driver], scen],
        ignore_index=True,
    )


def _refresh_carbon_regimes(cal) -> None:
    """시나리오 또는 diffusion σ 변경 뒤 국가별 파생값을 전부 동기화한다."""
    sigma_diff = cal.sigma("carbon_diffusion")
    for country in COUNTRIES:
        reg = carbon_regime(cal.carbon_scenarios(country), sigma_diff)
        cal.l_bar[country] = reg.l_bar
        cal.l_bind[country] = reg.l_bind
        cal.p_bind[country] = reg.p_bind
        cal.sigma_carbon_reform[country] = reg.sigma_unconditional
        cal.sigma_carbon_binding[country] = reg.sigma_binding
        jump_var = reg.sigma_unconditional**2 - sigma_diff**2
        bind_jump_var = reg.sigma_binding**2 - sigma_diff**2
        cal.carbon_var_decomp[country] = {
            "diffusion_var": sigma_diff**2,
            "unconditional_jump_var": jump_var,
            "unconditional_jump_share": jump_var / reg.sigma_unconditional**2,
            "binding_conditional_jump_var": bind_jump_var,
            "binding_conditional_jump_share": bind_jump_var / reg.sigma_binding**2,
        }


def _prepare_calibration(overrides: dict | None):
    ov = overrides or {}
    unknown_keys = sorted(set(ov) - OVERRIDE_KEYS)
    if unknown_keys:
        raise ValueError(f"unknown override keys: {unknown_keys}")
    cal = load_calibration()
    reference_l_bar = dict(cal.l_bar)

    sigma_names = set(cal.sigmas["driver"])
    for driver, val in ov.get("sigmas", {}).items():
        if driver not in sigma_names:
            raise ValueError(f"unknown sigma driver: {driver}")
        value = float(val)
        if value <= 0:
            raise ValueError(f"sigma {driver}는 양수여야 함")
        i = cal.sigmas.index[cal.sigmas["driver"] == driver][0]
        cal.sigmas.loc[i, "value"] = value

    for param, val in ov.get("pricing", {}).items():
        if param == "p_bind":
            raise ValueError("p_bind는 시나리오에서 파생 — carbon_scenarios_*로 바꿀 것")
        if param not in cal.pricing:
            raise ValueError(f"unknown pricing parameter: {param}")
        value = float(val)
        if value <= 0:
            raise ValueError(f"pricing {param}는 양수여야 함")
        cal.pricing[param] = value

    for country in COUNTRIES:
        key = f"carbon_scenarios_{country.lower()}"
        if key in ov:
            _replace_scenarios(cal, country, ov[key])
    _refresh_carbon_regimes(cal)

    intervention_ids = [str(v) for v in ov.get("interventions", [])]
    unknown_interventions = sorted(
        set(intervention_ids) - set(cal.interventions["intervention_id"])
    )
    if unknown_interventions:
        raise ValueError(f"unknown interventions: {unknown_interventions}")
    return cal, reference_l_bar, intervention_ids


def _artifact_tau() -> tuple[dict[str, float | None], list[dict]]:
    artifact = json.loads((OUT / "tau_star.json").read_text())
    return (
        {row["asset_id"]: row["tau_star_year"] for row in artifact["assets"]},
        [
            {
                "asset_id": row["asset_id"],
                "firm_id": row["firm_id"],
                "tau_star_year": row["tau_star_year"],
                "p_exercised": row["p_exercised"],
                "option_value_usd_t": row["option_value_usd_t"],
            }
            for row in artifact["assets"]
        ],
    )


def _pathway_summary(cal, firm_id: str, tau_map: dict[str, float | None]) -> dict:
    assets = cal.firms[cal.firms["firm_id"] == firm_id]
    years = np.arange(
        int(cal.lsm["base_year"]),
        int(cal.lsm["base_year"] + cal.lsm["horizon_years"]) + 1,
    )
    residual = dict(zip(cal.routes["route"], cal.routes["residual_intensity_tco2_t"]))
    priced_ids = set(assets[assets["category"] == "priced_route"]["asset_id"])
    private = firm_pathway(
        assets,
        {asset_id: tau_map.get(asset_id) for asset_id in priced_ids},
        years,
        residual,
    )
    required = firm_pathway(
        assets,
        {asset_id: cal.t_required[asset_id]["year"] for asset_id in priced_ids},
        years,
        residual,
    )
    gap = condition_gap(private["emissions_mtco2"], required["emissions_mtco2"], years)
    return {
        "cumulative_alignment_gap_mtco2": gap["cumulative_alignment_gap_mtco2"],
        "peak_annual_gap_mtco2": gap["peak_annual_gap_mtco2"],
        "first_misalignment_year": gap["first_misalignment_year"],
        "alignment_restored_year": gap["alignment_restored_year"],
        "annual_alignment_gap_mtco2": gap["annual_alignment_gap_mtco2"].tolist(),
        "t_required_source": cal.t_required_source,
    }


def _calculate(
    cal,
    tau_map: dict[str, float | None],
    diagnostics: list[dict],
    intervention_ids: list[str],
    mode: str,
) -> dict:
    risk_basis = (
        ENTERPRISE_RISK_BASIS
        if mode == "full_counterfactual"
        else ENTERPRISE_FIXED_RISK_BASIS
    )
    frame = firm_frame(cal, tau_map=tau_map)
    priced = frame[frame["category"] == "priced_route"]
    firms = []
    for firm_id, group in priced.groupby("firm_id", sort=True):
        ps = (
            apply_interventions(
                cal,
                group["route"].iloc[0],
                group["country"].iloc[0],
                group["elec_driver"].iloc[0],
                intervention_ids,
            )
            if intervention_ids
            else None
        )
        meta = firm_exposures(cal, group, ps=ps)
        base = anatomy_for(cal, meta, reform=False)
        reform = anatomy_for(cal, meta, reform=True)
        path = _pathway_summary(cal, firm_id, tau_map)
        years = np.arange(
            int(cal.lsm["base_year"]),
            int(cal.lsm["base_year"] + cal.lsm["horizon_years"]) + 1,
        )
        gap_loss = price_alignment_gap(
            np.asarray(path["annual_alignment_gap_mtco2"], dtype=float),
            years,
            base_year=float(cal.lsm["base_year"]),
            rate=float(meta["wacc"]),
            horizon_years=float(cal.lsm["horizon_years"]),
            reference_price_usd_tco2=float(
                cal.pricing[f"carbon_base_{meta['country'].lower()}"]
            ),
            scenarios=meta["params"].carbon.scenarios,
            risk_price_lambda=float(cal.pricing["lambda"]),
            risk_scale_k=float(cal.pricing["k"]),
            enterprise_value_usd_bn=float(meta["ev_usd_bn"]),
        )
        firms.append(
            {
                "firm_id": firm_id,
                "firm": meta["firm"],
                "route": meta["route"],
                "result_contract": result_descriptor(
                    RISK_CHARGE_METRIC,
                    risk_basis,
                    "SCENARIO_CONDITIONAL",
                    uncertainty="scenario, pricing, covariance and exposure calibration",
                    interpretation=(
                        "path and charge recomputed"
                        if mode == "full_counterfactual"
                        else "price stress only; no path inference"
                    ),
                ),
                "shares": base["shares"],
                "shares_reform": reform["shares"],
                "risk_charge_bps": base["premium_bps"],
                "risk_charge_reform_bps": reform["premium_bps"],
                "risk_charge_usd_t": base["premium_usd_t"],
                "transition_cost_sigma_usd_bn": base["sigma_b_usd_bn"],
                "annual_risk_charge_usd_m": annual_charge_usd_m(
                    base["premium_bps"], meta["ev_usd_bn"]
                ),
                "dominant_driver": dominant_driver(base["shares"]),
                "p_bind": meta["params"].carbon.p_bind,
                "alignment_gap_loss_result_contract": result_descriptor(
                    ALIGNMENT_GAP_LOSS_METRIC,
                    ALIGNMENT_GAP_LOSS_BASIS,
                    "PROVISIONAL",
                    uncertainty="surrogate required path and assumed carbon scenarios",
                    interpretation="reduced-form PV loss implied by the physical gap",
                ),
                "alignment_gap_risk_result_contract": result_descriptor(
                    ALIGNMENT_GAP_RISK_CHARGE_METRIC,
                    ALIGNMENT_GAP_LOSS_BASIS,
                    "PROVISIONAL",
                    uncertainty="gap-loss distribution plus assumed lambda and k",
                    interpretation="separate gap-linked charge; not additive to transition-cost charge",
                ),
                "expected_pv_gap_loss_usd_m": gap_loss["expected_pv_gap_loss_usd_m"],
                "sigma_pv_gap_loss_usd_m": gap_loss["sigma_pv_gap_loss_usd_m"],
                "gap_risk_charge_bps": gap_loss["gap_risk_charge_bps"],
                "gap_charge_aggregation_warning": gap_loss["aggregation_rule"],
                "private_transition_year_capacity_weighted": float(
                    np.average(group["tau_star_year"], weights=group["capacity_mt_yr"])
                ),
                **path,
            }
        )
    return {
        "calculation_mode": mode,
        "path_recomputed": mode == "full_counterfactual",
        "interventions": intervention_ids,
        "firms": firms,
        "assets": diagnostics,
        "derived": {
            "l_bar": dict(cal.l_bar),
            "l_bind": dict(cal.l_bind),
            "p_bind": dict(cal.p_bind),
            "sigma_carbon_reform": dict(cal.sigma_carbon_reform),
            "sigma_carbon_binding": dict(cal.sigma_carbon_binding),
        },
        "epistemics": {
            "shares": "MODEL_CONDITIONAL — scalar λ·p_bind에 항등 불변(P1), 노출모델·시나리오·캘리브레이션에 조건부",
            "risk_charge": "SCENARIO_CONDITIONAL — assumed λ·k·EV, 파생 p_bind에 조건부",
            "t_required": (
                "PROVISIONAL — surrogate; empirically identified firm mandate가 아님"
                if cal.required_path_provisional
                else "EMPIRICAL — raw pathway 기반"
            ),
        },
        "note": (
            "LSM τ*와 condition gap을 메모리에서 재계산"
            if mode == "full_counterfactual"
            else "최근 tau_star artifact를 고정한 빠른 민감도; 경로 효과로 해석 금지"
        ),
    }


def compute_fixed_exposure(overrides: dict | None = None) -> dict:
    """최근 τ* artifact를 고정한 빠른 가격·위험 민감도."""
    cal, _, intervention_ids = _prepare_calibration(overrides)
    tau_map, diagnostics = _artifact_tau()
    return _calculate(cal, tau_map, diagnostics, intervention_ids, "fixed_exposure")


def compute_full_counterfactual(overrides: dict | None = None) -> dict:
    """override 후 LSM τ*·pathway·condition gap까지 다시 푸는 순수 계산."""
    cal, _, intervention_ids = _prepare_calibration(overrides)
    # X9: drift는 build_spec이 유효 시나리오에서 직접 파생 — reference_l_bar 불필요
    tau_map, diagnostics = solve_tau_map(cal, intervention_ids=intervention_ids)
    return _calculate(cal, tau_map, diagnostics, intervention_ids, "full_counterfactual")


def compute(overrides: dict | None = None, *, mode: str = "fixed_exposure") -> dict:
    """CAP 계산 진입점. mode를 생략하면 하위호환용 fixed_exposure."""
    if mode == "fixed_exposure":
        return compute_fixed_exposure(overrides)
    if mode == "full_counterfactual":
        return compute_full_counterfactual(overrides)
    raise ValueError(f"unknown calculation mode: {mode}; expected one of {CALCULATION_MODES}")


def screen_transaction(request: dict) -> dict:
    """In-memory pre-deal screen with user-supplied transaction assumptions.

    Example:
        screen_transaction({
            "firm_id": "POSCO",
            "route": "h2_dri",
            "interventions": ["h2_cfd"],
            "terms": {"green_premium_usd_t": 240, "debt_share": 0.5},
        })

    No config or output file is modified.
    """
    cal = load_calibration()
    firm_id = str(request["firm_id"])
    route = str(request.get("route") or cal.firms.loc[
        cal.firms["firm_id"] == firm_id, "route"
    ].iloc[0])
    if route not in set(cal.routes["route"]):
        raise ValueError(f"unknown route: {route}")
    interventions = [str(v) for v in request.get("interventions", [])]
    unknown_interventions = sorted(set(interventions) - set(cal.interventions["intervention_id"]))
    if unknown_interventions:
        raise ValueError(f"unknown interventions: {unknown_interventions}")
    assets = firm_frame(cal)
    assets = assets[
        (assets["firm_id"] == firm_id) & (assets["category"] == "priced_route")
    ]
    if assets.empty:
        raise ValueError(f"firm has no priced route for transaction screening: {firm_id}")
    sector = str(assets["sector"].iloc[0])
    route_sector = str(cal.routes.set_index("route").loc[route, "sector"])
    if route_sector != sector:
        raise ValueError(f"route {route} belongs to {route_sector}, not firm sector {sector}")

    terms = DealTerms.from_row(cal.transaction_assumptions.iloc[0])
    term_overrides = request.get("terms", {})
    allowed = set(terms.__dict__)
    unknown_terms = sorted(set(term_overrides) - allowed)
    if unknown_terms:
        raise ValueError(f"unknown transaction terms: {unknown_terms}")
    terms = replace(terms, **term_overrides)

    before_economics = screen_project(cal, assets, route, terms, [])
    after_economics = screen_project(cal, assets, route, terms, interventions)
    before_risk = risk_for_project(cal, assets, route, [])
    after_risk = risk_for_project(cal, assets, route, interventions)
    return {
        "request": {
            "firm_id": firm_id,
            "route": route,
            "interventions": interventions,
            "terms": terms.__dict__,
        },
        "before": {"economics": before_economics, "risk": before_risk},
        "after": {"economics": after_economics, "risk": after_risk},
        "delta": {
            "project_npv_usd_m": (
                after_economics["investment"]["project_npv_usd_m"]
                - before_economics["investment"]["project_npv_usd_m"]
            ),
            "risk_charge_bps": after_risk["risk_charge_bps"] - before_risk["risk_charge_bps"],
            "required_green_premium_usd_t": (
                after_economics["break_evens"]["required_green_premium_usd_t"]
                - before_economics["break_evens"]["required_green_premium_usd_t"]
            ),
        },
        "epistemics": {
            "status": "SCENARIO_CONDITIONAL",
            "note": "pre-deal screen only; alternative-route feasibility and executable quotes require due diligence",
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(compute(), ensure_ascii=False, indent=2))
