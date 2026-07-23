"""Pure transaction-screening functions for technology and contract decisions.

The screening case is deliberately simple and transparent: a level annual
operating benefit, a route CAPEX, a project life, and level debt service.  It is
not a project-finance model and does not invent low-carbon product revenues.
Instead, it reports the contracted product premium required to make NPV and
DSCR gates pass.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .finance import annuity
from .interventions import ParamSet, apply_interventions, base_params
from .result_contract import (
    PROJECT_ECONOMICS_BASIS,
    PROJECT_NPV_METRIC,
    result_descriptor,
)


@dataclass(frozen=True)
class DealTerms:
    profile_id: str
    project_life_years: int
    debt_share: float
    debt_tenor_years: int
    target_dscr: float
    green_premium_usd_t: float
    annual_fee_usd_m: float
    upfront_fee_usd_m: float
    counterparty_pd_annual: float
    recovery_rate: float
    collateral_pct: float
    irr_ceiling: float
    status: str
    source: str
    notes: str

    def __post_init__(self) -> None:
        if self.project_life_years <= 0 or self.debt_tenor_years <= 0:
            raise ValueError("project life and debt tenor must be positive")
        for name in ("debt_share", "counterparty_pd_annual", "recovery_rate", "collateral_pct"):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.target_dscr <= 0 or self.irr_ceiling <= 0:
            raise ValueError("target DSCR and IRR ceiling must be positive")
        if self.green_premium_usd_t < 0 or self.annual_fee_usd_m < 0 or self.upfront_fee_usd_m < 0:
            raise ValueError("premium and fees cannot be negative")

    @classmethod
    def from_row(cls, row: pd.Series) -> "DealTerms":
        return cls(
            profile_id=str(row["profile_id"]),
            project_life_years=int(row["project_life_years"]),
            debt_share=float(row["debt_share"]),
            debt_tenor_years=int(row["debt_tenor_years"]),
            target_dscr=float(row["target_dscr"]),
            green_premium_usd_t=float(row["green_premium_usd_t"]),
            annual_fee_usd_m=float(row["annual_fee_usd_m"]),
            upfront_fee_usd_m=float(row["upfront_fee_usd_m"]),
            counterparty_pd_annual=float(row["counterparty_pd_annual"]),
            recovery_rate=float(row["recovery_rate"]),
            collateral_pct=float(row["collateral_pct"]),
            irr_ceiling=float(row["irr_ceiling"]),
            status=str(row["status"]),
            source=str(row["source"]),
            notes=str(row["notes"]),
        )


def solve_project_irr(
    annual_cash_usd_m: float, capex_usd_m: float, life_years: int, ceiling: float
) -> tuple[float | None, bool]:
    """IRR of level annual cash flows; returns (IRR, capped_at_ceiling)."""
    if annual_cash_usd_m <= 0 or capex_usd_m <= 0:
        return None, False

    def npv_at(rate: float) -> float:
        if rate <= np.finfo(float).eps:
            return annual_cash_usd_m * life_years - capex_usd_m
        return annual_cash_usd_m * annuity(rate, life_years) - capex_usd_m

    if npv_at(0.0) < 0:
        return None, False
    if npv_at(ceiling) > 0:
        return ceiling, True
    lo, hi = 0.0, ceiling
    for _ in range(np.finfo(float).nmant):
        mid = (lo + hi) / 2.0
        if npv_at(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0, False


def lifetime_default_probability(annual_pd: float, tenor_years: int) -> float:
    return float(1.0 - (1.0 - annual_pd) ** tenor_years)


def screen_project(
    cal,
    firm_assets: pd.DataFrame,
    route_name: str,
    terms: DealTerms,
    intervention_ids: list[str] | None = None,
) -> dict:
    """Screen one firm-scale route under one contract/policy transformation."""
    ids = intervention_ids or []
    route = cal.routes.set_index("route").loc[route_name]
    country = str(firm_assets["country"].iloc[0])
    elec_driver = str(firm_assets["elec_driver"].iloc[0])
    ps: ParamSet = (
        apply_interventions(
            cal,
            route_name,
            country,
            elec_driver,
            ids,
            base_year_override=float(cal.lsm["base_year"]),
            horizon_override=float(terms.project_life_years),
        )
        if ids
        else base_params(cal, route, country, elec_driver)
    )
    capacity_mt = float(firm_assets["capacity_mt_yr"].sum())
    baseline_intensity = float(
        np.average(
            firm_assets["emission_intensity_tco2_t"],
            weights=firm_assets["capacity_mt_yr"],
        )
    )
    delta_intensity = baseline_intensity - float(route["residual_intensity_tco2_t"])
    carbon_benefit = delta_intensity * ps.carbon.l_bar
    avoided_opex = float(route["avoided_opex_usd_t"])
    route_other_opex = float(route["route_opex_other_usd_t"])
    hydrogen_cost = float(route["q_h2_kg_t"]) * ps.p_h2
    electricity_cost = float(route["q_elec_mwh_t"]) * ps.p_elec
    feedstock_cost = float(route["q_feedstock_t_t"]) * ps.p_feedstock
    annual_benefit_before_green = (
        carbon_benefit
        + avoided_opex
        - route_other_opex
        - hydrogen_cost
        - electricity_cost
        - feedstock_cost
    )
    annual_benefit_usd_t = annual_benefit_before_green + terms.green_premium_usd_t

    capex_usd_t = float(route["k_capex_usd_t"]) * ps.k_capex_mult
    capex_usd_m = capex_usd_t * capacity_mt
    discount_rate = float(firm_assets["hurdle"].iloc[0]) + ps.wacc_delta
    debt_rate = float(firm_assets["wacc"].iloc[0]) + ps.wacc_delta
    project_annuity = annuity(discount_rate, terms.project_life_years)
    fee_pv_usd_m = (
        terms.upfront_fee_usd_m
        + terms.annual_fee_usd_m * annuity(discount_rate, terms.debt_tenor_years)
        if ids
        else 0.0
    )
    annual_cash_usd_m = annual_benefit_usd_t * capacity_mt
    project_npv_usd_m = annual_cash_usd_m * project_annuity - capex_usd_m - fee_pv_usd_m
    project_irr, irr_capped = solve_project_irr(
        annual_cash_usd_m, capex_usd_m + fee_pv_usd_m, terms.project_life_years, terms.irr_ceiling
    )

    debt_amount_usd_m = capex_usd_m * terms.debt_share
    annual_debt_service_usd_m = debt_amount_usd_m / annuity(debt_rate, terms.debt_tenor_years)
    dscr = annual_cash_usd_m / annual_debt_service_usd_m if annual_debt_service_usd_m else None
    required_green_for_npv = max(
        0.0,
        -project_npv_usd_m / (capacity_mt * project_annuity),
    )
    required_green_for_dscr = max(
        0.0,
        (terms.target_dscr * annual_debt_service_usd_m - annual_cash_usd_m) / capacity_mt,
    )
    required_green = max(required_green_for_npv, required_green_for_dscr)
    levelized_capex_and_fees = (capex_usd_m + fee_pv_usd_m) / project_annuity / capacity_mt
    break_even_carbon = (
        route_other_opex
        + hydrogen_cost
        + electricity_cost
        + feedstock_cost
        + levelized_capex_and_fees
        - avoided_opex
        - terms.green_premium_usd_t
    ) / delta_intensity
    q_h2 = float(route["q_h2_kg_t"])
    break_even_h2 = None
    if q_h2 > 0:
        break_even_h2 = (
            carbon_benefit
            + avoided_opex
            - route_other_opex
            - electricity_cost
            - feedstock_cost
            + terms.green_premium_usd_t
            - levelized_capex_and_fees
        ) / q_h2
    q_feedstock = float(route["q_feedstock_t_t"])
    break_even_feedstock = None
    if q_feedstock > 0:
        break_even_feedstock = (
            carbon_benefit
            + avoided_opex
            - route_other_opex
            - hydrogen_cost
            - electricity_cost
            + terms.green_premium_usd_t
            - levelized_capex_and_fees
        ) / q_feedstock

    npv_positive = project_npv_usd_m >= 0
    dscr_pass = dscr is not None and dscr >= terms.target_dscr
    irr_pass = project_irr is not None and project_irr >= discount_rate
    if npv_positive and dscr_pass and irr_pass:
        investment_decision = "INVESTABLE_SCREEN"
    elif npv_positive:
        investment_decision = "ECONOMIC_NOT_DEBT_BANKABLE"
    else:
        investment_decision = "NOT_ECONOMIC_ON_TERMS"

    return {
        "result_contract": result_descriptor(
            PROJECT_NPV_METRIC,
            PROJECT_ECONOMICS_BASIS,
            "SCENARIO_CONDITIONAL",
            uncertainty="illustrative transaction terms; no construction/ramp/tax/working-capital model",
            interpretation="pre-deal levelized screen, not executable valuation",
        ),
        "route": route_name,
        "sector": str(route["sector"]),
        "output_unit": str(route["output_unit"]),
        "applied_interventions": list(ps.applied),
        "capacity_mt": capacity_mt,
        "baseline_intensity_tco2_t": baseline_intensity,
        "residual_intensity_tco2_t": float(route["residual_intensity_tco2_t"]),
        "prices": {
            "expected_carbon_usd_t": ps.carbon.l_bar,
            "hydrogen_usd_kg": ps.p_h2,
            "electricity_usd_mwh": ps.p_elec,
            "feedstock_usd_t": ps.p_feedstock,
        },
        "unit_economics_usd_t": {
            "carbon_avoided_benefit": carbon_benefit,
            "avoided_legacy_opex": avoided_opex,
            "route_other_opex": -route_other_opex,
            "hydrogen_cost": -hydrogen_cost,
            "electricity_cost": -electricity_cost,
            "feedstock_cost": -feedstock_cost,
            "green_premium": terms.green_premium_usd_t,
            "annual_net_benefit": annual_benefit_usd_t,
            "levelized_capex_and_fees": -levelized_capex_and_fees,
        },
        "investment": {
            "capex_usd_m": capex_usd_m,
            "discount_rate": discount_rate,
            "project_life_years": terms.project_life_years,
            "project_npv_usd_m": project_npv_usd_m,
            "project_irr": project_irr,
            "irr_capped": irr_capped,
            "npv_positive": npv_positive,
            "irr_pass": irr_pass,
            "decision": investment_decision,
        },
        "debt": {
            "debt_rate": debt_rate,
            "debt_share": terms.debt_share,
            "debt_amount_usd_m": debt_amount_usd_m,
            "tenor_years": terms.debt_tenor_years,
            "annual_debt_service_usd_m": annual_debt_service_usd_m,
            "dscr": dscr,
            "target_dscr": terms.target_dscr,
            "dscr_pass": dscr_pass,
        },
        "break_evens": {
            "required_green_premium_npv_usd_t": required_green_for_npv,
            "required_green_premium_dscr_usd_t": required_green_for_dscr,
            "required_green_premium_usd_t": required_green,
            "break_even_carbon_usd_t": break_even_carbon,
            "break_even_hydrogen_usd_kg": break_even_h2,
            "break_even_feedstock_usd_t": break_even_feedstock,
        },
        "fees": {
            "annual_fee_usd_m": terms.annual_fee_usd_m if ids else 0.0,
            "upfront_fee_usd_m": terms.upfront_fee_usd_m if ids else 0.0,
            "fee_pv_usd_m": fee_pv_usd_m,
        },
    }
