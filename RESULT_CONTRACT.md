# CAP Result Contract v1.0

## 목적

CAP의 숫자는 단위만 같다고 비교할 수 없다. 직접 비교는 `metric_id`와 `basis_id`가 모두
같을 때만 허용한다. 이 규칙의 기계가독 정본은 `outputs/result_contract.json`이며, 아래는
사람이 읽는 계약이다.

## 핵심 basis

| basis ID | 무엇을 계산하는가 | 허용 용도 | 금지 용도 |
|---|---|---|---|
| `enterprise_transition_window.reform_priced.full_counterfactual.ev_normalized` | 기존 기업 자산이 사적/요구 전환시점을 따르는 transition-window 위험 | 기업 노출·계약 전후 위험 비교 | base-year 프로젝트 위험, 관측 스프레드 |
| `enterprise_transition_window.reform_priced.fixed_exposure.ev_normalized` | 최근 계산 경로를 고정한 가격 스트레스 | 동일 노출의 가격 민감도 | 전환시점·배출·alignment 효과 |
| `project_from_base_year.reform_priced.fixed_commissioning.ev_normalized` | 선택 기술이 기준연도에 가동된 프로젝트 위험 | 기술·계약 pre-deal 비교 | 기업 transition-window bps와 무보정 비교 |
| `project_levelized.expected_scenario.illustrative_terms` | 기대가격과 평준화 현금흐름에 따른 프로젝트 경제성 | NPV/DSCR/break-even 사전 스크린 | lender-grade valuation, executable quote |
| `enterprise_private_vs_required.full_counterfactual.provisional_required` | 사적 경로와 provisional required path 사이 누적 gap | 연구 진단·시나리오 비교 | 검증된 규제 의무 또는 compliance gap 주장 |

## Evidence grade

- `IDENTITY`: 수학적으로 모델 안에서 항상 성립한다.
- `MODEL_CONDITIONAL`: 노출 정의와 계산 구조에 조건부다.
- `SCENARIO_CONDITIONAL`: 가격 수준·확률·위험가격 가정에 조건부다.
- `EMPIRICAL`: 관측 자료로 해당 claim이 검증됐다.
- `PROVISIONAL`: surrogate 또는 미확정 입력이 핵심 의존성이다.
- `OPEN`: 아직 구현·검증되지 않았다.

표시 원칙은 보수적이다. 여러 grade가 걸리면 의사결정을 가장 제한하는 grade를 결과 가까이에
표시하고, 나머지는 artifact의 `claims`, `conditional_on`, `input_status`에 남긴다.

## 비교 규칙

1. `metric_id`가 다르면 비교하지 않는다.
2. `metric_id`가 같아도 `basis_id`가 다르면 숫자 차이를 효과로 해석하지 않는다.
3. before/after 효과는 동일 basis와 동일 입력 버전에서 한 변수군만 바꾼 counterfactual이어야 한다.
4. observed, verified, bankable, compliance 같은 단어는 각각의 외부 증거가 없는 한 사용하지 않는다.
5. 모든 결과팩은 artifact hash, config hash, git 상태와 release stage를 포함한다.

## 알려진 예시

H₂ CfD가 기업 transition window에서 만드는 charge 변화와, 기준연도에 H₂ DRI 프로젝트를
즉시 가동한다고 둔 charge 변화는 둘 다 bps지만 basis가 다르다. 따라서 각각의 before/after는
유효한 내부 비교지만 두 변화량끼리 직접 대조해 “어느 쪽이 진짜 효과”라고 결론 내릴 수 없다.
