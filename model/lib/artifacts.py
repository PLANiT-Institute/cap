"""outputs/*.json artifact 쓰기 — status 전파 장치 (PLAN §2.1).

uses에 든 파라미터 중 status=assumed가 하나라도 결과 '수준'에 들어가면
conditional_on 배열이 자동으로 붙는다. share(조성) artifact는 uses를 비워
proven으로 남는다 (Prop 1). 원장이 데이터 구조로 존재하게 하는 지점.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "outputs"
FLOAT_DECIMALS = 10  # 재현성: seed 고정 시 JSON diff 0을 위한 반올림


def _round(obj: Any) -> Any:
    if isinstance(obj, float):
        return None if math.isnan(obj) else round(obj, FLOAT_DECIMALS)
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v) for v in obj]
    return obj


def write_artifact(
    name: str,
    data: dict,
    param_status: dict[str, str],
    uses: list[str],
    note: str | None = None,
) -> Path:
    conditional = sorted(p for p in uses if param_status.get(p) == "assumed")
    payload: dict[str, Any] = {"artifact": name}
    if note:
        payload["note"] = note
    payload["conditional_on"] = conditional
    payload["status_of_inputs"] = {p: param_status.get(p, "derived") for p in sorted(uses)}
    payload.update(_round(data))
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n")
    return path
