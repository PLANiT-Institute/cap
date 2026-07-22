"""config/sheets/*.csv + config/scenarios.csv → config/calibration.xlsx 조립.

칼리브레이션 숫자의 편집 가능한 정본은 config/sheets/의 CSV들이다 (git diff 가능).
xlsx는 그 기계적 조립본 — 논문 Table 1의 기계가독 버전. 손으로 xlsx를 고쳤다면
make calibration이 덮어쓴다 (CSV를 고칠 것).
carbon_jump 시트는 scenarios.csv와 동일 스키마로 복제되지만 우선순위는 csv (PLAN §2.1).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config"

SHEETS = ["sigmas", "correlations", "pricing", "lsm"]


def main() -> None:
    out = CFG / "calibration.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        for name in SHEETS:
            pd.read_csv(CFG / "sheets" / f"{name}.csv").to_excel(
                xl, sheet_name=name, index=False
            )
        pd.read_csv(CFG / "scenarios.csv").to_excel(
            xl, sheet_name="carbon_jump", index=False
        )
    print(f"OK — {out.relative_to(ROOT)} ({', '.join(SHEETS + ['carbon_jump'])})")


if __name__ == "__main__":
    main()
