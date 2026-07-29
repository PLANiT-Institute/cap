"""s11: repeatable Korea/Japan dry-run pilot evidence packs.

These packs exercise the 20→40 operating workflow with the existing repository
inputs.  They are deliberately labelled dry runs: asset inputs are banded,
transaction terms are illustrative, and the required pathway remains a
surrogate.  Exact automated replay is tested here; independent analyst replay
and executable quotes remain 40-point gates.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.api import compute, screen_transaction  # noqa: E402
from model.lib.artifacts import MODEL_CONDITIONAL, OPEN, SCENARIO_CONDITIONAL, claim, write_artifact  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402

OUT = ROOT / "outputs"
REPORT_DIR = OUT / "pilots"
PILOT_FIRMS = ("POSCO", "NIPPON")
PILOT_INTERVENTION = "h2_cfd"
CAPABILITY_STAGE = "PILOT_READY_DRY_RUN_30"


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _files_hash(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(path.relative_to(ROOT).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _artifact(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


def _money(value: float) -> str:
    return f"{'−' if value < 0 else ''}${abs(value):,.1f}m"


def _transaction_point(firm_id: str, green_premium: float, **terms: float) -> dict:
    result = screen_transaction(
        {
            "firm_id": firm_id,
            "route": "h2_dri",
            "interventions": [PILOT_INTERVENTION],
            "terms": {"green_premium_usd_t": green_premium, **terms},
        }
    )["after"]["economics"]
    return {
        "green_premium_usd_t": green_premium,
        **terms,
        "project_npv_usd_m": result["investment"]["project_npv_usd_m"],
        "project_irr": result["investment"]["project_irr"],
        "dscr": result["debt"]["dscr"],
        "decision": result["investment"]["decision"],
        "remaining_required_green_premium_usd_t": result["break_evens"][
            "required_green_premium_usd_t"
        ],
    }


def _markdown(case: dict) -> str:
    decision = case["decision_summary"]
    enterprise = case["basis_separation"]["enterprise_transition_window"]
    project = case["basis_separation"]["project_from_base_year"]
    gates = case["forty_point_gates"]
    lines = [
        f"# CAP dry-run pilot — {case['firm']} H₂ DRI",
        "",
        "> **INTERNAL RESEARCH PREVIEW.** This is an automated dry run using banded asset data, "
        "illustrative terms and a surrogate required pathway. It is not an actual transaction pilot.",
        "",
        "## Decision summary",
        "",
        f"- Verdict: **{decision['verdict']}**",
        f"- Selected support: {decision['selected_support']}",
        f"- Project NPV: {_money(decision['project_npv_usd_m'])}",
        "- Gross incremental project NPV before counterparty EL: "
        f"{_money(decision['gross_incremental_project_npv_usd_m'])}",
        "- Counterparty-adjusted incremental NPV: "
        f"{_money(decision['counterparty_adjusted_incremental_npv_usd_m'])}",
        f"- Required contracted premium: ${decision['required_green_premium_usd_t']:,.1f}/t",
        f"- Annual CFADS shortfall: ${decision['annual_cfads_shortfall_usd_m']:,.1f}m",
        "",
        "## Basis separation",
        "",
        f"- Enterprise transition-window charge: {enterprise['after_bps']:.2f} bps "
        f"(`{enterprise['basis_id']}`)",
        f"- Project-from-base-year charge: {project['after_bps']:.2f} bps "
        f"(`{project['basis_id']}`)",
        "- These bps values are not directly comparable; only within-basis before/after deltas are effects.",
        "",
        "## Replay and 40-point gates",
        "",
        f"- Automated deterministic replay: {'PASS' if case['reproducibility']['exact_match'] else 'FAIL'}",
        f"- Traceable asset sources: {'PASS' if gates['traceable_asset_sources'] else 'FAIL'}",
        f"- Executable quote: {'PASS' if gates['executable_quote'] else 'OPEN'}",
        f"- Empirical required path: {'PASS' if gates['empirical_required_path'] else 'OPEN'}",
        f"- Independent analyst blind rerun: {'PASS' if gates['independent_analyst_blind_rerun'] else 'OPEN'}",
        f"- Eligible for 40/100: **{'YES' if gates['eligible_for_40'] else 'NO'}**",
        "",
        "The machine-readable stress results and input evidence are in `outputs/pilot_cases.json`.",
    ]
    return "\n".join(lines) + "\n"


def build(cal: CalibrationSet | None = None) -> dict:
    cal = cal or load_calibration()
    underwriting = _artifact("transition_underwriting")
    gaps = _artifact("condition_gap")
    deals = _artifact("deal_screening")
    enterprise_by_firm = {row["firm_id"]: row for row in underwriting["firms"]}
    gap_by_firm = {row["firm_id"]: row for row in gaps["firms"]}
    deal_by_firm = {row["firm_id"]: row for row in deals["firms"]}
    # 지문은 편집 정본(config/sheets/*.csv)에서 뜬다. 생성물 calibration.xlsx를
    # 넣으면 셀 값이 같아도 재조립 때마다 지문이 바뀌어 replay 판정이 흔들린다.
    config_paths = [
        ROOT / "config" / name
        for name in (
            "firms.csv",
            "routes.csv",
            "scenarios.csv",
            "interventions.csv",
            "transaction_assumptions.csv",
        )
    ] + sorted((ROOT / "config" / "sheets").glob("*.csv"))
    upstream_paths = [
        OUT / f"{name}.json"
        for name in (
            "condition_gap",
            "deal_screening",
            "result_contract",
            "transition_underwriting",
        )
    ]
    input_fingerprint = _files_hash(config_paths + upstream_paths)

    lambda_values = sorted({0.25, float(cal.pricing["lambda"]), 0.55})
    enterprise_stresses = {
        str(value): compute(
            {"pricing": {"lambda": value}, "interventions": [PILOT_INTERVENTION]},
            mode="fixed_exposure",
        )
        for value in lambda_values
    }

    cases = []
    for firm_id in PILOT_FIRMS:
        firm_assets = cal.firms[
            (cal.firms["firm_id"] == firm_id)
            & (cal.firms["category"] == "priced_route")
        ]
        if firm_assets.empty:
            raise ValueError(f"pilot firm has no priced-route assets: {firm_id}")
        route_name = str(firm_assets["route"].iloc[0])
        if route_name != "h2_dri":
            raise ValueError(f"pilot firm route must be h2_dri: {firm_id}={route_name}")

        request = {
            "firm_id": firm_id,
            "route": route_name,
            "interventions": [PILOT_INTERVENTION],
            "terms": {"green_premium_usd_t": 0.0},
        }
        run_a = screen_transaction(request)
        run_b = screen_transaction(request)
        replay_a = _canonical_hash(run_a)
        replay_b = _canonical_hash(run_b)
        before = run_a["before"]
        after = run_a["after"]
        economics = after["economics"]
        enterprise_firm = enterprise_by_firm[firm_id]
        enterprise_option = next(
            option
            for option in enterprise_firm["contract_options"]
            if option["intervention_id"] == PILOT_INTERVENTION
        )
        configured_deal = next(
            route_case
            for route_case in deal_by_firm[firm_id]["route_cases"]
            if route_case["is_configured_route"]
        )
        deal_option = next(
            option
            for option in configured_deal["options"]
            if option["intervention_id"] == PILOT_INTERVENTION
        )
        required_premium = float(
            economics["break_evens"]["required_green_premium_usd_t"]
        )
        annual_cfads = economics["debt"]["dscr"] * economics["debt"][
            "annual_debt_service_usd_m"
        ]
        cfads_shortfall = max(
            0.0,
            economics["debt"]["target_dscr"]
            * economics["debt"]["annual_debt_service_usd_m"]
            - annual_cfads,
        )

        premium_points = [0.0, required_premium + 0.1, required_premium + 50.0]
        transaction_stress = {
            "green_premium": [
                _transaction_point(firm_id, value) for value in premium_points
            ],
            "debt_share": [
                _transaction_point(firm_id, 0.0, debt_share=value)
                for value in (0.50, 0.60, 0.70)
            ],
            "target_dscr": [
                _transaction_point(firm_id, 0.0, target_dscr=value)
                for value in (1.15, 1.30, 1.45)
            ],
            "joint_gate_stress": _transaction_point(
                firm_id,
                required_premium + 0.1,
                debt_share=0.70,
                target_dscr=1.45,
            ),
        }
        risk_stress = []
        for value in lambda_values:
            result = next(
                row
                for row in enterprise_stresses[str(value)]["firms"]
                if row["firm_id"] == firm_id
            )
            risk_stress.append(
                {
                    "lambda": value,
                    "risk_charge_reform_bps": result["risk_charge_reform_bps"],
                    "basis_id": result["result_contract"]["basis_id"],
                    "interpretation": result["result_contract"]["interpretation"],
                }
            )

        traceable_sources = bool(firm_assets["source"].astype(str).str.len().gt(0).all())
        gates = {
            "traceable_asset_sources": traceable_sources,
            "automated_deterministic_replay": replay_a == replay_b,
            "executable_quote": False,
            "empirical_required_path": cal.t_required_source != "surrogate",
            "independent_analyst_blind_rerun": False,
            "actual_transaction_case": False,
        }
        gates["eligible_for_40"] = all(gates.values())

        case = {
            "case_id": f"{firm_id}_H2_DRI_H2_CFD_DRY_RUN_V1",
            "case_type": "AUTOMATED_DRY_RUN_EXISTING_CONFIG",
            "capability_stage": CAPABILITY_STAGE,
            "release_stage": "INTERNAL_RESEARCH_PREVIEW",
            "firm_id": firm_id,
            "firm": str(firm_assets["firm"].iloc[0]),
            "country": str(firm_assets["country"].iloc[0]),
            "sector": str(firm_assets["sector"].iloc[0]),
            "route": route_name,
            "decision_question": (
                "Does the modeled H2 CfD make the configured H2 DRI route pass absolute "
                "NPV, return and debt-service gates under the illustrative transaction profile?"
            ),
            "decision_summary": {
                "verdict": (
                    "ADVANCE"
                    if economics["investment"]["decision"] == "INVESTABLE_SCREEN"
                    else "FID_HOLD"
                ),
                "selected_support": "H2 CfD (CHPS-style)",
                "project_npv_usd_m": economics["investment"]["project_npv_usd_m"],
                "gross_incremental_project_npv_usd_m": run_a["delta"]["project_npv_usd_m"],
                "counterparty_adjusted_incremental_npv_usd_m": deal_option[
                    "net_incremental_value_usd_m"
                ],
                "counterparty_expected_loss_usd_m": deal_option[
                    "counterparty_adjustment"
                ]["expected_loss_usd_m"],
                "dscr": economics["debt"]["dscr"],
                "annual_cfads_shortfall_usd_m": cfads_shortfall,
                "required_green_premium_usd_t": required_premium,
                "decision_at_required_premium_plus_0_1": transaction_stress[
                    "green_premium"
                ][1]["decision"],
            },
            "basis_separation": {
                "enterprise_transition_window": {
                    "before_bps": enterprise_option["before_spread_bps"],
                    "after_bps": enterprise_option["after_spread_bps"],
                    "delta_bps": -enterprise_option["risk_cut_bps"],
                    **enterprise_option["result_contract"],
                },
                "project_from_base_year": {
                    "before_bps": before["risk"]["risk_charge_bps"],
                    "after_bps": after["risk"]["risk_charge_bps"],
                    "delta_bps": run_a["delta"]["risk_charge_bps"],
                    **after["risk"]["result_contract"],
                },
                "comparison_rule": (
                    "Do not compare enterprise and project bps directly; metric_id and basis_id "
                    "must both match."
                ),
            },
            "research_summary": {
                "cumulative_alignment_gap_mtco2": gap_by_firm[firm_id][
                    "cumulative_alignment_gap_mtco2"
                ],
                "alignment_result_contract": gap_by_firm[firm_id]["result_contract"],
                "t_required_source": cal.t_required_source,
            },
            "input_evidence": {
                "input_fingerprint_sha256": input_fingerprint,
                "pilot_generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "assets": [
                    {
                        "asset_id": str(row["asset_id"]),
                        "facility": str(row["facility"]),
                        "unit_number": str(row["unit_number"]),
                        "status": str(row["status"]),
                        "source": str(row["source"]),
                    }
                    for _, row in firm_assets.sort_values("asset_id").iterrows()
                ],
                "route_status": str(
                    cal.routes.set_index("route").loc[route_name, "status"]
                ),
                "intervention_status": str(
                    cal.interventions.set_index("intervention_id").loc[
                        PILOT_INTERVENTION, "status"
                    ]
                ),
                "transaction_terms_status": str(
                    cal.transaction_assumptions.iloc[0]["status"]
                ),
            },
            "stress_results": {
                "transaction": transaction_stress,
                "enterprise_fixed_exposure_pricing": risk_stress,
            },
            "reproducibility": {
                "method": "two fresh in-memory API calls with identical request and config",
                "run_a_sha256": replay_a,
                "run_b_sha256": replay_b,
                "exact_match": replay_a == replay_b,
                "status": "AUTOMATED_REPLAY_NOT_INDEPENDENT_ANALYST",
            },
            "forty_point_gates": gates,
            "open_evidence": [
                "executable H2 CfD or lender quote",
                "verified firm-specific required pathway",
                "independent analyst blind rerun",
                "construction, ramp, tax, working-capital and covenant cash-flow model",
                "actual counterparty credit and security terms",
            ],
        }
        cases.append(case)

    return {
        "capability_stage": CAPABILITY_STAGE,
        "release_stage": "INTERNAL_RESEARCH_PREVIEW",
        "forty_point_status": "NOT_ACHIEVED_REAL_CASES_AND_QUOTES_REQUIRED",
        "cases": cases,
    }


def main() -> int:
    cal = load_calibration()
    data = build(cal)
    write_artifact(
        "pilot_cases",
        data,
        cal.param_status,
        claims={
            "cases.decision_summary": claim(
                SCENARIO_CONDITIONAL,
                ["firms_registry", "routes_sensitivity", "transaction_assumptions", "interventions"],
                "dry-run investment screen under illustrative terms",
            ),
            "cases.reproducibility": claim(
                MODEL_CONDITIONAL,
                ["exposure_model", "transaction_assumptions"],
                "exact automated replay; not independent analyst validation",
            ),
            "cases.forty_point_gates": claim(
                OPEN,
                ["firms_registry", "t_required", "transaction_assumptions"],
                "actual cases, executable quotes and blind analyst replay remain open",
            ),
        },
        note="Korea/Japan pilot workflow dry run; not an actual transaction validation",
    )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for case in data["cases"]:
        (REPORT_DIR / f"{case['firm_id'].lower()}_h2_cfd_dry_run.md").write_text(
            _markdown(case)
        )
    print(
        f"OK — {len(data['cases'])} dry-run pilot packs; "
        "40/100 remains open pending actual cases and quotes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
