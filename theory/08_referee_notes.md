# 08. 알려진 도전 — referee notes {#referee-notes}

이 섹션은 약점 은폐를 막는 장치다. 각 항목은 위 공리·주장의 `challenged-by`가 역참조하며, 해소되면 상태를 갱신한다.

## R1 {#referee-1}
λ 균일성(A5)은 P1의 실질 전제다. Prop 1 자체는 동차성에 의한 항등식이라 trivial 비판 가능. → **대응**: s05 λ_k 감응도 모듈 (`outputs/lambda_k_sensitivity.json`, 최대 share 이동 {{lambda_k.max_shift_pct}}), A5의 공리 승격(완료).

**2026-07 문헌조사 갱신 — "미검증"이 아니라 "반증 우세"다.** A5를 지지하는 문헌은 5개 도메인 조사에서 한 편도 나오지 않았고(`theory/refs.bib`의 `% unsupported:`), 반대 방향 증거만 7편이다: 팩터별 위험가격 차이(Chen–Roll–Ross 1986; Bolton–Kacperczyk 2021, 2023), 추정 취약성(Kan–Zhang 1999; Lewellen–Nagel–Shanken 2010), 그리고 [[ready2018]] — 성분별 λ의 **부호가 반대**인 사례로, 이 경우 share 불변성의 해석적 의미가 사라진다. λ_k 감응도는 부수 robustness가 아니라 주 결과로 승격되어야 한다.

또한 방어 논리 자체에 결함이 있다: Kalkbrener(2005)·Denault(2001)의 Euler 배분 **유일성 정리는 coherent 위험측도를 전제**하는데 분산은 단조성을 만족하지 않는다([[artzneretal1999]]). "두 공리계가 수렴하므로 trivial하지 않다"는 답변은 CAP의 측도에 적용되지 않는다. 정확한 대응은 Euler 배분이 **어떤 목적함수 하에서 정당화되는지 직접 명시**하는 것이다([[tasche2008]]). `status: OPEN — 문헌 반증 우세`

## R2 {#referee-2}
점프 도입은 A1(분산=리스크)과 긴장한다 — 점프의 왜도·첨도는 분산이 못 담고, 점프리스크 가격 ≠ 확산리스크 가격(Merton). 시나리오 확률에 시장 규율 부재. → **부분 대응**: 국가별 factor 분리(carbon_kr/carbon_jp/cbam_common), p_bind를 시나리오 파생으로 일원화(Option A), 확산·점프 분산 분해를 artifact에 기록. 점프리스크의 별도 가격화는 여전히 OPEN. `status: PARTIAL`

## R3 {#referee-3}
클러스터 불교차의 절반은 A4의 배정 귀결. 미확약 기업의 route 전환 옵션이 감응도를 mixture로 만들어야 함. Hyundai의 기업 수준 anatomy와 자산 수준 stranding 범주의 모순. → **대응**: firms.csv category 분리 완료 — Hyundai 자산({{stranding.asset_ids}})은 anatomy에서 제외되고 `outputs/stranding.json`으로 분리. `status: PARTIAL`

## R4 {#referee-4}
WACC 순환성 — 전환프리미엄은 WACC의 구성요소인데 WACC 격차로 wedge를 "설명"하는 것은 부분 이중계산. `status: OPEN — 각주 인정 예정` (s03의 WACC-equalized 변형이 부분 대응: `outputs/wedge.json`의 `wedge_years_wacc_eq`)

## R5 {#referee-5}
p_bind가 행사정책(τ*)에 미도입 — LSM은 예산 없는 measure에서 풀고 p_bind는 밖에서 곱함. 내적 비일관. → **대응**: s03 실험 플래그 `p_bind_in_exercise` (기본 off, 현행 {{lsm.p_bind_in_exercise}}). intervention 엔진은 τ*를 파라미터 변환 후 재계산하므로 '수준 따로 타이밍 따로' 비판의 절반은 해소. `status: OPEN`

## R6 {#referee-6}
수익 측면 부재 — 그린스틸 프리미엄, CBAM 수출가격 채널. anatomy는 **gross exposure**임을 명시. `status: SCOPE-NOTE`

## R7 {#referee-7}
**팩터 회전 비불변성** — Euler 리스크기여는 팩터 좌표계 선택에 불변이 아니다([[roncalliweisang2016]]; Meucci 2009). CAP의 다섯 driver는 강하게 상관돼 있으므로(ρ(h2,elec)=0.7), driver를 어떻게 정의·분리하느냐가 share를 바꾼다. P1이 자랑하는 "scalar λ에 불변"보다 **driver 정의의 자유도가 훨씬 큰 취약점**이다. 현재 이 자유도는 `config/routes.csv`의 감응도 벡터 구성에 암묵적으로 고정돼 있고 대안 분해와 비교되지 않았다. → **미대응**. `status: OPEN — 문헌조사에서 신설(2026-07)`

## R8 {#referee-8}
**과점 하 옵션행사** — CAP은 τ*를 자산별 단독 최적화로 푼다. 경쟁 균형에서는 행사 임계값이 낮아지고 대기 프리미엄이 잠식된다([[grenadier2002]]). 한·일 철강은 5사 과점이며 route 선택과 전환 계획이 공개된다. 방향은 한쪽으로 명확하다 — 경쟁을 넣으면 τ*는 **앞당겨지고** wedge와 condition gap은 축소된다. 즉 현행 추정은 상한일 가능성. 추가로 [[decaire2020]]은 실물옵션 행사 시점의 1차 결정요인이 **동종기업의 행사 행동**임을 보인다(순진한 정보집합 하에서 57%가 조기 행사). 이는 τ*를 "사적 최적"으로 부르는 것 자체에 대한 도전이며, R8의 과점 채널과 같은 방향이다. → **미대응**. `status: OPEN — 문헌조사에서 신설(2026-07)`
