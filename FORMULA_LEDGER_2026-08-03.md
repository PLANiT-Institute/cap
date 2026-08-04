# CAP 산식·가정 대장 (FORMULA LEDGER) — 2026-08-03

> 목적: 툴의 **모든 산식과 가정값**을 프로세스 순서로 완전 열거하고, 할인율·드리프트의
> 사용처를 교차 감사한다. 근거: `model/`·`config/`·`outputs/` 전량 정독 + 재계산 검증
> (JFE/KOBE share 소수 4자리 재현, LSM seed 재현, σ-스케일 실험 8~12 seed).
> 이 문서는 감사 기록이며 정본 규칙은 CLAUDE.md·RESULT_CONTRACT.md가 유지한다.

---

## A. 가정값 대장 — config (모든 파라미터)

### A1. 변동성·드리프트 (`config/sheets/sigmas.csv`)

| driver | σ | band | **μ (drift)** | status |
|---|---|---|---|---|
| carbon_diffusion | 0.40 | 0.30–0.50 | **+0.086** | banded (KAU 확보 시 measured 승격) |
| h2 | 0.30 | 0.25–0.35 | **−0.05** | banded |
| elec_kr_regulated | 0.12 | 0.10–0.14 | −0.015 | banded |
| elec_kr_smp | 0.135 | 0.11–0.16 | −0.015 | banded |
| elec_jp | 0.22 | 0.18–0.25 | −0.015 | banded |
| feedstock | 0.25 | 0.18–0.35 | 0.00 | assumed |
| capex | 0.15 | 0.10–0.20 | **−0.03** | assumed |

μ는 **LSM 시뮬레이션과 행사가치 양쪽**에 들어간다 (§D 참조 — 이 문서의 핵심 발견).

### A2. 상관 (`config/sheets/correlations.csv`)

| pair | ρ | band | status |
|---|---|---|---|
| h2–elec | **0.70** | 0.55–0.80 | banded |
| elec–carbon | 0.30 | 0.00–0.50 | assumed |
| feedstock–carbon | 0.20 | 0.00–0.40 | assumed |
| feedstock–elec | 0.10 | 0.00–0.30 | assumed |
| h2–carbon, h2–capex, elec–capex, carbon–capex, feedstock–h2, feedstock–capex | 0.00 | 상단 0.2–0.3 | assumed |

### A3. 가격·리스크 스케일 (`config/sheets/pricing.csv`)

| param | 값 | status | 들어가는 곳 |
|---|---|---|---|
| λ | 0.40 | **assumed** | s04/s05/s13 charge, s08 surface |
| k | 0.40 | **assumed** | 상동 |
| carbon_base_kr | $14.93 | measured (2026-06-30 KAU) | LSM x₀, s13 기준가 |
| carbon_base_jp | $3.0 | banded | LSM x₀, s13 기준가 |
| fx_usdkrw / fx_usdjpy | 1300 / 150 | assumed | ingest 병기 |

### A4. 엔진 파라미터 (`config/sheets/lsm.csv`)

seed 42 · base_year 2026 · horizon **35년(→2061)** · n_paths 4000 · basis_degree 3 ·
**tau_exercise_threshold 0.5** (p_ex<0.5 → τ*=None) · mu_anchor_years 15 ·
p_bind_in_exercise **off** · λ그리드 0.15–0.65×6 · p_bind그리드 0.25–0.95×8 ·
band draws 200 · **dp_delta 0.05 (s12 영구옵션 δ — 고정 상수)** ·
λ_k = carbon 0.50 / h2 0.35 / elec 0.35 / feedstock 0.40 / capex 0.30 (전부 assumed)

### A5. 자산 (`config/firms.csv` — 13행)

