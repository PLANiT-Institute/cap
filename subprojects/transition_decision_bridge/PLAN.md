# Joint Risk Premium Implementation Plan

## 1. 한 줄 목표

> CAP의 transition-cost premium과 alignment-gap overlay를 동일한 탄소 위험요인에 연결해, 기존 결과를 재현하면서 이중계산 없는 `combined_total_bps`를 만든다.

## 2. 제품 정의와 범위

최종 결과의 정식 명칭은 **CAP combined conditional transition risk premium**이다.
이는 관측 채권·대출 스프레드나 주가 기대수익률이 아니라, CAP의 시나리오와
위험가격 `lambda × k`에 조건부인 기업 전환위험 charge다.

포함:

- 기존 transition-cost headline의 정확한 재현
- 기존 gap-loss overlay의 정확한 재현
- 두 component 사이의 명시적 covariance
- 기업별 base/intervention combined premium
- 독립·중앙·완전양의상관 경계
- combined premium 기준의 개입 재평가

제외:

- 완전한 3개 재무제표와 확률적 부도모형
- 관측 시장 스프레드 calibration
- BUY/SELL 또는 목표주가
- CAP 본체 수식의 즉시 변경
- surrogate `T_required`를 empirical이라고 승격

모든 구현은 이 서브프로젝트 안에 두며, 기존 core artifact는 read-only 입력으로
사용한다. 승격 gate를 통과하기 전에는 core `make all`과 web headline에 연결하지
않는다.

## 3. 왜 단순 합산이 아닌가

현재 두 charge는 같은 기업·지평을 보지만 서로 다른 확률처리를 쓴다.

| 항목 | Transition-cost | Alignment-gap |
|---|---|---|
| 손실기초 | driver별 PV cost exposure | discounted emissions gap × incremental carbon price |
| 분포 | binding-conditional sigma와 외부 `p_bind` | unconditional scenario loss distribution |
| 확률처리 | `p_bind` 한 번 곱함 | scenario probability 안에 이미 포함 |
| 연율화 | firm WACC, model horizon annuity | firm WACC, model horizon annuity |
| 정규화 | enterprise value | enterprise value |
| 현재 evidence | `SCENARIO_CONDITIONAL` | `PROVISIONAL` |

기간·연율화·EV 기준은 맞지만 두 손실이 같은 탄소상태에서 얼마나 함께 움직이는지
없다. 따라서 `premium_T + premium_G`는 상관계수 1을 암묵적으로 가정하는 상한이지
중앙 추정치가 아니다.

## 4. 선택한 수학적 접근

### 4.1 Reconciled factor-covariance lane

기존 transition-cost exposure vector를 다음처럼 둔다.

```text
w = E ⊙ sigma
sigma_B = sqrt(w' rho w)
sigma_T = p_bind × sigma_B
```

여기서 `E`는 driver별 PV exposure, `sigma`는 기존 reform-priced sigma,
`rho`는 기존 driver correlation matrix다. 이 정의는 현재 headline을 정확히
재현한다.

Gap loss의 PV 표준편차는 기존 `sigma_G`를 그대로 사용한다. Gap loss와 탄소
시나리오 수준의 확률가중 상관을 `rho_CG`라고 하면, transition aggregate와 gap
loss의 상관은 다음이다.

```text
rho_TC = (rho w)_carbon / sigma_B
rho_TG = rho_TC × rho_CG
```

`rho_CG`는 각 국가 scenario probability로 탄소수준과
`max(carbon level - reference price, 0)`의 weighted correlation을 직접 계산한다.
Gap 규모는 양의 scalar이므로 상관에는 영향을 주지 않는다. Gap이 0이면
`rho_TG`는 `null`이고 combined premium은 transition headline과 동일하다.

공동 PV 표준편차와 premium은 다음과 같다.

```text
sigma_J = sqrt(sigma_T^2 + sigma_G^2 + 2 rho_TG sigma_T sigma_G)
premium_J = lambda × k × sigma_J / annuity(WACC, horizon) / EV × 10,000
```

두 component가 같은 `lambda`, `k`, annuity, EV를 쓰므로 bps에서 직접 계산해도
동일하다.

