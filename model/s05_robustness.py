"""s05: robustness — share envelope, λ×p_bind 불변성, 클러스터 분리, λ_k 감응도.

- share_envelopes: σ·ρ band 내 draw(n_band_draws) → 기업별 driver share의 분포 포락
  (노출 E는 base 고정 — envelope은 공분산 불확실성만 반영; τ* 재계산 없음, LEDGER 표기)
- lambda_invariance: λ×p_bind 격자에서 share 벡터 불변(소수점 6자리) + 수준 스윙 (Prop 1 데모)
- cluster_separation: band draw 전체에서 두 클러스터 carbon share 구간의 불교차 여부 (A4 절반은 배정)
- lambda_k_sensitivity: driver별 λ_k 허용 시 share 이동 (R1 대응 — A5 공리의 스트레스)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.anatomy import DRIVERS, euler_shares, lambda_k_shares, risk_charge_annual_usd  # noqa: E402
from model.lib.artifacts import IDENTITY, MODEL_CONDITIONAL, SCENARIO_CONDITIONAL, claim, write_artifact  # noqa: E402
from model.lib.finance import nearest_psd  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402
from model.s04_anatomy import ANATOMY_DEPS, BPS, anatomy_for, firm_exposures, firm_frame  # noqa: E402

SHARE_DECIMALS = 6  # Prop 1 데모 판정 자릿수 (논문 서술 단위)


def band_draw(cal: CalibrationSet, rng: np.random.Generator, elec_driver: str):
    """σ·ρ를 band 내 균등 draw — ρ는 PSD 사영."""
    sig_tbl = cal.sigmas.set_index("driver")
    def draw_sigma(d):
        lo, hi = float(sig_tbl.loc[d, "band_lo"]), float(sig_tbl.loc[d, "band_hi"])
        return rng.uniform(lo, hi)
    sig = np.array([
        draw_sigma("carbon_diffusion"),
        draw_sigma("h2"),
        draw_sigma(elec_driver),
        draw_sigma("feedstock"),
        draw_sigma("capex"),
    ])
    rho = np.eye(len(DRIVERS))
    for _, r in cal.correlations.iterrows():
        try:
            i, j = DRIVERS.index(r["driver_i"]), DRIVERS.index(r["driver_j"])
        except ValueError:
            continue
        v = rng.uniform(float(r["band_lo"]), float(r["band_hi"]))
        rho[i, j] = rho[j, i] = v
    return sig, nearest_psd(rho)


def main() -> int:
    cal = load_calibration()
    rng = np.random.default_rng(int(cal.lsm["seed"]))
    frame = firm_frame(cal)
    priced = frame[frame["category"] == "priced_route"]
    metas = {fid: firm_exposures(cal, g) for fid, g in priced.groupby("firm_id", sort=True)}

    n_draws = int(cal.lsm["n_band_draws"])
    draws: dict[str, list[np.ndarray]] = {fid: [] for fid in metas}
    for _ in range(n_draws):
        for fid, meta in metas.items():
            sig, rho = band_draw(cal, rng, meta["elec_driver"])
            _, shares = euler_shares(meta["E"] * sig, rho)
            draws[fid].append(shares)

    envelopes = []
    for fid, meta in metas.items():
        arr = np.array(draws[fid])
        envelopes.append(
            {
                "firm_id": fid,
                "firm": meta["firm"],
                "cluster": {
                    "h2_dri": "h2_route",
                    "e_cracker": "electric_route",
                    "ccus_cracker": "capture_route",
                    "circular_olefins": "feedstock_route",
                }.get(meta["route"], "grid_route"),
                "envelope": {
                    d: {
                        "lo": float(arr[:, i].min()),
                        "hi": float(arr[:, i].max()),
                        "median": float(np.median(arr[:, i])),
                    }
                    for i, d in enumerate(DRIVERS)
                },
            }
        )
    write_artifact(
        "share_envelopes",
        {"n_draws": n_draws, "firms": envelopes},
        cal.param_status,
        claims={"firms.envelope": claim(MODEL_CONDITIONAL, ANATOMY_DEPS,
                                        "노출 E base 고정 — 공분산 불확실성만; τ* 재계산 없음")},
        note="σ·ρ band draw 포락 — share가 캘리브레이션에 조건부임을 그대로 보여주는 장치",
    )

    # λ×p_bind 격자 — 수준 스윙 + share 불변성
    lam_grid = np.linspace(cal.lsm["lambda_grid_lo"], cal.lsm["lambda_grid_hi"], int(cal.lsm["lambda_grid_n"]))
    pb_grid = np.linspace(cal.lsm["p_bind_grid_lo"], cal.lsm["p_bind_grid_hi"], int(cal.lsm["p_bind_grid_n"]))
    horizon = float(cal.lsm["horizon_years"])
    grid_rows = []
    max_share_dev = 0.0
    for fid, meta in metas.items():
        base = anatomy_for(cal, meta, reform=False)
        base_shares = np.array([base["shares"][d] for d in DRIVERS])
        for lam in lam_grid:
            for pb in pb_grid:
                # share는 (a,σ,ρ)만의 함수 — λ·p_bind에 재계산해도 동일해야 함 (P1)
                sig, rho = cal.rho_matrix(meta["elec_driver"])
                _, shares = euler_shares(meta["E"] * sig, rho)
                dev = float(np.max(np.abs(shares - base_shares)))
                max_share_dev = max(max_share_dev, dev)
                pi = (
                    risk_charge_annual_usd(
                        cal.pricing["k"], lam, pb, base["sigma_b_usd_bn"],
                        meta["wacc"], horizon,
                    )
                    / meta["ev_usd_bn"] * BPS
                )
                grid_rows.append({"firm_id": fid, "lambda": float(lam), "p_bind": float(pb), "premium_bps": pi})
    levels = [r["premium_bps"] for r in grid_rows]
    write_artifact(
        "lambda_invariance",
        {
            "grid": grid_rows,
            "level_min_bps": float(min(levels)),
            "level_max_bps": float(max(levels)),
            "max_share_deviation": max_share_dev,
            "share_invariant_to_decimals": int(SHARE_DECIMALS) if max_share_dev < 10 ** -SHARE_DECIMALS else 0,
        },
        cal.param_status,
        claims={
            "max_share_deviation": claim(IDENTITY, [],
                                         "고정 노출·공분산 아래 scalar λ·p_bind 소거 — 동차성 항등 (P1의 전부)"),
            "grid.premium_bps": claim(SCENARIO_CONDITIONAL, ANATOMY_DEPS + ["k", "ev_usd_bn"],
                                      "가상 λ×p_bind 격자 위 conditional risk charge"),
        },
        note="P1 데모 — 고정 exposure에서 share 불변, 수준만 스윙. anatomy 전체의 calibration 독립 주장 아님",
    )

    # 클러스터 분리 (band draw 기반)
    h2_carbon = np.concatenate([
        np.array(draws[f])[:, 0]
        for f, m in metas.items()
        if m["sector"] == "steel" and m["route"] == "h2_dri"
    ])
    grid_carbon = np.concatenate([
        np.array(draws[f])[:, 0]
        for f, m in metas.items()
        if m["sector"] == "steel" and m["route"] != "h2_dri"
    ])
    write_artifact(
        "cluster_separation",
        {
            "h2_route_carbon_share": {"lo": float(h2_carbon.min()), "hi": float(h2_carbon.max())},
            "grid_route_carbon_share": {"lo": float(grid_carbon.min()), "hi": float(grid_carbon.max())},
            "separated": bool(h2_carbon.max() < grid_carbon.min()),
            "gap": float(grid_carbon.min() - h2_carbon.max()),
        },
        cal.param_status,
        claims={"separated": claim(MODEL_CONDITIONAL, ANATOMY_DEPS,
                                   "절반은 A4 배정의 귀결 — route 감응도 0 구성")},
        note="두 클러스터 불교차 — 은폐하지 않음",
    )

    # λ_k 감응도 (R1): driver별 위험가격 허용 시 share 이동
    lam_k = np.array([cal.lsm[f"lambda_k_{d}"] for d in DRIVERS])
    lam_rows = []
    for fid, meta in metas.items():
        sig, rho = cal.rho_matrix(meta["elec_driver"])
        w = meta["E"] * sig
        _, uniform = euler_shares(w, rho)
        shifted = lambda_k_shares(w, rho, lam_k)
        lam_rows.append(
            {
                "firm_id": fid,
                "shares_uniform_lambda": dict(zip(DRIVERS, uniform.tolist())),
                "shares_lambda_k": dict(zip(DRIVERS, shifted.tolist())),
                "max_shift": float(np.max(np.abs(shifted - uniform))),
            }
        )
    write_artifact(
        "lambda_k_sensitivity",
        {"lambda_k": dict(zip(DRIVERS, lam_k.tolist())), "firms": lam_rows},
        cal.param_status,
        claims={"firms": claim(MODEL_CONDITIONAL, ANATOMY_DEPS + ["lambda"],
                               "A5 깨질 때 share 이동 — P1이 scalar 공통 λ에만 성립함을 보이는 스트레스")},
        note="R1 대응 λ_k 감응도",
    )
    print(
        f"OK — envelope {n_draws} draws, λ-grid share max dev {max_share_dev:.2e}, "
        f"levels {min(levels):.2f}–{max(levels):.2f} bps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
