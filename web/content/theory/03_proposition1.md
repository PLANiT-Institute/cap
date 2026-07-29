# 03. Proposition 1 — 수준과 조성의 분리 {#proposition1}

## 주장 P1 {#claim-lambda-invariance}

P1의 정확한 의미는 다음으로 **제한**된다:

> "고정된 exposure vector와 covariance structure 아래에서, 모든 driver에 공통으로 곱해지는 scalar λ와 p_bind는 driver share에서 소거된다."

이것은 동차성에 의한 **수학적 항등(IDENTITY)** 이고, 그 이상이 아니다. 다음 주장은 하지 않는다:
- ~~anatomy가 calibration-independent이다~~
- ~~mix 전체가 empirical하게 proven이다~~
- ~~모든 assumed input은 level에만 들어가고 mix에는 들어가지 않는다~~

시나리오 수준·상대확률, WACC, 전환시점, route 가격·원단위·σ·ρ가 바뀌면 **share도 바뀐다** (회귀 테스트로 고정: `test_shares_move_with_scenarios_and_wacc`). 올바른 표기: **"model-conditional mix · invariant to scalar λ and p_bind"**.

또한 Euler share는 우선 **전환비용 불확실성의 구성**이다 — 시장 위험프리미엄의 구성이 실증 식별된 것이 아니다. SDF/β′λ 기반 asset-pricing identification은 연구 확장사항(OPEN)이며 현재 구현에 존재하지 않는다.

`status: IDENTITY (scalar 소거) · 성립 조건은 A5`

**수치 데모**: λ×p_bind 격자 전체에서 share 벡터의 최대 이탈은 0.0e+00 (소수점 6자리 불변), 수준은 1.64–54.47bps로 스윙 (`model/s05_robustness.py` → `outputs/lambda_invariance.json`).

## 공리 A5 — λ 균일성 {#axiom-uniform-lambda}

단일 λ가 모든 드라이버에 공통이다. P1의 성립 조건은 명제가 아니라 이 공리다. 드라이버별 λ_k를 허용하면 s_k = λ_k·RC_k/Σλ_j·RC_j가 되어 불변성이 깨진다. 탄소정책 점프리스크(시스템적), 수소 기술리스크(부분 분산가능), 원료 상품리스크의 위험가격이 같다는 보장은 없다.

`status: AXIOM · challenged-by: #referee-1 · robustness: s05 λ_k 감응도 모듈`

**λ_k 스트레스 결과**: driver별 λ_k 허용 시 기업별 share 최대 이동 8.2% (`outputs/lambda_k_sensitivity.json`).
