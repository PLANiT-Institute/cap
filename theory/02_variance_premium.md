# 02. 리스크는 평균이 아니라 분산 {#variance-premium}

## 공리 A1 {#axiom-variance-not-mean}

강제 행사될 옵션이 위험한 이유는 기대비용이 아니라 산포다. 크지만 거의 확실한 비용은 알려진 부채이고, 중간이지만 사납게 불확실한 비용이 리스크다. 따라서 anatomy는 평균비용 분해가 아니라 **분산 분해**다.

`status: AXIOM`

이 공리의 경험적 발톱이 Figure 4다: POSCO의 탄소는 비용 share {{cost.POSCO.carbon_pct}} vs 위험 share {{risk.POSCO.carbon_pct}} — 평균으로 나누면 anatomy를 잘못 말한다. (`outputs/cost_vs_risk.json`)

## 공리 A2 — 부호 규약 (단일 실패 지점) {#axiom-budget-binds}

미전환을 short volatility(σ↑ = 악화)로 취급하는 것은 넷제로 예산이 구속력을 가질 때만 성립한다. 예산이 없으면 표준 실물옵션 결과대로 변동성은 대기 옵션 보유자에게 이익이다. 심사자가 "예산이 구속한다"를 기각하면 노출은 옵션 가치로 뒤집힌다. 우리는 이를 숨기지 않고 공리로 명시한다. 구속확률 p_bind는 국가별 시나리오에서 파생되며(Option A: Σ prob(binds=1)) scalar 곱으로 수준에 들어간다 — scalar인 한 share에서 소거되지만(P1), 시나리오 자체가 바뀌면 ℓ_bind를 통해 share도 움직인다.

`status: AXIOM · referenced-by: config/scenarios.csv binds 컬럼 (p_bind 파생)`

## 공리 A3 — 선형 비용함수 {#axiom-linear-cost}

전환비용은 섹터 공통 드라이버 집합에 선형: **B = aᵀX**. 현행 X는 탄소·수소·전력·원료·CAPEX이며, route가 쓰지 않는 성분의 감응도는 0이다. 감응도 벡터 a는 기업의 기술 포지션이 결정한다 — 확약 기업은 발표 route, 미확약 기업은 요구 감축심도에서의 최소비용 feasible route를 상속.

`status: AXIOM · referenced-by: config/routes.csv 전체`

## 공리 A4 — route 감응도 배정 {#axiom-route-sensitivity}

scrap/가스-route의 수소 감응도와 철강 route의 원료 감응도는 0으로 구성상 박힌다. 석유화학 route는 반대로 수소가 0이고 전력·원료 감응도를 가진다. 따라서 클러스터 분리는 절반은 결과, 절반은 route 설계의 귀결이다 — 이를 결과 서술에서 숨기지 않는다. 요구 심도가 어떤 priced route도 초과하는 자산은 anatomy에서 제외하고 stranding 범주로 분리한다(`firms.csv.category = no_feasible_route`).

`status: AXIOM · challenged-by: #referee-3`

**현행 stranding**: {{stranding.asset_ids}} (`outputs/stranding.json`).
