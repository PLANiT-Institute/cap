#!/usr/bin/env python3
"""Generate the isolated Transition Decision Bridge artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bridge import build_from_repo, render_markdown


HERE = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = HERE.parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=HERE / "outputs")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    artifact = build_from_repo(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "risk_premium_decision.json"
    md_path = output_dir / "risk_premium_decision.md"
    json_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md_path.write_text(render_markdown(artifact), encoding="utf-8")
    print(
        f"[transition-decision-bridge] firms={artifact['portfolio']['firm_count']} "
        f"headline={artifact['portfolio']['ev_weighted_headline_bps']:.2f}bps "
        "combined=NOT_PUBLISHED"
    )
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()

