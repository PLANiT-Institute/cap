"""References/INDEX.md 생성 — theory/refs.bib이 진실원천, 색인은 파생물.

도메인별로 엔트리를 묶고, anchor를 supports/counters로 나눠 표기한다.
심층 노트(References/<citekey>.md)가 있으면 링크한다.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "theory" / "refs.bib"
OUT = ROOT / "References" / "INDEX.md"

ENTRY = re.compile(r"@(\w+)\{([^,]+),(.*?)\n\}", re.S)
# 한 줄에 여러 필드가 오는 엔트리가 있으므로 줄바꿈에 기대지 않는다. {CO2} 같은 1단 중괄호 허용.
FIELD = re.compile(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}")


def short_author(raw: str) -> str:
    names = [n.split(",")[0].strip() for n in raw.split(" and ")]
    return " & ".join(names) if len(names) <= 2 else f"{names[0]} 외"


def main() -> int:
    entries = []
    for m in ENTRY.finditer(BIB.read_text()):
        fields = dict(FIELD.findall(m.group(3)))
        kw = {k.strip() for k in fields.get("keywords", "").split(",") if k.strip()}
        entries.append(
            {
                "key": m.group(2).strip(),
                "author": " ".join(fields.get("author", "?").split()),
                "title": " ".join(fields.get("title", "?").split()),
                "year": fields.get("year", "?").strip(),
                "domains": sorted(k.split(":", 1)[1] for k in kw if k.startswith("domain:")),
                "supports": sorted(k.split(":", 1)[1] for k in kw if k.startswith("supports:")),
                "counters": sorted(k.split(":", 1)[1] for k in kw if k.startswith("counters:")),
            }
        )

    domains = sorted({d for e in entries for d in e["domains"]})
    lines = [
        "# 문헌 색인 (자동 생성 — `make ledger`)",
        "",
        f"`theory/refs.bib` {len(entries)}편. 이 파일을 손으로 고치지 말 것.",
        "",
        "`+` = 지지(supports), `−` = 반박(counters). 굵은 citekey는 심층 노트가 있다.",
        "",
        "## Anchor 대차대조표",
        "",
        "공리·주장·referee note마다 지지와 반박이 몇 편인지. 논문 쓸 때 이 표에서 시작할 것 —",
        "반박이 지지보다 많은 anchor는 그 비대칭 자체가 서술에 들어가야 한다.",
        "",
        "| anchor | 지지 | 반박 | 반박 문헌 |",
        "|---|---|---|---|",
    ]
    gated = re.compile(r"^(axiom-|claim-|referee-\d|proposition|purpose|wedge|carbon-jump|variance-premium|contracts-identification|contribution)")
    anchor_names = sorted(
        {a for e in entries for a in e["supports"] + e["counters"] if gated.match(a)}
    )
    for a in anchor_names:
        sup = [e["key"] for e in entries if a in e["supports"]]
        con = [e["key"] for e in entries if a in e["counters"]]
        mark = " ⚠" if len(con) > len(sup) else ""
        lines.append(f"| #{a}{mark} | {len(sup)} | {len(con)} | {', '.join(con) or '—'} |")
    lines.append("")
    for d in domains:
        rows = sorted((e for e in entries if d in e["domains"]), key=lambda e: e["key"])
        lines += [f"## {d} ({len(rows)}편)", "", "| citekey | 문헌 | anchor |", "|---|---|---|"]
        for e in rows:
            note = ROOT / "References" / f"{e['key']}.md"
            key = f"**[{e['key']}]({e['key']}.md)**" if note.exists() else e["key"]
            anchors = ", ".join([f"+{a}" for a in e["supports"]] + [f"−{a}" for a in e["counters"]])
            lines.append(
                f"| {key} | {short_author(e['author'])} ({e['year']}), {e['title']} | {anchors or '—'} |"
            )
        lines.append("")

    OUT.write_text("\n".join(lines))
    notes = len(list((ROOT / "References").glob("*.md"))) - 1
    print(f"OK — References/INDEX.md: {len(entries)}편, 도메인 {len(domains)}개, 심층 노트 {notes}편")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
