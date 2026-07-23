"""s09: transaction screening — which contract and technology looks investable?

This is a transparent pre-deal screen, not an executable investment recommendation.
It evaluates each route and intervention on project NPV/IRR, level-debt DSCR,
required green premium, residual conditional risk charge, and a simple
counterparty expected-loss adjustment.  Alternative routes remain feasibility
OPEN unless they match the firm's configured route.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import MODEL_CONDITIONAL, OPEN, SCENARIO_CONDITIONAL, claim, write_artifact  # noqa: E402
from model.lib.interventions import apply_interventions, base_params  # noqa: E402
from model.lib.result_contract import (  # noqa: E402
    PROJECT_RISK_BASIS,
    RISK_CHARGE_METRIC,
    result_descriptor,
)
from model.lib.transactions import (  # noqa: E402
    DealTerms,
    lifetime_default_probability,
    screen_project,
)
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402
from model.s04_anatomy import ANATOMY_DEPS, LEVEL_DEPS, anatomy_for, firm_exposures, firm_frame  # noqa: E402

OUT = ROOT / "outputs"


def risk_for_project(cal: CalibrationSet, firm_assets: pd.DataFrame, route_name: str, ids: list[str]) -> dict:
    route = cal.routes.set_index("route").loc[route_name]
    country = str(firm_assets["country"].iloc[0])
    elec_driver = str(firm_assets["elec_driver"].iloc[0])
    ps = (
        apply_interventions(cal, route_name, country, elec_driver, ids)
        if ids
        else base_params(cal, route, country, elec_driver)
    )
    project = firm_assets.copy()
    project["route"] = route_name
    project["t_switch_year"] = float(cal.lsm["base_year"])
    meta = firm_exposures(cal, project, ps=ps)
    anatomy = anatomy_for(cal, meta, reform=True)
    return {
        "result_contract": result_descriptor(
            RISK_CHARGE_METRIC,
            PROJECT_RISK_BASIS,
            "SCENARIO_CONDITIONAL",
            uncertainty="immediate commissioning, route, covariance and pricing assumptions",
            interpretation="project-at-base-year charge; not enterprise transition-window charge",
        ),
        "risk_charge_bps": anatomy["premium_bps"],
        "risk_charge_usd_t": anatomy["premium_usd_t"],
        "sigma_b_usd_bn": anatomy["sigma_b_usd_bn"],
        "shares": anatomy["shares"],
    }


def _contract_tenor(cal: CalibrationSet, intervention_id: str, fallback: int) -> int:
    table = cal.interventions.set_index("intervention_id")
    row = table.loc[intervention_id]
    if row["operation"] != "combine":
        return max(1, int(row["end_year"]) - int(row["start_year"]))
    tenors = [
        int(table.loc[c, "end_year"]) - int(table.loc[c, "start_year"])
        for c in str(row["components"]).split(";")
        if c
    ]
    return max(tenors) if tenors else fallback


def _contract_decision(net_value: float, risk_cut_bps: float, investment_decision: str) -> str:
    bankable = investment_decision == "INVESTABLE_SCREEN"
    if net_value > 0 and risk_cut_bps > 0:
        return "DUE_DILIGENCE_CANDIDATE" if bankable else "IMPROVES_BUT_NOT_BANKABLE"
    if net_value > 0:
        return "VALUE_WITH_RISK_TRADEOFF" if bankable else "VALUE_TRADEOFF_NOT_BANKABLE"
    if risk_cut_bps > 0:
        return "DE_RISKING_BUT_VALUE_NEGATIVE"
    return "RENEGOTIATE_OR_REJECT"


def _pareto(options: list[dict]) -> list[str]:
    """Non-dominated on higher project NPV and higher risk-charge cut."""
    frontier = []
    for option in options:
        dominated = any(
            other["net_incremental_value_usd_m"] >= option["net_incremental_value_usd_m"]
            and other["risk_cut_bps"] >= option["risk_cut_bps"]
            and (
                other["net_incremental_value_usd_m"] > option["net_incremental_value_usd_m"]
                or other["risk_cut_bps"] > option["risk_cut_bps"]
            )
            for other in options
            if other is not option
        )
        if not dominated:
            frontier.append(option["intervention_id"])
    return frontier


def build(cal: CalibrationSet) -> dict:
    terms = DealTerms.from_row(cal.transaction_assumptions.iloc[0])
    frame = firm_frame(cal)
    priced = frame[frame["category"] == "priced_route"]
    intervention_ids = list(cal.interventions["intervention_id"])
    iv_table = cal.interventions.set_index("intervention_id")
    firms = []

    for firm_id, firm_assets in priced.groupby("firm_id", sort=True):
        current_route = str(firm_assets["route"].iloc[0])
        sector = str(firm_assets["sector"].iloc[0])
        route_names = list(cal.routes.loc[cal.routes["sector"] == sector, "route"])
        route_cases = []
        for route_name in route_names:
            base_econ = screen_project(cal, firm_assets, route_name, terms, [])
            base_risk = risk_for_project(cal, firm_assets, route_name, [])
            options = []
            for intervention_id in intervention_ids:
                row = iv_table.loc[intervention_id]
                applicable = (
                    str(row["applicable_sector"]) in ("all", sector)
                    and str(row["applicable_route"]) in ("all", route_name)
                )
                econ = screen_project(cal, firm_assets, route_name, terms, [intervention_id])
                risk = risk_for_project(cal, firm_assets, route_name, [intervention_id])
                incremental = (
                    econ["investment"]["project_npv_usd_m"]
                    - base_econ["investment"]["project_npv_usd_m"]
                )
                tenor = _contract_tenor(cal, intervention_id, terms.debt_tenor_years)
                lifetime_pd = lifetime_default_probability(terms.counterparty_pd_annual, tenor)
                cva = (
                    max(incremental, 0.0)
                    * lifetime_pd
                    * (1.0 - terms.recovery_rate)
                    * (1.0 - terms.collateral_pct)
                    if str(row["instrument_type"]) not in ("policy", "grant")
                    else 0.0
                )
                net_value = incremental - cva
                risk_cut = base_risk["risk_charge_bps"] - risk["risk_charge_bps"]
                options.append(
                    {
                        "intervention_id": intervention_id,
                        "label": str(row["label"]),
                        "instrument_type": str(row["instrument_type"]),
                        "decision_owner": str(row["decision_owner"]),
                        "term_sheet": {
                            "modelled_core": str(row["modelled_terms"]),
                            "must_have_clauses": [
                                term.strip()
                                for term in str(row["diligence_terms"]).split(";")
                                if term.strip()
                            ],
                            "coverage_pct": float(row["coverage"]) * 100.0,
                            "modelled_start_year": int(row["start_year"]),
                            "modelled_end_year": int(row["end_year"]),
                        },
                        "applicable": applicable,
                        "economics": econ,
                        "risk": risk,
                        "risk_cut_bps": risk_cut,
                        "gross_incremental_value_usd_m": incremental,
                        "counterparty_adjustment": {
                            "tenor_years": tenor,
                            "lifetime_pd": lifetime_pd,
                            "expected_loss_usd_m": cva,
                        },
                        "net_incremental_value_usd_m": net_value,
                        "contract_decision": _contract_decision(
                            net_value, risk_cut, econ["investment"]["decision"]
                        ),
                    }
                )

            applicable_options = [o for o in options if o["applicable"]]
            best_value = max(applicable_options, key=lambda o: o["net_incremental_value_usd_m"])
            best_risk = max(applicable_options, key=lambda o: o["risk_cut_bps"])
            executable = [
                o
                for o in applicable_options
                if o["instrument_type"] in ("offtake_contract", "energy_contract", "financing")
            ]
            passes_both = [
                o for o in executable
                if o["net_incremental_value_usd_m"] > 0 and o["risk_cut_bps"] > 0
            ]
            best_contract = (
                max(passes_both, key=lambda o: o["net_incremental_value_usd_m"])
                if passes_both
                else None
            )
            route_cases.append(
                {
                    "route": route_name,
                    "is_configured_route": route_name == current_route,
                    "feasibility_status": "CONFIGURED_ROUTE"
                    if route_name == current_route
                    else "OPEN_NOT_TECHNICALLY_VALIDATED",
                    "base": {"economics": base_econ, "risk": base_risk},
                    "options": options,
                    "frontier": {
                        "pareto_interventions": _pareto(applicable_options),
                        "best_value": best_value["intervention_id"],
                        "best_de_risker": best_risk["intervention_id"],
                        "best_bilateral_contract_screen": None
                        if best_contract is None
                        else best_contract["intervention_id"],
                    },
                }
            )

        configured = next(r for r in route_cases if r["is_configured_route"])
        configured_residual = float(
            cal.routes.set_index("route").loc[current_route, "residual_intensity_tco2_t"]
        )
        for route_case in route_cases:
            route_residual = float(
                cal.routes.set_index("route").loc[route_case["route"], "residual_intensity_tco2_t"]
            )
            route_case["meets_configured_decarbonization_depth"] = (
                route_residual <= configured_residual
            )
        configured_candidates = [configured["base"]["economics"]] + [
            o["economics"] for o in configured["options"] if o["applicable"]
        ]
        configured_best = max(
            configured_candidates, key=lambda e: e["investment"]["project_npv_usd_m"]
        )
        route_leaders = []
        for route_case in route_cases:
            cases = [route_case["base"]["economics"]] + [
                o["economics"] for o in route_case["options"] if o["applicable"]
            ]
            route_leaders.append(
                (route_case, max(cases, key=lambda e: e["investment"]["project_npv_usd_m"]))
            )
        economic_route, economic_case = max(
            route_leaders, key=lambda pair: pair[1]["investment"]["project_npv_usd_m"]
        )
        climate_equivalent = [
            pair for pair in route_leaders if pair[0]["meets_configured_decarbonization_depth"]
        ]
        climate_route, climate_case = max(
            climate_equivalent, key=lambda pair: pair[1]["investment"]["project_npv_usd_m"]
        )
        action = (
            "PROCEED_TO_DUE_DILIGENCE"
            if configured_best["investment"]["decision"] == "INVESTABLE_SCREEN"
            else "NEGOTIATE_PRICE_SUPPORT_OR_GREEN_PREMIUM"
        )
        firms.append(
            {
                "firm_id": firm_id,
                "firm": str(firm_assets["firm"].iloc[0]),
                "sector": sector,
                "country": str(firm_assets["country"].iloc[0]),
                "configured_route": current_route,
                "route_cases": route_cases,
                "recommendation": {
                    "action": action,
                    "configured_route_best_npv_usd_m": configured_best["investment"]["project_npv_usd_m"],
                    "configured_route_required_green_premium_usd_t": configured_best["break_evens"]["required_green_premium_usd_t"],
                    "economic_leader_route": economic_route["route"],
                    "economic_leader_feasibility": economic_route["feasibility_status"],
                    "economic_leader_npv_usd_m": economic_case["investment"]["project_npv_usd_m"],
                    "economic_leader_meets_configured_depth": economic_route["meets_configured_decarbonization_depth"],
                    "climate_equivalent_leader_route": climate_route["route"],
                    "climate_equivalent_leader_feasibility": climate_route["feasibility_status"],
                    "climate_equivalent_leader_npv_usd_m": climate_case["investment"]["project_npv_usd_m"],
                    "note": "unconstrained leader may not provide equivalent decarbonization; alternative routes remain economics-only until technology, feedstock and infrastructure feasibility are validated",
                },
            }
        )

    return {
        "release_stage": "INTERNAL_RESEARCH_PREVIEW",
        "comparison_warning": (
            "Project risk uses immediate base-year commissioning and is not directly comparable "
            "with enterprise transition-window bps unless basis_id matches."
        ),
        "profile": {
            **terms.__dict__,
            "debt_rate_rule": "firm WACC plus intervention WACC delta",
            "quote_status": "ILLUSTRATIVE_NOT_EXECUTABLE",
        },
        "definitions": {
            "project_npv": "firm-scale simultaneous replacement screen: level annual operating benefit plus configured green premium, less route CAPEX and explicit fees",
            "net_incremental_value": "incremental project NPV less simple counterparty expected-loss adjustment",
            "investment_decision": "screening gate only; no construction, ramp-up, tax, working-capital or terminal-value model",
            "technology_comparison": "economic comparison; non-configured routes have OPEN feasibility",
            "horizons": "deal economics uses the transaction project life for contract coverage; conditional risk charge retains the paper's configured risk horizon",
        },
        "firms": firms,
    }


def main() -> int:
    cal = load_calibration()
    data = build(cal)
    write_artifact(
        "deal_screening",
        data,
        cal.param_status,
        claims={
            "firms.route_cases.base.economics": claim(
                SCENARIO_CONDITIONAL,
                ["routes_sensitivity", "firms_registry", "scenarios", "transaction_assumptions"],
                "screening NPV/IRR/DSCR; no tax, ramp-up, construction or terminal value",
            ),
            "firms.route_cases.options": claim(
                MODEL_CONDITIONAL,
                LEVEL_DEPS + ["interventions", "transaction_assumptions"],
                "contract value and residual conditional charge under illustrative transaction terms",
            ),
            "firms.recommendation.economic_leader_route": claim(
                OPEN,
                ANATOMY_DEPS + ["transaction_assumptions"],
                "non-configured route feasibility is not validated",
            ),
        },
        note="pre-deal screen: contract value, project investability, debt service and technology alternatives",
    )
    route_case_count = sum(len(firm["route_cases"]) for firm in data["firms"])
    print(f"OK — deal screening for {len(data['firms'])} firms / {route_case_count} sector-valid route cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