```text
premium_J = sqrt(
    premium_T^2
    + premium_G^2
    + 2 rho_TG premium_T premium_G
)
```

이 lane의 장점은 다음 세 불변식을 동시에 지키는 것이다.

1. gap premium이 0이면 기존 transition premium과 정확히 같다.
2. transition premium이 0이면 기존 gap premium과 정확히 같다.
3. 각 component의 기존 발표값을 재보정하거나 임의로 축소하지 않는다.

### 4.2 Structural joint-state validation lane

Reconciled lane과 별도로 국가 탄소 scenario를 공통 draw로 뽑고, 나머지 driver를
상관된 residual shock으로 생성하는 고정 seed simulation을 둔다. 이 lane은 새
headline을 바로 만들지 않고 analytical covariance의 방향·크기·tail behavior를
검증한다.

```text
J ~ categorical(country carbon scenario probabilities)
Z ~ correlated driver residuals
transition loss = f(E, scenario carbon level, Z)
gap loss = discounted gap × max(scenario carbon level - reference, 0)
```

이 simulation이 기존 component를 재현하지 못하면 analytical lane을 core로
승격하지 않는다. 특히 scenario jump와 diffusion sigma를 동시에 넣어 탄소위험을
두 번 세지 않도록 별도 variance reconciliation 표를 남긴다.

## 5. 입력계약

| 입력 | 사용 필드 | 통제 |
|---|---|---|
| `outputs/transition_underwriting.json` | headline bps, EV, intervention terms | 기업 중복·음수·누락 실패 |
| `outputs/alignment_gap_loss.json` | sigma, overlay bps, scenario losses | 확률합 1, gap 음수 실패 |
| `outputs/intervention_impacts.json` | before/after component charges | base reconciliation 실패 시 중단 |
| `outputs/cost_vs_risk.json` | driver별 PV exposure | firm coverage와 driver set 고정 |
| `outputs/calibration_resolved.json` | sigmas, correlations, p_bind, scenarios | matrix 대칭·PSD·확률합 검증 |
| `config/firms.csv` | firm별 `elec_driver` | firm invariant 검증 |
| `outputs/tau_star.json` | intervention별 전환시점 | intervention factor state 재생성 |

모든 입력은 SHA256과 source path를 결과에 기록한다. source hash가 바뀌면 결과를
다시 생성해야 하며, 오래된 결과를 조용히 재사용하지 않는다.

## 6. 예정 파일 구조

```text
subprojects/transition_decision_bridge/
├── PLAN.md
├── bridge.py                       # 기존 decision packaging
├── joint_inputs.py                 # core artifact adapter + validation
├── joint_premium.py                # covariance and premium pure functions
├── run_joint.py                    # deterministic CLI
├── outputs/
│   ├── risk_premium_decision.json
│   ├── risk_premium_decision.md
│   ├── joint_risk_premium.json
│   └── joint_risk_premium.md
└── tests/
    ├── test_bridge.py
    ├── test_joint_math.py
    ├── test_joint_reconciliation.py
    └── test_joint_interventions.py
```

## 7. 결과계약

기업별 결과는 최소 다음 구조를 갖는다.

```json
{
  "firm_id": "POSCO",
  "components": {
    "transition_headline_bps": 19.34,
    "gap_overlay_bps": 7.63
  },
  "joint_dependence": {
    "rho_transition_carbon": 0.63,
    "rho_carbon_gap": 1.00,
    "rho_transition_gap": 0.63
  },
  "combined": {
    "independence_bps": 20.79,
    "central_bps": 24.86,
    "perfect_positive_upper_bps": 26.98,
    "combined_total_bps": 24.86
  },
  "evidence_grade": "PROVISIONAL"
}
```

숫자는 설명용 예시이며 구현 결과로 재생성한다. `combined_total_bps`에는 항상
central correlation, source hashes, evidence grade, non-market-spread 경고가 함께
나간다.

## 8. 구현 순서와 acceptance criteria

### WP0 — Baseline freeze

- 현재 6개 기업의 component 값과 source hash를 golden fixture로 고정한다.
- 현재 decision bridge 결과를 변경 없이 재생성한다.

