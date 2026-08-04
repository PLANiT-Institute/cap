"""s07: 감축경로 — 인과사슬의 원인층 (개편 §2).

기업별 4+N 경로 (전부 자산별 계산 → 합산):
  BAU / private(τ*) / required(T_required) / intervention별(τ*(C))
+ condition gap 지표 (timing gap, cumulative excess emissions gap 등).

required가 surrogate면 경로·지표에 PROVISIONAL이 붙는다 —
"Required pathway is a provisional surrogate and must not be interpreted as
an empirically identified firm mandate."
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import MODEL_CONDITIONAL, PROVISIONAL, claim, write_artifact  # noqa: E402
from model.lib.pathways import condition_gap, firm_pathway, required_firm_pathway  # noqa: E402
from model.lib.result_contract import (  # noqa: E402
    ALIGNMENT_GAP_BASIS,
    ALIGNMENT_GAP_METRIC,
    result_descriptor,
)
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402

OUT = ROOT / "outputs"

PATH_DEPS = ["firms_registry", "routes_sensitivity", "t_required", "exposure_model"]


def switch_maps(cal: CalibrationSet) -> tuple[dict, dict, dict[str, dict]]:
    """(private, required, interventions) — asset_id → 전환연도 or None."""
    tau_art = json.loads((OUT / "tau_star.json").read_text())
    private = {a["asset_id"]: a["tau_star_year"] for a in tau_art["assets"]}
    required = {aid: t["year"] for aid, t in cal.t_required.items()}
    interventions = {
        iid: dict(m)
        for iid, m in tau_art["interventions"].items()
    }
    return private, required, interventions


def build(cal: CalibrationSet) -> tuple[dict, dict]:
    base_year = int(cal.lsm["base_year"])
    years = np.arange(base_year, base_year + int(cal.lsm["horizon_years"]) + 1)
    residual = dict(zip(cal.routes["route"], cal.routes["residual_intensity_tco2_t"]))
    private, _required, interventions = switch_maps(cal)
    prov = cal.required_path_provisional

    pathways_out: dict = {
        "base_year": base_year,
        "years": years.tolist(),
        "t_required_source": cal.t_required_source,
        "required_disclaimer": (
            "Required pathway is a provisional surrogate and must not be interpreted "
            "as an empirically identified firm mandate."
            if prov else "Required pathway from GCAM raw output."
        ),
        "firms": [],
    }
    gaps_out: dict = {"firms": [], "t_required_source": cal.t_required_source}

    def series(track: dict, base0: float) -> dict:
        e = track["emissions_mtco2"]
        return {
            "emissions_mtco2": e.tolist(),
            "emissions_index_base100": (e / base0 * 100.0).tolist(),
            "cumulative_emissions_mtco2": track["cumulative_mtco2"].tolist(),
            "transitioned_capacity_mt": track["transitioned_capacity_mt"].tolist(),
        }

    for firm_id, g in cal.firms.groupby("firm_id", sort=True):
        # BAU는 stranding 포함 전 자산 미전환; private/required는 priced 자산만 전환
        bau = firm_pathway(g, {}, years, residual)
        base0 = float(bau["emissions_mtco2"][0])
        priced_ids = set(g[g["category"] == "priced_route"]["asset_id"])
        pmap = {a: private.get(a) for a in priced_ids}
        p_track = firm_pathway(g, pmap, years, residual)
        # S3: required는 풀 연속 q(t) — 자산 배정 계단이 아님 (사적 경로는 계단 유지)
        r_track = required_firm_pathway(g, years, residual, cal.t_required, cal.required_pool_paths)
        gap = condition_gap(p_track["emissions_mtco2"], r_track["emissions_mtco2"], years)

        ivs = {}
        for iid, imap in interventions.items():
            iv_track = firm_pathway(g, {a: imap.get(a) for a in priced_ids}, years, residual)
            iv_gap = condition_gap(iv_track["emissions_mtco2"], r_track["emissions_mtco2"], years)  # 동일 r_track
            ivs[iid] = {
                **series(iv_track, base0),
                "cumulative_alignment_gap_mtco2": iv_gap["cumulative_alignment_gap_mtco2"],
                "status": "MODEL_CONDITIONAL",
            }

        asset_gaps = []
        cap_w, gap_w = 0.0, 0.0
        for _, a in g.iterrows():
            aid = a["asset_id"]
            tr = cal.t_required[aid]
            tau = private.get(aid)
            tg = (tau - tr["year"]) if (tau is not None and tr["year"] is not None) else None
            asset_gaps.append(
                {
                    "asset_id": aid,
                    "facility": f"{a['facility']} {a['unit_number']}",
                    "capacity_mt": float(a["capacity_mt_yr"]),
                    "intensity_tco2_t": float(a["emission_intensity_tco2_t"]),
                    "route": a["route"],
                    "category": a["category"],
                    "tau_star_year": tau,
                    "t_required": tr["year"],
                    "t_required_status": tr["status"],
                    "t_required_pathway_kind": tr["pathway_kind"],
                    "t_required_headline_eligible": tr["headline_eligible"],
                    "timing_gap_years": tg,
                }
            )
            if tg is not None:
                cap_w += float(a["capacity_mt_yr"])
                gap_w += tg * float(a["capacity_mt_yr"])

        pathways_out["firms"].append(
            {
                "firm_id": firm_id,
                "firm": g["firm"].iloc[0],
                "sector": g["sector"].iloc[0],
                "country": g["country"].iloc[0],
                "pathways": {
                    "bau": {**series(bau, base0), "status": "MODEL_CONDITIONAL",
                            "assumptions": "현행 설비·강도 유지, 폐쇄·전환 없음 (명시적 기준선)"},
                    "private": {**series(p_track, base0), "status": "MODEL_CONDITIONAL",
                                "assumptions": "자산별 τ* (LSM)"},
                    "required": {**series(r_track, base0),
                                 "status": "PROVISIONAL" if prov else "EMPIRICAL",
                                 "assumptions": "풀 연속 q(t) pro-rata (S3; surrogate 시 PROVISIONAL)"},
                    "interventions": ivs,
                },
            }
        )
        gaps_out["firms"].append(
            {
                "result_contract": result_descriptor(
                    ALIGNMENT_GAP_METRIC,
                    ALIGNMENT_GAP_BASIS,
                    "PROVISIONAL" if prov else "MODEL_CONDITIONAL",
                    uncertainty="required pathway source and private transition model",
                    interpretation="surrogate-conditioned central case" if prov else "raw-pathway comparison",
                ),
                "firm_id": firm_id,
                "firm": g["firm"].iloc[0],
                "sector": g["sector"].iloc[0],
                "assets": asset_gaps,
                "capacity_weighted_timing_gap_years": (gap_w / cap_w) if cap_w else None,
                "cumulative_alignment_gap_mtco2": gap["cumulative_alignment_gap_mtco2"],
                "peak_annual_gap_mtco2": gap["peak_annual_gap_mtco2"],
                "first_misalignment_year": gap["first_misalignment_year"],
                "alignment_restored_year": gap["alignment_restored_year"],
                "annual_alignment_gap_mtco2": gap["annual_alignment_gap_mtco2"].tolist(),
                "cumulative_gap_by_year_mtco2": np.cumsum(gap["annual_alignment_gap_mtco2"]).tolist(),
            }
        )
    return pathways_out, gaps_out


def main() -> int:
    cal = load_calibration()
    pathways, gaps = build(cal)
    prov_claim = PROVISIONAL if cal.t_required_source == "surrogate" else MODEL_CONDITIONAL
    write_artifact(
        "emissions_pathways_by_firm",
        pathways,
        cal.param_status,
        claims={
            "firms.pathways.bau": claim(MODEL_CONDITIONAL, PATH_DEPS),
            "firms.pathways.private": claim(MODEL_CONDITIONAL, PATH_DEPS + ["carbon_base_kr", "carbon_base_jp"]),
            "firms.pathways.required": claim(prov_claim, PATH_DEPS,
                                             "surrogate — 실증 식별된 기업 의무 아님"),
            "firms.pathways.interventions": claim(MODEL_CONDITIONAL, PATH_DEPS + ["interventions"]),
        },
        note="인과사슬의 원인층 — 자산별 연간 배출, 기업 합산",
    )
    write_artifact(
        "condition_gap",
        gaps,
        cal.param_status,
        claims={
            "firms.cumulative_alignment_gap_mtco2": claim(
                prov_claim, PATH_DEPS, "핵심 상태 변수 — 용량·강도 반영 누적 초과배출"
            ),
        },
        note="condition gap — timing gap + cumulative excess emissions",
    )
    for f in gaps["firms"]:
        print(
            f"{f['firm_id']:8s} cum_gap={f['cumulative_alignment_gap_mtco2']:7.1f} MtCO₂ "
            f"cap-w timing={f['capacity_weighted_timing_gap_years'] and round(f['capacity_weighted_timing_gap_years'],1)}y "
            f"first_misalign={f['first_misalignment_year']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
