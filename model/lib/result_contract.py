"""CAP result contract — 숫자의 계산 기준과 허용 해석을 기계가독 형태로 고정.

같은 metric 이름이라도 exposure scope나 valuation basis가 다르면 직접 비교할 수
없다. 모든 투자·연구 화면은 이 catalog의 basis_id와 evidence_grade를 사용한다.
"""
from __future__ import annotations

CONTRACT_VERSION = "1.0"
RELEASE_STAGE = "INTERNAL_RESEARCH_PREVIEW"

ENTERPRISE_RISK_BASIS = "enterprise_transition_window.reform_priced.full_counterfactual.ev_normalized"
ENTERPRISE_FIXED_RISK_BASIS = "enterprise_transition_window.reform_priced.fixed_exposure.ev_normalized"
PROJECT_RISK_BASIS = "project_from_base_year.reform_priced.fixed_commissioning.ev_normalized"
PROJECT_ECONOMICS_BASIS = "project_levelized.expected_scenario.illustrative_terms"
ALIGNMENT_GAP_BASIS = "enterprise_private_vs_required.full_counterfactual.provisional_required"
ALIGNMENT_GAP_LOSS_BASIS = "enterprise_private_vs_required.scenario_gap_loss.provisional_required"
LEVEL_WEDGE_BASIS = "project_levelized.closed_form_approximation.derived_coefficients"


RISK_CHARGE_METRIC = "conditional_risk_charge_bps"
LEVEL_WEDGE_METRIC = "level_wedge_usd_t"
PROJECT_NPV_METRIC = "project_npv_usd_m"
ALIGNMENT_GAP_METRIC = "cumulative_alignment_gap_mtco2"
ALIGNMENT_GAP_LOSS_METRIC = "alignment_gap_loss_pv_usd"
ALIGNMENT_GAP_RISK_CHARGE_METRIC = "alignment_gap_loss_risk_charge_bps"


def result_descriptor(
    metric_id: str,
    basis_id: str,
    evidence_grade: str,
    *,
    uncertainty: str,
    interpretation: str,
) -> dict:
    return {
        "metric_id": metric_id,
        "basis_id": basis_id,
        "evidence_grade": evidence_grade,
        "uncertainty": uncertainty,
        "interpretation": interpretation,
    }


def catalog() -> dict:
    return {
        "contract_version": CONTRACT_VERSION,
        "release_stage": RELEASE_STAGE,
        "comparison_rule": (
            "Direct numerical comparison is allowed only when metric_id and basis_id both match."
        ),
        "bases": {
            ENTERPRISE_RISK_BASIS: {
                "label": "Enterprise transition-window risk",
                "exposure_scope": "existing enterprise assets",
                "transition_rule": "asset-level min(private tau*, required year)",
                "regime": "reform-priced",
                "path_mode": "full_counterfactual",
                "normalization": "enterprise value",
                "allowed_use": "enterprise exposure and contract-risk comparison",
                "prohibited_use": "project-at-commissioning risk or observed market spread",
            },
            ENTERPRISE_FIXED_RISK_BASIS: {
                "label": "Enterprise fixed-exposure price stress",
                "exposure_scope": "existing enterprise assets using latest solved transition path",
                "transition_rule": "tau* and alignment path held fixed",
                "regime": "caller-supplied scenario",
                "path_mode": "fixed_exposure",
                "normalization": "enterprise value",
                "allowed_use": "comparative pricing sensitivity",
                "prohibited_use": "timing, alignment or emissions consequence",
            },
            PROJECT_RISK_BASIS: {
                "label": "Project-at-commissioning risk",
                "exposure_scope": "selected technology across screened firm capacity",
                "transition_rule": "project commissioned at model base year",
                "regime": "reform-priced",
                "path_mode": "fixed commissioning",
                "normalization": "enterprise value",
                "allowed_use": "technology and contract pre-deal comparison",
                "prohibited_use": "comparison with enterprise-window bps without rebasing",
            },
            PROJECT_ECONOMICS_BASIS: {
                "label": "Illustrative levelized project economics",
                "exposure_scope": "selected technology across screened firm capacity",
                "transition_rule": "project starts at model base year",
                "regime": "scenario-weighted expected prices",
                "path_mode": "level annual cash flow",
                "normalization": "project cash flow",
                "allowed_use": "break-even and pre-deal screening",
                "prohibited_use": "lender-grade project finance or executable valuation",
            },
            ALIGNMENT_GAP_BASIS: {
                "label": "Enterprise private-versus-required alignment gap",
                "exposure_scope": "asset-level enterprise emissions",
                "transition_rule": "private tau* versus required pathway",
                "regime": "physical emissions pathway",
                "path_mode": "full_counterfactual",
                "normalization": "cumulative MtCO2",
                "allowed_use": "scenario comparison and research diagnosis",
                "prohibited_use": "empirically identified firm mandate while required path is surrogate",
            },
            ALIGNMENT_GAP_LOSS_BASIS: {
                "label": "Scenario-valued private-versus-required alignment-gap loss",
                "exposure_scope": "discounted annual excess emissions on the private path",
                "transition_rule": "private tau* versus required pathway",
                "regime": "unconditional country carbon-scenario distribution",
                "path_mode": "full_counterfactual",
                "normalization": "PV USD and enterprise-value bps",
                "allowed_use": "reduced-form gap valuation and like-for-like intervention comparison",
                "prohibited_use": (
                    "addition to transition-cost charge without a joint covariance model, or "
                    "verified compliance-loss interpretation while required path is surrogate"
                ),
            },
        },
        "metrics": {
            RISK_CHARGE_METRIC: {
                "unit": "bps",
                "public_label": "conditional risk charge",
                "prohibited_label": "observed spread",
            },
            PROJECT_NPV_METRIC: {
                "unit": "USD million",
                "public_label": "illustrative project NPV",
                "prohibited_label": "executable valuation",
            },
            ALIGNMENT_GAP_METRIC: {
                "unit": "MtCO2",
                "public_label": "surrogate-conditioned alignment gap",
                "prohibited_label": "verified compliance gap",
            },
            ALIGNMENT_GAP_LOSS_METRIC: {
                "unit": "PV USD",
                "public_label": "scenario-valued alignment-gap loss",
                "prohibited_label": "verified compliance liability",
            },
            ALIGNMENT_GAP_RISK_CHARGE_METRIC: {
                "unit": "bps",
                "public_label": "alignment-gap loss risk charge",
                "prohibited_label": "observed spread or additive total premium",
            },
        },
    }
