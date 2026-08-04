#!/usr/bin/env python3
"""Generate reconciled joint risk-premium artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from joint_inputs import DEFAULT_REPO_ROOT, build_joint_artifact, render_joint_markdown


HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=HERE / "outputs")
    args = parser.parse_args()

    artifact = build_joint_artifact(args.repo_root)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "joint_risk_premium.json"
    markdown_path = output_dir / "joint_risk_premium.md"
    json_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(render_joint_markdown(artifact), encoding="utf-8")
    print(
        f"[joint-risk-premium] firms={artifact['portfolio']['firm_count']} "
        f"combined={artifact['portfolio']['ev_weighted_combined_bps']:.2f}bps "
        f"status={artifact['publication_gate']['status']}"
    )
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()

