"""s06: intervention impacts — 개입이 τ*·경로·anatomy·수준을 일관되게 바꾼다.

각 intervention에 대해 (reform-priced 관점, 국가별 regime):
- τ* before/after (자산별 + 용량가중)
- timing gap·cumulative emissions gap before/after (lib/pathways)
- residual risk anatomy before/after — coverage·tenor·basis 반영, 근거 없는 0 금지
- conditional risk charge before/after + residual unhedged
- standalone / sequential(package 순서) / order-averaged(Shapley) 기여
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.anatomy import DRIVERS  # noqa: E402
from model.lib.artifacts import MODEL_CONDITIONAL, SCENARIO_CONDITIONAL, claim, write_artifact  # noqa: E402
from model.lib.interventions import apply_interventions  # noqa: E402
from model.lib.pathways import condition_gap, firm_pathway  # noqa: E402
from model.lib.result_contract import (  # noqa: E402
    ALIGNMENT_GAP_BASIS,
    ALIGNMENT_GAP_METRIC,
    ENTERPRISE_RISK_BASIS,
    RISK_CHARGE_METRIC,
    result_descriptor,
)
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402
from model.s04_anatomy import ANATOMY_DEPS, anatomy_for, firm_exposures, firm_frame  # noqa: E402

OUT = ROOT / "outputs"


def firm_state(
    cal: CalibrationSet, firm_id: str, tau_map: dict | None, ids: list[str], basis_case: str = "lo"
) -> dict:
    """한 기업의 (anatomy, charge, gap) 상태 — 개입 ids 적용.

    basis_case="hi"는 계약 잔여 basis를 문헌 최악(Peña 외 2024)으로 두고 다시 푼다.
    """
    frame = firm_frame(cal, tau_map=tau_map)
    g_all = frame[frame["firm_id"] == firm_id]
    g = g_all[g_all["category"] == "priced_route"]
    if g.empty:
        return {}
    ps = apply_interventions(
        cal, g["route"].iloc[0], g["country"].iloc[0], g["elec_driver"].iloc[0], ids,
        basis_case=basis_case,
    )
    meta = firm_exposures(cal, g, ps=ps)
    an = anatomy_for(cal, meta, reform=True)  # 정책 점프 가격화 관점 (문서화)
    base_year = int(cal.lsm["base_year"])
    years = np.arange(base_year, base_year + int(cal.lsm["horizon_years"]) + 1)
    residual = dict(zip(cal.routes["route"], cal.routes["residual_intensity_tco2_t"]))
    priced_ids = set(g["asset_id"])
    pmap = dict(zip(g_all["asset_id"], g_all["tau_star_year"]))
    rmap = {a: cal.t_required[a]["year"] for a in g_all["asset_id"]}
    p_track = firm_pathway(g_all, {a: pmap.get(a) for a in priced_ids}, years, residual)
    r_track = firm_pathway(g_all, {a: rmap.get(a) for a in priced_ids}, years, residual)
    gap = condition_gap(p_track["emissions_mtco2"], r_track["emissions_mtco2"], years)
    tau_capw = float(np.average(g["tau_star_year"], weights=g["capacity_mt_yr"]))
    tg = [
        (t - rmap[a]) for a, t in zip(g["asset_id"], g["tau_star_year"]) if rmap.get(a) is not None
    ]
    return {
        "risk_result_contract": result_descriptor(
            RISK_CHARGE_METRIC,
            ENTERPRISE_RISK_BASIS,
            "SCENARIO_CONDITIONAL",
            uncertainty="lambda, k, scenarios, covariance and exposure calibration",
            interpretation="enterprise transition-window risk; not project-at-commissioning risk",
        ),
        "alignment_result_contract": result_descriptor(
            ALIGNMENT_GAP_METRIC,
            ALIGNMENT_GAP_BASIS,
            "PROVISIONAL" if cal.t_required_source == "surrogate" else "MODEL_CONDITIONAL",
            uncertainty="required pathway source and private transition model",
            interpretation="surrogate-conditioned central case" if cal.t_required_source == "surrogate" else "raw-pathway comparison",
        ),
        "tau_star_cap_weighted": tau_capw,
        "timing_gap_mean_years": float(np.mean(tg)) if tg else None,
        "cumulative_gap_mtco2": gap["cumulative_alignment_gap_mtco2"],
        "shares": an["shares"],
        "sigma_b_usd_bn": an["sigma_b_usd_bn"],
        "risk_charge_bps": an["premium_bps"],
        "double_count_warning": ps.double_count_warning,
    }


def main() -> int:
    cal = load_calibration()
    tau_art = json.loads((OUT / "tau_star.json").read_text())
    iv_tau = tau_art["interventions"]
    iv_ids = list(iv_tau.keys())
    package_row = cal.interventions.set_index("intervention_id").loc["package"]
    components = [c for c in str(package_row["components"]).split(";") if c]

    firms = sorted(set(cal.firms[cal.firms["category"] == "priced_route"]["firm_id"]))
    out_firms = []
    for fid in firms:
        before = firm_state(cal, fid, tau_map=None, ids=[])
        ivs = {}
        for iid in iv_ids:
            after = firm_state(cal, fid, tau_map=iv_tau[iid], ids=[iid])
            high = firm_state(cal, fid, tau_map=iv_tau[iid], ids=[iid], basis_case="hi")
            ivs[iid] = {
                "label": cal.interventions.set_index("intervention_id").loc[iid, "label"],
                "before": {k: before[k] for k in ("tau_star_cap_weighted", "timing_gap_mean_years",
                                                  "cumulative_gap_mtco2", "risk_charge_bps", "sigma_b_usd_bn")},
                "after": {k: after[k] for k in ("tau_star_cap_weighted", "timing_gap_mean_years",
                                                "cumulative_gap_mtco2", "risk_charge_bps", "sigma_b_usd_bn")},
                "delta": {
                    "tau_star_years": after["tau_star_cap_weighted"] - before["tau_star_cap_weighted"],
                    "cumulative_gap_mtco2": after["cumulative_gap_mtco2"] - before["cumulative_gap_mtco2"],
                    "risk_charge_bps": after["risk_charge_bps"] - before["risk_charge_bps"],
                    "risk_charge_bps_high_basis": high["risk_charge_bps"] - before["risk_charge_bps"],
                },
                "residual": {
                    "shares": after["shares"],
                    "sigma_b_usd_bn": after["sigma_b_usd_bn"],
                    "risk_charge_bps": after["risk_charge_bps"],
                    "risk_charge_bps_high_basis": high["risk_charge_bps"],
                    "note": "coverage·tenor·basis 반영 잔여 — 0으로 만들지 않음. "
                            "high_basis는 헤지 유효성 실측이 낮다는 문헌(Peña 외 2024)의 최악 경계",
                },
                "double_count_warning": after["double_count_warning"],
                "assumptions": cal.interventions.set_index("intervention_id").loc[iid, "notes"],
            }

        # sequential (package 구성 순서대로 누적) — 순서 의존성 명시
        seq = []
        prev_charge = before["risk_charge_bps"]
        for j in range(1, len(components) + 1):
            ids_j = components[:j]
            st = firm_state(cal, fid, tau_map=iv_tau["package"], ids=ids_j)
            seq.append({"after_ids": ids_j, "risk_charge_bps": st["risk_charge_bps"],
                        "cut_bps": prev_charge - st["risk_charge_bps"]})
            prev_charge = st["risk_charge_bps"]

        # order-averaged (Shapley) — risk charge 감축 기여, 2^n 부분집합
        shapley = {c: 0.0 for c in components}
        n = len(components)
        charge_cache: dict[frozenset, float] = {}

        def charge_of(subset: frozenset) -> float:
            if subset not in charge_cache:
                st = firm_state(cal, fid, tau_map=iv_tau["package"] if subset else None,
                                ids=sorted(subset))
                charge_cache[subset] = st["risk_charge_bps"]
            return charge_cache[subset]

        for c in components:
            others = [x for x in components if x != c]
            for r in range(len(others) + 1):
                for combo in itertools.combinations(others, r):
                    s = frozenset(combo)
                    weight = (
                        float(math.factorial(r) * math.factorial(n - r - 1))
                        / float(math.factorial(n))
                    )
                    shapley[c] += weight * (charge_of(s) - charge_of(s | {c}))

        out_firms.append(
            {
                "firm_id": fid,
                "before": before,
                "interventions": ivs,
                "sequential_package": {
                    "order": components,
                    "steps": seq,
                    "note": "순차 소거는 적용 순서에 따라 배분이 달라진다 — order-averaged 참조",
                },
                "order_averaged_contribution_bps": shapley,
            }
        )

    write_artifact(
        "intervention_impacts",
        {"interventions": iv_ids, "firms": out_firms,
         "perspective": "reform-priced (국가별 σ_reform 관점)"},
        cal.param_status,
        claims={
            "firms.interventions.delta": claim(
                MODEL_CONDITIONAL, ANATOMY_DEPS + ["interventions"],
                "coverage·tenor 1차 근사; τ*·경로·anatomy·수준 동시 재계산",
            ),
            "firms.interventions.residual.risk_charge_bps_high_basis": claim(
                SCENARIO_CONDITIONAL, ANATOMY_DEPS + ["interventions", "lambda", "k", "ev_usd_bn"],
                "basis_sigma_hi(문헌 최악) 하 잔여 — Δπ를 밴드로 읽을 것",
            ),
            "firms.interventions.residual.risk_charge_bps": claim(
                SCENARIO_CONDITIONAL, ANATOMY_DEPS + ["interventions", "lambda", "k", "ev_usd_bn"],
                "잔여 conditional risk charge — fully-hedged 0 주장 금지",
            ),
        },
        note="개입 = 파라미터 변환: τ* before/after, gap before/after, residual anatomy, charge",
    )
    for f in out_firms:
        pk = f["interventions"].get("package", {})
        if pk:
            print(
                f"{f['firm_id']:8s} package: Δτ*={pk['delta']['tau_star_years']:+.1f}y "
                f"Δgap={pk['delta']['cumulative_gap_mtco2']:+.1f}Mt "
                f"charge {pk['before']['risk_charge_bps']:.1f}→{pk['after']['risk_charge_bps']:.1f}bps"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