완료조건:

- 기존 core 테스트 42개 통과
- 기존 bridge 테스트 전부 통과
- 작업 시작 전 component 값과 정확히 일치

### WP1 — Joint input adapter

- artifact와 config에서 `E`, `sigma`, `rho`, `p_bind`, scenario loss factor를 읽는다.
- 기업·국가·전력 driver를 명시적으로 연결한다.
- central correlation matrix의 대칭·대각 1·PSD를 검사한다.

완료조건:

- 재계산한 `sigma_B`가 source transition sigma와 절대오차 `1e-8 USD bn` 이내
- 모든 `rho_transition_gap`이 `[-1, 1]`
- driver, firm, scenario 누락 시 fail closed

### WP2 — Base combined premium

- 독립, 중앙, 완전양의상관 세 값을 계산한다.
- 기업별·EV 가중 portfolio 결과를 만든다.
- component sum은 중앙값이 아니라 명시적 상한으로만 표시한다.

완료조건:

- `abs(T-G) <= combined <= T+G`
- gap=0이면 combined=T
- 중앙값이 independence와 positive upper 사이에 있음
- `p_bind`를 gap component에 다시 곱하지 않음

### WP3 — Intervention combined premium

- 개입별 after exposure/sigma/correlation을 다시 만든다.
- combined premium 감소, physical gap 변화, gap overlay 변화를 동시에 기록한다.
- 추천 개입을 combined premium 기준으로 재평가한다.

완료조건:

- before state가 WP2 base와 일치
- source after transition/gap charge와 각각 일치
- `no_tradeoff`는 combined 감소, gap 비증가, overlay 비증가를 모두 충족
- package와 standalone을 섞지 않고 source intervention ID를 보존

### WP4 — Sensitivity and structural validation

- `rho=0`, central, `rho=1` 경계를 항상 제공한다.
- correlation band, contract basis lo/hi, lambda×p_bind를 별도 축으로 둔다.
- fixed-seed joint-state simulation으로 analytical covariance를 교차검증한다.

완료조건:

- 동일 seed·입력에서 byte-stable JSON
- simulation standard error와 analytical 차이를 함께 보고
- PSD가 아닌 sampled matrix를 조용히 보정하지 않고 reject/flag
- sensitivity 축을 섞어 하나의 가짜 confidence interval로 표시하지 않음

### WP5 — Publication gate

- JSON과 Markdown decision pack을 생성한다.
- provisional·scenario-conditional·observed를 UI/문서에서 분리한다.
- core integration 여부를 별도 결정한다.

완료조건:

- 아래 publication gate 전부 통과
- `combined_total_bps`가 관측 spread 또는 lender quote로 표현되지 않음
- root result contract를 변경하지 않은 상태로 subproject 결과 확정

## 9. 테스트 행렬

### 수학 불변식

- variance decomposition identity
- component recovery
- zero-component reduction
- correlation bounds
- perfect-correlation upper bound
- annuity/EV unit equivalence

### 데이터 불변식

- firm-level country/route/WACC/EV/elec_driver 일치
- scenario probabilities sum to one
- nonnegative gap and loss sigma
- source SHA256 완전성
- firm coverage exact match

### 개입 불변식

- before state equals base
- irrelevant intervention has zero change
- applicable flag honored
- high-basis result does not overwrite central
- double-count warning propagates

### 회귀 fixture

- POSCO, NIPPON은 주요 pilot golden case
- JFE/KOBE는 carbon-dominant correlation edge case
- NCC는 feedstock-dominant mixed-factor case

## 10. Publication gate

`combined_total_bps`를 숫자로 발행하려면 다음을 모두 통과해야 한다.

1. **Reconciliation:** 두 component가 기존 artifact와 허용오차 내 일치.
2. **Probability:** transition의 `p_bind`와 gap scenario probability가 각각 한 번만 반영.
3. **Covariance:** 식, factor lineage, correlation matrix가 모두 추적 가능.
4. **Bounds:** 중앙값이 이론적 lower/upper bound 안에 존재.
5. **Data:** firm/scenario/driver 누락 없음.
6. **Evidence:** surrogate `T_required` 때문에 전체 combined grade는 `PROVISIONAL` 유지.
7. **Language:** observed spread, financing saving, regulatory liability로 오인시키지 않음.
8. **Regression:** core 42개와 subproject 전체 테스트 통과.

