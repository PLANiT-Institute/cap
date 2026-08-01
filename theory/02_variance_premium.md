# 02. 리스크는 평균이 아니라 분산 {#variance-premium}

## 공리 A1 {#axiom-variance-not-mean}

강제 행사될 옵션이 위험한 이유는 기대비용이 아니라 산포다. 크지만 거의 확실한 비용은 알려진 부채이고, 중간이지만 사납게 불확실한 비용이 리스크다. 따라서 anatomy는 평균비용 분해가 아니라 **분산 분해**다.

`status: AXIOM`

이 공리의 경험적 발톱이 Figure 4다: POSCO의 탄소는 비용 share {{cost.POSCO.carbon_pct}} vs 위험 share {{risk.POSCO.carbon_pct}} — 평균으로 나누면 anatomy를 잘못 말한다. (`outputs/cost_vs_risk.json`)

## 공리 A2 — 부호 규약 (단일 실패 지점) {#axiom-budget-binds}

미전환을 short volatility(σ↑ = 악화)로 취급하는 것은 넷제로 예산이 구속력을 가질 때만 성립한다. 예산이 없으면 표준 실물옵션 결과대로 변동성은 대기 옵션 보유자에게 이익이다. 심사자가 "예산이 구속한다"를 기각하면 노출은 옵션 가치로 뒤집힌다. 우리는 이를 숨기지 않고 공리로 명시한다. 구속확률 p_bind는 국가별 시나리오에서 파생된다(Option A: Σ prob(binds=1)). transition-cost charge는 **조건부 수준 E[level|bind]와 조건부 σ_binding**을 짝지은 뒤 p_bind를 한 번만 곱한다. 별도 gap-loss 레인은 전체 시나리오 손실분포를 직접 사용하므로 p_bind를 다시 곱하지 않는다. scalar인 p_bind는 share에서 소거되지만(P1), 시나리오 자체가 바뀌면 ℓ_bind와 σ_binding을 통해 share도 움직인다.

`status: AXIOM · referenced-by: config/scenarios.csv binds 컬럼 (p_bind 파생)`

## 공리 A3 — 선형 비용함수 {#axiom-linear-cost}

전환비용은 섹터 공통 드라이버 집합에 선형: **B = aᵀX**. 현행 X는 탄소·수소·전력·원료·CAPEX이며, route가 쓰지 않는 성분의 감응도는 0이다. 감응도 벡터 a는 기업의 기술 포지션이 결정한다 — 확약 기업은 발표 route, 미확약 기업은 요구 감축심도에서의 최소비용 feasible route를 상속.

**선형성은 전역 성질이 아니라 국소 근사다 (2026-07 문헌조사).** 문헌은 방향에 따라 갈린다:

- *지지 (탄소가격 방향, 국소)*: 한국 H₂-DRI-EAF 비용이 탄소가 $15/$30/$50에서 $596/$571/$537per t로 움직인다 — 기울기 −1.67, −1.70 USD/t per $1/tCO₂로 사실상 선형(gei2024). 우리가 다루는 탄소가 구간에서는 근사가 성립한다.
- *반증 (수소·시간 방향)*: 수입 수소 캐리어 비용이 해외 생산원가의 **1.5–2.5배**로 붙어 가격 전가가 비선형이고(shibata2023), 감축수단 간 상호작용·적용 순서가 비용을 경로의존적으로 만들며(Rissman 외 2020), MACC의 가법성 자체가 비판받는다(Kesicki 2012). 학습곡선은 시간에 따라 a를 움직인다.

따라서 A3는 **"관측 가격 구간 안에서, 고정 시점의 route 기술 사양 하에서 선형"**으로 읽어야 한다. 두 조건 밖(가격 구간 이탈, 다년 학습효과)에서 B=aᵀX는 1차 테일러 근사이며, 이 사실은 σ_B를 통해 share에까지 전파된다.

`status: AXIOM (국소 근사) · referenced-by: config/routes.csv 전체 · 상세: PAPER_DIFF.md D10·D15`

## 공리 A4 — route 감응도 배정 {#axiom-route-sensitivity}

scrap/가스-route의 수소 감응도와 철강 route의 원료 감응도는 0으로 구성상 박힌다. 석유화학 route는 반대로 수소가 0이고 전력·원료 감응도를 가진다. 따라서 클러스터 분리는 절반은 결과, 절반은 route 설계의 귀결이다 — 이를 결과 서술에서 숨기지 않는다. 요구 심도가 어떤 priced route도 초과하는 자산은 anatomy에서 제외하고 stranding 범주로 분리한다(`firms.csv.category = no_feasible_route`).

`status: AXIOM · challenged-by: #referee-3`

**현행 stranding**: {{stranding.asset_ids}} (`outputs/stranding.json`).
