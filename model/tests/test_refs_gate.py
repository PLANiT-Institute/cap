"""문헌 게이트 파싱 회귀 — 주석의 예시가 실제 지지로 잡히면 게이트가 무력해진다."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("check_anchors", ROOT / "scripts" / "check_anchors.py")
check_anchors = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_anchors)

BIB_SAMPLE = """\
% 예시: keywords = {domain:jump-risk, supports:referee-9}
% deferred: axiom-linear-cost, referee-4
% deferred: referee-6
% 이 줄은 지시어가 아니므로 유예 목록에 들어가면 안 된다: axiom-uniform-lambda

@article{merton1976,
  title = {Option pricing when underlying stock returns are discontinuous},
  keywords = {domain:jump-risk, supports:referee-2, supports:axiom-variance-not-mean},
}
"""


def test_bib_supports(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(BIB_SAMPLE)
    supports, deferred = check_anchors.bib_supports(bib)

    assert supports == {"referee-2", "axiom-variance-not-mean"}
    assert "referee-9" not in supports, "주석 속 예시가 지지로 잡히면 안 된다"
    assert deferred == {"axiom-linear-cost", "referee-4", "referee-6"}
    assert "axiom-uniform-lambda" not in deferred, "deferred: 로 시작하지 않는 주석은 무시"


def test_gate_excludes_section_header() -> None:
    """#referee-notes는 섹션 헤더이지 referee note가 아니다."""
    assert check_anchors.GATED.match("referee-1")
    assert check_anchors.GATED.match("axiom-uniform-lambda")
    assert check_anchors.GATED.match("claim-lambda-invariance")
    assert not check_anchors.GATED.match("referee-notes")
    assert not check_anchors.GATED.match("wedge")


def test_missing_bib_is_empty(tmp_path: Path) -> None:
    assert check_anchors.bib_supports(tmp_path / "nope.bib") == (set(), set())
