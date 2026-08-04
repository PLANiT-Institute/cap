"""s13: explicit condition-gap -> loss-distribution -> risk-charge bridge.

The physical gap remains produced by s07.  This stage values that gap under the
country carbon-scenario table and emits a separate, provisional result basis.
It does not add the result to s04 transition-cost anatomy because their joint
covariance has not been identified.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import PROVISIONAL, claim, write_artifact  # noqa: E402
from model.lib.gap_pricing import price_alignment_gap  # noqa: E402
from model.lib.result_contract import (  # noqa: E402
    ALIGNMENT_GAP_LOSS_BASIS,
    ALIGNMENT_GAP_LOSS_METRIC,
    ALIGNMENT_GAP_RISK_CHARGE_METRIC,
    result_descriptor,
)
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402
from model.s07_pathways import build as build_pathways  # noqa: E402

GAP_PRICE_DEPS = [
    "firms_registry",
    "t_required",
    "scenarios",
    "carbon_base_kr",
    "carbon_base_jp",
    "lambda",
    "k",
    "ev_usd_bn",
]


def build(cal: CalibrationSet, gaps: dict | None = None) -> dict:
    if gaps is None:
        _, gaps = build_pathways(cal)
    base_year = float(cal.lsm["base_year"])
    horizon = float(cal.lsm["horizon_years"])
    years = np.arange(int(base_year), int(base_year + horizon) + 1)
    firms = []

    for gap in gaps["firms"]:
        firm_id = gap["firm_id"]
        g = cal.firms[cal.firms["firm_id"] == firm_id]
        country = str(g["country"].iloc[0])
        rate = float(g["wacc"].iloc[0])
        ev_usd_bn = float(g["ev_usd_bn"].iloc[0])
        result = price_alignment_gap(
            np.asarray(gap["annual_alignment_gap_mtco2"], dtype=float),
            years,
            base_year=base_year,
            rate=rate,
            horizon_years=horizon,
            reference_price_usd_tco2=float(
                cal.pricing[f"carbon_base_{country.lower()}"]
            ),
            scenarios=cal.carbon_scenarios(country),
            risk_price_lambda=float(cal.pricing["lambda"]),
            risk_scale_k=float(cal.pricing["k"]),
            enterprise_value_usd_bn=ev_usd_bn,
        )
        firms.append(
            {
                "firm_id": firm_id,
                "firm": gap["firm"],
                "sector": str(g["sector"].iloc[0]),
                "country": country,
                "cumulative_alignment_gap_mtco2": gap[
                    "cumulative_alignment_gap_mtco2"
                ],
                "loss_result_contract": result_descriptor(
                    ALIGNMENT_GAP_LOSS_METRIC,
                    ALIGNMENT_GAP_LOSS_BASIS,
                    "PROVISIONAL",
                    uncertainty=(
                        "surrogate required pathway, private transition model, carbon scenario "
                        "levels/probabilities and constant scenario price over the horizon"
                    ),
                    interpretation="reduced-form PV loss distribution implied by the physical gap",
                ),
                "risk_result_contract": result_descriptor(
                    ALIGNMENT_GAP_RISK_CHARGE_METRIC,
                    ALIGNMENT_GAP_LOSS_BASIS,
                    "PROVISIONAL",
                    uncertainty="loss distribution plus assumed lambda and k",
                    interpretation=(
                        "gap-linked charge on its own basis; not additive to transition-cost charge"
                    ),
                ),
                **result,
            }
        )

    return {
        "formula": "PV_loss_j = sum_t DF_t * G_t * max(P_j - P_reference, 0)",
        "status": "PROVISIONAL",
        "aggregation_warning": (
            "Gap-linked and transition-cost charges are alternative result bases. "
            "Do not sum them until their covariance and joint state model are specified."
        ),
        "firms": firms,
    }


def main() -> int:
    cal = load_calibration()
    data = build(cal)
    write_artifact(
        "alignment_gap_loss",
        data,
        cal.param_status,
        claims={
            "firms.expected_pv_gap_loss_usd_m": claim(
                PROVISIONAL,
                GAP_PRICE_DEPS,
                "physical gap mapped to the unconditional country scenario-loss distribution",
            ),
            "firms.gap_risk_charge_bps": claim(
                PROVISIONAL,
                GAP_PRICE_DEPS,
                "lambda*k*sigma(PV gap loss), annualized; p_bind is not multiplied twice",
            ),
        },
        note=(
            "Explicit gap-to-loss bridge. Separate from transition-cost anatomy pending a joint "
            "state/covariance model."
        ),
        sector_enabled=cal.sector_enabled,
    )
    print(f"OK — alignment-gap loss bridge for {len(data['firms'])} firms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