| 기업 | 자산 | 용량 Mt | reline | 강도 | route | **WACC** | **hurdle** | EV $bn |
|---|---|---|---|---|---|---|---|---|
| POSCO | A01/A02/A06/A07 | 4.2/3.5/3.3/3.5 | 2037/33/31/36 | 2.0–2.1 | h2_dri | **7.5%** | 10% | 40 |
| HYUNDAI | A03/A08 | 3.8/3.7 | 2040/28 | 2.1 | scrap_eaf (no_feasible) | **10.5%** | 12% | 18 |
| NIPPON | A04/A09 | 5.2/2.8 | 2034/32 | 1.9 | h2_dri | **5.75%** | 6% | 40 |
| JFE | A05/A10 | 4.5/3.7 | 2036/34 | 2.0 | scrap_eaf | **5.75%** | 6% | 15 |
| KOBE | A11 | 2.6 | 2033 | 1.95 | ng_dri | **5.75%** | 6% | 8 |
| KR_NCC | P01 | 2.0 | 2032 | 1.30 | e_cracker | 7.0% | 9% | 15 |
| JP_NCC | P02 | 1.3 | 2030 | 1.30 | ccus_cracker | 5.0% | 7% | 10 |

주의: **hurdle 열은 LSM에서 사용되지 않는다** — s09 거래 스크린의 할인율로만 쓰인다 (§D R-3).

### A6. Route 감응도 (`config/routes.csv`)

| route | q_h2 kg/t | q_elec MWh/t | q_feed t/t | 잔여강도 | K $/t | avoided | other_opex |
|---|---|---|---|---|---|---|---|
| h2_dri | 60 | 0.8 | 0 | 0.10 | 470 | 436.5 | 380 |
| scrap_eaf | 0 | 0.60 | **0** | 0.40 | 200 | 436.5 | **500** (고철 1.1t×$400 포함, 결정론) |
| ng_dri | 0 | 0.70 | **0** | 0.80 | 300 | 436.5 | 460 (NG 포함, 결정론) |
| e_cracker | 0 | 1.50 | 1.30 | 0.13 | 650 | 1050 | 100 |
| ccus_cracker | 0 | 0.65 | 1.30 | 0.39 | 550 | 1050 | 150 |
| circular_olefins | 0 | 1.10 | 1.15 | 0.26 | 900 | 1050 | 140 |

기준가: p_h2 $5.5/kg · p_elec KR $75 / JP $95 · p_feedstock $650 (석유화학; 철강은 더미 $1).
**철강의 원료(고철·NG·석탄·광석) 가격은 avoided/other_opex 안의 상수** — 확률 드라이버가 아니다.

### A7. 탄소 시나리오 (`config/scenarios.csv`) 와 파생값

| 국가 | 시나리오 (수준$·확률·구속) | 파생: p_bind | ℓ̄ | ℓ_bind | σ_reform | σ_binding |
|---|---|---|---|---|---|---|
| KR | SQ 12·0.45·0 / MSR 35·0.35·1 / CBAM 85·0.20·1 | **0.55** | 34.65 | **53.18** | 0.88 | 0.60 |
| JP | SQ 5·0.50·0 / GX 30·0.35·1 / CBAM 85·0.15·1 | **0.50** | 23.25 | **46.50** | 1.13 | 0.67 |

### A8. 개입 (`config/interventions.csv` — 전부 assumed)

| id | 변환 | 값 | coverage | tenor | basis σ (lo/hi) |
|---|---|---|---|---|---|
| h2_cfd | p_h2·σ_h2 CfD | strike $3.0/kg | 0.7 | 2030–45 | 0.05/0.285 |
| ppa | p_elec·σ_elec CfD | $65/MWh | 0.6 | 2028–43 | 0.03/0.128 |
| capex_subsidy | K ×0.7 | −30% | 1.0 | 2026–61 | — |
| carbon_reform | SQ확률 절반→구속 재배분 | shift 1.0 | — | 2027– | — |
| concessional | WACC −150bp | −0.015 | 1.0 | — | — |
| feedstock_hedge / circular_feedstock | p_feed·σ_feed collar | $650 | 0.7/0.65 | 2028–44 | 0.06·0.08/0.238 |
| package | 위 조합 (concessional 제외) | — | — | — | — |

### A9. 거래 프로파일 (`config/transaction_assumptions.csv` — assumed)

life 25y · debt 60% · tenor 15y · target DSCR 1.30 · green premium $0 · fees $0 ·
PD 1%/yr · recovery 40% · IRR ceiling 100%

### A10. s02가 만드는 파생값

- k_offcycle_mult = K12_mid / K11_mid = **1.489** (reline 밖 전환의 CAPEX 페널티)
- T_required: sector×country×route 풀에서 **reline 연도순 큐 + 누적용량 문턱** (§C s02)
- carbon_var_decomp (진단용): jump_var = σ_reform² − σ_diff²

