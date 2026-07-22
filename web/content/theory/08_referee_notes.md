# 08. 알려진 도전 — referee notes {#referee-notes}

이 섹션은 약점 은폐를 막는 장치다. 각 항목은 위 공리·주장의 `challenged-by`가 역참조하며, 해소되면 상태를 갱신한다.

## R1 {#referee-1}
λ 균일성(A5)은 미검증 가정이고 P1의 실질 전제다. Prop 1 자체는 동차성에 의한 항등식이라 trivial 비판 가능. → **대응**: s05 λ_k 감응도 모듈 (`outputs/lambda_k_sensitivity.json`, 최대 share 이동 8.9%), A5의 공리 승격(완료). `status: OPEN`

## R2 {#referee-2}
점프 도입은 A1(분산=리스크)과 긴장한다 — 점프의 왜도·첨도는 분산이 못 담고, 점프리스크 가격 ≠ 확산리스크 가격(Merton). 시나리오 확률에 시장 규율 부재 — CBAM certificate 경로·EUA-KAU 스프레드 앵커링 필요. `status: OPEN`

## R3 {#referee-3}
클러스터 불교차의 절반은 A4의 배정 귀결. 미확약 기업의 route 전환 옵션이 감응도를 mixture로 만들어야 함. Hyundai의 기업 수준 anatomy와 자산 수준 stranding 범주의 모순. → **대응**: firms.csv category 분리 완료 — Hyundai 자산(A03, A08)은 anatomy에서 제외되고 `outputs/stranding.json`으로 분리. `status: PARTIAL`

## R4 {#referee-4}
WACC 순환성 — 전환프리미엄은 WACC의 구성요소인데 WACC 격차로 wedge를 "설명"하는 것은 부분 이중계산. `status: OPEN — 각주 인정 예정` (s03의 WACC-equalized 변형이 부분 대응: `outputs/wedge.json`의 `wedge_years_wacc_eq`)

## R5 {#referee-5}
p_bind가 행사정책(τ*)에 미도입 — LSM은 예산 없는 measure에서 풀고 p_bind는 밖에서 곱함. 내적 비일관. → **대응**: s03 실험 플래그 `p_bind_in_exercise` (기본 off, 현행 OFF). `status: OPEN`

## R6 {#referee-6}
수익 측면 부재 — 그린스틸 프리미엄, CBAM 수출가격 채널. anatomy는 **gross exposure**임을 명시. `status: SCOPE-NOTE`
