"""s04: Euler 분해 → 전환비용 불확실성의 구성 (risk anatomy).

교정된 해석 (개편 §1):
- Euler share는 우선 '전환비용 불확실성의 구성'이다. 시장 위험프리미엄의 구성이
  실증 식별된 것이 아니다.
- share는 scalar λ·p_bind에는 항등적으로 불변(P1)이지만, 노출 모델·전환시점·
  시나리오·WACC·route 캘리브레이션에는 조건부다 → MODEL_CONDITIONAL.
- 절대 수준은 conditional risk charge — λ·p_bind(파생)·k·EV·시나리오에 조건부.

구조: 전환연도 t_sw = 자산별 τ* (S4 — 사적 경로 정합; τ*=None이면 지평말 =
지평 내 미전환. View 1의 '못 움직인다'와 View 2의 노출이 같은 미래를 본다.
R-7 자기모순 해소 — 이전의 min(τ*, T_required)는 required 시점 전환을 가정했다).
τ*=None 기업의 탄소 지배 share는 퇴행이 아니라 **집중**(단일 노출)이라는 발견.
자산별 노출 PV를 계산해 기업으로 합산 (기업 평균 연도 선계산 금지).
탄소 수준은 국가별 ℓ_bind (KR 시나리오를 JP에 적용하지 않음).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.anatomy import DRIVERS, euler_shares, risk_charge_annual_usd  # noqa: E402
from model.lib.artifacts import (  # noqa: E402
    IDENTITY,
    MODEL_CONDITIONAL,
    SCENARIO_CONDITIONAL,
    claim,
    write_artifact,
)
from model.lib.finance import annuity, df, pv_window  # noqa: E402
from model.lib.interventions import ParamSet, base_params  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402

OUT = ROOT / "outputs"
BPS = 1e4  # 단위 환산 상수

ANATOMY_DEPS = [
    "exposure_model",
    "routes_sensitivity",
    "firms_registry",
    "scenarios",
    "t_required",
    "sigma_carbon_diffusion",
    "sigma_h2",
    "sigma_feedstock",
    "rho_h2_elec",
    "rho_feedstock_carbon",
]
LEVEL_DEPS = ANATOMY_DEPS + ["lambda", "p_bind", "k", "ev_usd_bn"]


def firm_frame(cal: CalibrationSet, tau_map: dict[str, float | None] | None = None) -> pd.DataFrame:
    """자산 프레임 + 전환연도. tau_map으로 intervention τ*(C) 주입 가능."""
    if tau_map is None:
        tau_art = json.loads((OUT / "tau_star.json").read_text())
        base_tau = {a["asset_id"]: a["tau_star_year"] for a in tau_art["assets"]}
    else:
        base_tau = tau_map
    horizon_end = cal.lsm["base_year"] + cal.lsm["horizon_years"]
    rows = []
    for _, a in cal.firms.iterrows():
        aid = a["asset_id"]
        tau = base_tau.get(aid)
        tau_eff = tau if tau is not None else horizon_end
        treq = cal.t_required[aid]["year"]
        # S4: t_sw = τ* — 노출은 사적 경로를 따른다 (required 시점 전환 가정 제거)
        rows.append({**a.to_dict(), "tau_star_year": tau_eff, "t_required": treq,
                     "t_switch_year": tau_eff})
    return pd.DataFrame(rows)


def asset_exposure(cal: CalibrationSet, a: pd.Series, ps: ParamSet, rate: float) -> np.ndarray:
    """자산 하나의 노출 PV 벡터 (USD, 자산 전체). 자산별 계산 → 기업 합산용."""
    route = cal.routes.set_index("route").loc[a["route"]]
    horizon = float(cal.lsm["horizon_years"])
    base_year = float(cal.lsm["base_year"])
    t_sw = min(max(float(a["t_switch_year"]) - base_year, 0.0), horizon)
    cap_t = float(a["capacity_mt_yr"]) * 1e6
    e_carbon = (
        float(a["emission_intensity_tco2_t"]) * ps.carbon.l_bind * annuity(rate, t_sw)
        + float(route["residual_intensity_tco2_t"]) * ps.carbon.l_bind * pv_window(rate, t_sw, horizon)
    ) * cap_t
    e_h2 = float(route["q_h2_kg_t"]) * ps.p_h2 * pv_window(rate, t_sw, horizon) * cap_t
    e_elec = float(route["q_elec_mwh_t"]) * ps.p_elec * pv_window(rate, t_sw, horizon) * cap_t
    e_feedstock = (
        float(route["q_feedstock_t_t"])
        * ps.p_feedstock
        * pv_window(rate, t_sw, horizon)
        * cap_t
    )
    e_capex = float(route["k_capex_usd_t"]) * ps.k_capex_mult * df(rate, t_sw) * cap_t
    return np.array([e_carbon, e_h2, e_elec, e_feedstock, e_capex])


def firm_exposures(
    cal: CalibrationSet,
    g: pd.DataFrame,
    ps: ParamSet | None = None,
    rate_override: float | None = None,
) -> dict:
    """기업 = 자산별 노출의 합. ps로 intervention 파라미터 주입."""
    country = g["country"].iloc[0]
    elec_driver = g["elec_driver"].iloc[0]
    route = g["route"].iloc[0]
    if ps is None:
        ps = base_params(cal, cal.routes.set_index("route").loc[route], country, elec_driver)
    wacc = (float(g["wacc"].iloc[0]) if rate_override is None else float(rate_override)) + ps.wacc_delta
    E = np.zeros(len(DRIVERS))
    for _, a in g.iterrows():
        E += asset_exposure(cal, a, ps, wacc)
    cap_mt = float(g["capacity_mt_yr"].sum())
    return {
        "E": E,  # USD (기업 전체)
        "capacity_mt": cap_mt,
        "wacc": wacc,
        "ev_usd_bn": float(g["ev_usd_bn"].iloc[0]),
        "elec_driver": elec_driver,
        "route": route,
        "sector": str(g["sector"].iloc[0]),
        "country": country,
        "firm": g["firm"].iloc[0],
        "params": ps,
        "t_switch_year_cap_weighted": float(
            np.average(g["t_switch_year"], weights=g["capacity_mt_yr"])
        ),
    }


def anatomy_for(cal: CalibrationSet, meta: dict, reform: bool) -> dict:
    ps: ParamSet = meta["params"]
    carbon_sigma = ps.carbon.sigma_binding if reform else cal.sigma("carbon_diffusion")
    sig, rho = cal.rho_matrix(meta["elec_driver"], carbon_sigma=carbon_sigma)
    sig = sig.copy()
    sig[1], sig[2], sig[3] = ps.sigma_h2, ps.sigma_elec, ps.sigma_feedstock
    w = meta["E"] * sig
    sigma_b, shares = euler_shares(w, rho)
    horizon = float(cal.lsm["horizon_years"])
    sigma_b_bn = sigma_b / 1e9
    pi_annual = risk_charge_annual_usd(
        cal.pricing["k"], cal.pricing["lambda"], ps.carbon.p_bind,
        sigma_b, meta["wacc"], horizon,
    )
    return {
        "shares": dict(zip(DRIVERS, shares.tolist())),
        "sigma_b_usd_bn": sigma_b_bn,
        "premium_bps": pi_annual / (meta["ev_usd_bn"] * 1e9) * BPS,
        "premium_usd_t": pi_annual / (meta["capacity_mt"] * 1e6),
    }


def main() -> int:
    cal = load_calibration()
    frame = firm_frame(cal)
    priced = frame[frame["category"] == "priced_route"]
    stranded = frame[frame["category"] == "no_feasible_route"]
    wacc_eq = float(priced["wacc"].mean())

    shares_out, levels_out, cost_risk_out = [], [], []
    for firm_id, g in priced.groupby("firm_id", sort=True):
        meta = firm_exposures(cal, g)
        base = anatomy_for(cal, meta, reform=False)
        reform = anatomy_for(cal, meta, reform=True)
        meta_eq = firm_exposures(cal, g, rate_override=wacc_eq)
        base_eq = anatomy_for(cal, meta_eq, reform=False)
        reform_eq = anatomy_for(cal, meta_eq, reform=True)
        cost_total = float(meta["E"].sum())
        cluster = {
            "h2_dri": "h2_route",
            "e_cracker": "electric_route",
            "ccus_cracker": "capture_route",
            "circular_olefins": "feedstock_route",
        }.get(meta["route"], "grid_route")
        shares_out.append(
            {
                "firm_id": firm_id,
                "firm": meta["firm"],
                "country": meta["country"],
                "sector": meta["sector"],
                "route": meta["route"],
                "cluster": cluster,
                "capacity_mt": meta["capacity_mt"],
                "t_switch_year": meta["t_switch_year_cap_weighted"],
                "residual_intensity_tco2_t": float(
                    cal.routes.set_index("route").loc[meta["route"], "residual_intensity_tco2_t"]
                ),
                "shares": base["shares"],
                "shares_reform": reform["shares"],
            }
        )
        levels_out.append(
            {
                "firm_id": firm_id,
                "firm": meta["firm"],
                "sector": meta["sector"],
                "premium_bps": base["premium_bps"],
                "premium_reform_bps": reform["premium_bps"],
                "premium_usd_t": base["premium_usd_t"],
                "premium_reform_usd_t": reform["premium_usd_t"],
                "premium_bps_wacc_eq": base_eq["premium_bps"],
                "premium_reform_bps_wacc_eq": reform_eq["premium_bps"],
                "wacc": meta["wacc"],
                "p_bind": meta["params"].carbon.p_bind,
                "l_bind": meta["params"].carbon.l_bind,
                "sigma_b_usd_bn": base["sigma_b_usd_bn"],
                "sigma_b_reform_usd_bn": reform["sigma_b_usd_bn"],
            }
        )
        cost_risk_out.append(
            {
                "firm_id": firm_id,
                "firm": meta["firm"],
                "sector": meta["sector"],
                "cost_shares": dict(zip(DRIVERS, (meta["E"] / cost_total).tolist())),
                "risk_shares": base["shares"],
                "exposure_pv_usd_bn": dict(zip(DRIVERS, (meta["E"] / 1e9).tolist())),
            }
        )

    write_artifact(
        "shares_by_firm",
        {"drivers": DRIVERS, "firms": shares_out},
        cal.param_status,
        claims={
            "firms.shares": claim(
                MODEL_CONDITIONAL, ANATOMY_DEPS,
                "전환비용 불확실성의 구성 — scalar λ·p_bind에는 항등 불변(P1), "
                "노출 모델·시나리오·전환시점·캘리브레이션에는 조건부",
            ),
            "shares_sum_to_one": claim(IDENTITY, [], "Euler 분해 항등"),
        },
        note="risk anatomy — model-conditional mix (conditional premium 필드 없음; premium_levels 분리)",
        sector_enabled=cal.sector_enabled,
    )
    write_artifact(
        "premium_levels",
        {"wacc_eq": wacc_eq, "firms": levels_out},
        cal.param_status,
        claims={
            "firms.premium_bps": claim(
                SCENARIO_CONDITIONAL, LEVEL_DEPS,
                "conditional risk charge — assumed λ·k·EV, 파생 p_bind, 시나리오에 조건부. "
                "시장 위험프리미엄의 실증 식별이 아님",
            ),
        },
        note="conditional risk charge — $/t는 EV 독립, wacc_eq는 R4 통제",
        sector_enabled=cal.sector_enabled,
    )
    write_artifact(
        "cost_vs_risk",
        {"drivers": DRIVERS, "firms": cost_risk_out},
        cal.param_status,
        claims={
            "firms": claim(MODEL_CONDITIONAL, ANATOMY_DEPS, "평균 분해 vs 분산 분해 (A1)"),
        },
        note="cost vs risk shares — 평균으로 나누면 anatomy를 잘못 말한다",
        sector_enabled=cal.sector_enabled,
    )
    write_artifact(
        "stranding",
        {
            "assets": stranded[
                ["asset_id", "firm_id", "firm", "sector", "country", "facility", "unit_number",
                 "capacity_mt_yr", "emission_intensity_tco2_t", "route", "source"]
            ].to_dict(orient="records"),
            "rule": "요구 감축심도가 모든 priced route의 심도를 초과 — anatomy 제외, stranding/closure branch (A4/R3)",
        },
        cal.param_status,
        claims={"assets": claim(MODEL_CONDITIONAL, ["firms_registry", "routes_sensitivity"])},
        note="no_feasible_route — priced-route 배치 풀을 소비하지 않음",
        sector_enabled=cal.sector_enabled,
    )
    for f, l in zip(shares_out, levels_out):
        print(
            f"{f['firm_id']:8s} {f['cluster']:10s} "
            + " ".join(f"{d}={f['shares'][d]:.3f}" for d in DRIVERS)
            + f" | π={l['premium_bps']:.1f}bps (p_bind {l['p_bind']:.2f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
