"""make check-anchors — 이론↔config↔문헌 anchor 검증 (PLAN §4.1).

1) config가 참조하는 모든 anchor가 theory/*.md에 실재하는가
2) 어떤 공리({#axiom-*} 또는 '## 공리' 블록)도 config에서 고아가 아닌가
3) theory/refs.bib의 모든 supports:X가 theory/*.md에 실재하는가
4) 모든 공리·주장·referee note가 최소 하나의 문헌에 지지되는가
   (refs.bib의 '% deferred:' 줄에 적힌 anchor는 면제)
깨지면 exit 1 → CI/빌드 실패.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEORY = ROOT / "theory"
CFG = ROOT / "config"

BIB = THEORY / "refs.bib"

ANCHOR_DEF = re.compile(r"\{#([a-z0-9-]+)\}")
ANCHOR_REF = re.compile(r"#([a-z0-9-]{3,})")
SUPPORTS = re.compile(r"supports:([a-z0-9-]+)")
# 반박 문헌은 counters:로 단다 — anchor 실재는 검증하되 게이트는 채우지 않는다
COUNTERS = re.compile(r"counters:([a-z0-9-]+)")
ANCHOR_WORD = re.compile(r"[a-z0-9-]{3,}")

# 문헌 지지가 필수인 anchor (공리·주장·referee note — 섹션 헤더 #referee-notes는 제외)
GATED = re.compile(r"^(axiom-|claim-|referee-\d)")


def theory_anchors() -> tuple[set[str], set[str]]:
    """(전체 anchor, 공리 anchor)."""
    all_a, axioms = set(), set()
    for md in sorted(THEORY.glob("*.md")):
        if md.name == "LEDGER.md":
            continue
        for line in md.read_text().splitlines():
            m = ANCHOR_DEF.search(line)
            if not m:
                continue
            a = m.group(1)
            all_a.add(a)
            if a.startswith("axiom-") or line.strip().startswith("## 공리"):
                axioms.add(a)
    return all_a, axioms


def config_refs() -> set[str]:
    refs = set()
    for f in list(CFG.rglob("*.csv")):
        for m in ANCHOR_REF.finditer(f.read_text()):
            refs.add(m.group(1))
    return refs


def bib_supports(bib: Path = BIB) -> tuple[set[str], set[str], set[str], set[str]]:
    """(지지 anchor, 반박 anchor, 유예 anchor, 무지지 anchor).

    지시어는 '% deferred: a, b' / '% unsupported: c' 줄에 적는다. 여러 줄 가능하며
    각 줄이 지시어로 시작해야 한다 — 이어쓰기는 인정하지 않는다.

    deferred = 이번 회차에 조사하지 않았다. unsupported = 조사했고 지지 문헌이 없다.
    둘을 구분하는 이유: 후자는 조사 결과이지 미완이 아니다.
    """
    directives = {"deferred:": set(), "unsupported:": set()}
    supports, counters = set(), set()
    if not bib.exists():
        return supports, counters, directives["deferred:"], directives["unsupported:"]
    for line in bib.read_text().splitlines():
        if not line.startswith("%"):  # 주석의 예시가 실제 지지로 잡히지 않게
            supports |= {m.group(1) for m in SUPPORTS.finditer(line)}
            counters |= {m.group(1) for m in COUNTERS.finditer(line)}
            continue
        body = line.lstrip("%").strip()
        for name, acc in directives.items():
            if body.startswith(name):
                acc |= set(ANCHOR_WORD.findall(body[len(name) :]))
    return supports, counters, directives["deferred:"], directives["unsupported:"]


def main() -> int:
    anchors, axioms = theory_anchors()
    refs = config_refs()
    supports, counters, deferred, unsupported = bib_supports()
    missing = sorted(r for r in refs if r not in anchors)
    orphans = sorted(a for a in axioms if a not in refs)
    dangling = sorted((supports | counters) - anchors)
    stale_deferred = sorted((deferred | unsupported) - anchors)
    gated = {a for a in anchors if GATED.match(a)}
    uncited = sorted(gated - supports - deferred - unsupported)
    # 'unsupported' 선언은 반박 문헌을 실제로 걸어둔 anchor에만 허용한다 — 조용한 탈출구 방지
    hollow = sorted(unsupported - counters)
    ok = True
    if missing:
        ok = False
        print("FAIL — config가 참조하지만 theory에 없는 anchor:", file=sys.stderr)
        for a in missing:
            print(f"  #{a}", file=sys.stderr)
    if orphans:
        ok = False
        print("FAIL — config 어디서도 참조되지 않는 고아 공리:", file=sys.stderr)
        for a in orphans:
            print(f"  #{a}", file=sys.stderr)
    if dangling:
        ok = False
        print("FAIL — refs.bib이 참조하지만 theory에 없는 anchor:", file=sys.stderr)
        for a in dangling:
            print(f"  #{a}", file=sys.stderr)
    if hollow:
        ok = False
        print("FAIL — unsupported로 선언했으나 반박 문헌(counters:)도 없는 anchor:", file=sys.stderr)
        for a in hollow:
            print(f"  #{a} — 조사했다면 반박 문헌이라도 남아야 한다", file=sys.stderr)
    if stale_deferred:
        ok = False
        print("FAIL — refs.bib의 deferred/unsupported 목록에 있지만 theory에 없는 anchor:", file=sys.stderr)
        for a in stale_deferred:
            print(f"  #{a}", file=sys.stderr)
    if uncited:
        ok = False
        print("FAIL — 지지 문헌이 없는 공리·주장·referee note:", file=sys.stderr)
        for a in uncited:
            print(f"  #{a}", file=sys.stderr)
        print("  (조사 후 refs.bib에 supports:<anchor>를 달거나 deferred에 명시할 것)", file=sys.stderr)
    if unsupported:
        print("NOTE — 조사했으나 지지 문헌이 없는 anchor (반박 문헌만 존재):")
        for a in sorted(unsupported):
            print(f"  #{a}")
    if redundant := sorted((deferred | unsupported) & supports):
        print("NOTE — 유예 목록에 있으나 이미 지지되는 anchor (deferred에서 뺄 것):")
        for a in redundant:
            print(f"  #{a}")
    if ok:
        print(
            f"OK — anchors {len(anchors)}개, config 참조 {len(refs & anchors)}개, "
            f"공리 {len(axioms)}개 전부 비고아, "
            f"게이트 {len(gated)}개 중 지지 {len(gated & supports)}개·유예 {len(gated & deferred)}개, "
            f"반박 문헌이 붙은 anchor {len(counters)}개"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
