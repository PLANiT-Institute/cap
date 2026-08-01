"""Reduced-form pricing bridge from the physical alignment gap to loss risk.

The bridge implements the lineage equation documented in the knowledge base:

    PV loss_j = sum_t DF_t * G_t * max(P_j - P_reference, 0)

where G_t is the annual private-minus-required emissions gap and j indexes the
country carbon scenarios.  Scenario probabilities are used once to form the
unconditional loss distribution; ``p_bind`` is therefore *not* multiplied a
second time.

This is deliberately a separate result basis from transition-cost anatomy.
Without a covariance model the two risk charges cannot be added defensibly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .finance import annuity

MT_TO_T = 1e6
BPS = 1e4


def discounted_gap_tco2(
    annual_gap_mtco2: np.ndarray,
    years: np.ndarray,
    base_year: float,
    rate: float,
) -> float:
    """Present-value quantity of an annual emissions gap, in discounted tCO2."""
    gap = np.asarray(annual_gap_mtco2, dtype=float)
    yrs = np.asarray(years, dtype=float)
    if gap.shape != yrs.shape:
        raise ValueError("annual gap and years must have identical shapes")
    if np.any(gap < 0):
        raise ValueError("annual alignment gap cannot be negative")
    periods = yrs - float(base_year) + 1.0  # annual flow paid at each year-end
    if np.any(periods <= 0):
        raise ValueError("years must not precede the model base year")
    discount = (1.0 + float(rate)) ** (-periods)
    return float(np.dot(gap * MT_TO_T, discount))


def price_alignment_gap(
    annual_gap_mtco2: np.ndarray,
    years: np.ndarray,
    *,
    base_year: float,
    rate: float,
    horizon_years: float,
    reference_price_usd_tco2: float,
    scenarios: pd.DataFrame,
    risk_price_lambda: float,
    risk_scale_k: float,
    enterprise_value_usd_bn: float,
) -> dict:
    """Map an annual physical gap to a scenario loss distribution and charge.

    The scenario table supplies ``level_usd``, ``prob`` and ``binds``.  The
    incremental price is floored at zero because this lane values adverse
    repricing of excess emissions, not a windfall when a scenario price is
    below the dated reference price.
    """
    required = {"scenario", "level_usd", "prob", "binds"}
    missing = required.difference(scenarios.columns)
    if missing:
        raise ValueError(f"carbon scenarios missing columns: {sorted(missing)}")

    probs = scenarios["prob"].to_numpy(float)
    if np.any(probs < 0) or not np.isclose(probs.sum(), 1.0):
        raise ValueError("carbon scenario probabilities must be nonnegative and sum to one")

    pv_gap_tco2 = discounted_gap_tco2(annual_gap_mtco2, years, base_year, rate)
    levels = scenarios["level_usd"].to_numpy(float)
    incremental = np.maximum(levels - float(reference_price_usd_tco2), 0.0)
    losses = pv_gap_tco2 * incremental
    mean_loss = float(np.dot(probs, losses))
    sigma_loss = float(np.sqrt(np.dot(probs, (losses - mean_loss) ** 2)))
    annual_charge = (
        float(risk_scale_k)
        * float(risk_price_lambda)
        * sigma_loss
        / annuity(float(rate), float(horizon_years))
    )
    ev_usd = float(enterprise_value_usd_bn) * 1e9

    rows = []
    for (_, row), delta, loss in zip(scenarios.iterrows(), incremental, losses):
        rows.append(
            {
                "scenario": str(row["scenario"]),
                "probability": float(row["prob"]),
                "binds": bool(row["binds"]),
                "level_usd_tco2": float(row["level_usd"]),
                "incremental_price_usd_tco2": float(delta),
                "pv_gap_loss_usd_m": float(loss / 1e6),
            }
        )

    return {
        "discounted_gap_mtco2": pv_gap_tco2 / MT_TO_T,
        "reference_price_usd_tco2": float(reference_price_usd_tco2),
        "scenario_losses": rows,
        "expected_pv_gap_loss_usd_m": mean_loss / 1e6,
        "sigma_pv_gap_loss_usd_m": sigma_loss / 1e6,
        "annual_gap_risk_charge_usd_m": annual_charge / 1e6,
        "gap_risk_charge_bps": annual_charge / ev_usd * BPS if ev_usd > 0 else None,
        "probability_treatment": (
            "unconditional scenario distribution; p_bind is embedded in scenario probabilities "
            "and is not multiplied again"
        ),
        "aggregation_rule": (
            "separate basis; do not add to transition-cost charge without an explicit covariance"
        ),
    }
