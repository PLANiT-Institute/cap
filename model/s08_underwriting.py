"""s08: investor underwriting + corporate contract decision artifact.

This stage does not introduce a new pricing theory.  It translates the paper's
existing conditional risk charge and intervention counterfactuals into:

- investor view: model-implied spread, PV uncertainty, annual charge equivalent,
  risk anatomy, and a transparent lambda x p_bind sensitivity surface;
- treasury view: contract terms, residual risk, bps reduction, annual risk-charge
  equivalent, and the separate pathway-alignment effect.

The annual USD value is *not* a forecast financing saving.  It is the bps change
applied to EV, using the same normalization as the conditional risk charge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import (  # noqa: E402
    MODEL_CONDITIONAL,
    PROVISIONAL,
    SCENARIO_CONDITIONAL,
    claim,
    write_artifact,
)
from model.lib.underwriting import (  # noqa: E402
    annual_charge_usd_m,
    classify_intervention,
    contract_terms,
    dominant_driver,
)
from model.lib.result_contract import (  # noqa: E402
    ALIGNMENT_GAP_LOSS_BASIS,
    ALIGNMENT_GAP_LOSS_METRIC,
    ALIGNMENT_GAP_RISK_CHARGE_METRIC,
    ENTERPRISE_RISK_BASIS,
    RISK_CHARGE_METRIC,
    result_descriptor,
)
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402
from model.s04_anatomy import ANATOMY_DEPS, LEVEL_DEPS  # noqa: E402

OUT = ROOT / "outputs"


def _artifact(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


def _sensitivity(cal: CalibrationSet, firm_id: str, base_charge: float, country: str) -> dict:
    """Hold exposure fixed and move only scalar lambda and p_bind."""
    base_lambda = float(cal.pricing["lambda"])
    base_p_bind = float(cal.p_bind[country])
    lambdas = np.unique(
        np.append(
            np.linspace(
                cal.lsm["lambda_grid_lo"],
                cal.lsm["lambda_grid_hi"],
                int(cal.lsm["lambda_grid_n"]),
            ),
            base_lambda,
        )
    )
    p_binds = np.unique(
        np.append(
            np.linspace(
                cal.lsm["p_bind_grid_lo"],
                cal.lsm["p_bind_grid_hi"],
                int(cal.lsm["p_bind_grid_n"]),
            ),
            base_p_bind,
        )
    )
    rows = []
    for lam in lambdas:
        for pb in p_binds:
            spread = base_charge * float(lam) / base_lambda * float(pb) / base_p_bind
            rows.append(
                {
                    "firm_id": firm_id,
                    "lambda": float(lam),
                    "p_bind": float(pb),
                    "spread_bps": spread,
                }
            )
    levels = [r["spread_bps"] for r in rows]
    return {
        "lambdas": [float(v) for v in lambdas],
        "p_binds": [float(v) for v in p_binds],
        "rows": rows,
        "range_bps": {"lo": min(levels), "hi": max(levels)},
        "base": {"lambda": base_lambda, "p_bind": base_p_bind, "spread_bps": base_charge},
        "note": "fixed exposure and covariance; scalar pricing sensitivity only",
    }


def build(cal: CalibrationSet) -> dict:
    impacts = _artifact("intervention_impacts")
    levels = {f["firm_id"]: f for f in _artifact("premium_levels")["firms"]}
    shares = {f["firm_id"]: f for f in _artifact("shares_by_firm")["firms"]}
    envelopes = {f["firm_id"]: f for f in _artifact("share_envelopes")["firms"]}
    impact_by_firm = {f["firm_id"]: f for f in impacts["firms"]}
    gap_loss_by_firm = {
        f["firm_id"]: f for f in _artifact("alignment_gap_loss")["firms"]
    }
    iv_table = cal.interventions.set_index("intervention_id")

    firm_rows = []
    for firm_id, impact in sorted(impact_by_firm.items()):
        level = levels[firm_id]
        share = shares[firm_id]
        g = cal.firms[
            (cal.firms["firm_id"] == firm_id) & (cal.firms["category"] == "priced_route")
        ]
        country = str(g["country"].iloc[0])
        ev_usd_bn = float(g["ev_usd_bn"].iloc[0])
        base = impact["before"]
        base_charge = float(base["risk_charge_bps"])
        base_sigma = float(base["sigma_b_usd_bn"])
        gap_loss = gap_loss_by_firm[firm_id]

        options = []
        for intervention_id, iv in impact["interventions"].items():
            row = iv_table.loc[intervention_id]
            after_charge = float(iv["after"]["risk_charge_bps"])
            cut_bps = base_charge - after_charge
            after_sigma = float(iv["after"]["sigma_b_usd_bn"])
            applicable_route = str(row["applicable_route"])
            applicable_sector = str(row["applicable_sector"])
            applicable = (
                (applicable_sector == "all" or applicable_sector == str(share["sector"]))
                and (applicable_route == "all" or applicable_route == str(share["route"]))
            )
            options.append(
                {
                    "intervention_id": intervention_id,
                    "label": str(row["label"]),
                    "applicable": applicable,
                    "result_contract": result_descriptor(
                        RISK_CHARGE_METRIC,
                        ENTERPRISE_RISK_BASIS,
                        "SCENARIO_CONDITIONAL",
                        uncertainty="contract coverage, tenor, basis and pricing assumptions",
                        interpretation="enterprise transition-window residual charge",
                    ),
                    "terms": contract_terms(
                        row,
                        iv_table,
                        sector=str(share["sector"]),
                        route=str(share["route"]),
                    ),
                    "before_spread_bps": base_charge,
                    "after_spread_bps": after_charge,
                    "risk_cut_bps": cut_bps,
                    "risk_cut_pct": cut_bps / base_charge if base_charge else None,
                    "annual_risk_charge_value_usd_m": annual_charge_usd_m(cut_bps, ev_usd_bn),
                    "before_sigma_usd_bn": base_sigma,
                    "after_sigma_usd_bn": after_sigma,
                    "sigma_cut_pct": (base_sigma - after_sigma) / base_sigma if base_sigma else None,
                    "residual_charge_ratio": after_charge / base_charge if base_charge else None,
                    "residual_shares": iv["residual"]["shares"],
                    "dominant_residual_driver": dominant_driver(iv["residual"]["shares"]),
                    "delta_tau_years": float(iv["delta"]["tau_star_years"]),
                    "delta_gap_mtco2": float(iv["delta"]["cumulative_gap_mtco2"]),
                    "gap_loss_before_usd_m": float(
                        iv["before"]["expected_pv_gap_loss_usd_m"]
                    ),
                    "gap_loss_after_usd_m": float(
                        iv["after"]["expected_pv_gap_loss_usd_m"]
                    ),
                    "gap_risk_charge_before_bps": float(
                        iv["before"]["gap_risk_charge_bps"]
                    ),
                    "gap_risk_charge_after_bps": float(
                        iv["after"]["gap_risk_charge_bps"]
                    ),
                    "gap_risk_charge_delta_bps": float(
                        iv["delta"]["gap_risk_charge_bps"]
                    ),
                    "gap_charge_basis_warning": (
                        "separate from transition-cost spread; do not add"
                    ),
                    "decision_class": classify_intervention(
                        float(iv["delta"]["risk_charge_bps"]),
                        float(iv["delta"]["cumulative_gap_mtco2"]),
                    ),
                    "double_count_warning": bool(iv["double_count_warning"]),
                }
            )

        ranked = sorted(
            [o for o in options if o["applicable"] and o["risk_cut_bps"] > 0],
            key=lambda o: o["risk_cut_bps"],
            reverse=True,
        )
        for rank, option in enumerate(ranked, start=1):
            option["de_risking_rank"] = rank
        top = ranked[0] if ranked else None
        package_attr = impact["order_averaged_contribution_bps"]

        firm_rows.append(
            {
                "firm_id": firm_id,
                "firm": str(share["firm"]),
                "sector": str(share["sector"]),
                "country": country,
                "route": str(share["route"]),
                "capacity_mt": float(share["capacity_mt"]),
                "enterprise_value_usd_bn": ev_usd_bn,
                "wacc": float(level["wacc"]),
                "underwriting": {
                    "result_contract": result_descriptor(
                        RISK_CHARGE_METRIC,
                        ENTERPRISE_RISK_BASIS,
                        "SCENARIO_CONDITIONAL",
                        uncertainty="lambda x p_bind sensitivity plus model-conditional exposure",
                        interpretation="enterprise transition-window charge; not observed spread",
                    ),
                    "model_implied_spread_bps": base_charge,
                    "annual_risk_charge_usd_m": annual_charge_usd_m(base_charge, ev_usd_bn),
                    "transition_cost_sigma_usd_bn": base_sigma,
                    "sigma_to_enterprise_value": base_sigma / ev_usd_bn,
                    "dominant_driver": dominant_driver(base["shares"]),
                    "risk_anatomy": base["shares"],
                    "share_envelope": envelopes[firm_id]["envelope"],
                    "share_envelope_perspective": "base-regime covariance band; current anatomy is reform-priced and may sit outside it",
                    "sensitivity": _sensitivity(cal, firm_id, base_charge, country),
                },
                "alignment_gap_loss": {
                    "loss_result_contract": result_descriptor(
                        ALIGNMENT_GAP_LOSS_METRIC,
                        ALIGNMENT_GAP_LOSS_BASIS,
                        "PROVISIONAL",
                        uncertainty="surrogate required path and assumed carbon scenarios",
                        interpretation="reduced-form scenario PV loss implied by the physical gap",
                    ),
                    "risk_result_contract": result_descriptor(
                        ALIGNMENT_GAP_RISK_CHARGE_METRIC,
                        ALIGNMENT_GAP_LOSS_BASIS,
                        "PROVISIONAL",
                        uncertainty="gap-loss distribution plus assumed lambda and k",
                        interpretation="separate gap-linked charge; not additive to transition-cost charge",
                    ),
                    "cumulative_alignment_gap_mtco2": gap_loss[
                        "cumulative_alignment_gap_mtco2"
                    ],
                    "expected_pv_gap_loss_usd_m": gap_loss[
                        "expected_pv_gap_loss_usd_m"
                    ],
                    "sigma_pv_gap_loss_usd_m": gap_loss["sigma_pv_gap_loss_usd_m"],
                    "gap_risk_charge_bps": gap_loss["gap_risk_charge_bps"],
                    "aggregation_warning": gap_loss["aggregation_rule"],
                },
                "contract_options": options,
                "decision_summary": {
                    "best_de_risker": None
                    if top is None
                    else {
                        "intervention_id": top["intervention_id"],
                        "label": top["label"],
                        "risk_cut_bps": top["risk_cut_bps"],
                        "annual_risk_charge_value_usd_m": top["annual_risk_charge_value_usd_m"],
                        "decision_class": top["decision_class"],
                    },
                    "dominant_unhedged_driver": dominant_driver(base["shares"]),
                    "explanation": "ranked by positive reduction in the model-implied conditional risk charge; contract price is not yet observed",
                },
                "package_attribution": {
                    "order_averaged_cut_bps": package_attr,
                    "note": "Shapley allocation of package risk-charge change; negative means the component adds charge",
                },
            }
        )

    portfolio = sorted(
        [
            {
                "firm_id": f["firm_id"],
                "firm": f["firm"],
                "sector": f["sector"],
                "route": f["route"],
                "spread_bps": f["underwriting"]["model_implied_spread_bps"],
                "result_contract": f["underwriting"]["result_contract"],
                "annual_risk_charge_usd_m": f["underwriting"]["annual_risk_charge_usd_m"],
                "sigma_to_enterprise_value": f["underwriting"]["sigma_to_enterprise_value"],
                "dominant_driver": f["underwriting"]["dominant_driver"],
            }
            for f in firm_rows
        ],
        key=lambda f: f["spread_bps"],
        reverse=True,
    )
    return {
        "perspective": "reform-priced transition-cost risk; fixed-exposure scalar sensitivity",
        "definitions": {
            "model_implied_spread": "conditional risk charge, not an observed bond or loan spread",
            "annual_risk_charge_value": "bps change applied to enterprise value; not a forecast financing saving",
            "risk_anatomy": "Euler decomposition of transition-cost uncertainty under the calibrated exposure model",
            "contract_ranking": "benefit-only ranking until observed contract premiums/support costs are supplied",
            "gap_linked_charge": (
                "scenario-valued physical-gap loss on a separate basis; never added to the "
                "transition-cost charge without a joint covariance model"
            ),
        },
        "portfolio": portfolio,
        "firms": firm_rows,
    }


def main() -> int:
    cal = load_calibration()
    data = build(cal)
    write_artifact(
        "transition_underwriting",
        data,
        cal.param_status,
        claims={
            "firms.underwriting.risk_anatomy": claim(
                MODEL_CONDITIONAL,
                ANATOMY_DEPS,
                "technology-contingent transition-cost uncertainty; not market beta identification",
            ),
            "firms.underwriting.model_implied_spread_bps": claim(
                SCENARIO_CONDITIONAL,
                LEVEL_DEPS,
                "conditional risk-charge normalization; not an observed loan or bond spread",
            ),
            "firms.contract_options": claim(
                MODEL_CONDITIONAL,
                LEVEL_DEPS + ["interventions"],
                "coverage, tenor and basis retained; benefit-only ranking pending observed contract cost",
            ),
            "firms.alignment_gap_loss": claim(
                PROVISIONAL,
                ["t_required", "scenarios", "carbon_base_kr", "carbon_base_jp",
                 "lambda", "k", "ev_usd_bn"],
                "physical gap mapped to a separate scenario-loss basis; not added to enterprise charge",
            ),
        },
        note="paper-to-product layer: investor underwriting and corporate contract decision views",
    )
    print(f"OK — transition underwriting for {len(data['firms'])} priced-route firms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
