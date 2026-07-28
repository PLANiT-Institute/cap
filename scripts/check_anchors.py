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


def bib_supports(bib: Path = BIB) -> tuple[set[str], set[str]]:
    """(문헌이 지지하는 anchor, 유예 anchor).

    유예는 '% deferred: a, b, c' 줄에 적는다. 여러 줄 가능하며 각 줄이
    'deferred:'로 시작해야 한다 — 이어쓰기는 인정하지 않는다.
    """
    if not bib.exists():
        return set(), set()
    supports, deferred = set(), set()
    for line in bib.read_text().splitlines():
        if not line.startswith("%"):  # 주석의 예시가 실제 지지로 잡히지 않게
            supports |= {m.group(1) for m in SUPPORTS.finditer(line)}
            continue
        body = line.lstrip("%").strip()
        if body.startswith("deferred:"):
            deferred |= set(ANCHOR_WORD.findall(body[len("deferred:") :]))
    return supports, deferred


def main() -> int:
    anchors, axioms = theory_anchors()
    refs = config_refs()
    supports, deferred = bib_supports()
    missing = sorted(r for r in refs if r not in anchors)
    orphans = sorted(a for a in axioms if a not in refs)
    dangling = sorted(s for s in supports if s not in anchors)
    stale_deferred = sorted(d for d in deferred if d not in anchors)
    gated = {a for a in anchors if GATED.match(a)}
    uncited = sorted(gated - supports - deferred)
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
        print("FAIL — refs.bib이 supports하지만 theory에 없는 anchor:", file=sys.stderr)
        for a in dangling:
            print(f"  #{a}", file=sys.stderr)
    if stale_deferred:
        ok = False
        print("FAIL — refs.bib의 deferred 목록에 있지만 theory에 없는 anchor:", file=sys.stderr)
        for a in stale_deferred:
            print(f"  #{a}", file=sys.stderr)
    if uncited:
        ok = False
        print("FAIL — 지지 문헌이 없는 공리·주장·referee note:", file=sys.stderr)
        for a in uncited:
            print(f"  #{a}", file=sys.stderr)
        print("  (조사 후 refs.bib에 supports:<anchor>를 달거나 deferred에 명시할 것)", file=sys.stderr)
    if redundant := sorted(deferred & supports):
        print("NOTE — 유예 목록에 있으나 이미 지지되는 anchor (deferred에서 뺄 것):")
        for a in redundant:
            print(f"  #{a}")
    if ok:
        print(
            f"OK — anchors {len(anchors)}개, config 참조 {len(refs & anchors)}개, "
            f"공리 {len(axioms)}개 전부 비고아, "
            f"게이트 {len(gated)}개 중 지지 {len(gated & supports)}개·유예 {len(gated & deferred)}개"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