---

## B. 프로세스별 산식 대장

### s01_ingest — raw→parquet
결측 NaN 유지 · ISO/USD 병기 · σ 승격 규칙: 시계열 도착 시
`σ = std(Δln P) × √연율화` 로 measured 대체 (KAU→carbon_diffusion, SMP→elec_kr_smp, 상관도 실측 대체).

### s02_calibrate — CalibrationSet (단일 관문)
- ℓ̄ = Σ pⱼ ℓⱼ · **ℓ_bind = Σ pⱼℓⱼ·1(bind) / p_bind** · p_bind = Σ pⱼ·1(bind)
- **σ_carbon_reform² = σ_diff² + Σ pⱼ(ℓⱼ−ℓ̄)²/ℓ̄²** (점프혼합; 분산 계층에만)
- σ_binding: 구속 조건부 분포로 동일 공식 (E[ℓ|bind]와 짝, p_bind는 한 번만 곱하는 규약)
- T_required(자산) = 풀 곡선 Q(t)가 누적용량 문턱에 닿는 첫 해.
  h2_dri: logistic surrogate L=38Mt (KR raw 없음 — MISSING). **비H₂ route: 곡선을
  풀 용량으로 재정규화 → 마지막 자산은 구조적으로 지평말(2061)** [결함, §D R-6]

### s03_lsm — 사적 전환시점 τ*
- 상태: 5-드라이버 GBM. `Δln X = (μ − σ²/2) + σ·Chol(ρ)·z`, x₀ = [탄소현물, 5.5, 75/95, p_feed, K]
- **행사가치(교환옵션 payoff)**:
  `EV(t) = Δ강도·p_C·GA(μ_C) + (avoided−other)·A − q_h2·p_h2·GA(μ_h2) − q_el·p_el·GA(μ_el) − q_f·p_f·GA(μ_f) − K·mult(t)`
  - GA = growth_annuity(r, μ, 잔여년): `Σ e^{μs}/(1+r)^s` — **q = e^μ/(1+r) > 1이면 발산 성향** (§D R-1)
  - mult = 1.0 (t ≥ reline) / **1.489** (off-cycle)
  - 할인율 r = **자산 WACC** (hurdle 아님)
- LSM: ITM 경로에 log-3차 다항 회귀로 계속가치 추정, `EV > cont`면 행사
- **τ* = E[min(τ, H)]** (미행사=지평말) · p_exercised < **0.5** → τ*=None
- carbon_reform 개입: μ_C += ln(ℓ̄′/ℓ̄)/15 (drift 재앵커)
- p_bind는 행사에 불진입 (플래그 off) — **τ*는 예산 없는 measure에서 결정**

### s04_anatomy — Euler 분해와 charge
- t_sw = **min(τ*, T_required)** (τ*=None → 지평말) [View 1과의 정합 문제, §D R-7]
- 자산 노출 PV (USD):
  - `E_carbon = [강도·ℓ_bind·A(r,t_sw) + 잔여·ℓ_bind·PV(t_sw,H)] × cap`  ← **전환 전+후, ℓ_bind 사용**
  - `E_h2 = q_h2·p_h2·PV(t_sw,H)·cap` — **전환 후만**
  - `E_elec = q_el·p_el·PV(t_sw,H)·cap` — **전환 후만, 현물가**
  - `E_feed = q_f·p_f·PV(t_sw,H)·cap` (철강은 q_f=0)
  - `E_capex = K·DF(t_sw)·cap`
- w = E∘σ (reform: σ_carbon=σ_binding) → **s_k = w_k(ρw)_k / wᵀρw** (Σ=1 항등)
- σ_B = √(wᵀρw)
- **charge: π_annual = k·λ·p_bind·σ_B / annuity(WACC, 35)** → bps = π/EV·10⁴, $/t = π/용량

### s05_robustness
- envelope: σ·ρ band 균등 draw ×200 (E 고정 — 공분산 불확실성만)
- λ×p_bind 격자: share 불변(기계정밀도) + 수준 스윙 (P1 데모)
- λ_k: s_k = λ_k·RC_k / Σλⱼ·RCⱼ
- σ-linearity: A01에서 σ스케일 7점 회귀 — **R² 0.814** (0.99 주장 대비 약함)

