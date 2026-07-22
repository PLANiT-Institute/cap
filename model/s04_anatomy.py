"""s04: Euler 분해 → driver shares (Fig 3), cost vs risk shares (Fig 4).

노출 구성 (A3: B = aᵀX 선형):
- 전환연도 t_sw = 자산별 min(τ*, T^GCAM)의 용량가중 평균 — 예산 구속 세계에서
  옵션은 요구연도에 강제 행사된다 (§01). τ* 미행사 자산은 T^GCAM.
- E_carbon = 현재강도 × ℓ_bind × PV[0, t_sw] + 잔여강도 × ℓ_bind × PV[t_sw, H]
  (수준은 구속 조건부 ℓ_bind — A2: p_bind는 수준에만)
- E_h2   = q_h2 × p_h2 × PV[t_sw, H]
- E_elec = q_elec × p_elec × PV[t_sw, H]
- E_capex = K × df(t_sw)
- w_k = E_k σ_k, σ_B² = wᵀρw, s_k = w_k(ρw)_k/σ_B² (Euler; Σ=1)
- cost share = E_k/ΣE (평균 분해 — Fig 4의 대조축, A1)

no_feasible_route 자산은 anatomy에서 제외되고 stranding.json으로 분리 (A4).
reform-priced 변형: σ_carbon → sqrt(σ_diff²+jump) (#claim-policy-repricing).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.anatomy import DRIVERS, euler_shares  # noqa: E402
from model.lib.artifacts import write_artifact  # noqa: E402
from model.lib.finance import annuity, df, pv_window  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402

OUT = ROOT / "outputs"
BPS = 1e4  # 단위 환산 상수 (bps)


def firm_frame(cal: CalibrationSet) -> pd.DataFrame:
    tau = {a["asset_id"]: a for a in json.loads((OUT / "tau_star.json").read_text())["assets"]}
    horizon_end = cal.lsm["base_year"] + cal.lsm["horizon_years"]
    rows = []
    for _, a in cal.firms.iterrows():
        t = tau[a["asset_id"]]
        tau_year = t["tau_star_year"] if t["tau_star_year"] is not None else horizon_end
        rows.append({**a.to_dict(), "tau_star_year": tau_year, "t_gcam": cal.t_gcam[a["asset_id"]],
                     "t_switch_year": min(tau_year, cal.t_gcam[a["asset_id"]])})
    return pd.DataFrame(rows)


def firm_exposures(cal: CalibrationSet, g: pd.DataFrame) -> dict:
    """기업 하나의 (E 벡터, 메타). g = priced 자산들."""
    cap = g["crude_steel_mt_yr"].to_numpy(float)
    w_cap = cap / cap.sum()
    route = cal.routes.set_index("route").loc[g["route"].iloc[0]]
    country = g["country"].iloc[0]
    wacc = float(g["wacc"].iloc[0])
    horizon = float(cal.lsm["horizon_years"])
    base_year = float(cal.lsm["base_year"])
    t_sw = float(np.dot(w_cap, g["t_switch_year"].to_numpy(float)) - base_year)
    t_sw = min(max(t_sw, 0.0), horizon)
    intensity = float(np.dot(w_cap, g["emission_intensity_tco2_t"].to_numpy(float)))
    p_elec = float(route["p_elec_base_kr_usd_mwh"] if country == "KR" else route["p_elec_base_jp_usd_mwh"])

    e_carbon = (
        intensity * cal.l_bind * annuity(wacc, t_sw)
        + float(route["residual_intensity_tco2_t"]) * cal.l_bind * pv_window(wacc, t_sw, horizon)
    )
    e_h2 = float(route["q_h2_kg_t"]) * float(route["p_h2_base_usd_kg"]) * pv_window(wacc, t_sw, horizon)
    e_elec = float(route["q_elec_mwh_t"]) * p_elec * pv_window(wacc, t_sw, horizon)
    e_capex = float(route["k_capex_usd_t"]) * df(wacc, t_sw)
    return {
        "E": np.array([e_carbon, e_h2, e_elec, e_capex]),
        "t_switch_year": t_sw + base_year,
        "capacity_mt": float(cap.sum()),
        "wacc": wacc,
        "ev_usd_bn": float(g["ev_usd_bn"].iloc[0]),
        "elec_driver": g["elec_driver"].iloc[0],
        "route": g["route"].iloc[0],
        "country": country,
        "firm": g["firm"].iloc[0],
    }


def anatomy_for(cal: CalibrationSet, meta: dict, carbon_sigma: float) -> dict:
    sig, rho = cal.rho_matrix(meta["elec_driver"], carbon_sigma=carbon_sigma)
    w = meta["E"] * sig
    sigma_b, shares = euler_shares(w, rho)
    horizon = float(cal.lsm["horizon_years"])
    sigma_b_usd_bn = sigma_b * meta["capacity_mt"] * 1e6 / 1e9
    pi_bps = (
        cal.pricing["k"] * cal.pricing["lambda"] * cal.pricing["p_bind"]
        * sigma_b_usd_bn / annuity(meta["wacc"], horizon) / meta["ev_usd_bn"] * BPS
    )
    return {
        "shares": dict(zip(DRIVERS, shares.tolist())),
        "sigma_b_usd_t": sigma_b,
        "sigma_b_usd_bn": sigma_b_usd_bn,
        "premium_bps": pi_bps,
    }


def main() -> int:
    cal = load_calibration()
    frame = firm_frame(cal)
    priced = frame[frame["category"] == "priced_route"]
    stranded = frame[frame["category"] == "no_feasible_route"]

    firms_out, cost_risk_out = [], []
    for firm_id, g in priced.groupby("firm_id", sort=True):
        meta = firm_exposures(cal, g)
        base = anatomy_for(cal, meta, cal.sigma("carbon_diffusion"))
        reform = anatomy_for(cal, meta, cal.sigma_carbon_reform)
        cost_total = float(meta["E"].sum())
        cost_shares = dict(zip(DRIVERS, (meta["E"] / cost_total).tolist()))
        cluster = "h2_route" if meta["route"] == "h2_dri" else "grid_route"
        firms_out.append(
            {
                "firm_id": firm_id,
                "firm": meta["firm"],
                "country": meta["country"],
                "route": meta["route"],
                "cluster": cluster,
                "capacity_mt": meta["capacity_mt"],
                "t_switch_year": meta["t_switch_year"],
                "shares": base["shares"],
                "shares_reform": reform["shares"],
                "sigma_b_usd_bn": base["sigma_b_usd_bn"],
                "sigma_b_reform_usd_bn": reform["sigma_b_usd_bn"],
                "premium_bps": base["premium_bps"],
                "premium_reform_bps": reform["premium_bps"],
            }
        )
        cost_risk_out.append(
            {
                "firm_id": firm_id,
                "firm": meta["firm"],
                "cost_shares": cost_shares,
                "risk_shares": base["shares"],
                "exposure_pv_usd_t": dict(zip(DRIVERS, meta["E"].tolist())),
            }
        )

    write_artifact(
        "shares_by_firm",
        {"drivers": DRIVERS, "firms": firms_out},
        cal.param_status,
        uses=[],  # 조성은 proven — λ·p_bind 불진입 (Prop 1); 수준 필드는 아래 artifact
        note="Fig 3 — driver risk shares (Euler). premium_bps 필드만 conditional (levels artifact 참조)",
    )
    write_artifact(
        "premium_levels",
        {
            "firms": [
                {k: f[k] for k in ("firm_id", "firm", "premium_bps", "premium_reform_bps",
                                   "sigma_b_usd_bn", "sigma_b_reform_usd_bn")}
                for f in firms_out
            ]
        },
        cal.param_status,
        uses=["lambda", "p_bind", "k", "ev_usd_bn", "scenarios"],
        note="절대 수준 (bps) — λ·p_bind·k·EV에 조건부 (§07 원장)",
    )
    write_artifact(
        "cost_vs_risk",
        {"drivers": DRIVERS, "firms": cost_risk_out},
        cal.param_status,
        uses=[],
        note="Fig 4 — 평균(비용) 분해 vs 분산(리스크) 분해 (A1의 경험적 발톱)",
    )
    write_artifact(
        "stranding",
        {
            "assets": stranded[
                ["asset_id", "firm_id", "firm", "country", "facility", "bf_number",
                 "crude_steel_mt_yr", "emission_intensity_tco2_t", "route", "source"]
            ].to_dict(orient="records"),
            "rule": "요구 감축심도가 모든 priced route의 심도를 초과 — anatomy 제외, stranding 분리 (A4/R3)",
        },
        cal.param_status,
        uses=["firms_registry"],
        note="no_feasible_route 자산 — Fig 3와 §4.6의 모순을 데이터 수준에서 차단",
    )
    for f in firms_out:
        print(
            f"{f['firm_id']:8s} {f['cluster']:10s} "
            + " ".join(f"{d}={f['shares'][d]:.3f}" for d in DRIVERS)
            + f" | reform carbon={f['shares_reform']['carbon']:.3f} | π={f['premium_bps']:.1f}bps"
        )
    print(f"stranded: {list(stranded['asset_id'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
