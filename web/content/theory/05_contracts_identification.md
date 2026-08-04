# 05. 계약 = identification device {#contracts-identification}

## 주장 I1 {#claim-separately-contractible}

각 driver는 실재하는 상품으로 **개별 계약 가능**하다 — 이것이 분해의 식별 장치다. 수소 CfD, PPA, circular-feedstock offtake, CAPEX 지원, 탄소정책 계약/제도가 각각 대응한다. 단 계약은 σ=0 스위치가 아니라 **파라미터 변환**이다 (`config/interventions.csv` → `model/lib/interventions.py`): coverage·tenor·basis risk가 남는 잔여를 만들고, "fully contracted → 0 bps" 주장은 하지 않는다. 개입은 τ*·감축경로·anatomy·수준을 **동시에** 재계산한다 (`outputs/intervention_impacts.json` — standalone / sequential / order-averaged(Shapley) 기여 병기; 순차 소거는 적용 순서 의존).

현행 발견: H₂ CfD 단독(계약가 $3/kg, coverage·tenor 반영)은 τ*를 앞당기지 못하고 **오히려 늦춘다** (POSCO +1.11y, charge +0.19bps). 두 메커니즘이 겹친다: ① blended 수소가로도 route가 여전히 사적 적자인데 σ-절단이 행사 트리거인 유리한 실현(싼 수소)을 함께 제거한다; ② 사적 경로의 노출창 [τ*, H]는 계약 tenor(2030–2045) **밖**이다 — 현재 조건의 계약은 문제가 되는 연도에 도달하지 못한다 (감사 2026-08-04). 금융비용 채널(σ_B→스프레드→WACC→τ*, S2)을 배선해도 이 지연은 남는다: 그 채널은 이 추정기의 MC 해상도 아래다. **조합(package)만이 τ*와 gap을 동시에 움직인다** (-1.1y, -24 MtCO₂). carbon reform은 gap을 닫으면서 가격되는 탄소 부담을 **키운다** — timing 수단이지 risk 절감 수단이 아니다.

`status: MODEL_CONDITIONAL · 코드 대응: model/s06_interventions.py`

계약 원천 데이터: `data/processed/instruments.parquet` (JOGMEC CfD, CHPS, GX 채권 등).