### s06_interventions — 개입 = 파라미터 변환
- coverage×tenor 1차 근사: `cov_t = coverage × (계약창∩지평)/지평`
- CfD: `p′ = cov_t·strike + (1−cov_t)·p` · `σ′ = (1−cov_t)·σ + cov_t·basis_σ`
- reform: SQ확률 절반→구속 비례 재배분 후 regime 재계산
- 각 개입: τ* 재解 (LSM) → t_sw → anatomy·charge·gap·gap-loss 재계산
- 기여 분해: standalone / sequential / **Shapley (2ⁿ 부분집합, charge에 대해)**

### s07_pathways / lib/pathways — 배출 경로와 gap
- 자산 배출 = **계단함수**: `cap×강도 → (switch 후) cap×잔여강도` [부분전환 표현 불가]
- gap_t = max(E_private − E_required, 0) · **cumulative_gap = Σ gap_t** (할인 없음, 물리량)

### s13_gap_pricing — gap의 축약형 가치화
- `PV_loss_j = Σ_t DF_t(WACC)·G_t·max(P_j − P_ref, 0)` (P_ref = 국가 현물)
- E[loss]·σ_loss는 전 시나리오 확률로 (p_bind 재곱 금지)
- `gap_charge = k·λ·σ_loss / annuity(WACC,35) / EV` — anatomy charge와 **합산 금지 (별도 basis)**

### s08_underwriting
- 감응도 표면: `spread(λ′,p′) = base × λ′/λ × p′/p_bind` (순수 스케일)
- 개입 분류: Δcharge·Δgap 부호 조합 → dual_benefit / de_risking_with_alignment_tradeoff / …

### s09_deal_screening / lib/transactions — 거래 스크린
- 연간편익 $/t = **Δ강도·ℓ̄** + avoided − other − q_h2·p_h2 − q_el·p_el − q_f·p_f + green_premium
  (탄소편익은 **ℓ̄ 무조건부 기대** — 세 번째 탄소가격 표현, §D R-8)
- NPV = cash·annuity(**hurdle**, 25) − capex · IRR 이분법 · DSCR = cash / [debt·60% / annuity(**WACC**,15)]
- break-even 탄소/수소/원료가, required green premium (NPV·DSCR 각각)
- 게이트: NPV≥0 ∧ DSCR≥1.3 ∧ IRR≥hurdle → INVESTABLE_SCREEN

### s12_level_wedge — 폐형해 레인 (별도 basis)
- LEVEL = h2+elec+feed+other+**CRF(WACC,25)·K** − avoided − Δ강도·탄소현물
- σ_project = √(wᵀρw)/gross (노출가중 변동계수)
- **m(σ) = β/(β−1), β from (r=WACC, δ=dp_delta=0.05)** ← δ 고정 가정 [§D R-2]
- WEDGE = (m−1)·LEVEL

### s10/s11/api
- s10: result_contract 정본 산출 · s11: POSCO/NIPPON 결정론 재실행(SHA 대조)
- api.compute: fixed_exposure(τ* 고정) / full_counterfactual(τ*·gap 재解) — 파일 불변
- api.screen_transaction: s09의 오버라이드 버전

---

## C. 아웃풋 대장 (`outputs/*.json` 24개)

