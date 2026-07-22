"""회귀 테스트 — 논문 검산 고정 (PLAN 실행순서 3).

논문 대조 수치는 여기 '기대값'으로 고정된다. 파이프라인이 바뀌어 깨지면
그것은 발견이거나 회귀 — PAPER_DIFF.md 갱신 없이 조용히 통과 기준을 바꾸지 말 것.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs"

from model.lib.anatomy import DRIVERS, euler_shares  # noqa: E402
from model.lib.jump import sigma_carbon_combined  # noqa: E402
from model.s02_calibrate import load_calibration  # noqa: E402


@pytest.fixture(scope="module")
def cal():
    return load_calibration()


def art(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


def test_sigma_carbon_040_to_088(cal):
    """논문 §04 검산: 시나리오 {12·.45, 35·.35, 85·.20} → 0.40 → 0.88."""
    levels = cal.scenarios["level_usd"].to_numpy(float)
    probs = cal.scenarios["prob"].to_numpy(float)
    assert sigma_carbon_combined(0.40, levels, probs) == pytest.approx(0.88, abs=0.005)
    assert cal.sigma_carbon_reform == pytest.approx(
        sigma_carbon_combined(cal.sigma("carbon_diffusion"), levels, probs)
    )


def test_euler_shares_sum_to_one():
    w = np.array([3.0, 2.0, 1.0, 0.5])
    rho = np.array([[1, 0, 0.3, 0], [0, 1, 0.7, 0], [0.3, 0.7, 1, 0], [0, 0, 0, 1.0]])
    sigma_b, shares = euler_shares(w, rho)
    assert shares.sum() == pytest.approx(1.0)
    assert sigma_b > 0


def test_shares_by_firm_sum_to_one():
    for f in art("shares_by_firm")["firms"]:
        assert sum(f["shares"].values()) == pytest.approx(1.0, abs=1e-9)
        assert sum(f["shares_reform"].values()) == pytest.approx(1.0, abs=1e-9)


def test_lambda_invariance_prop1():
    """Prop 1: λ×p_bind 격자 전체에서 share 불변 (소수점 6자리), 수준은 스윙."""
    inv = art("lambda_invariance")
    assert inv["max_share_deviation"] < 1e-6
    assert inv["level_max_bps"] / inv["level_min_bps"] > 10  # 수준은 크게 스윙


def test_cluster_separation():
    sep = art("cluster_separation")
    assert sep["separated"] is True
    assert sep["gap"] > 0


def test_reform_raises_carbon_share():
    """§04: reform-priced에서 모든 기업의 carbon share 상승."""
    for f in art("shares_by_firm")["firms"]:
        assert f["shares_reform"]["carbon"] > f["shares"]["carbon"]


def test_h2_route_zero_h2_only_for_grid_cluster():
    """A4: scrap/가스 route의 수소 감응도는 구성상 0."""
    for f in art("shares_by_firm")["firms"]:
        if f["cluster"] == "grid_route":
            assert f["shares"]["h2"] == pytest.approx(0.0, abs=1e-12)
        else:
            assert f["shares"]["h2"] > 0


def test_stranding_excluded_from_anatomy():
    """no_feasible_route 자산은 anatomy 부재 + stranding 존재 (Hyundai A03/A08)."""
    anatomy_firms = {f["firm_id"] for f in art("shares_by_firm")["firms"]}
    stranded = {a["asset_id"] for a in art("stranding")["assets"]}
    assert "HYUNDAI" not in anatomy_firms
    assert stranded == {"A03", "A08"}


def test_delta_pi_positive():
    """I1: Δπ = π(미확약) − π(확약) > 0, 전 기업."""
    for r in art("delta_pi_ranking")["ranking"]:
        assert r["delta_pi_bps"] > 0


def test_conditional_on_machinery():
    """status 전파: 수준 artifact엔 conditional_on 비어있지 않고, 조성 artifact엔 비어있음."""
    assert "lambda" in art("premium_levels")["conditional_on"]
    assert "p_bind" in art("premium_levels")["conditional_on"]
    assert art("shares_by_firm")["conditional_on"] == []
    assert art("cost_vs_risk")["conditional_on"] == []


def test_sigma_linearity_r2():
    assert art("sigma_linearity")["r_squared"] > 0.9


def test_manifest_records_gcam_source():
    m = json.loads((OUT / "manifest.json").read_text())
    assert m["t_gcam_source"] in ("surrogate", "gcam_raw")
    assert m["seed"] == int(load_calibration().lsm["seed"])


def test_cost_vs_risk_differ():
    """A1의 경험적 발톱: 평균 분해 ≠ 분산 분해 (POSCO 탄소 36% vs 44% 류)."""
    for f in art("cost_vs_risk")["firms"]:
        diffs = [abs(f["cost_shares"][d] - f["risk_shares"][d]) for d in DRIVERS]
        assert max(diffs) > 0.01


def test_calculator_api_overrides():
    """계산기 원칙: compute()가 파일 안 건드리고 오버라이드 반영 — MCP 시임."""
    from model.api import compute

    base = compute()
    hi = compute({"pricing": {"lambda": 0.8}})
    for b, h in zip(base["firms"], hi["firms"]):
        assert h["premium_bps"] == pytest.approx(b["premium_bps"] * 0.8 / 0.4)  # 수준 스케일
        for d in DRIVERS:
            assert h["shares"][d] == pytest.approx(b["shares"][d])  # 조성 불변 (P1)
    scen = compute({"carbon_scenarios": [
        {"scenario": "SQ", "level_usd": 12, "prob": 0.5, "binds": 0},
        {"scenario": "REFORM", "level_usd": 60, "prob": 0.5, "binds": 1},
    ]})
    assert scen["derived"]["l_bind"] == pytest.approx(60.0)
    assert scen["derived"]["sigma_carbon_reform"] != pytest.approx(base["derived"]["sigma_carbon_reform"])
