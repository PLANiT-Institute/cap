# LEDGER — proven vs conditional 원장

논리는 [07_ledger_logic.md](07_ledger_logic.md). 아래 자동 섹션은 `make ledger`가
config status에서 생성한다 — 손으로 고치지 말 것. 해설은 이 상단에만 쓴다.

<!-- AUTO:BEGIN -->

## Proven (조성 — λ·p_bind 불진입, Prop 1)

- driver shares, cost vs risk 분해, 클러스터 분리, share envelope, Δπ 서열의 *구조*
- 근거: `outputs/lambda_invariance.json`의 share 불변성 데모

## Conditional (수준 — status=assumed 파라미터 경유)

| 파라미터 | 값 | status | anchor |
|---|---|---|---|
| lambda | 0.4 | **assumed** | #axiom-uniform-lambda |
| p_bind | 0.65 | **assumed** | #axiom-budget-binds |
| k | 0.4 | **assumed** | #claim-lambda-invariance |
| fx_usdkrw | 1300.0 | **assumed** | #ledger-logic |
| fx_usdjpy | 150.0 | **assumed** | #ledger-logic |
| carbon_base_kr | 9.5 | **measured** | #claim-policy-repricing |
| carbon_base_jp | 3.0 | **banded** | #claim-policy-repricing |

## σ 캘리브레이션 상태

| driver | 값 | band | status | confidence |
|---|---|---|---|---|
| carbon_diffusion | 0.4 | [0.3, 0.5] | **banded** | LOW |
| h2 | 0.3 | [0.25, 0.35] | **banded** | LOW |
| elec_kr_regulated | 0.12 | [0.1, 0.14] | **banded** | MEDIUM |
| elec_kr_smp | 0.135 | [0.11, 0.16] | **banded** | MEDIUM |
| elec_jp | 0.22 | [0.18, 0.25] | **banded** | MEDIUM |
| capex | 0.15 | [0.1, 0.2] | **assumed** | LOW |

## ρ 상태

| pair | 값 | status |
|---|---|---|
| h2×elec | 0.7 | **banded** |
| elec×carbon | 0.3 | **assumed** |
| h2×carbon | 0.0 | **assumed** |
| h2×capex | 0.0 | **assumed** |
| elec×capex | 0.0 | **assumed** |
| carbon×capex | 0.0 | **assumed** |

## 시나리오 (탄소 점프 — 확률은 assumed, R2)

| 시나리오 | 수준 USD | 확률 | binds |
|---|---|---|---|
| SQ | 12 | 0.45 | 0 |
| MSR | 35 | 0.35 | 1 |
| CBAM | 85 | 0.2 | 1 |

## 상시 표기 근사·플래그

- 탄소 점프는 **분산 계층에만** 추가 (regime-switching LSM 아님) — [04_carbon_jump.md](04_carbon_jump.md)
- `p_bind_in_exercise` (R5 실험 변형): 구현됨 · 현재 **OFF**
- T^GCAM 출처: **surrogate** (raw 미확보 시 logistic surrogate — `data/raw/gcam/MISSING.md`)
- s05 envelope은 공분산 불확실성만 반영 (τ* 재계산 없음)
- measured 승격 이력: ['carbon_diffusion', 'mu_carbon', 'carbon_base_kr']
- provenance UNKNOWN 출처 파일: 0개

<!-- AUTO:END -->