| artifact | 내용 | 산식 원천 | 지배 가정 |
|---|---|---|---|
| calibration_resolved | 파생값 전체 | s02 | 시나리오(assumed) |
| tau_star | 자산 τ*·p_ex·옵션가치 | s03 | **μ vs WACC (R-1)**, threshold 0.5 |
| wedge | τ*−T_required | s03−s02 | T_required(surrogate) |
| sigma_linearity | π 선형화 R²=0.814 | s03 | — |
| shares_by_firm | Euler 조성 | s04 | **t_sw 창(R-6·R-7), ℓ_bind vs 현물(R-5), q_feed=0(R-9)** |
| premium_levels | charge bps·$/t | s04 | λ·k(assumed), p_bind, EV |
| cost_vs_risk | 평균 vs 분산 분해 | s04 | 상동 |
| stranding | Hyundai 분리 | s04 | A4 |
| share_envelopes | σρ 포락 | s05 | E 고정 (τ* 미재계산) |
| lambda_invariance | P1 데모 | s05 | 항등 |
| cluster_separation | 두 클러스터 불교차 | s05 | R-6 오염 (JFE·KOBE) |
| lambda_k_sensitivity | λ_k 이동 | s05 | λ_k(assumed) |
| intervention_impacts | 개입별 Δτ*·Δgap·Δcharge·Shapley | s06 | **στ* 부호(R-1), 계단 Δgap, threshold 사각(KOBE·JFE 0)** |
| emissions_pathways_by_firm | BAU/private/required | s07 | 계단함수 |
| condition_gap | 누적 초과배출 | s07 | T_required(R-6) |
| alignment_gap_loss | gap 손실분포·charge | s13 | λ·k, 시나리오, WACC |
| transition_underwriting | 투자자/재무 뷰 | s08 | 상류 전부 상속 |
| deal_screening | NPV·DSCR·break-even | s09 | **ℓ̄ 사용(R-8), hurdle/WACC 분리(R-3)**, 프로파일 |
| result_contract | metric·basis 계약 | s10 | — |
| pilot_cases | 재현 증거팩 | s11 | — |
| level_wedge | LEVEL/WEDGE 폐형해 | s12 | **δ=0.05(R-2), 탄소=현물(R-5)** |
| reference_prices | 연단위 관측 대조 | s01 | — |
| manifest | 해시·seed·dirty | run_all | — |

---

## D. 할인율·드리프트·가격 교차 감사 — "왜 놓쳤나"의 답

anchor 시스템은 **파라미터↔이론**을 검증하지만 **파라미터↔파라미터** 정합은 아무도
검증하지 않았다. 아래 9건이 그 사각지대다.

### R-1. μ_carbon > WACC — 탄소 레그가 초임계 (가장 치명적)

| 기업 | WACC | δ_carbon = r − μ(0.086) | 결과 |
|---|---|---|---|
| NIPPON/JFE/KOBE | 5.75% | **−2.85%p** | 기다림이 드리프트로 지배 |
| JP_NCC | 5.0% | **−3.6%p** | 상동 |
| POSCO | 7.5% | **−1.1%p** | 상동 |
| KR_NCC | 7.0% | −1.6%p | 상동 |
| HYUNDAI | 10.5% | **+1.9%p** | 유일한 정상영역 |

δ<0이면 영구옵션은 "영원히 대기"가 최적 — 유한지평·reline이 강제로 자를 뿐.
검증된 귀결: **σ↑ → τ*↓ (모든 τ 정의에서, seed 12/12)**, σ-절단 계약(CfD)은
유리한 실현을 제거해 **p_exercised를 낮추고 전환을 늦춘다** (0.74→0.58).
theory/01·10의 WEDGE 서사와 부호가 반대다.

### R-2. s12는 δ=+5%를 가정 — 두 레인이 반대 세계
`dp_delta=0.05` (config 상수). LSM은 δ<0, 폐형해는 δ>0. **m(σ) 레인의 "σ↑→더 기다림"과
LSM의 "σ↑→더 빨리"는 basis 차이가 아니라 모형 세계의 충돌.** DECISIONS X9 후보.

### R-3. hurdle과 WACC의 어정쩡한 분업
LSM(사적 최적)은 WACC로 할인 — hurdle 열은 s09 스크린만 사용. 기업의 사적 행사에
허들 프리미엄이 없다면 hurdle의 존재 이유가, 있다면 LSM의 할인율이 설명돼야 한다.

### R-4. 물리측도 드리프트로 옵션을 평가하면서 λ를 밖에서 또 곱한다
s03은 μ(물리측도 기대수익) 그대로 행사 — 리스크 중립화 없음. s04는 σ_B에 λ·k를 곱해
리스크 가격을 청구. **한 시스템 안에서 리스크가 두 번, 서로 다른 방식으로 처리된다.**

### R-5. 탄소가격의 세 가지 표현이 병존

| 사용처 | 탄소가격 | 값 (KR/JP) |
|---|---|---|
| s03 LSM (τ*) | **현물 + GBM drift 8.6%** | 14.93/3.0 → 2061년 기대 ~**$300/$60** |
| s04 anatomy (조성·charge) | **ℓ_bind 조건부** | 53.2/46.5 (고정 수준) |
| s09 스크린 (NPV) | **ℓ̄ 무조건부** | 34.65/23.25 |
| s12 LEVEL | **현물** | 14.93/3.0 |

