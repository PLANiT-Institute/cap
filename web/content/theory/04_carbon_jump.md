# 04. 탄소 드라이버 — 확산 + 정책 점프 {#carbon-jump}

## 주장 C1 {#claim-policy-repricing}

한국 철강이 지는 경제적 탄소리스크는 KAU 현물(~$14.93, 얇고 행정적으로 경계지어진 시장)이 아니라 **이산적 정책 repricing** — MSR 도입, 이월제한 개혁, CBAM 연계 — 이다. 이를 확산 + 시나리오 점프혼합으로 표현한다:

$$\sigma^2_{carbon} = \sigma^2_{diff} + \sum_j p_j(\ell_j - \bar\ell)^2/\bar\ell^2$$

시나리오 {SQ $12 · 0.45} · {MSR $35 · 0.35} · {CBAM $85 · 0.20}로 σ_carbon은 0.40("개혁 미가격") → **0.88**("개혁 가격")로 상승하고, POSCO의 탄소 share는 49.5% → 82.2%로 뒤집힌다. 그 차이가 곧 자국 정책 불확실성이 만든 프리미엄의 몫이다 — 한국 철강 프리미엄의 탄소 share는 자국 정부의 정책 궤적에 대한 노출이라는 해석의 엔진.

`status: CLAIM · conditional-on: scenarios.csv 확률 (시장 규율 미비) · challenged-by: #referee-2`

**구현 주의**: 점프는 분산 계층에만 추가된다 (regime-switching LSM 아님). 노출의 *수준*은 구속 조건부 시나리오 평균 ℓ_bind = 53.18 USD/t를 쓰고 (A2: p_bind는 수준에만), *분산*은 전 시나리오 산포로 계산한다. 이 근사는 LEDGER에 상시 표기.
