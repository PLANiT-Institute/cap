"""Read-only adapter from CAP core states to a reconciled joint premium."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(DEFAULT_REPO_ROOT))

from bridge import sha256  # noqa: E402
from joint_premium import (  # noqa: E402
    combine_premiums_bps,
    factor_dependence,
    weighted_correlation,
)
from model.lib.anatomy import DRIVERS  # noqa: E402
from model.lib.interventions import apply_interventions  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402
from model.s04_anatomy import anatomy_for, firm_exposures, firm_frame  # noqa: E402


SCHEMA_VERSION = "0.2.0"
RECONCILIATION_TOLERANCE = 1e-8
MIN_COMBINED_CUT_BPS = 0.1
MIN_GAP_CUT_MTCO2 = 1.0
MIN_OVERLAY_CUT_BPS = 0.1


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _round(value: float | int | None) -> float | None:
    return None if value is None else round(float(value), 10)


def _assert_close(label: str, actual: float, expected: float) -> float:
    error = abs(float(actual) - float(expected))
    if error > RECONCILIATION_TOLERANCE:
        raise ValueError(
            f"{label} failed reconciliation: actual={actual}, expected={expected}, error={error}"
        )
    return error


def _factor_state(
    cal: CalibrationSet,
    firm_id: str,
    *,
    tau_map: dict[str, float | None] | None,
    intervention_ids: list[str],
    basis_case: str = "lo",
) -> dict[str, Any]:
    frame = firm_frame(cal, tau_map=tau_map)
    firm_rows = frame[frame["firm_id"] == firm_id]
    priced = firm_rows[firm_rows["category"] == "priced_route"]
    if priced.empty:
        raise ValueError(f"no priced-route assets for {firm_id}")
    route = str(priced["route"].iloc[0])
    country = str(priced["country"].iloc[0])
    elec_driver = str(priced["elec_driver"].iloc[0])
    ps = apply_interventions(
        cal,
        route,
        country,
        elec_driver,
        intervention_ids,
        basis_case=basis_case,
    )
    meta = firm_exposures(cal, priced, ps=ps)
    sigmas, rho = cal.rho_matrix(
        elec_driver, carbon_sigma=float(ps.carbon.sigma_binding)
    )
    sigmas = sigmas.copy()
    sigmas[1], sigmas[2], sigmas[3] = (
        ps.sigma_h2,
        ps.sigma_elec,
        ps.sigma_feedstock,
    )
    exposures = np.asarray(meta["E"], dtype=float)
    factor_weights = exposures * sigmas

    scenarios = ps.carbon.scenarios
    probabilities = scenarios["prob"].to_numpy(float)
    levels = scenarios["level_usd"].to_numpy(float)
    reference = float(cal.pricing[f"carbon_base_{country.lower()}"])
    gap_loss_factor = np.maximum(levels - reference, 0.0)
    rho_carbon_gap = weighted_correlation(levels, gap_loss_factor, probabilities)
    dependence = factor_dependence(factor_weights, rho, rho_carbon_gap)
    anatomy = anatomy_for(cal, meta, reform=True)

    return {
        "firm_id": firm_id,
        "country": country,
        "route": route,
        "elec_driver": elec_driver,
        "wacc": float(meta["wacc"]),
        "enterprise_value_usd_bn": float(meta["ev_usd_bn"]),
        "p_bind": float(ps.carbon.p_bind),
        "drivers": list(DRIVERS),
        "exposure_pv_usd_bn": (exposures / 1e9).tolist(),
        "effective_sigmas": sigmas.tolist(),
        "factor_weights_usd_bn": (factor_weights / 1e9).tolist(),
        "rho": rho.tolist(),
        "transition_sigma_usd_bn": float(dependence["transition_sigma"]) / 1e9,
        "transition_premium_bps": float(anatomy["premium_bps"]),
        "rho_transition_carbon": dependence["rho_transition_carbon"],
        "rho_carbon_gap": dependence["rho_carbon_gap"],
        "rho_transition_gap": dependence["rho_transition_gap"],
        "scenario_probability_treatment": (
            "transition p_bind applied once in source charge; gap probabilities embedded once; "
            "correlation changes covariance only"
        ),
        "applied_interventions": list(ps.applied),
        "double_count_warning": bool(ps.double_count_warning),
    }


def _combined_state(
    factor_state: dict[str, Any],
    *,
    transition_bps: float,
    gap_bps: float,
    source_transition_sigma_usd_bn: float,
) -> dict[str, Any]:
    sigma_error = _assert_close(
        f"{factor_state['firm_id']} transition sigma",
        factor_state["transition_sigma_usd_bn"],
        source_transition_sigma_usd_bn,
    )
    premium_error = _assert_close(
        f"{factor_state['firm_id']} transition premium",
        factor_state["transition_premium_bps"],
        transition_bps,
    )
    rho = factor_state["rho_transition_gap"] if float(gap_bps) > 0 else None
    combined = combine_premiums_bps(transition_bps, gap_bps, rho)
    return {
        "components": {
            "transition_headline_bps": _round(transition_bps),
            "gap_overlay_bps": _round(gap_bps),
        },
        "joint_dependence": {
            "rho_transition_carbon": _round(
                factor_state["rho_transition_carbon"]
            ),
            "rho_carbon_gap": _round(factor_state["rho_carbon_gap"]),
            "rho_transition_gap": _round(rho),
            "method": "reconciled aggregate-factor covariance",
        },
        "combined": {key: _round(value) for key, value in combined.items()},
        "reconciliation": {
            "source_transition_sigma_usd_bn": _round(
                source_transition_sigma_usd_bn
            ),
            "recomputed_transition_sigma_usd_bn": _round(
                factor_state["transition_sigma_usd_bn"]
            ),
            "sigma_abs_error_usd_bn": _round(sigma_error),
            "source_transition_premium_bps": _round(transition_bps),
            "recomputed_transition_premium_bps": _round(
                factor_state["transition_premium_bps"]
            ),
            "premium_abs_error_bps": _round(premium_error),
            "tolerance": RECONCILIATION_TOLERANCE,
        },
        "factor_lineage": {
            "drivers": factor_state["drivers"],
            "exposure_pv_usd_bn": [
                _round(value) for value in factor_state["exposure_pv_usd_bn"]
            ],
            "effective_sigmas": [
                _round(value) for value in factor_state["effective_sigmas"]
            ],
            "factor_weights_usd_bn": [
                _round(value) for value in factor_state["factor_weights_usd_bn"]
            ],
            "p_bind": _round(factor_state["p_bind"]),
            "elec_driver": factor_state["elec_driver"],
            "probability_treatment": factor_state[
                "scenario_probability_treatment"
            ],
        },
    }


def _material(option: dict[str, Any]) -> bool:
    return bool(
        float(option["combined_reduction_bps"]) >= MIN_COMBINED_CUT_BPS
        or float(option["alignment_gap_change_mtco2"]) <= -MIN_GAP_CUT_MTCO2
        or float(option["gap_overlay_change_bps"]) <= -MIN_OVERLAY_CUT_BPS
    )


def _best(options: list[dict[str, Any]], *, dual: bool = False) -> dict[str, Any] | None:
    eligible = []
    for option in options:
        if not option["applicable"] or float(option["combined_reduction_bps"]) <= 0:
            continue
        if float(option["alignment_gap_change_mtco2"]) > 0:
            continue
        if float(option["gap_overlay_change_bps"]) > 0:
            continue
        if dual and float(option["alignment_gap_change_mtco2"]) >= 0:
            continue
        eligible.append(option)
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda row: (
            float(row["combined_reduction_bps"]),
            -float(row["after_combined_bps"]),
            row["intervention_id"],
        ),
    )


def _decision_status(
    no_tradeoff: dict[str, Any] | None, dual: dict[str, Any] | None
) -> str:
    if dual is not None and dual["material_model_effect"]:
        return "DUAL_BENEFIT_DUE_DILIGENCE"
    if no_tradeoff is not None and no_tradeoff["material_model_effect"]:
        return "NO_TRADEOFF_DUE_DILIGENCE"
    if no_tradeoff is not None:
        return "MODEL_EFFECT_BELOW_MATERIALITY"
    return "NO_TRADEOFF_DE_RISKER"


def build_joint_artifact(repo_root: Path) -> dict[str, Any]:
    repo = repo_root.resolve()
    source_paths = {
        "transition_underwriting": repo / "outputs" / "transition_underwriting.json",
        "alignment_gap_loss": repo / "outputs" / "alignment_gap_loss.json",
        "intervention_impacts": repo / "outputs" / "intervention_impacts.json",
        "tau_star": repo / "outputs" / "tau_star.json",
        "cost_vs_risk": repo / "outputs" / "cost_vs_risk.json",
        "calibration_resolved": repo / "outputs" / "calibration_resolved.json",
        "firms_config": repo / "config" / "firms.csv",
    }
    for label, path in source_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"required joint input missing: {label}={path}")

    underwriting = _load(source_paths["transition_underwriting"])
    gap_loss = _load(source_paths["alignment_gap_loss"])
    impacts = _load(source_paths["intervention_impacts"])
    tau_star = _load(source_paths["tau_star"])
    cal = load_calibration()

    gap_by_firm = {row["firm_id"]: row for row in gap_loss["firms"]}
    impacts_by_firm = {row["firm_id"]: row for row in impacts["firms"]}
    option_flags = {
        row["firm_id"]: {
            option["intervention_id"]: bool(option["applicable"])
            for option in row["contract_options"]
        }
        for row in underwriting["firms"]
    }

    firms = []
    for source_firm in underwriting["firms"]:
        firm_id = source_firm["firm_id"]
        if firm_id not in gap_by_firm or firm_id not in impacts_by_firm:
            raise ValueError(f"joint inputs missing firm {firm_id}")
        source_gap = gap_by_firm[firm_id]
        source_impact = impacts_by_firm[firm_id]
        transition_bps = float(
            source_firm["underwriting"]["model_implied_spread_bps"]
        )
        gap_bps = float(source_gap["gap_risk_charge_bps"])
        source_sigma = float(
            source_firm["underwriting"]["transition_cost_sigma_usd_bn"]
        )
        _assert_close(
            f"{firm_id} base transition source",
            source_impact["before"]["risk_charge_bps"],
            transition_bps,
        )
        _assert_close(
            f"{firm_id} base gap source",
            source_impact["before"]["gap_risk_charge_bps"],
            gap_bps,
        )

        base_factor = _factor_state(
            cal, firm_id, tau_map=None, intervention_ids=[]
        )
        base_joint = _combined_state(
            base_factor,
            transition_bps=transition_bps,
            gap_bps=gap_bps,
            source_transition_sigma_usd_bn=source_sigma,
        )

        intervention_rows = []
        for intervention_id, source_iv in source_impact["interventions"].items():
            if intervention_id not in tau_star["interventions"]:
                raise ValueError(f"tau_star missing intervention {intervention_id}")
            tau_map = tau_star["interventions"][intervention_id]
            after_factor = _factor_state(
                cal,
                firm_id,
                tau_map=tau_map,
                intervention_ids=[intervention_id],
            )
            after_joint = _combined_state(
                after_factor,
                transition_bps=float(source_iv["after"]["risk_charge_bps"]),
                gap_bps=float(source_iv["after"]["gap_risk_charge_bps"]),
                source_transition_sigma_usd_bn=float(
                    source_iv["after"]["sigma_b_usd_bn"]
                ),
            )
            high_factor = _factor_state(
                cal,
                firm_id,
                tau_map=tau_map,
                intervention_ids=[intervention_id],
                basis_case="hi",
            )
            high_transition_bps = float(
                source_iv["residual"]["risk_charge_bps_high_basis"]
            )
            _assert_close(
                f"{firm_id}/{intervention_id} high-basis transition premium",
                high_factor["transition_premium_bps"],
                high_transition_bps,
            )
            high_combined = combine_premiums_bps(
                high_transition_bps,
                float(source_iv["after"]["gap_risk_charge_bps"]),
                high_factor["rho_transition_gap"]
                if float(source_iv["after"]["gap_risk_charge_bps"]) > 0
                else None,
            )
            base_combined = float(base_joint["combined"]["central_bps"])
            after_combined_bps = float(after_joint["combined"]["central_bps"])
            row = {
                "intervention_id": intervention_id,
                "label": source_iv["label"],
                "applicable": option_flags[firm_id].get(intervention_id, True),
                "before_combined_bps": _round(base_combined),
                "after_combined_bps": _round(after_combined_bps),
                "after_high_basis_combined_bps": _round(
                    high_combined["central_bps"]
                ),
                "combined_reduction_bps": _round(
                    base_combined - after_combined_bps
                ),
                "alignment_gap_change_mtco2": _round(
                    source_iv["delta"]["cumulative_gap_mtco2"]
                ),
                "gap_overlay_change_bps": _round(
                    source_iv["delta"]["gap_risk_charge_bps"]
                ),
                "transition_component_change_bps": _round(
                    source_iv["delta"]["risk_charge_bps"]
                ),
                "after_joint_dependence": after_joint["joint_dependence"],
                "double_count_warning": bool(source_iv["double_count_warning"]),
            }
            row["material_model_effect"] = _material(row)
            if float(row["combined_reduction_bps"]) > 0:
                if (
                    float(row["alignment_gap_change_mtco2"]) <= 0
                    and float(row["gap_overlay_change_bps"]) <= 0
                ):
                    row["decision_class"] = (
                        "dual_benefit"
                        if float(row["alignment_gap_change_mtco2"]) < 0
                        else "no_tradeoff_de_risking"
                    )
                else:
                    row["decision_class"] = "de_risking_with_tradeoff"
            else:
                row["decision_class"] = "risk_increasing_or_unchanged"
            intervention_rows.append(row)

        no_tradeoff = _best(intervention_rows)
        dual = _best(intervention_rows, dual=True)
        firms.append(
            {
                "firm_id": firm_id,
                "firm": source_firm["firm"],
                "country": source_firm["country"],
                "sector": source_firm["sector"],
                "route": source_firm["route"],
                "enterprise_value_usd_bn": _round(
                    source_firm["enterprise_value_usd_bn"]
                ),
                "base": base_joint,
                "interventions": intervention_rows,
                "decision": {
                    "best_no_tradeoff_de_risker": no_tradeoff,
                    "best_dual_benefit": dual,
                    "status": _decision_status(no_tradeoff, dual),
                },
                "evidence_grade": "PROVISIONAL",
                "interpretation": (
                    "combined conditional transition risk premium; not an observed spread"
                ),
            }
        )

    total_ev = sum(float(row["enterprise_value_usd_bn"]) for row in firms)

    def ev_weighted(path: tuple[str, ...]) -> float:
        total = 0.0
        for row in firms:
            value: Any = row
            for key in path:
                value = value[key]
            total += float(row["enterprise_value_usd_bn"]) * float(value)
        return total / total_ev

    return {
        "artifact": "joint_risk_premium",
        "schema_version": SCHEMA_VERSION,
        "one_line": (
            "Combine CAP transition-cost and alignment-gap premiums through an explicit "
            "shared-carbon covariance without double counting."
        ),
        "method": {
            "name": "reconciled aggregate-factor covariance",
            "formula": (
                "pi_joint = sqrt(pi_transition^2 + pi_gap^2 + "
                "2*rho_transition_gap*pi_transition*pi_gap)"
            ),
            "rho_formula": (
                "rho_transition_gap = ((rho*w)_carbon/sqrt(w' rho w)) "
                "* corr(carbon_level, gap_loss_factor)"
            ),
            "probability_control": (
                "transition p_bind remains embedded once in its source component; gap scenario "
                "probabilities remain embedded once; covariance adds no probability multiplier"
            ),
            "evidence_grade": "PROVISIONAL",
            "market_spread": False,
        },
        "source_artifacts": {
            key: {"path": str(path.relative_to(repo)), "sha256": sha256(path)}
            for key, path in source_paths.items()
        },
        "materiality_gate": {
            "combined_reduction_bps": MIN_COMBINED_CUT_BPS,
            "alignment_gap_reduction_mtco2": MIN_GAP_CUT_MTCO2,
            "gap_overlay_reduction_bps": MIN_OVERLAY_CUT_BPS,
            "rule": "at least one reduction threshold",
        },
        "portfolio": {
            "firm_count": len(firms),
            "enterprise_value_usd_bn": _round(total_ev),
            "ev_weighted_transition_bps": _round(
                ev_weighted(("base", "components", "transition_headline_bps"))
            ),
            "ev_weighted_gap_overlay_bps": _round(
                ev_weighted(("base", "components", "gap_overlay_bps"))
            ),
            "ev_weighted_combined_bps": _round(
                ev_weighted(("base", "combined", "central_bps"))
            ),
            "ev_weighted_component_sum_upper_bps": _round(
                ev_weighted(("base", "combined", "perfect_positive_upper_bps"))
            ),
            "interpretation": (
                "EV-weighted average issuer charge; not a portfolio risk measure because "
                "cross-firm covariance is not modeled"
            ),
        },
        "firms": firms,
        "publication_gate": {
            "status": "SUBPROJECT_PROVISIONAL",
            "core_or_web_promoted": False,
            "passed": [
                "component reconciliation",
                "single probability treatment",
                "explicit factor covariance",
                "correlation bounds",
                "source lineage",
            ],
            "remaining": [
                "structural joint-state simulation cross-check",
                "validated T_required",
                "external or holdout calibration",
                "separate approval for core/web promotion",
            ],
        },
    }


def render_joint_markdown(artifact: dict[str, Any]) -> str:
    portfolio = artifact["portfolio"]
    lines = [
        "# CAP Joint Risk Premium",
        "",
        f"> {artifact['one_line']}",
        "",
        "## Portfolio readout",
        "",
        f"- EV-weighted transition component: **{portfolio['ev_weighted_transition_bps']:.2f} bps**",
        f"- EV-weighted gap component: **{portfolio['ev_weighted_gap_overlay_bps']:.2f} bps**",
        f"- EV-weighted combined premium: **{portfolio['ev_weighted_combined_bps']:.2f} bps**",
        f"- Perfect-positive component-sum upper: **{portfolio['ev_weighted_component_sum_upper_bps']:.2f} bps**",
        "",
        "The combined value is a PROVISIONAL model-conditional issuer charge, not an observed "
        "spread. The portfolio number is an EV-weighted average; it is not a portfolio risk measure.",
        "",
        "## Firms",
        "",
        "| Firm | Transition | Gap | rho(T,G) | Independence | Combined | Positive upper | No-tradeoff option | Combined cut |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for firm in artifact["firms"]:
        base = firm["base"]
        dependence = base["joint_dependence"]
        combined = base["combined"]
        option = firm["decision"]["best_no_tradeoff_de_risker"]
        if option is None:
            option_label = "None"
            cut = "—"
        else:
            option_label = option["label"]
            cut = f"{option['combined_reduction_bps']:.2f}"
        rho = dependence["rho_transition_gap"]
        rho_text = "—" if rho is None else f"{rho:.3f}"
        lines.append(
            f"| {firm['firm']} | {base['components']['transition_headline_bps']:.2f} | "
            f"{base['components']['gap_overlay_bps']:.2f} | {rho_text} | "
            f"{combined['independence_bps']:.2f} | {combined['central_bps']:.2f} | "
            f"{combined['perfect_positive_upper_bps']:.2f} | {option_label} | {cut} |"
        )
    lines.extend(
        [
            "",
            "## Publication controls",
            "",
            "- `p_bind` is not applied to the gap component a second time.",
            "- Component sum is reported only as the perfect-positive-correlation upper bound.",
            "- `T_required` remains surrogate-conditioned, so the combined result remains PROVISIONAL.",
            "- Core and web promotion remain blocked pending structural simulation and explicit approval.",
            "",
        ]
    )
    return "\n".join(lines)

