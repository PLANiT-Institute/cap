"""s03: 교환옵션 LSM → τ* (base + intervention별), wedge, σ_B 선형성.

- τ*_i: 자산별 사적 최적 전환연도 (예산 없는 measure — A2)
- intervention별 τ*(C): lib/interventions의 파라미터 변환 후 LSM 재실행
  (σ만 바꾸는 게 아니라 가격 수준·K·할인율·탄소 drift가 함께 움직인다)
- wedge_i = τ*_i − T_required_i + WACC-equalized 변형
- sigma_linearity: 옵션가치의 σ 선형성 (risk-charge 선형화의 수치 근거)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import (  # noqa: E402
    MODEL_CONDITIONAL,
    PROVISIONAL,
    claim,
    write_artifact,
)
from model.lib.interventions import ParamSet, apply_interventions, base_params  # noqa: E402
from model.lib.lsm_engine import LsmSpec, lsm_tau_star  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402


def build_spec(
    cal: CalibrationSet,
    asset: dict,
    rate: float,
    seed_offset: int,
    ps: ParamSet | None = None,
    reference_l_bar: dict[str, float] | None = None,
) -> LsmSpec:
    route = cal.routes.set_index("route").loc[asset["route"]]
    country = asset["country"]
    if ps is None:
        ps = base_params(cal, route, country, asset["elec_driver"])
    p_carbon = cal.pricing["carbon_base_kr"] if country == "KR" else cal.pricing["carbon_base_jp"]
    sig, rho = cal.rho_matrix(asset["elec_driver"])
    sig = sig.copy()
    sig[1], sig[2], sig[3] = ps.sigma_h2, ps.sigma_elec, ps.sigma_feedstock
    mu = cal.mu_vector(asset["elec_driver"]).copy()
    # carbon_reform → ℓ̄ 이동을 drift 재앵커로 반영 (근사; mu_anchor_years는 config)
    base_regime = base_params(cal, route, country, asset["elec_driver"]).carbon
    reference_level = (
        base_regime.l_bar
        if reference_l_bar is None
        else float(reference_l_bar[country])
    )
    if ps.carbon.l_bar != reference_level:
        mu[0] += float(np.log(ps.carbon.l_bar / reference_level)) / cal.lsm["mu_anchor_years"]
    base_year = int(cal.lsm["base_year"])
    return LsmSpec(
        x0=np.array([
            p_carbon,
            ps.p_h2,
            ps.p_elec,
            ps.p_feedstock,
            route["k_capex_usd_t"] * ps.k_capex_mult,
        ]),
        sigma=sig,
        mu=mu,
        rho=rho,
        delta_intensity=asset["emission_intensity_tco2_t"] - route["residual_intensity_tco2_t"],
        q_h2=route["q_h2_kg_t"],
        q_elec=route["q_elec_mwh_t"],
        q_feedstock=route["q_feedstock_t_t"],
        avoided_opex=route["avoided_opex_usd_t"],
        route_opex_other=route["route_opex_other_usd_t"],
        k_reline_mult=1.0,
        k_offcycle_mult=cal.k_offcycle_mult,
        reline_t=max(0, int(asset["next_investment_year"]) - base_year),
        rate=rate + ps.wacc_delta,
        horizon=int(cal.lsm["horizon_years"]),
        n_paths=int(cal.lsm["n_paths"]),
        basis_degree=int(cal.lsm["basis_degree"]),
        seed=int(cal.lsm["seed"]) + seed_offset,
    )


def tau_year_of(cal: CalibrationSet, res: dict) -> float | None:
    """τ* 정본 = E[min(τ, H)] (미행사=지평말). 개입에 단조 반응; p_exercised 병기.
    p_exercised < tau_exercise_threshold이면 '지평 내 사적 전환 없음'으로 None."""
    if res["p_exercised"] < cal.lsm["tau_exercise_threshold"]:
        return None
    return int(cal.lsm["base_year"]) + res["tau_expected"]


def solve_tau_map(
    cal: CalibrationSet,
    intervention_ids: list[str] | None = None,
    reference_l_bar: dict[str, float] | None = None,
) -> tuple[dict[str, float | None], list[dict]]:
    """파일을 읽거나 쓰지 않고 자산별 τ*를 다시 푼다.

    ``reference_l_bar``는 API scenario override 전의 기대 탄소가격이다. 이를 넘기면
    override가 만든 기대가격 이동이 LSM drift에 반영된다. 배치 의무(T_required)는
    별도 층이므로 사적 최적 전환을 푸는 이 함수가 변경하지 않는다.
    """
    ids = intervention_ids or []
    threshold = float(cal.lsm["tau_exercise_threshold"])
    tau_map: dict[str, float | None] = {}
    diagnostics: list[dict] = []
    for seed_offset, (_, row) in enumerate(cal.firms.iterrows()):
        asset = row.to_dict()
        ps = (
            apply_interventions(
                cal,
                asset["route"],
                asset["country"],
                asset["elec_driver"],
                ids,
            )
            if ids
            else None
        )
        result = lsm_tau_star(
            build_spec(
                cal,
                asset,
                asset["wacc"],
                seed_offset,
                ps,
                reference_l_bar=reference_l_bar,
            ),
            tau_threshold=threshold,
        )
        tau_year = tau_year_of(cal, result)
        tau_map[asset["asset_id"]] = tau_year
        diagnostics.append(
            {
                "asset_id": asset["asset_id"],
                "firm_id": asset["firm_id"],
                "tau_star_year": tau_year,
                "p_exercised": result["p_exercised"],
                "option_value_usd_t": result["option_value"],
            }
        )
    return tau_map, diagnostics


def main() -> int:
    cal = load_calibration()
    base_year = int(cal.lsm["base_year"])
    wacc_eq = float(cal.firms["wacc"].mean())
    p_bind_flag = bool(int(cal.lsm["p_bind_in_exercise"]))
    intervention_ids = [
        i for i in cal.interventions["intervention_id"]
    ]

    tau_rows, wedge_rows = [], []
    tau_interventions: dict[str, dict[str, float | None]] = {i: {} for i in intervention_ids}
    for i, (_, a) in enumerate(cal.firms.iterrows()):
        asset = a.to_dict()
        thr = float(cal.lsm["tau_exercise_threshold"])
        res = lsm_tau_star(build_spec(cal, asset, asset["wacc"], i), tau_threshold=thr)
        res_eq = lsm_tau_star(build_spec(cal, asset, wacc_eq, i), tau_threshold=thr)
        tau_year = tau_year_of(cal, res)
        tau_year_eq = tau_year_of(cal, res_eq)
        treq = cal.t_required[asset["asset_id"]]
        for iid in intervention_ids:
            ps = apply_interventions(cal, asset["route"], asset["country"], asset["elec_driver"], [iid])
            res_c = lsm_tau_star(build_spec(cal, asset, asset["wacc"], i, ps), tau_threshold=thr)
            tau_interventions[iid][asset["asset_id"]] = tau_year_of(cal, res_c)
        row = {
            "asset_id": asset["asset_id"],
            "firm_id": asset["firm_id"],
            "firm": asset["firm"],
            "facility": f"{asset['facility']} {asset['unit_number']}",
            "sector": asset["sector"],
            "emission_intensity_tco2_t": asset["emission_intensity_tco2_t"],
            "country": asset["country"],
            "route": asset["route"],
            "category": asset["category"],
            "tau_star_year": tau_year,
            "tau_star_year_wacc_eq": tau_year_eq,
            "p_exercised": res["p_exercised"],
            "option_value_usd_t": res["option_value"],
        }
        if p_bind_flag:
            res_pb = lsm_tau_star(
                build_spec(cal, asset, asset["wacc"], i),
                exercise_relax=cal.p_bind[asset["country"]],
            )
            row["tau_star_year_p_bind"] = tau_year_of(cal, res_pb)
        tau_rows.append(row)
        wedge_rows.append(
            {
                "asset_id": asset["asset_id"],
                "firm": asset["firm"],
                "firm_id": asset["firm_id"],
                "facility": f"{asset['facility']} {asset['unit_number']}",
                "sector": asset["sector"],
                "emission_intensity_tco2_t": asset["emission_intensity_tco2_t"],
                "country": asset["country"],
                "category": asset["category"],
                "t_required": treq["year"],
                "t_required_status": treq["status"],
                "tau_star_year": tau_year,
                "timing_gap_years": (tau_year - treq["year"])
                if (tau_year is not None and treq["year"] is not None)
                else None,
                "tau_star_year_wacc_eq": tau_year_eq,
            }
        )

    lsm_deps = ["carbon_base_kr", "carbon_base_jp", "routes_sensitivity", "firms_registry",
                "exposure_model"]
    write_artifact(
        "tau_star",
        {
            "base_year": base_year,
            "p_bind_in_exercise": p_bind_flag,
            "assets": tau_rows,
            "interventions": tau_interventions,
        },
        cal.param_status,
        claims={
            "assets.tau_star_year": claim(MODEL_CONDITIONAL, lsm_deps,
                                          "LSM GBM (config μ drift; 행사가치도 동일 μ로 성장 — "
                                          "measure 일치); 예산 없는 measure (A2)"),
            "interventions": claim(MODEL_CONDITIONAL, lsm_deps + ["interventions"],
                                   "coverage·tenor 1차 근사 후 τ* 재계산"),
        },
        note="사적 최적 전환연도 — base + intervention별",
    )
    write_artifact(
        "wedge",
        {"t_required_source": cal.t_required_source, "assets": wedge_rows},
        cal.param_status,
        claims={
            "assets.timing_gap_years": claim(
                PROVISIONAL, lsm_deps + ["t_required"],
                "T_required는 surrogate — 실증 식별된 의무 아님",
            ),
        },
        note="timing gap = τ* − T_required (#claim-wedge-conjunction)",
    )

    rep = cal.firms[cal.firms["category"] == "priced_route"].iloc[0].to_dict()
    n_grid = int(cal.lsm["sigma_linearity_n"])
    lo = float((cal.sigmas["band_lo"] / cal.sigmas["value"]).mean())
    hi = float((cal.sigmas["band_hi"] / cal.sigmas["value"]).mean())
    scales = np.linspace(lo, hi, n_grid)
    values = [
        lsm_tau_star(build_spec(cal, rep, rep["wacc"], 0), sigma_scale=float(s))["option_value"]
        for s in scales
    ]
    coeffs = np.polyfit(scales, values, 1)
    fitted = np.polyval(coeffs, scales)
    ss_res = float(np.sum((np.array(values) - fitted) ** 2))
    ss_tot = float(np.sum((np.array(values) - np.mean(values)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    write_artifact(
        "sigma_linearity",
        {
            "asset_id": rep["asset_id"],
            "sigma_scale": list(map(float, scales)),
            "option_value_usd_t": list(map(float, values)),
            "r_squared": r2,
        },
        cal.param_status,
        claims={"r_squared": claim(MODEL_CONDITIONAL, ["routes_sensitivity", "exposure_model"],
                                   "band 범위 내 선형 근사의 수치 근거")},
        note="risk-charge 선형화 π≈k·λ·p_bind·σ_B의 유효성 체크",
    )
    print(f"OK — τ* base+{len(intervention_ids)} interventions × {len(tau_rows)} assets, σ-linearity R²={r2:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
