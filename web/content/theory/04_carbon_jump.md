# 04. 탄소 드라이버 — 확산 + 정책 점프 {#carbon-jump}

## 주장 C1 {#claim-policy-repricing}

한국 철강이 지는 경제적 탄소리스크는 KAU 현물(~$14.93, 얇고 행정적으로 경계지어진 시장)이 아니라 **이산적 정책 repricing** — MSR 도입, 이월제한 개혁, CBAM 연계 — 이다. 이를 확산 + 시나리오 점프혼합으로 표현한다:

$$\sigma^2_{carbon} = \sigma^2_{diff} + \sum_j p_j(\ell_j - \bar\ell)^2/\bar\ell^2$$

탄소는 **국가별 factor**다: carbon_kr(K-ETS)·carbon_jp(GX-ETS)에 CBAM 연계는 cbam_common 공통요인으로 태그된다. KR 시나리오 {SQ $12 · 0.45} · {MSR $35 · 0.35} · {CBAM $85 · 0.20} → σ 0.40→**0.88**, ℓ_bind 53.2; JP 시나리오 {SQ $5 · 0.50} · {GX_COMPLIANCE $30 · 0.35} · {CBAM $85 · 0.15} → σ→**1.13**, ℓ_bind 46.5. KR 시나리오를 JP 기업에 적용하지 않는다. POSCO 탄소 share는 개혁 가격화 시 21.8% → 38.5%.

**p_bind 정의 (Option A)**: p_bind(country) = Σ prob(binds=1) — 시나리오에서 **파생**되며 별도 파라미터가 아니다. 현행 KR 0.55, JP 0.50. 혼합 금지를 스키마가 강제한다.

`status: CLAIM · conditional-on: scenarios.csv 확률 (시장 규율 미비) · challenged-by: #referee-2`

**구현 주의 (근사 2건, 상시 표기)**: ① 점프는 분산 계층에만 추가 (regime-switching LSM 아님). ② 점프에 확산과 **동일한 상관·동일 연σ**를 적용 — Merton식 점프리스크 분리는 미구현(OPEN). transition-cost charge는 `E[level|bind]`와 일치하는 조건부 분산을 쓰며 그 jump share는 KR 56%, JP 65%다. 전체 시나리오의 무조건부 jump share(KR 80%, JP 88%)는 진단용으로 별도 기록하고 같은 charge 식에 섞지 않는다.
