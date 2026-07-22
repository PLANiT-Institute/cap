"""s06: 계약 = identification device (§05 #claim-separately-contractible).

waterfall: 실재 상품으로 driver를 순차 소거 —
H₂ CfD(CHPS) → σ_h2=0, carbon CfD → σ_carbon=0, PPA → σ_elec=0, 자본보조 → σ_capex=0.
각 단계의 σ_B·π 잔여를 기록. Δπ = π(미확약) − π(전계약) > 0.
"어느 계약이 가장 많이 깎는가"는 따름정리 — waterfall의 역할은 처방이 아니라 식별.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.anatomy import DRIVERS, euler_shares  # noqa: E402
from model.lib.artifacts import write_artifact  # noqa: E402
from model.lib.finance import annuity  # noqa: E402
from model.s02_calibrate import load_calibration  # noqa: E402
from model.s04_anatomy import BPS, firm_exposures, firm_frame  # noqa: E402

CONTRACTS = [
    ("h2_cfd", "h2", "H₂ CfD (CHPS-style)"),
    ("carbon_cfd", "carbon", "Carbon CfD (tail truncation)"),
    ("ppa", "elec", "PPA (power fixed)"),
    ("capex_subsidy", "capex", "Capital subsidy (CAPEX fixed)"),
]


def main() -> int:
    cal = load_calibration()
    frame = firm_frame(cal)
    priced = frame[frame["category"] == "priced_route"]
    horizon = float(cal.lsm["horizon_years"])
    k, lam, pb = cal.pricing["k"], cal.pricing["lambda"], cal.pricing["p_bind"]

    waterfalls, ranking = [], []
    for fid, g in priced.groupby("firm_id", sort=True):
        meta = firm_exposures(cal, g)
        scale = meta["capacity_mt"] * 1e6 / 1e9  # USD/t → USD bn

        def run_waterfall(rho: np.ndarray, sig: np.ndarray) -> list[dict]:
            def pi_of(sig_vec: np.ndarray) -> tuple[float, float]:
                sigma_b, _ = euler_shares(meta["E"] * sig_vec, rho)
                bn = sigma_b * scale
                return bn, k * lam * pb * bn / annuity(meta["wacc"], horizon) / meta["ev_usd_bn"] * BPS

            sig_now = sig.copy()
            sigma0_bn, pi0 = pi_of(sig_now)
            steps = [{"step": "uncommitted", "label": "Uncommitted", "sigma_b_usd_bn": sigma0_bn,
                      "premium_bps": pi0, "cut_bps": 0.0}]
            prev = pi0
            for step_id, driver, label in CONTRACTS:
                sig_now[DRIVERS.index(driver)] = 0.0
                bn, pi = pi_of(sig_now)
                steps.append({"step": step_id, "label": label, "sigma_b_usd_bn": bn,
                              "premium_bps": pi, "cut_bps": prev - pi})
                prev = pi
            return steps

        sig_base, rho = cal.rho_matrix(meta["elec_driver"])
        sig_reform, _ = cal.rho_matrix(meta["elec_driver"], carbon_sigma=cal.sigma_carbon_reform)
        steps = run_waterfall(rho, sig_base)
        steps_reform = run_waterfall(rho, sig_reform)
        pi0, prev = steps[0]["premium_bps"], steps[-1]["premium_bps"]
        waterfalls.append({"firm_id": fid, "firm": meta["firm"], "route": meta["route"],
                           "steps": steps, "steps_reform": steps_reform})
        ranking.append({"firm_id": fid, "firm": meta["firm"], "pi_uncommitted_bps": pi0,
                        "pi_committed_bps": prev, "delta_pi_bps": pi0 - prev})

    ranking.sort(key=lambda r: -r["delta_pi_bps"])
    uses = ["lambda", "p_bind", "k", "ev_usd_bn", "scenarios"]
    write_artifact(
        "waterfall",
        {"contracts": [{"step": s, "driver": d, "label": l} for s, d, l in CONTRACTS], "firms": waterfalls},
        cal.param_status,
        uses=uses,
        note="Fig 6 — 계약별 순차 소거 waterfall. 개별 계약 가능성이 분해의 식별 장치 (§05)",
    )
    write_artifact(
        "delta_pi_ranking",
        {"ranking": ranking},
        cal.param_status,
        uses=uses,
        note="Δπ = π(미확약) − π(확약) > 0 — 전환의 재무가치, 수준은 λ·p_bind 조건부",
    )
    for r in ranking:
        print(f"{r['firm_id']:8s} Δπ={r['delta_pi_bps']:.1f}bps ({r['pi_uncommitted_bps']:.1f}→{r['pi_committed_bps']:.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
