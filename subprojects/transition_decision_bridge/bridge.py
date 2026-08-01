"""Decision bridge for CAP risk-premium artifacts.

The bridge packages existing core outputs without recalculating them.  Its most
important invariant is that the transition-cost headline and the alignment-gap
overlay are never added while their joint covariance is unidentified.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1.0"
AGGREGATION_STATUS = "SEPARATE_BASES_PENDING_JOINT_COVARIANCE"
MIN_HEADLINE_CUT_BPS = 0.1
MIN_GAP_CUT_MTCO2 = 1.0
MIN_OVERLAY_CUT_BPS = 0.1


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _round(value: float | int | None) -> float | None:
    return None if value is None else round(float(value), 10)


def _sensitivity_range(underwriting: dict[str, Any]) -> dict[str, Any]:
    rows = underwriting["sensitivity"]["rows"]
    values = [float(row["spread_bps"]) for row in rows]
    if not values:
        raise ValueError("risk-premium sensitivity grid is empty")
    return {
        "low_bps": _round(min(values)),
        "high_bps": _round(max(values)),
        "interpretation": "grid envelope across configured lambda and p_bind; not a confidence interval",
    }


def _option_view(option: dict[str, Any]) -> dict[str, Any]:
    risk_cut = float(option["risk_cut_bps"])
    gap_change = float(option["delta_gap_mtco2"])
    overlay_change = float(option["gap_risk_charge_delta_bps"])
    return {
        "intervention_id": option["intervention_id"],
        "label": option["label"],
        "decision_class": option["decision_class"],
        "before_headline_bps": _round(option["before_spread_bps"]),
        "residual_headline_bps": _round(option["after_spread_bps"]),
        "headline_reduction_bps": _round(option["risk_cut_bps"]),
        "alignment_gap_change_mtco2": _round(option["delta_gap_mtco2"]),
        "gap_overlay_change_bps": _round(option["gap_risk_charge_delta_bps"]),
        "annual_headline_value_reduction_usd_m": _round(
            option["annual_risk_charge_value_usd_m"]
        ),
        "material_model_effect": (
            risk_cut >= MIN_HEADLINE_CUT_BPS
            or gap_change <= -MIN_GAP_CUT_MTCO2
            or overlay_change <= -MIN_OVERLAY_CUT_BPS
        ),
    }


def _best_option(
    options: list[dict[str, Any]],
    *,
    alignment_safe: bool = False,
    overlay_safe: bool = False,
    dual_benefit: bool = False,
) -> dict[str, Any] | None:
    eligible = []
    for option in options:
        if not option["applicable"] or float(option["risk_cut_bps"]) <= 0:
            continue
        gap_change = float(option["delta_gap_mtco2"])
        overlay_change = float(option["gap_risk_charge_delta_bps"])
        if alignment_safe and gap_change > 0:
            continue
        if overlay_safe and overlay_change > 0:
            continue
        if dual_benefit and gap_change >= 0:
            continue
        eligible.append(option)
    if not eligible:
        return None
    winner = max(
        eligible,
        key=lambda item: (
            float(item["risk_cut_bps"]),
            -float(item["after_spread_bps"]),
            item["intervention_id"],
        ),
    )
    return _option_view(winner)


def _decision_status(
    no_tradeoff_option: dict[str, Any] | None, dual_option: dict[str, Any] | None
) -> str:
    if dual_option is not None and dual_option["material_model_effect"]:
        return "DUAL_BENEFIT_DUE_DILIGENCE"
    if no_tradeoff_option is not None and no_tradeoff_option["material_model_effect"]:
        return "NO_TRADEOFF_DUE_DILIGENCE"
    if no_tradeoff_option is not None:
        return "MODEL_EFFECT_BELOW_MATERIALITY"
    return "NO_TRADEOFF_DE_RISKER"


def build_artifact(
    underwriting: dict[str, Any],
    gap_loss: dict[str, Any],
    *,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic decision artifact from existing CAP outputs."""
    gap_by_firm = {row["firm_id"]: row for row in gap_loss["firms"]}
    underwriting_ids = [row["firm_id"] for row in underwriting["firms"]]
    if len(underwriting_ids) != len(set(underwriting_ids)):
        raise ValueError("duplicate firm_id in transition_underwriting")
    missing = sorted(set(underwriting_ids) - set(gap_by_firm))
    if missing:
        raise ValueError(f"alignment-gap loss missing firms: {missing}")

    firms = []
    for firm in underwriting["firms"]:
        firm_id = firm["firm_id"]
        uw = firm["underwriting"]
        gap = gap_by_firm[firm_id]
        central = float(uw["model_implied_spread_bps"])
        overlay = float(gap["gap_risk_charge_bps"])
        if central < 0 or overlay < 0:
            raise ValueError(f"negative risk premium for {firm_id}")

        options = firm["contract_options"]
        best = _best_option(options)
        safe = _best_option(options, alignment_safe=True)
        no_tradeoff = _best_option(options, alignment_safe=True, overlay_safe=True)
        dual = _best_option(
            options, alignment_safe=True, overlay_safe=True, dual_benefit=True
        )
        firms.append(
            {
                "firm_id": firm_id,
                "firm": firm["firm"],
                "country": firm["country"],
                "sector": firm["sector"],
                "route": firm["route"],
                "enterprise_value_usd_bn": _round(firm["enterprise_value_usd_bn"]),
                "decision_ready_risk_premium": {
                    "headline_bps": _round(central),
                    "headline_annual_value_usd_m": _round(uw["annual_risk_charge_usd_m"]),
                    "sensitivity_range": _sensitivity_range(uw),
                    "dominant_driver": uw["dominant_driver"],
                    "evidence_grade": uw["result_contract"]["evidence_grade"],
                    "interpretation": "conditional enterprise transition risk premium; not an observed spread",
                },
                "alignment_gap_overlay": {
                    "overlay_bps": _round(overlay),
                    "expected_pv_gap_loss_usd_m": _round(gap["expected_pv_gap_loss_usd_m"]),
                    "sigma_pv_gap_loss_usd_m": _round(gap["sigma_pv_gap_loss_usd_m"]),
                    "cumulative_alignment_gap_mtco2": _round(
                        gap["cumulative_alignment_gap_mtco2"]
                    ),
                    "evidence_grade": gap["risk_result_contract"]["evidence_grade"],
                    "interpretation": "separate provisional overlay; not additive to the headline",
                },
                "final_premium_publication": {
                    "published_headline_bps": _round(central),
                    "separate_gap_overlay_bps": _round(overlay),
                    "combined_total_bps": None,
                    "aggregation_status": AGGREGATION_STATUS,
                    "is_observed_market_spread": False,
                },
                "decision_options": {
                    "best_de_risker": best,
                    "best_alignment_safe_de_risker": safe,
                    "best_no_tradeoff_de_risker": no_tradeoff,
                    "best_dual_benefit": dual,
                    "decision_status": _decision_status(no_tradeoff, dual),
                },
            }
        )

    total_ev = sum(float(row["enterprise_value_usd_bn"]) for row in firms)
    if total_ev <= 0:
        raise ValueError("portfolio enterprise value must be positive")
    weighted_headline = sum(
        float(row["enterprise_value_usd_bn"])
        * float(row["decision_ready_risk_premium"]["headline_bps"])
        for row in firms
    ) / total_ev
    weighted_overlay = sum(
        float(row["enterprise_value_usd_bn"])
        * float(row["alignment_gap_overlay"]["overlay_bps"])
        for row in firms
    ) / total_ev

    return {
        "artifact": "risk_premium_decision",
        "schema_version": SCHEMA_VERSION,
        "purpose": "decision-ready packaging of CAP risk premium and alignment-gap overlay",
        "one_line": "Translate CAP transition gaps and intervention effects into a decision-ready risk premium without double counting.",
        "source_artifacts": source_metadata or {},
        "publication_policy": {
            "headline_metric": "conditional enterprise transition risk premium in bps",
            "gap_metric": "separate provisional alignment-gap overlay in bps",
            "combined_total_bps": None,
            "aggregation_status": AGGREGATION_STATUS,
            "materiality_gate": {
                "headline_reduction_bps": MIN_HEADLINE_CUT_BPS,
                "alignment_gap_reduction_mtco2": MIN_GAP_CUT_MTCO2,
                "gap_overlay_reduction_bps": MIN_OVERLAY_CUT_BPS,
                "rule": "an option is material when at least one reduction threshold is met",
            },
            "unlock_conditions": [
                "shared annual scenario draws for transition-cost and gap losses",
                "identified covariance or a joint cash-flow state model",
                "matched horizon, discounting and EV normalization",
                "validated T_required benchmark or probability distribution",
                "external or holdout calibration",
            ],
        },
        "portfolio": {
            "firm_count": len(firms),
            "enterprise_value_usd_bn": _round(total_ev),
            "ev_weighted_headline_bps": _round(weighted_headline),
            "ev_weighted_separate_gap_overlay_bps": _round(weighted_overlay),
            "combined_total_bps": None,
            "aggregation_status": AGGREGATION_STATUS,
        },
        "firms": firms,
    }


