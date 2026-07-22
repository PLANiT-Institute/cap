"""make ledger — theory/LEDGER.md의 자동 생성 섹션 재생성 (PLAN §4.2).

2층 구조: AUTO 마커 사이는 스크립트 소유 (config status에서 생성), 그 밖은 수동 해설.
proven vs conditional 표는 손으로 쓰지 않는다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "theory" / "LEDGER.md"
BEGIN, END = "<!-- AUTO:BEGIN -->", "<!-- AUTO:END -->"

MANUAL_DEFAULT = """# LEDGER — proven vs conditional 원장

논리는 [07_ledger_logic.md](07_ledger_logic.md). 아래 자동 섹션은 `make ledger`가
config status에서 생성한다 — 손으로 고치지 말 것. 해설은 이 상단에만 쓴다.

"""


def auto_section() -> str:
    cfg = ROOT / "config"
    sigmas = pd.read_csv(cfg / "sheets" / "sigmas.csv")
    correlations = pd.read_csv(cfg / "sheets" / "correlations.csv")
    pricing = pd.read_csv(cfg / "sheets" / "pricing.csv")
    lsm = pd.read_csv(cfg / "sheets" / "lsm.csv")
    scenarios = pd.read_csv(cfg / "scenarios.csv")
    manifest_p = ROOT / "outputs" / "manifest.json"
    manifest = json.loads(manifest_p.read_text()) if manifest_p.exists() else {}
    prov = (ROOT / "data" / "DATA_PROVENANCE.md")
    unknown_srcs = prov.read_text().count("| UNKNOWN |") if prov.exists() else 0

    lines = [BEGIN, "", "## Proven (조성 — λ·p_bind 불진입, Prop 1)", "",
             "- driver shares, cost vs risk 분해, 클러스터 분리, share envelope, Δπ 서열의 *구조*",
             "- 근거: `outputs/lambda_invariance.json`의 share 불변성 데모", "",
             "## Conditional (수준 — status=assumed 파라미터 경유)", "",
             "| 파라미터 | 값 | status | anchor |", "|---|---|---|---|"]
    for _, r in pricing.iterrows():
        lines.append(f"| {r['param']} | {r['value']} | **{r['status']}** | {r['theory_anchor']} |")
    lines += ["", "## σ 캘리브레이션 상태", "",
              "| driver | 값 | band | status | confidence |", "|---|---|---|---|---|"]
    for _, r in sigmas.iterrows():
        lines.append(
            f"| {r['driver']} | {r['value']} | [{r['band_lo']}, {r['band_hi']}] | **{r['status']}** | {r['confidence']} |"
        )
    lines += ["", "## ρ 상태", "", "| pair | 값 | status |", "|---|---|---|"]
    for _, r in correlations.iterrows():
        lines.append(f"| {r['driver_i']}×{r['driver_j']} | {r['value']} | **{r['status']}** |")
    lines += ["", "## 시나리오 (탄소 점프 — 확률은 assumed, R2)", "",
              "| 시나리오 | 수준 USD | 확률 | binds |", "|---|---|---|---|"]
    for _, r in scenarios.iterrows():
        lines.append(f"| {r['scenario']} | {r['level_usd']} | {r['prob']} | {r['binds']} |")

    pb_flag = int(dict(zip(lsm["param"], lsm["value"])).get("p_bind_in_exercise", 0))
    lines += [
        "", "## 상시 표기 근사·플래그", "",
        f"- 탄소 점프는 **분산 계층에만** 추가 (regime-switching LSM 아님) — [04_carbon_jump.md](04_carbon_jump.md)",
        f"- `p_bind_in_exercise` (R5 실험 변형): 구현됨 · 현재 **{'ON' if pb_flag else 'OFF'}**",
        f"- T^GCAM 출처: **{manifest.get('t_gcam_source', '미실행')}** (raw 미확보 시 logistic surrogate — `data/raw/gcam/MISSING.md`)",
        f"- s05 envelope은 공분산 불확실성만 반영 (τ* 재계산 없음)",
        f"- measured 승격 이력: {manifest.get('measured_overrides') or '없음 (KAU/SMP/JEPX 미확보)'}",
        f"- provenance UNKNOWN 출처 파일: {unknown_srcs}개",
        "", END,
    ]
    return "\n".join(lines)


def main() -> None:
    if LEDGER.exists():
        text = LEDGER.read_text()
        if BEGIN in text and END in text:
            pre = text.split(BEGIN)[0]
            post = text.split(END)[1]
        else:
            pre, post = text + "\n", "\n"
    else:
        pre, post = MANUAL_DEFAULT, "\n"
    LEDGER.write_text(pre + auto_section() + post)
    print(f"OK — {LEDGER.relative_to(ROOT)} 자동 섹션 갱신")


if __name__ == "__main__":
    main()
