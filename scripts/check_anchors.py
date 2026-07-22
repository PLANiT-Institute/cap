"""make check-anchors — 이론↔config 양방향 anchor 검증 (PLAN §4.1).

1) config가 참조하는 모든 anchor가 theory/*.md에 실재하는가
2) 어떤 공리({#axiom-*} 또는 '## 공리' 블록)도 config에서 고아가 아닌가
깨지면 exit 1 → CI/빌드 실패.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEORY = ROOT / "theory"
CFG = ROOT / "config"

ANCHOR_DEF = re.compile(r"\{#([a-z0-9-]+)\}")
ANCHOR_REF = re.compile(r"#([a-z0-9-]{3,})")


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


def main() -> int:
    anchors, axioms = theory_anchors()
    refs = config_refs()
    missing = sorted(r for r in refs if r not in anchors)
    orphans = sorted(a for a in axioms if a not in refs)
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
    if ok:
        print(f"OK — anchors {len(anchors)}개, config 참조 {len(refs & anchors)}개, 공리 {len(axioms)}개 전부 비고아")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
