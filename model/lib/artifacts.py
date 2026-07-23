"""outputs/*.json artifact 쓰기 — epistemic status + field-level lineage.

파라미터 status(measured/banded/assumed)와 별개로 claim 수준 상태를 둔다:
  IDENTITY             수학적 항등 (예: Σ share = 1, scalar λ·p_bind 소거)
  MODEL_CONDITIONAL    모델 구조(노출 정의·선형 B=aᵀX·전환시점 규칙)에 조건부
  SCENARIO_CONDITIONAL 시나리오 수준·확률 가정에 조건부
  EMPIRICAL            관측자료로 검증됨
  PROVISIONAL          surrogate·미확정 데이터 기반
  OPEN                 미구현·미검증

artifact 전체가 아니라 result block별로 {status, depends_on}을 기록한다.
'uses=[] → proven' 패턴은 제거됐다 — share도 MODEL_CONDITIONAL이다 (P1 교정).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "outputs"
FLOAT_DECIMALS = 10  # 재현성: seed 고정 시 JSON diff 0을 위한 반올림

IDENTITY = "IDENTITY"
MODEL_CONDITIONAL = "MODEL_CONDITIONAL"
SCENARIO_CONDITIONAL = "SCENARIO_CONDITIONAL"
EMPIRICAL = "EMPIRICAL"
PROVISIONAL = "PROVISIONAL"
OPEN = "OPEN"


def _round(obj: Any) -> Any:
    if isinstance(obj, float):
        return None if math.isnan(obj) else round(obj, FLOAT_DECIMALS)
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v) for v in obj]
    return obj


def claim(status: str, depends_on: list[str], note: str | None = None) -> dict:
    """result block 하나의 epistemic 상태 선언."""
    out: dict[str, Any] = {"status": status, "depends_on": sorted(depends_on)}
    if note:
        out["note"] = note
    return out


def write_artifact(
    name: str,
    data: dict,
    param_status: dict[str, str],
    claims: dict[str, dict],
    note: str | None = None,
) -> Path:
    """claims: {field_or_block: claim(...)}. depends_on의 assumed 파라미터가
    conditional_on으로 집계된다 (하위호환 필드)."""
    assumed = sorted(
        {
            d
            for c in claims.values()
            for d in c.get("depends_on", [])
            if param_status.get(d) == "assumed"
        }
    )
    payload: dict[str, Any] = {"artifact": name}
    if note:
        payload["note"] = note
    payload["claims"] = claims
    payload["conditional_on"] = assumed
    payload["input_status"] = {
        d: param_status.get(d, "derived")
        for c in claims.values()
        for d in c.get("depends_on", [])
    }
    payload.update(_round(data))
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n")
    return path
