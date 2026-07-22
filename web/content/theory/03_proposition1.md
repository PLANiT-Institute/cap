# 03. Proposition 1 — 수준과 조성의 분리 {#proposition1}

## 주장 P1 {#claim-lambda-invariance}

프리미엄이 π = k·λ·p_bind·σ_B의 곱 구조인 한, driver share s_k = RC_k/σ_B는 (a, σ, R)만의 정확한 함수다. λ와 p_bind는 1차 동차성에 의해 비율에서 소거된다. **케이크의 크기는 조건부여도 조각의 비율은 증명된다** — 이것이 "anatomy는 proven, 수준은 conditional"이라는 원장 구조의 수학적 근거 전부다.

`status: CLAIM (동차성에 의한 항등 — 성립 조건은 A5)`

**수치 데모**: λ×p_bind 격자 전체에서 share 벡터의 최대 이탈은 0.0e+00 (소수점 6자리 불변), 수준은 1.59–45.48bps로 스윙 (`model/s05_robustness.py` → `outputs/lambda_invariance.json`).

## 공리 A5 — λ 균일성 {#axiom-uniform-lambda}

단일 λ가 네 드라이버에 공통이다. P1의 성립 조건은 명제가 아니라 이 공리다. 드라이버별 λ_k를 허용하면 s_k = λ_k·RC_k/Σλ_j·RC_j가 되어 불변성이 깨진다. 탄소정책 점프리스크(시스템적)와 수소 기술리스크(부분 분산가능)의 위험가격이 같다는 보장은 없다.

`status: AXIOM · challenged-by: #referee-1 · robustness: s05 λ_k 감응도 모듈`

**λ_k 스트레스 결과**: driver별 λ_k 허용 시 기업별 share 최대 이동 8.9% (`outputs/lambda_k_sensitivity.json`).
