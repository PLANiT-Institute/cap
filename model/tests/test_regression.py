"""회귀 테스트 — pathway-first 개편 (지시 §9의 17항목).

수치를 맞추기 위한 하드코딩 금지 — 구조적 성질만 고정한다.
stale artifact 방지: 핵심 검증(경로·gap)은 outputs를 읽지 않고
lib/pathways·s07.build를 in-memory로 재계산해 대조한다.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs"

from model.lib.anatomy import DRIVERS, euler_shares  # noqa: E402
from model.lib.gap_pricing import price_alignment_gap  # noqa: E402
from model.lib.interventions import apply_interventions  # noqa: E402
from model.lib.jump import sigma_carbon_binding, sigma_carbon_combined  # noqa: E402
from model.lib.pathways import asset_annual_emissions, condition_gap, firm_pathway  # noqa: E402
from model.lib.result_contract import (  # noqa: E402
    ALIGNMENT_GAP_BASIS,
    ALIGNMENT_GAP_LOSS_BASIS,
    ALIGNMENT_GAP_LOSS_METRIC,
    ALIGNMENT_GAP_RISK_CHARGE_METRIC,
    ENTERPRISE_FIXED_RISK_BASIS,
    ENTERPRISE_RISK_BASIS,
    PROJECT_ECONOMICS_BASIS,
    PROJECT_RISK_BASIS,
    RISK_CHARGE_METRIC,
)
from model.lib.underwriting import annual_charge_usd_m  # noqa: E402
from model.s02_calibrate import load_calibration  # noqa: E402
from model.s07_pathways import build, switch_maps  # noqa: E402


@pytest.fixture(scope="module")
def cal():
    return load_calibration()


@pytest.fixture(scope="module")
def fresh(cal):
    """s07 산출을 in-memory 재생성 — stale artifact 우회."""
    return build(cal)


def art(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


# 1. 자산별 배출 합 = 기업 배출
def test_asset_sum_equals_firm(cal):
    years = np.arange(2026, 2062)
    residual = dict(zip(cal.routes["route"], cal.routes["residual_intensity_tco2_t"]))
    g = cal.firms[cal.firms["firm_id"] == "POSCO"]
    track = firm_pathway(g, {}, years, residual)
    manual = sum(
        asset_annual_emissions(a["capacity_mt_yr"], a["emission_intensity_tco2_t"],
                               residual[a["route"]], None, years)
        for _, a in g.iterrows()
    )
    assert np.allclose(track["emissions_mtco2"], manual)


# 2. BAU는 기존 집약도 유지
def test_bau_flat(fresh):
    pathways, _ = fresh
    for f in pathways["firms"]:
        bau = f["pathways"]["bau"]["emissions_mtco2"]
        assert max(bau) == pytest.approx(min(bau))
        assert f["pathways"]["bau"]["transitioned_capacity_mt"][-1] == 0


# 3/4. private/required 전환연도 = τ*/T_required (자산 단위)
def test_switch_years_match_sources(cal, fresh):
    private, required, _ = switch_maps(cal)
    years = np.arange(int(cal.lsm["base_year"]),
                      int(cal.lsm["base_year"] + cal.lsm["horizon_years"]) + 1)
    residual = dict(zip(cal.routes["route"], cal.routes["residual_intensity_tco2_t"]))
    a = cal.firms[cal.firms["asset_id"] == "A01"].iloc[0]
    tau = private["A01"]
    e = asset_annual_emissions(a["capacity_mt_yr"], a["emission_intensity_tco2_t"],
                               residual[a["route"]], tau, years)
    if tau is not None:
        drop_year = years[np.argmax(np.diff(e) < 0) + 1]
        assert drop_year == pytest.approx(np.ceil(tau), abs=1)
    treq = required["A01"]
    assert treq == cal.t_required["A01"]["year"]


# 5. cumulative alignment gap ≥ 0
def test_gap_nonnegative(fresh):
    _, gaps = fresh
    for f in gaps["firms"]:
        assert f["cumulative_alignment_gap_mtco2"] >= 0
        assert all(g >= 0 for g in f["annual_alignment_gap_mtco2"])


def test_gap_pricing_bridge_is_zero_at_zero_and_linear_in_gap(cal):
    """The physical gap must be a live input to both loss and charge."""
    base_year = int(cal.lsm["base_year"])
    horizon = int(cal.lsm["horizon_years"])
    years = np.arange(base_year, base_year + horizon + 1)
    common = {
        "base_year": base_year,
        "rate": float(cal.firms[cal.firms["firm_id"] == "POSCO"]["wacc"].iloc[0]),
        "horizon_years": horizon,
        "reference_price_usd_tco2": float(cal.pricing["carbon_base_kr"]),
        "scenarios": cal.carbon_scenarios("KR"),
        "risk_price_lambda": float(cal.pricing["lambda"]),
        "risk_scale_k": float(cal.pricing["k"]),
        "enterprise_value_usd_bn": float(
            cal.firms[cal.firms["firm_id"] == "POSCO"]["ev_usd_bn"].iloc[0]
        ),
    }
    zero = price_alignment_gap(np.zeros_like(years, dtype=float), years, **common)
    one = price_alignment_gap(np.ones_like(years, dtype=float), years, **common)
    two = price_alignment_gap(np.full_like(years, 2.0, dtype=float), years, **common)

    assert zero["expected_pv_gap_loss_usd_m"] == 0
    assert zero["gap_risk_charge_bps"] == 0
    assert one["expected_pv_gap_loss_usd_m"] > 0
    assert one["sigma_pv_gap_loss_usd_m"] > 0
    assert two["expected_pv_gap_loss_usd_m"] == pytest.approx(
        2 * one["expected_pv_gap_loss_usd_m"]
    )
    assert two["gap_risk_charge_bps"] == pytest.approx(2 * one["gap_risk_charge_bps"])
    assert "not multiplied again" in one["probability_treatment"]


# 6. τ*를 앞당기는 개입은 cumulative gap을 늘리지 않는다 (일반적으로 감소)
def test_intervention_gap_direction():
    imp = art("intervention_impacts")
    for f in imp["firms"]:
        for iid, iv in f["interventions"].items():
            if iv["delta"]["tau_star_years"] < -1e-9:
                assert iv["delta"]["cumulative_gap_mtco2"] <= 1e-6


# 7. scalar λ/p_bind만 변경 시 고정 exposure 아래 share 불변 (IDENTITY)
def test_p1_scalar_invariance():
    inv = art("lambda_invariance")
    assert inv["max_share_deviation"] < 1e-9
    assert inv["claims"]["max_share_deviation"]["status"] == "IDENTITY"


# 8. 시나리오·WACC를 바꾸면 share가 변할 수 있다 (P1 과잉주장 방지)
def test_shares_move_with_scenarios_and_wacc():
    from model.api import compute

    base = compute()
    scen = compute({"carbon_scenarios_kr": [
        {"scenario": "SQ", "level_usd": 12, "prob": 0.1, "binds": 0},
        {"scenario": "HARD", "level_usd": 120, "prob": 0.9, "binds": 1},
    ]})
    b = next(f for f in base["firms"] if f["firm_id"] == "POSCO")
    s = next(f for f in scen["firms"] if f["firm_id"] == "POSCO")
    assert abs(s["shares_reform"]["carbon"] - b["shares_reform"]["carbon"]) > 1e-3


# 9. p_bind 정의 일관 (Option A: 파생)
def test_p_bind_derived(cal):
    for c in ("KR", "JP"):
        scen = cal.carbon_scenarios(c)
        assert cal.p_bind[c] == pytest.approx(
            float(scen.loc[scen["binds"] == 1, "prob"].sum())
        )


# 10. KR 시나리오가 JP 기업에 자동 적용되지 않음
def test_country_carbon_separation(cal):
    assert cal.l_bind["KR"] != pytest.approx(cal.l_bind["JP"])
    lv = art("premium_levels")
    by = {f["firm_id"]: f for f in lv["firms"]}
    assert by["POSCO"]["p_bind"] == pytest.approx(cal.p_bind["KR"])
    assert by["NIPPON"]["p_bind"] == pytest.approx(cal.p_bind["JP"])
    assert by["POSCO"]["l_bind"] != pytest.approx(by["NIPPON"]["l_bind"])


# 11. no_feasible_route가 priced 풀을 소비하지 않음
def test_stranding_not_in_deployment_pool(cal):
    for aid, t in cal.t_required.items():
        cat = cal.firms.set_index("asset_id").loc[aid, "category"]
        if cat == "no_feasible_route":
            assert t["pool"] == "stranding" and t["year"] is None
        else:
            assert t["pool"] != "stranding"


def test_required_path_pools_never_mix_countries_and_surrogates_are_not_headline(cal):
    for aid, t in cal.t_required.items():
        row = cal.firms.set_index("asset_id").loc[aid]
        if t["pool"] != "stranding":
            assert f":{row['country']}:" in t["pool"]
        if t["status"] == "PROVISIONAL":
            assert t["headline_eligible"] is False
            assert t["pathway_kind"] in {
                "SURROGATE",
                "SURROGATE_RESCALED",
                "INVESTMENT_CYCLE_SURROGATE",
            }


# 12. 기업 평균 전환연도 방식 미사용 — 자산별 전환이 계단으로 나타남
def test_asset_level_steps(fresh):
    pathways, _ = fresh
    posco = next(f for f in pathways["firms"] if f["firm_id"] == "POSCO")
    req = np.array(posco["pathways"]["required"]["emissions_mtco2"])
    drops = np.sum(np.diff(req) < -1e-9)
    assert drops >= 2  # 자산 4개가 서로 다른 해에 전환 → 복수 계단


# 13. intervention 후 residual risk가 근거 없이 0이 되지 않음
def test_residual_never_zero():
    imp = art("intervention_impacts")
    for f in imp["firms"]:
        for iid, iv in f["interventions"].items():
            assert iv["residual"]["risk_charge_bps"] > 0
            assert iv["residual"]["sigma_b_usd_bn"] > 0


# 14. artifact dependency가 실제 assumed input을 포함
def test_claims_carry_assumed_deps():
    lv = art("premium_levels")
    deps = lv["claims"]["firms.premium_bps"]["depends_on"]
    for p in ("lambda", "k", "ev_usd_bn", "scenarios"):
        assert p in deps
    assert "lambda" in lv["conditional_on"]
    sh = art("shares_by_firm")
    assert sh["claims"]["firms.shares"]["status"] == "MODEL_CONDITIONAL"


# 15. manifest가 dirty tree·lineage를 기록
def test_manifest_lineage():
    m = art("manifest")
    for k in ("git_sha", "git_dirty", "git_dirty_before_run", "git_dirty_after_run",
              "code_sha256", "config_sha256",
              "raw_data_sha256", "processed_data_sha256", "seed",
              "t_required_source", "dependency_lock_sha256",
              "web_dependency_lock_sha256", "artifacts"):
        assert k in m
    assert isinstance(m["git_dirty"], bool)
    assert m["git_dirty"] == m["git_dirty_before_run"]


def test_candidate_inputs_are_ingested_but_fail_closed_as_evidence_only():
    contract = json.loads((ROOT / "data/processed/candidate_input_contract.json").read_text())
    params = next(d for d in contract["datasets"] if d["dataset"] == "params_consolidated")
    assert (ROOT / params["processed_file"]).is_file()
    assert params["pipeline_role"] == "calibration_evidence_only"
    assert params["model_effect"].startswith("none_until_DECISIONS")
    assert "do not imply model consumption" in contract["rule"]


# 16. theory live-value 치환 unresolved 없음
def test_theory_render_clean():
    r = subprocess.run(
        ["uv", "run", "python", "scripts/render_theory.py"], cwd=ROOT,
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr


# 검산 유지: σ_carbon 점프혼합 (KR)
def test_sigma_carbon_kr(cal):
    scen = cal.carbon_scenarios("KR")
    assert sigma_carbon_combined(
        0.40, scen["level_usd"].to_numpy(float), scen["prob"].to_numpy(float)
    ) == pytest.approx(0.88, abs=0.005)


def test_binding_charge_uses_matching_conditional_level_and_sigma(cal):
    for country in ("KR", "JP"):
        scen = cal.carbon_scenarios(country)
        conditional = sigma_carbon_binding(
            cal.sigma("carbon_diffusion"),
            scen["level_usd"].to_numpy(float),
            scen["prob"].to_numpy(float),
            scen["binds"].to_numpy(int),
        )
        assert cal.sigma_carbon_binding[country] == pytest.approx(conditional)
        assert cal.sigma_carbon_binding[country] < cal.sigma_carbon_reform[country]

    posco = next(f for f in art("premium_levels")["firms"] if f["firm_id"] == "POSCO")
    assert posco["p_bind"] == pytest.approx(cal.p_bind["KR"])


# 구조 유지: share 합=1 (IDENTITY), 클러스터 분리
def test_shares_identity_and_clusters():
    sh = art("shares_by_firm")
    for f in sh["firms"]:
        assert sum(f["shares"].values()) == pytest.approx(1.0, abs=1e-9)
    sep = art("cluster_separation")
    assert sep["separated"] is True


# 개입 coverage 근사: h2_cfd가 σ_h2를 0으로 만들지 않음
def test_coverage_keeps_basis_risk(cal):
    ps = apply_interventions(cal, "h2_dri", "KR", "elec_kr_regulated", ["h2_cfd"])
    assert 0 < ps.sigma_h2 < cal.sigma("h2")
    ps2 = apply_interventions(cal, "h2_dri", "KR", "elec_kr_regulated", ["capex_subsidy"])
    assert ps2.k_capex_mult < 1.0
    feed = apply_interventions(cal, "circular_olefins", "KR", "elec_kr_smp", ["circular_feedstock"])
    assert 0 < feed.sigma_feedstock < cal.sigma("feedstock")
    naphtha = apply_interventions(cal, "e_cracker", "KR", "elec_kr_smp", ["feedstock_hedge"])
    assert 0 < naphtha.sigma_feedstock < cal.sigma("feedstock")


def test_underwriting_translation_and_ranking():
    """금융 화면은 기존 charge를 번역할 뿐 관측 스프레드로 재명명하지 않는다."""
    uw = art("transition_underwriting")
    assert "not an observed" in uw["definitions"]["model_implied_spread"]
    for firm in uw["firms"]:
        u = firm["underwriting"]
        assert u["annual_risk_charge_usd_m"] == pytest.approx(
            annual_charge_usd_m(u["model_implied_spread_bps"], firm["enterprise_value_usd_bn"])
        )
        assert sum(u["risk_anatomy"].values()) == pytest.approx(1.0)
        gap_loss = firm["alignment_gap_loss"]
        assert gap_loss["risk_result_contract"]["basis_id"] == ALIGNMENT_GAP_LOSS_BASIS
        assert gap_loss["risk_result_contract"]["basis_id"] != u["result_contract"]["basis_id"]
        assert "not add" in gap_loss["aggregation_warning"]
        assert u["sensitivity"]["range_bps"]["lo"] > 0
        assert u["sensitivity"]["range_bps"]["hi"] > u["sensitivity"]["range_bps"]["lo"]
        sensitivity_base = u["sensitivity"]["base"]
        assert any(
            row["lambda"] == sensitivity_base["lambda"]
            and row["p_bind"] == sensitivity_base["p_bind"]
            and row["spread_bps"] == pytest.approx(sensitivity_base["spread_bps"])
            for row in u["sensitivity"]["rows"]
        )
        positive = [o for o in firm["contract_options"] if o["applicable"] and o["risk_cut_bps"] > 0]
        best = firm["decision_summary"]["best_de_risker"]
        if positive:
            assert best["risk_cut_bps"] == pytest.approx(max(o["risk_cut_bps"] for o in positive))
        for option in firm["contract_options"]:
            assert option["residual_charge_ratio"] > 0


def test_deal_screening_keeps_value_risk_and_bankability_separate():
    deals = art("deal_screening")
    assert deals["profile"]["quote_status"] == "ILLUSTRATIVE_NOT_EXECUTABLE"
    for firm in deals["firms"]:
        assert firm["sector"] in {"steel", "petrochemicals"}
        assert all(
            route_case["base"]["economics"]["sector"] == firm["sector"]
            for route_case in firm["route_cases"]
        )
        configured = next(r for r in firm["route_cases"] if r["is_configured_route"])
        assert configured["feasibility_status"] == "CONFIGURED_ROUTE"
        assert configured["meets_configured_decarbonization_depth"] is True
        for route_case in firm["route_cases"]:
            applicable = [o for o in route_case["options"] if o["applicable"]]
            computed_frontier = {
                option["intervention_id"]
                for option in applicable
                if not any(
                    other["net_incremental_value_usd_m"] >= option["net_incremental_value_usd_m"]
                    and other["risk_cut_bps"] >= option["risk_cut_bps"]
                    and (
                        other["net_incremental_value_usd_m"] > option["net_incremental_value_usd_m"]
                        or other["risk_cut_bps"] > option["risk_cut_bps"]
                    )
                    for other in applicable
                    if other is not option
                )
            }
            assert set(route_case["frontier"]["pareto_interventions"]) == computed_frontier
            econ_cases = [route_case["base"]["economics"]] + [
                o["economics"] for o in route_case["options"] if o["applicable"]
            ]
            for econ in econ_cases:
                be = econ["break_evens"]
                assert be["required_green_premium_usd_t"] == pytest.approx(
                    max(be["required_green_premium_npv_usd_t"], be["required_green_premium_dscr_usd_t"])
                )
                if econ["investment"]["decision"] != "INVESTABLE_SCREEN":
                    assert not (econ["investment"]["npv_positive"] and econ["debt"]["dscr_pass"])
            for option in route_case["options"]:
                assert option["counterparty_adjustment"]["expected_loss_usd_m"] >= 0
                assert option["term_sheet"]["modelled_core"]
                assert len(option["term_sheet"]["must_have_clauses"]) >= 3
                if option["contract_decision"] == "DUE_DILIGENCE_CANDIDATE":
                    assert option["economics"]["investment"]["decision"] == "INVESTABLE_SCREEN"
        rec = firm["recommendation"]
        climate_leader = next(
            r for r in firm["route_cases"] if r["route"] == rec["climate_equivalent_leader_route"]
        )
        assert climate_leader["meets_configured_decarbonization_depth"] is True


def test_transaction_api_terms_move_investment_economics():
    from model.api import screen_transaction

    base = screen_transaction({"firm_id": "POSCO", "route": "h2_dri"})
    supported = screen_transaction({
        "firm_id": "POSCO",
        "route": "h2_dri",
        "interventions": ["h2_cfd"],
        "terms": {"green_premium_usd_t": 500.0},
    })
    assert (
        supported["after"]["economics"]["investment"]["project_npv_usd_m"]
        > base["after"]["economics"]["investment"]["project_npv_usd_m"]
    )
    assert supported["after"]["economics"]["break_evens"]["required_green_premium_usd_t"] == 0
    with pytest.raises(ValueError):
        screen_transaction({"firm_id": "POSCO", "terms": {"debt_share": 1.5}})
    with pytest.raises(ValueError):
        screen_transaction({"firm_id": "POSCO", "route": "e_cracker"})


def test_api_separates_fixed_exposure_from_full_counterfactual():
    from model.api import compute

    base_fixed = compute(mode="fixed_exposure")
    base_full = compute(mode="full_counterfactual")
    fixed_posco = next(f for f in base_fixed["firms"] if f["firm_id"] == "POSCO")
    full_posco = next(f for f in base_full["firms"] if f["firm_id"] == "POSCO")
    assert base_fixed["path_recomputed"] is False
    assert base_full["path_recomputed"] is True
    assert full_posco["cumulative_alignment_gap_mtco2"] == pytest.approx(
        fixed_posco["cumulative_alignment_gap_mtco2"]
    )
    assert full_posco["gap_risk_charge_bps"] == pytest.approx(
        fixed_posco["gap_risk_charge_bps"]
    )
    assert (
        full_posco["alignment_gap_risk_result_contract"]["basis_id"]
        == ALIGNMENT_GAP_LOSS_BASIS
    )

    hard_reform = {
        "carbon_scenarios_kr": [
            {"scenario": "HARD", "level_usd": 500.0, "prob": 1.0, "binds": 1},
        ]
    }
    shocked_fixed = compute(hard_reform, mode="fixed_exposure")
    shocked_full = compute(hard_reform, mode="full_counterfactual")
    shocked_fixed_posco = next(
        f for f in shocked_fixed["firms"] if f["firm_id"] == "POSCO"
    )
    shocked_full_posco = next(
        f for f in shocked_full["firms"] if f["firm_id"] == "POSCO"
    )
    assert shocked_fixed_posco["private_transition_year_capacity_weighted"] == pytest.approx(
        fixed_posco["private_transition_year_capacity_weighted"]
    )
    assert (
        shocked_full_posco["private_transition_year_capacity_weighted"]
        < shocked_fixed_posco["private_transition_year_capacity_weighted"]
    )
    assert (
        shocked_full_posco["cumulative_alignment_gap_mtco2"]
        < shocked_fixed_posco["cumulative_alignment_gap_mtco2"]
    )


def test_api_refreshes_all_carbon_regimes_and_rejects_ambiguous_inputs():
    from model.api import compute

    base = compute()
    changed = compute({"sigmas": {"carbon_diffusion": 0.55}})
    for country in ("KR", "JP"):
        assert (
            changed["derived"]["sigma_carbon_reform"][country]
            > base["derived"]["sigma_carbon_reform"][country]
        )
    with pytest.raises(ValueError, match="unknown calculation mode"):
        compute(mode="hybrid")
    with pytest.raises(ValueError, match="unknown override keys"):
        compute({"silent_typo": {}})


def test_petrochemical_feedstock_is_a_live_risk_driver():
    deals = art("deal_screening")
    petro = [firm for firm in deals["firms"] if firm["sector"] == "petrochemicals"]
    assert petro
    assert all(len(firm["route_cases"]) == 3 for firm in petro)
    for firm in petro:
        for route_case in firm["route_cases"]:
            if route_case["route"] == "circular_olefins":
                assert route_case["base"]["risk"]["shares"]["feedstock"] > 0
                option = next(
                    o for o in route_case["options"]
                    if o["intervention_id"] == "circular_feedstock"
                )
                assert option["applicable"] is True
                assert option["risk_cut_bps"] > 0


def test_result_contract_prevents_cross_basis_bps_comparison():
    contract = art("result_contract")
    underwriting = art("transition_underwriting")
    deals = art("deal_screening")

    assert contract["contract_version"] == "1.0"
    assert contract["release_stage"] == "INTERNAL_RESEARCH_PREVIEW"
    assert "metric_id and basis_id both match" in contract["comparison_rule"]

    enterprise = underwriting["firms"][0]["underwriting"]["result_contract"]
    project_case = deals["firms"][0]["route_cases"][0]
    project = project_case["base"]["risk"]["result_contract"]
    economics = project_case["base"]["economics"]["result_contract"]

    assert enterprise["metric_id"] == project["metric_id"] == RISK_CHARGE_METRIC
    assert enterprise["basis_id"] == ENTERPRISE_RISK_BASIS
    assert project["basis_id"] == PROJECT_RISK_BASIS
    assert enterprise["basis_id"] != project["basis_id"]
    assert economics["basis_id"] == PROJECT_ECONOMICS_BASIS

    gap_loss = art("alignment_gap_loss")
    gap_firm = gap_loss["firms"][0]
    assert gap_firm["loss_result_contract"]["metric_id"] == ALIGNMENT_GAP_LOSS_METRIC
    assert (
        gap_firm["risk_result_contract"]["metric_id"]
        == ALIGNMENT_GAP_RISK_CHARGE_METRIC
    )
    assert gap_firm["risk_result_contract"]["basis_id"] == ALIGNMENT_GAP_LOSS_BASIS
    assert gap_firm["risk_result_contract"]["basis_id"] != ENTERPRISE_RISK_BASIS
    assert "not multiplied again" in gap_firm["probability_treatment"]


def test_result_contract_is_attached_across_research_and_investor_artifacts():
    underwriting = art("transition_underwriting")
    impacts = art("intervention_impacts")
    gaps = art("condition_gap")
    deals = art("deal_screening")
    impact_by_firm = {firm["firm_id"]: firm for firm in impacts["firms"]}

    for firm in underwriting["firms"]:
        assert firm["underwriting"]["result_contract"]["basis_id"] == ENTERPRISE_RISK_BASIS
        impact = impact_by_firm[firm["firm_id"]]
        for option in firm["contract_options"]:
            descriptor = option["result_contract"]
            assert descriptor["basis_id"] == ENTERPRISE_RISK_BASIS
            assert option["after_spread_bps"] == pytest.approx(
                impact["interventions"][option["intervention_id"]]["residual"]["risk_charge_bps"]
            )

    for firm in gaps["firms"]:
        descriptor = firm["result_contract"]
        assert descriptor["basis_id"] == ALIGNMENT_GAP_BASIS
        assert descriptor["evidence_grade"] == "PROVISIONAL"

    assert deals["release_stage"] == "INTERNAL_RESEARCH_PREVIEW"
    assert "not directly comparable" in deals["comparison_warning"]
    for firm in deals["firms"]:
        for route_case in firm["route_cases"]:
            cases = [route_case["base"]] + route_case["options"]
            for case in cases:
                assert case["risk"]["result_contract"]["basis_id"] == PROJECT_RISK_BASIS
                assert case["economics"]["result_contract"]["basis_id"] == PROJECT_ECONOMICS_BASIS


def test_internal_release_controls_and_validation_docs_exist():
    required_docs = {
        "MILESTONE_20.md",
        "RESULT_CONTRACT.md",
        "MODEL_CARD.md",
        "VALIDATION_PLAN.md",
        "PUBLIC_RELEASE_CHECKLIST.md",
        "PILOT_CASE_TEMPLATE.md",
        ".github/workflows/ci.yml",
    }
    assert all((ROOT / path).is_file() for path in required_docs)

    page = (ROOT / "web/app/page.tsx").read_text()
    dashboard = (ROOT / "web/components/UnderwritingDashboard.tsx").read_text()
    frontier = (ROOT / "web/components/DealVisuals.tsx").read_text()
    assert "not cleared for external release" in page
    assert "Do not read their numeric difference as contract impact" in dashboard
    assert "not directly comparable with enterprise transition-window bps" in frontier


def test_korea_japan_pilot_dry_runs_are_reproducible_and_fail_closed():
    pilots = art("pilot_cases")
    assert pilots["capability_stage"] == "PILOT_READY_DRY_RUN_30"
    assert pilots["release_stage"] == "INTERNAL_RESEARCH_PREVIEW"
    assert pilots["forty_point_status"] == "NOT_ACHIEVED_REAL_CASES_AND_QUOTES_REQUIRED"
    assert {case["firm_id"] for case in pilots["cases"]} == {"POSCO", "NIPPON"}

    for case in pilots["cases"]:
        replay = case["reproducibility"]
        assert replay["exact_match"] is True
        assert replay["run_a_sha256"] == replay["run_b_sha256"]
        assert replay["status"] == "AUTOMATED_REPLAY_NOT_INDEPENDENT_ANALYST"

        gates = case["forty_point_gates"]
        assert gates["traceable_asset_sources"] is True
        assert gates["automated_deterministic_replay"] is True
        assert gates["executable_quote"] is False
        assert gates["empirical_required_path"] is False
        assert gates["independent_analyst_blind_rerun"] is False
        assert gates["actual_transaction_case"] is False
        assert gates["eligible_for_40"] is False

        decision = case["decision_summary"]
        assert decision["verdict"] == "FID_HOLD"
        assert decision["gross_incremental_project_npv_usd_m"] > 0
        assert (
            decision["counterparty_adjusted_incremental_npv_usd_m"]
            < decision["gross_incremental_project_npv_usd_m"]
        )
        assert decision["decision_at_required_premium_plus_0_1"] == "INVESTABLE_SCREEN"

        enterprise = case["basis_separation"]["enterprise_transition_window"]
        project = case["basis_separation"]["project_from_base_year"]
        assert enterprise["basis_id"] == ENTERPRISE_RISK_BASIS
        assert project["basis_id"] == PROJECT_RISK_BASIS
        assert enterprise["basis_id"] != project["basis_id"]
        for point in case["stress_results"]["enterprise_fixed_exposure_pricing"]:
            assert point["basis_id"] == ENTERPRISE_FIXED_RISK_BASIS

        assert case["input_evidence"]["input_fingerprint_sha256"]
        assert all(asset["source"] for asset in case["input_evidence"]["assets"])

    assert (OUT / "pilots/posco_h2_cfd_dry_run.md").is_file()
    assert (OUT / "pilots/nippon_h2_cfd_dry_run.md").is_file()
    pilot_page = (ROOT / "web/app/pilots/page.tsx").read_text()
    assert "Not two validated deals" in pilot_page
    assert "Automated replay is not an independent analyst review" in pilot_page


# --- D4: RC_k < 0이면 '조성' 서술이 무너진다 (PAPER_DIFF 갱신 4, Tasche 2008) ---


def test_shares_stay_in_unit_interval():
    """s_k가 [0,1] 밖으로 나가면 '탄소 C%, 수소 H%…'라는 서술 자체가 성립하지 않는다."""
    for name in ("shares_by_firm", "share_envelopes"):
        for firm in art(name)["firms"]:
            for key, value in firm.items():
                if not isinstance(value, dict):
                    continue
                for driver, share in value.items():
                    if driver in DRIVERS and isinstance(share, (int, float)):
                        assert -1e-12 <= share <= 1 + 1e-12, f"{name}/{firm.get('firm')}/{key}/{driver}={share}"


def test_nonnegative_correlation_bands_are_what_keep_shares_a_composition():
    """s_k ∈ [0,1]은 항등식이 아니라 ρ ≥ 0의 귀결이다.

    w ≥ 0이므로 ρ의 모든 성분이 음이 아니면 (ρw)_k ≥ 0 → RC_k ≥ 0. 음의 상관을
    config에 넣는 순간 이 성질이 깨지므로, 그때는 조성 서술을 함께 고쳐야 한다.
    """
    rho = pd.read_csv(ROOT / "config" / "sheets" / "correlations.csv")
    assert (rho["band_lo"] >= 0).all(), (
        "음의 상관 밴드가 들어왔다 — s_k가 [0,1] 밖으로 나갈 수 있으므로 "
        "theory/02_variance_premium.md의 '조성' 서술을 먼저 고칠 것"
    )


def test_negative_covariance_actually_breaks_the_composition():
    """위 가드가 지키는 실패 모드를 실제로 보여준다 — 클리핑으로 덮으면 Σ=1이 깨진다."""
    rho = np.eye(5)
    rho[0, 1] = rho[1, 0] = -0.9
    w = np.array([1.0, 0.2, 0.0, 0.0, 0.0])
    _, shares = euler_shares(w, rho)
    assert shares.min() < 0, "음의 공분산에서 RC_k < 0이 나와야 한다"
    assert shares.sum() == pytest.approx(1.0), "음수여도 Euler 항등(Σ=1)은 유지된다"


def test_high_basis_never_improves_the_hedge():
    """basis 밴드: 잔여 위험은 basis가 커질수록 나빠지거나 같아야 한다 (PAPER_DIFF D12)."""
    impacts = art("intervention_impacts")
    shrunk = []
    for firm in impacts["firms"]:
        for iid, iv in firm["interventions"].items():
            lo = iv["delta"]["risk_charge_bps"]
            hi = iv["delta"]["risk_charge_bps_high_basis"]
            assert hi >= lo - 1e-9, f"{firm['firm_id']}/{iid}: hi basis가 lo보다 좋다"
            if lo < -0.5:  # 유의미한 위험 감축이 있던 계약만
                shrunk.append((firm["firm_id"], iid, lo, hi))
    assert shrunk, "위험을 줄이는 계약이 하나도 없으면 이 테스트가 무의미하다"
    # 문헌 최악 basis에서 감축분이 최소 30% 사라지는 사례가 있어야 한다 —
    # 사라지지 않는다면 basis가 결과에 안 들어간다는 뜻이고 그 자체가 버그다.
    assert any(hi > lo * 0.7 for _, _, lo, hi in shrunk)


# --- s12: LEVEL/WEDGE 폐형해 레인 (2026-07-29) ---


def test_level_wedge_structure_and_basis_separation():
    """구조 검산: wedge=(m−1)·LEVEL 항등, var share 합=1, LSM과 basis 격리."""
    from model.lib.result_contract import LEVEL_WEDGE_BASIS

    lw = art("level_wedge")
    assert lw["result_contract"]["basis_id"] == LEVEL_WEDGE_BASIS
    assert lw["result_contract"]["basis_id"] != ENTERPRISE_RISK_BASIS
    for firm in lw["firms"]:
        b = firm["base"]
        assert b["level_gap_usd_t"] >= 0
        assert b["trigger_multiple_project"] > 1
        assert b["wedge_usd_t"] == pytest.approx(
            (b["trigger_multiple_project"] - 1) * b["level_gap_usd_t"]
        )
        assert sum(b["gap_variance_shares"].values()) == pytest.approx(1.0, abs=1e-6)
        # 검증 노트의 핵심: 탄소 단독 귀속(legacy)은 project-σ 방식과 다른 답을 내야 한다
        # (같다면 교정이 무의미했다는 뜻) — h2-route에서 legacy가 더 크다
        if firm["base"]["route"] == "h2_dri":
            assert (
                b["legacy_attribution"]["wedge_usd_t_overstated"] > b["wedge_usd_t"]
            )


# --- LSM drift 일치 (2026-07-31): 행사가치와 시뮬레이션 measure가 같은 μ를 봐야 한다 ---


def test_exercise_value_is_drift_consistent(cal):
    """growth_annuity(μ=0)=annuity 항등 + μ_carbon>0이면 행사가치가 무성장 대비 커진다.

    (F1 회귀 방지: payoff가 현물가를 동결하면 조기 행사가 체계적으로 저평가되어
    τ*가 늦어지고 wedge가 과대된다.)"""
    from model.lib.finance import annuity, growth_annuity
    from model.lib.lsm_engine import exercise_value
    from model.s03_lsm import build_spec

    wacc = float(cal.firms["wacc"].iloc[0])
    for n in (1, 5, 20):
        assert growth_annuity(wacc, 0.0, n) == pytest.approx(annuity(wacc, n))

    asset = cal.firms[cal.firms["category"] == "priced_route"].iloc[0].to_dict()
    spec = build_spec(cal, asset, asset["wacc"], 0)
    assert spec.mu[0] > 0, "carbon μ가 양수라는 전제 (config sigmas.mu) — 바뀌면 이 테스트 재검토"
    x = spec.x0[None, :]
    t = 1
    with_drift = exercise_value(spec, x, t)[0]
    flat_spec = build_spec(cal, asset, asset["wacc"], 0)
    flat_spec.mu = np.zeros_like(spec.mu)
    without_drift = exercise_value(flat_spec, x, t)[0]
    # carbon 절감(+μ)과 h2/elec/capex 비용 하락(−μ) 모두 행사가치를 올린다
    assert with_drift > without_drift
