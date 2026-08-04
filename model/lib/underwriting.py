"""Transition-risk underwriting helpers.

The paper's core object is a technology-contingent risk allocation problem:
technology chooses exposures, and contracts transform those exposures.  This
module translates the existing anatomy and conditional risk charge into
decision-useful underwriting quantities without relabelling them as observed
market prices.

All values remain conditional on the same calibration used by the model.  Unit
conversion constants below are not behavioural parameters.
"""
from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

BPS_PER_UNIT = 1e4
MILLION_PER_BILLION = 1e3


def dominant_driver(shares: Mapping[str, float]) -> str:
    """Return the largest Euler risk contributor."""
    if not shares:
        return "unavailable"
    return max(shares, key=shares.__getitem__)


def annual_charge_usd_m(spread_bps: float, enterprise_value_usd_bn: float) -> float:
    """bps on EV -> annual USD million risk-charge equivalent."""
    return float(spread_bps) / BPS_PER_UNIT * float(enterprise_value_usd_bn) * MILLION_PER_BILLION


def classify_intervention(
    delta_charge_bps: float,
    delta_gap_mtco2: float,
    *,
    charge_tol_bps: float,
    gap_tol_mtco2: float,
) -> str:
    """Keep de-risking and pathway alignment as separate decision dimensions.

    Tolerances are **materiality** thresholds supplied by the caller from config,
    not floating-point epsilon. Until the 2026-08-04 audit this used
    sqrt(eps) ~ 1.5e-8, so a 1e-4 bps move was labelled `de_risking_only` and
    could be ranked as a firm's best de-risking contract.
    """
    de_risks = delta_charge_bps < -charge_tol_bps
    adds_risk = delta_charge_bps > charge_tol_bps
    aligns = delta_gap_mtco2 < -gap_tol_mtco2
    worsens_alignment = delta_gap_mtco2 > gap_tol_mtco2
    if de_risks and aligns:
        return "dual_benefit"
    if de_risks and worsens_alignment:
        return "de_risking_with_alignment_tradeoff"
    if de_risks:
        return "de_risking_only"
    if adds_risk and aligns:
        return "alignment_with_risk_tradeoff"
    if adds_risk:
        return "risk_increasing"
    if aligns:
        return "alignment_only"
    return "no_material_model_effect"


def target_drivers(
    row: pd.Series,
    table: pd.DataFrame,
    *,
    sector: str | None = None,
    route: str | None = None,
) -> list[str]:
    """Map an intervention's parameter transformation to financial risk drivers."""
    if row["operation"] == "combine":
        targets: list[str] = []
        for component in str(row["components"]).split(";"):
            if component:
                component_row = table.loc[component]
                if sector is not None and str(component_row["applicable_sector"]) not in ("all", sector):
                    continue
                if route is not None and str(component_row["applicable_route"]) not in ("all", route):
                    continue
                targets.extend(target_drivers(component_row, table, sector=sector, route=route))
        return list(dict.fromkeys(targets))
    parameter = str(row["parameter"])
    if parameter.startswith("p_h2"):
        return ["h2"]
    if parameter.startswith("p_elec"):
        return ["elec"]
    if parameter.startswith("p_feedstock"):
        return ["feedstock"]
    if parameter.startswith("k_capex"):
        return ["capex"]
    if parameter.startswith("carbon"):
        return ["carbon"]
    if parameter == "wacc":
        return ["financing"]
    return ["multiple"]


def contract_terms(
    row: pd.Series,
    table: pd.DataFrame,
    *,
    sector: str | None = None,
    route: str | None = None,
) -> dict:
    """Expose the actual coverage/tenor/basis assumptions used by the engine."""
    components = [c for c in str(row.get("components", "")).split(";") if c and c != "nan"]
    if row["operation"] == "combine":
        components = [
            component
            for component in components
            if (sector is None or str(table.loc[component, "applicable_sector"]) in ("all", sector))
            and (route is None or str(table.loc[component, "applicable_route"]) in ("all", route))
        ]
    return {
        "operation": str(row["operation"]),
        "instrument_type": str(row["instrument_type"]),
        "decision_owner": str(row["decision_owner"]),
        "targets": target_drivers(row, table, sector=sector, route=route),
        "coverage": None if row["operation"] == "combine" else float(row["coverage"]),
        "basis_sigma": None if row["operation"] == "combine" else float(row["basis_sigma"]),
        "start_year": None if row["operation"] == "combine" else int(row["start_year"]),
        "end_year": None if row["operation"] == "combine" else int(row["end_year"]),
        "components": components,
        "status": str(row["status"]),
        "notes": str(row["notes"]),
    }