외부 거래자료 calibration과 validated `T_required`가 들어오기 전까지
`MARKET_READY`, `LENDER_GRADE`, `EMPIRICAL` 표시는 금지한다.

## 11. 주요 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| jump와 diffusion 이중계산 | premium 과대 | analytical reconciliation과 structural lane 분리 |
| `p_bind` 재곱 | gap premium 과소 | component recovery test와 확률 lineage 필드 |
| assumed correlation | false precision | independence/central/upper 세 값 동시 공개 |
| non-PSD matrix | 허위 covariance | fail closed; sensitivity에서 조용한 projection 금지 |
| surrogate `T_required` | gap component 불안정 | 전체 evidence를 `PROVISIONAL`로 cap |
| 개입 후 factor state 미재계산 | 잘못된 ranking | 개입별 `E`, sigma, rho 재생성 |
| scope creep | CAP 본체 희석 | subproject 격리, 3-statement/market pricing 제외 |

## 12. 사전 feasibility 결과

현재 central factor correlation을 단순 적용한 read-only 계산은 다음 수준이다.
아직 regression·intervention·publication gate 전이므로 indicative 값이다.

| Firm | Transition | Gap | Indicative combined | Component sum upper |
|---|---:|---:|---:|---:|
| JFE | 23.99 | 6.70 | 30.68 | 30.69 |
| JP NCC | 17.88 | 2.01 | 18.61 | 19.88 |
| Kobe | 15.84 | 0.15 | 15.99 | 15.99 |
| KR NCC | 16.42 | 1.60 | 17.02 | 18.01 |
| Nippon | 11.33 | 7.14 | 15.73 | 18.46 |
| POSCO | 19.34 | 7.63 | 24.86 | 26.98 |

EV 가중 indicative combined premium은 약 **20.73bps**다. 이는 단순합
`16.71 + 5.75 = 22.46bps`보다 낮다. 기업별 transition risk가 carbon factor에
노출되는 정도가 다르기 때문에 covariance credit도 기업별로 달라지는 것이 핵심이다.

## 13. Definition of Done

- `joint_risk_premium.json`과 `.md`가 deterministic하게 생성된다.
- 6개 기업과 모든 applicable intervention이 포함된다.
- component recovery, covariance, probability, bounds 테스트가 모두 통과한다.
- combined 기준 개입 ranking이 별도 표시된다.
- 결과는 `PROVISIONAL combined conditional transition risk premium`으로만 표현된다.
- core 모델·web 승격은 별도 승인 전까지 일어나지 않는다.

## 14. Implementation status — 2026-08-01

완료:

- WP0 baseline freeze
- WP1 joint input adapter와 fail-closed reconciliation
- WP2 기업별·EV 가중 base combined premium
- WP3 개입별 combined premium과 no-tradeoff ranking
- core 43개, subproject 17개 테스트

구현 중 발견·수정한 기존 불일치:

- `s04.firm_frame`은 exposure 계산을 위해 `tau*=None`을 horizon end로 치환한다.
- `s06`이 이 exposure proxy를 emissions switch year로 재사용해 JFE·Kobe의 gap을
  과소계산하고 있었다.
- `s07`은 intervention tau를 base tau와 `min()` 처리해, `s06`의 full
  counterfactual과 다른 경로를 만들고 있었다.
- emissions pathway에는 raw `None`과 intervention tau를 그대로 사용하도록 통일했고,
  s06·s07·s13의 base/intervention gap이 일치하는 회귀 테스트를 추가했다.

현재 결과:

- EV 가중 transition component: `16.71bps`
- EV 가중 gap component: `5.75bps`
- EV 가중 combined premium: `20.73bps`
- perfect-positive component-sum upper: `22.46bps`

남음:

- WP4 structural joint-state simulation cross-check
- correlation-band sensitivity
- validated `T_required`와 외부/holdout calibration
- 별도 승인 후 core result contract 또는 web 승격 여부 결정
