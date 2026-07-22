"""DATA_PROVENANCE.md 생성 + raw 완전등록 검증.

data/provenance.yaml의 패턴 레지스트리를 data/raw/ 실파일과 대조:
- 미등록 파일 발견 → exit 1 (make ingest 실패 조건)
- 등록됐지만 부재한 필수 파일은 문제 아님 (선택 수집 패턴)
- 파일마다 SHA256 계산해 한 줄씩 DATA_PROVENANCE.md에 기록
"""
from __future__ import annotations

import fnmatch
import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
REGISTRY = ROOT / "data" / "provenance.yaml"
OUT = ROOT / "data" / "DATA_PROVENANCE.md"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    registry = yaml.safe_load(REGISTRY.read_text())["registry"]
    files = sorted(
        p for p in RAW.rglob("*") if p.is_file() and p.name != ".DS_Store"
    )
    rows, unregistered = [], []
    for p in files:
        rel = p.relative_to(RAW).as_posix()
        entry = next((e for e in registry if fnmatch.fnmatch(rel, e["pattern"])), None)
        if entry is None:
            unregistered.append(rel)
            continue
        rows.append((rel, entry, sha256(p)))

    if unregistered:
        print("PROVENANCE FAIL — 미등록 raw 파일:", file=sys.stderr)
        for rel in unregistered:
            print(f"  {rel}", file=sys.stderr)
        print("data/provenance.yaml에 등록 후 재실행.", file=sys.stderr)
        return 1

    lines = [
        "# DATA PROVENANCE",
        "",
        "`scripts/provenance.py`가 `data/provenance.yaml`에서 자동 생성 — 직접 수정 금지.",
        "출처 불명 파일은 source=UNKNOWN으로 표기되고 LEDGER에 반영된다.",
        "",
        "| 파일 | 내용 | 출처 | 수집일 | 단위 | 라이선스 | SHA256 |",
        "|---|---|---|---|---|---|---|",
    ]
    for rel, e, digest in rows:
        lines.append(
            f"| `{rel}` | {e['contents']} | {e['source']} | {e['collected']} "
            f"| {e['units']} | {e['license']} | `{digest[:16]}…` |"
        )
    unknown = [rel for rel, e, _ in rows if str(e["source"]).upper() == "UNKNOWN"]
    lines += ["", f"등록 파일 {len(rows)}개 · 출처불명 {len(unknown)}개"]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"OK — {len(rows)} files registered, {len(unknown)} UNKNOWN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