특히 LSM의 시뮬레이션 탄소가는 2061년 평균 ~$300(KR)에 도달 — **시나리오 표의 최대값
$85와 완전히 다른 분포**다. 같은 "탄소가격"이 네 곳에서 네 개의 다른 객체다.
JFE·KOBE 탄소 조성 지배의 ~15배 스케일(ℓ_bind/현물)이 여기서 나온다.

### R-6. 비H₂ 풀 재정규화의 종점 아티팩트
`curve/curve[-1]×pool_cap` → 풀 마지막 자산의 T_required = 항상 2061.
A05(JFE 최대)·A11(KOBE)이 여기 걸림 → gap 과소 + **s04 전환후 창=0 → 탄소 100%**.

### R-7. t_sw = min(τ*, T_required)의 자기모순
View 1은 "required에 전환하지 않는다"(gap>0)를 주장하면서, View 2의 노출은
required 시점에 전환한 것으로 계산한다 (POSCO t_sw=2036 vs τ*=2044.7).

### R-8. charge 연율화 창 불일치
σ_B는 노출창(t_sw 전후)의 PV인데 연율화는 항상 annuity(WACC, **35년 전체**).
노출이 짧은 기업의 연간 charge가 상대적으로 희석된다.

### R-9. 철강 원료가격의 결정론 처리
scrap($400/t)·NG·석탄($250/t)·광석($110/t)은 avoided/other_opex 안의 상수 —
σ=0. q_feedstock 배관은 존재하나 철강 행이 0. JFE 비용의 ~88%가 고철인데
그 변동성이 anatomy·LSM 양쪽에서 0이다. (config 값 입력만으로 활성화 가능)

---

## E. 지배구조 진단 — 무엇이 결과를 실제로 움직이는가

각 아웃풋의 1차 민감도(현행 설정 기준, 재계산 실험 근거):

| 아웃풋 | 1차 지배 | 2차 | σ(불확실성)의 역할 |
|---|---|---|---|
| τ* | **μ vs r (드리프트 격차)**, reline 창, LEVEL 항 | K·off-cycle 페널티 | **역방향** (σ↑→τ*↓) |
| LEVEL | route 원단위×기준가 (결정론 산수) | WACC (CRF) | 없음 |
| WEDGE(s12) | LEVEL × m(σ) | δ 가정 | 정방향 — 단 δ=5% 가정 하에서만 |
| gap | T_required(surrogate)·τ* | 계단 해상도(~7Mt/자산·년) | τ* 경유 간접 |
| 조성(share) | **노출창 t_sw·ℓ_bind 스케일·q_feed=0** | σ·ρ 밴드 | 부차적 (밴드 내 이동) |
| charge bps | **λ·k (곱셈 상수)**·σ_B·EV | p_bind | σ_B 경유 |
| NPV/DSCR | 원단위·ℓ̄·hurdle·거래 프로파일 | 개입 | 없음 (결정론 스크린) |

**요약**: 현행 설정에서 이 툴의 답을 결정하는 것은 ① 기대가격 경로(μ)와 할인율의
격차, ② 수준 항(원단위×가격, CAPEX), ③ 노출창 정의다. σ는 τ*에는 역방향,
조성에는 밴드 내 이동, charge에는 assumed 상수(λ·k) 뒤의 스케일로만 작동한다.
"불확실성이 자본을 막는다"는 서사는 **현행 엔진의 산출이 아니다** — 단, 이는
R-1·R-4의 측도 선택에 조건부이며, 위험조정 드리프트(δ>0 보장)로 바꾸면
불확실성의 고전적 역할이 복원된다. 이 선택이 X9이다.

---

*작성: 2026-08-03 구조 감사. 검증 방법: 전 모듈 정독, JFE/KOBE/POSCO/NIPPON 노출
수기 재계산(soutput 4자리 일치), LSM seed 42 재현(τ* 2044.86 vs artifact 2044.72,
p_ex 동일), σ-스케일·CfD 채널분리 실험(8–12 seed). 데이터 품질은 범위 외.*
