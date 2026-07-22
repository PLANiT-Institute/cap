"""s03: 교환옵션 LSM → τ*, wedge, σ_B 선형성 (Fig 2, §3.4).

- τ*_i: 자산별 사적 최적 전환연도 (LSM, 예산 없는 measure — A2)
- wedge_i = τ*_i − T_i^GCAM (#claim-wedge-conjunction) + WACC-equalized 변형
- sigma_linearity: 옵션가치가 σ_B에 선형인지 (R² 체크; π=kλp_bind·σ_B 근사의 근거)
- p_bind_in_exercise 플래그(R5): on이면 τ*(p_bind) 변형도 산출
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import write_artifact  # noqa: E402
from model.lib.lsm_engine import LsmSpec, lsm_tau_star  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402


def build_spec(cal: CalibrationSet, asset: dict, rate: float, seed_offset: int) -> LsmSpec:
    route = cal.routes.set_index("route").loc[asset["route"]]
    country = asset["country"]
    p_elec = route["p_elec_base_kr_usd_mwh"] if country == "KR" else route["p_elec_base_jp_usd_mwh"]
    p_carbon = cal.pricing["carbon_base_kr"] if country == "KR" else cal.pricing["carbon_base_jp"]
    sig, rho = cal.rho_matrix(asset["elec_driver"])
    base_year = int(cal.lsm["base_year"])
    return LsmSpec(
        x0=np.array([p_carbon, route["p_h2_base_usd_kg"], p_elec, route["k_capex_usd_t"]]),
        sigma=sig,
        mu=cal.mu_vector(asset["elec_driver"]),
        rho=rho,
        delta_intensity=asset["emission_intensity_tco2_t"] - route["residual_intensity_tco2_t"],
        q_h2=route["q_h2_kg_t"],
        q_elec=route["q_elec_mwh_t"],
        avoided_opex=route["avoided_opex_usd_t"],
        route_opex_other=route["route_opex_other_usd_t"],
        k_reline_mult=1.0,
        k_offcycle_mult=cal.k_offcycle_mult,
        reline_t=max(0, int(asset["next_reline_year"]) - base_year),
        rate=rate,
        horizon=int(cal.lsm["horizon_years"]),
        n_paths=int(cal.lsm["n_paths"]),
        basis_degree=int(cal.lsm["basis_degree"]),
        seed=int(cal.lsm["seed"]) + seed_offset,
    )


def main() -> int:
    cal = load_calibration()
    base_year = int(cal.lsm["base_year"])
    wacc_eq = float(cal.firms["wacc"].mean())
    p_bind_flag = bool(int(cal.lsm["p_bind_in_exercise"]))
    p_bind = cal.pricing["p_bind"]

    tau_rows, wedge_rows = [], []
    for i, (_, a) in enumerate(cal.firms.iterrows()):
        asset = a.to_dict()
        res = lsm_tau_star(build_spec(cal, asset, asset["wacc"], i))
        res_eq = lsm_tau_star(build_spec(cal, asset, wacc_eq, i))
        tau_year = (base_year + res["tau_mean"]) if res["tau_mean"] is not None else None
        tau_year_eq = (base_year + res_eq["tau_mean"]) if res_eq["tau_mean"] is not None else None
        t_gcam = cal.t_gcam[asset["asset_id"]]
        row = {
            "asset_id": asset["asset_id"],
            "firm_id": asset["firm_id"],
            "firm": asset["firm"],
            "country": asset["country"],
            "route": asset["route"],
            "category": asset["category"],
            "tau_star_year": tau_year,
            "tau_star_year_wacc_eq": tau_year_eq,
            "p_exercised": res["p_exercised"],
            "option_value_usd_t": res["option_value"],
        }
        if p_bind_flag:
            res_pb = lsm_tau_star(build_spec(cal, asset, asset["wacc"], i), exercise_relax=p_bind)
            row["tau_star_year_p_bind"] = (
                (base_year + res_pb["tau_mean"]) if res_pb["tau_mean"] is not None else None
            )
        tau_rows.append(row)
        wedge_rows.append(
            {
                "asset_id": asset["asset_id"],
                "firm": asset["firm"],
                "firm_id": asset["firm_id"],
                "facility": f"{asset['facility']} {asset['bf_number']}",
                "emission_intensity_tco2_t": asset["emission_intensity_tco2_t"],
                "country": asset["country"],
                "category": asset["category"],
                "t_gcam": t_gcam,
                "tau_star_year": tau_year,
                "wedge_years": (tau_year - t_gcam) if tau_year is not None else None,
                "tau_star_year_wacc_eq": tau_year_eq,
                "wedge_years_wacc_eq": (tau_year_eq - t_gcam) if tau_year_eq is not None else None,
            }
        )

    write_artifact(
        "tau_star",
        {"base_year": base_year, "p_bind_in_exercise": p_bind_flag, "assets": tau_rows},
        cal.param_status,
        uses=["carbon_base_kr", "carbon_base_jp", "routes_sensitivity", "firms_registry"],
        note="LSM 사적 최적 전환연도 — 예산 없는 measure (A2); drift 0 평탄 기대경로",
    )
    write_artifact(
        "wedge",
        {"t_gcam_source": cal.t_gcam_source, "assets": wedge_rows},
        cal.param_status,
        uses=["carbon_base_kr", "carbon_base_jp", "routes_sensitivity", "firms_registry"],
        note="Exposure_i = τ*_i − T_i^GCAM (#claim-wedge-conjunction); Fig 2 덤벨 + WACC-equalized",
    )

    # σ_B 선형성: 대표 자산(첫 priced_route)에서 σ 스케일 격자 → 옵션가치 회귀 R²
    rep = cal.firms[cal.firms["category"] == "priced_route"].iloc[0].to_dict()
    n_grid = int(cal.lsm["sigma_linearity_n"])
    # 스케일 범위 = 캘리브레이션 band가 함의하는 상대 폭 (선형 근사의 유효 영역)
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
        uses=["routes_sensitivity"],
        note="옵션가치의 σ 선형성 — π=k·λ·p_bind·σ_B 선형 근사의 수치 근거 (§3.4 R² 체크)",
    )
    print(f"OK — τ*/wedge {len(tau_rows)} assets, σ-linearity R²={r2:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
