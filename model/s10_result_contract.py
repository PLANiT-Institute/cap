"""s10: 투자·연구 결과의 metric/basis/evidence 계약을 artifact로 출력."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import MODEL_CONDITIONAL, claim, write_artifact  # noqa: E402
from model.lib.result_contract import catalog  # noqa: E402
from model.s02_calibrate import load_calibration  # noqa: E402


def main() -> int:
    cal = load_calibration()
    write_artifact(
        "result_contract",
        catalog(),
        cal.param_status,
        claims={
            "bases": claim(
                MODEL_CONDITIONAL,
                ["exposure_model", "transaction_assumptions", "t_required"],
                "계산 기준 metadata; 수치 claim이 아니라 비교 가능성 계약",
            )
        },
        note="metric_id와 basis_id가 모두 같을 때만 수치 직접 비교 허용",
    )
    print("OK — result contract v1.0 (internal research preview)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
