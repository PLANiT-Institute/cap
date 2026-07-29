# LEDGER — proven vs conditional 원장

논리는 [07_ledger_logic.md](07_ledger_logic.md). 아래 자동 섹션은 `make ledger`가
config status에서 생성한다 — 손으로 고치지 말 것. 해설은 이 상단에만 쓴다.

**A5(λ 균일성)의 status는 `assumed`이되, "아직 검증 안 된 가정"이 아니다.** 2026-07 문헌조사
결과 A5를 지지하는 문헌은 한 편도 없고 반대 방향 증거만 7편이다 — 상태는 **반증 우세**다
(`theory/refs.bib`의 `% unsupported: axiom-uniform-lambda`, [08_referee_notes.md](08_referee_notes.md) R1,
`PAPER_DIFF.md` D1). config의 λ=0.4는 수준(bps)만 움직이고 share는 못 움직이므로(P1) 결과의
조성은 여전히 λ에 불변이지만, **driver별 λ_k를 허용하면 조성도 움직인다.** 따라서
`outputs/lambda_k_sensitivity.json`은 부수 robustness가 아니라 주 결과로 읽어야 한다.

조성(share)이 [0,1]에 머무는 것도 항등식이 아니라 **ρ ≥ 0의 귀결**이다. 음의 상관이 들어오면
RC_k < 0이 되어 "탄소 C%, 수소 H%…"라는 서술 자체가 깨진다 (`PAPER_DIFF.md` D4,
회귀 테스트 `test_nonnegative_correlation_bands_are_what_keep_shares_a_composition`).

<!-- AUTO:BEGIN -->

## Claim 수준 상태 (artifact `claims` 블록)

| 상태 | 대상 |
|---|---|
| IDENTITY | share 합=1, scalar λ·p_bind 소거 (P1의 전부) |
| MODEL_CONDITIONAL | driver shares, τ*, 클러스터 분리, envelope, 개입 Δ |
| SCENARIO_CONDITIONAL | conditional risk charge (bps·$/t), ℓ_bind, 파생 p_bind |
| EMPIRICAL | σ_carbon-diffusion (KAU), 연단위 레퍼런스 |
| PROVISIONAL | T_required (surrogate), route별 경로 부재 rescale |
| OPEN | SDF/βλ 식별, Merton식 점프리스크 분리, p_bind 행사정책 |

p_bind는 파라미터가 아니라 파생이다 (Option A: Σ prob(binds=1), 국가별).

## Assumed 파라미터 (conditional risk charge 경유)

| 파라미터 | 값 | status | anchor |
|---|---|---|---|
| lambda | 0.4 | **assumed** | #axiom-uniform-lambda |
| k | 0.4 | **assumed** | #claim-lambda-invariance |
| fx_usdkrw | 1300.0 | **assumed** | #ledger-logic |
| fx_usdjpy | 150.0 | **assumed** | #ledger-logic |
| carbon_base_kr | 14.93 | **measured** | #claim-policy-repricing |
| carbon_base_jp | 3.0 | **banded** | #claim-policy-repricing |

## σ 캘리브레이션 상태

| driver | 값 | band | status | confidence |
|---|---|---|---|---|
| carbon_diffusion | 0.4 | [0.3, 0.5] | **banded** | LOW |
| h2 | 0.3 | [0.25, 0.35] | **banded** | LOW |
| elec_kr_regulated | 0.12 | [0.1, 0.14] | **banded** | MEDIUM |
| elec_kr_smp | 0.135 | [0.11, 0.16] | **banded** | MEDIUM |
| elec_jp | 0.22 | [0.18, 0.25] | **banded** | MEDIUM |
| feedstock | 0.25 | [0.18, 0.35] | **assumed** | LOW |
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
| feedstock×carbon | 0.2 | **assumed** |
| feedstock×elec | 0.1 | **assumed** |
| feedstock×h2 | 0.0 | **assumed** |
| feedstock×capex | 0.0 | **assumed** |

## 시나리오 (탄소 점프 — 확률은 assumed, R2)

| 시나리오 | 수준 USD | 확률 | binds |
|---|---|---|---|
| SQ | 12 | 0.45 | 0 |
| MSR | 35 | 0.35 | 1 |
| CBAM | 85 | 0.2 | 1 |
| SQ | 5 | 0.5 | 0 |
| GX_COMPLIANCE | 30 | 0.35 | 1 |
| CBAM | 85 | 0.15 | 1 |

## 상시 표기 근사·플래그

- 탄소 점프는 **분산 계층에만** 추가 (regime-switching LSM 아님) — [04_carbon_jump.md](04_carbon_jump.md)
- `p_bind_in_exercise` (R5 실험 변형): 구현됨 · 현재 **OFF**
- T_required 출처: **surrogate** — surrogate이면 'provisional; 실증 식별된 기업 의무 아님'. route별 경로 부재 시 h2 곡선 rescale (PROVISIONAL)
- 점프에 확산과 동일 ρ·연σ 적용 — 근사 (Merton 분리 OPEN)
- 개입 coverage·tenor 결합은 1차 근사; residual risk는 0이 되지 않음
- working tree dirty: **True**
- s05 envelope은 공분산 불확실성만 반영 (τ* 재계산 없음)
- measured 승격 이력: ['carbon_diffusion']
- provenance UNKNOWN 출처 파일: 0개

<!-- AUTO:END -->