def render_markdown(artifact: dict[str, Any]) -> str:
    lines = [
        "# CAP Risk Premium Decision Pack",
        "",
        f"> {artifact['one_line']}",
        "",
        "## Publication rule",
        "",
        "The headline is CAP's conditional enterprise transition risk premium. "
        "The gap premium is a separate provisional overlay. The two are not added "
        "until a joint covariance or cash-flow state model exists.",
        "",
        "## Portfolio",
        "",
        f"- EV-weighted headline: **{artifact['portfolio']['ev_weighted_headline_bps']:.2f} bps**",
        f"- EV-weighted separate gap overlay: **{artifact['portfolio']['ev_weighted_separate_gap_overlay_bps']:.2f} bps**",
        "- Combined total: **not published — separate bases**",
        "",
        "## Firms",
        "",
        "| Firm | Headline (bps) | Sensitivity grid (bps) | Gap overlay (bps) | PV gap loss (USDm) | No-tradeoff option | Residual headline (bps) | Gap change (MtCO2) |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for firm in artifact["firms"]:
        premium = firm["decision_ready_risk_premium"]
        sensitivity = premium["sensitivity_range"]
        gap = firm["alignment_gap_overlay"]
        option = firm["decision_options"]["best_no_tradeoff_de_risker"]
        if option is None:
            option_label = "None"
            residual = "—"
            gap_change = "—"
        else:
            option_label = option["label"]
            residual = f"{option['residual_headline_bps']:.2f}"
            gap_change = f"{option['alignment_gap_change_mtco2']:.2f}"
        lines.append(
            f"| {firm['firm']} | {premium['headline_bps']:.2f} | "
            f"{sensitivity['low_bps']:.2f}–{sensitivity['high_bps']:.2f} | "
            f"{gap['overlay_bps']:.2f} | {gap['expected_pv_gap_loss_usd_m']:.1f} | "
            f"{option_label} | {residual} | {gap_change} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a transparent model-conditional decision screen, not an observed bond or loan spread.",
            "- `combined_total_bps` is intentionally null while the two bases lack a joint covariance.",
            "- A no-tradeoff option lowers headline risk without increasing either the modeled emissions gap or its separate overlay.",
            "- Due-diligence status also requires a material change: 0.1bp headline, 1MtCO2 gap, or 0.1bp overlay reduction.",
            "",
        ]
    )
    return "\n".join(lines)


def build_from_repo(repo_root: Path) -> dict[str, Any]:
    source_paths = {
        "transition_underwriting": repo_root / "outputs" / "transition_underwriting.json",
        "alignment_gap_loss": repo_root / "outputs" / "alignment_gap_loss.json",
    }
    metadata = {
        key: {
            "path": str(path.relative_to(repo_root)),
            "sha256": sha256(path),
        }
        for key, path in source_paths.items()
    }
    return build_artifact(
        load_json(source_paths["transition_underwriting"]),
        load_json(source_paths["alignment_gap_loss"]),
        source_metadata=metadata,
    )
