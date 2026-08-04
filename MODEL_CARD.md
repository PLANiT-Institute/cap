# CAP Model Card — Internal Research Preview

## 1. 모델 정체성

- 이름: CAP — Capital Allocation Pathway (구명 "Carbon-transition Asset Pricing"은 2026-08-03 폐기 — README name note)
- 릴리스 단계: `INTERNAL_RESEARCH_PREVIEW`
- 현재 구현 수준: 30/100 pilot-ready dry run
- 외부 공개 최소선: 90/100
- 계산 단위: 한·일 철강 5사 11개 고로(= 5사 조강의 약 1/3, 기업별 21–48%인 **부분 함대**)와
  한·일 석유화학 NCC archetype 2개. 부분 함대 π를 기업 전체 EV로 나눈 bps는 기업 간
  비교 불가 — $/t·Δ·순위를 쓸 것 (DECISIONS X12)
- 기본 목적: 기술 경로 → 전환 현금흐름 노출 → 조건부 위험부담 → 개입 후 잔여위험 → 프로젝트 경제성의 의사결정 사슬을 일관되게 계산

## 2. 의도된 사용자와 용도

투자자는 절대 NPV, DSCR, 필요 프리미엄과 조건부 위험 변화를 별도 gate로 본다. 기업 재무는
계약의 coverage·tenor·basis가 어떤 위험 driver를 남기는지 본다. 연구자는 사적 전환시점,
required path, 누적 alignment gap, 조건부 위험부담 사이의 구조를 재현·반증한다.

허용되는 용도는 내부 가설검토, 민감도 분석, 파일럿 대상 우선순위, 데이터 수집 질문 설계다.
신용등급, 투자자문, 대출가격, 규제 준수 판정, executable valuation과 term sheet에는 사용할 수 없다.

## 3. 계산 사슬

1. asset/route/config와 캘리브레이션을 읽는다.
2. LSM으로 사적 전환시점 `tau*`를 구한다.
3. provisional `T_required`와 비교해 경로 및 alignment gap을 구한다.
4. 연도별 gap을 국가 시나리오의 추가 탄소가격에 사상해 별도 gap-loss 분포와 charge를 구한다.
5. route별 현금흐름 driver 노출과 covariance로 transition cost uncertainty를 독립적으로 분해한다.
6. 조건부 탄소 수준·조건부 sigma와 `lambda × p(bind)`로 transition-cost charge를 정규화한다.
7. 계약·정책 개입을 파라미터 변환으로 적용하고 경로와 두 risk basis를 다시 계산한다.
8. 별도의 levelized transaction screen에서 NPV, IRR, DSCR, break-even, counterparty EL을 계산한다.

기업 transition-window 결과와 base-year 프로젝트 결과는 동일 계산이 아니며 `basis_id`로 분리된다.
gap-loss charge 역시 별도 basis이며 joint covariance가 없으므로 transition-cost charge와 합산하지 않는다.

## 4. 주요 입력과 현재 증거 상태

- 원본과 lineage: `data/DATA_PROVENANCE.md`, `outputs/manifest.json`
- 파라미터 상태: `measured`, `banded`, `assumed`를 config와 artifact에서 추적
- required path: 현재 `surrogate`, 따라서 alignment gap은 `PROVISIONAL`
- 거래조건: `ILLUSTRATIVE_NOT_EXECUTABLE`
- 석유화학: 기업 실측치가 아닌 archetype 가정
- 위험가격·일부 상관·거래가격: 가정 의존성이 남아 있음

입력 상태가 개선돼도 모델 구조의 타당성이 자동으로 입증되지는 않는다. empirical input과
empirical claim을 구분한다.

## 5. 핵심 출력

| 출력 | 단위 | 기본 evidence | 주요 제한 |
|---|---:|---|---|
| conditional risk charge | bps | `SCENARIO_CONDITIONAL` | 관측 spread가 아님 |
| risk anatomy share | % | `MODEL_CONDITIONAL` | 노출·covariance·전환 규칙에 조건부 |
| cumulative alignment gap | MtCO₂ | `PROVISIONAL` | required path가 surrogate |
| scenario-valued gap loss / charge | USDm / bps | `PROVISIONAL` | 별도 reduced-form basis; transition-cost charge와 합산 금지 |
| project NPV/IRR/DSCR | USDm/%/x | `SCENARIO_CONDITIONAL` | illustrative levelized screen |
| required green premium | USD/t | `SCENARIO_CONDITIONAL` | 계약 가능 가격 예측이 아닌 break-even |

## 6. 거래모델에 포함되지 않은 항목

현 단계 거래모델은 construction draw, commissioning ramp, 세금, 감가상각 세부, 운전자본,
terminal value, refinancing, covenant waterfall, stochastic default, CVA 및 실제 lender term을
완전한 project-finance cash-flow model로 구현하지 않는다. 부채금리는 firm WACC와 개입 delta에서
시작하며, counterparty EL은 단순 PD × LGD screen이다.

따라서 정확한 소수점은 계산 재현성을 위한 것이지 추정 정확도의 표현이 아니다.

## 7. 검증 상태

현재 검증은 구조 항등, 경로 산술, 국가 시나리오 분리, intervention residual, result-contract,
API mode 분리, 거래 gate, artifact lineage, theory anchor, 정적 웹 build와 POSCO·NIPPON 자동
dry-run 재실행을 포함한다. 자동 재실행은 독립 분석가 검토가 아니다. 아직 없는 것은 실제 거래
holdout backtest, executable quote, 독립적인 외부 모델 검토, 사용자 오류율 측정, 다기관 재현이다.

세부 프로토콜은 `VALIDATION_PLAN.md`, 공개 조건과 게이트는 `STATUS.md`를 따른다.

## 8. 변경 통제

모든 결과에는 config/code/raw/processed hash와 실행 전·후 git dirty 상태를 남긴다. basis 변경은 단순 UI
변경이 아니라 result-contract major 변경으로 취급한다. 모델 결론을 바꾸는 config·formula·scope
변경은 최소 한 개의 회귀 또는 검증 테스트와 변경 이유를 동반해야 한다.
