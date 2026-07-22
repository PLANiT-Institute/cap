# 05. 계약 = identification device {#contracts-identification}

## 주장 I1 {#claim-separately-contractible}

각 driver share는 실재하는 상품으로 개별 소거 가능하다: **H₂ CfD(CHPS) → 수소, carbon CfD → 탄소, PPA → 전력, 자본보조 → CAPEX**. Δπ = π(미확약) − π(확약) > 0. 이 개별 계약 가능성이 분해가 회계적 허구가 아님을 식별한다. "어느 계약이 가장 많이 깎는가"는 따름정리로 강등된다 — waterfall의 역할은 처방이 아니라 식별이다.

`status: CLAIM · 코드 대응: model/s06_contracts.py`

**현행 Δπ 서열** (`outputs/delta_pi_ranking.json`, 수준은 λ·p_bind 조건부):

{{delta_pi.table}}

계약 원천 데이터: `data/processed/instruments.parquet` (JOGMEC CfD, CHPS, GX 채권 등 — `data/raw/research/CAP_instruments_2026-07-03.csv`).
