# CAP Validation Plan

## 목적과 원칙

검증의 질문은 “숫자가 그럴듯한가”가 아니라 다음 네 가지다.

1. 코드가 정의된 계산을 정확히 수행하는가.
2. 정의된 계산이 의사결정 질문과 맞는가.
3. 입력과 불확실성이 결론을 얼마나 바꾸는가.
4. 실제 사례에서 유용성과 오류가 어느 정도인가.

검증 실패는 평균 점수로 상쇄하지 않는다. basis 혼동, lineage 누락, required path provenance 실패,
핵심 gate 역전은 각각 release blocker다.

## 검증 층위

| 층위 | 검증 내용 | 현재 증거 | 20점 상태 |
|---|---|---|---|
| V1 산술·항등 | share 합, gap 비음수, 자산합=기업합, break-even max gate | pytest 회귀 | PASS |
| V2 구현·계약 | fixed/full mode 분리, basis ID, artifact lineage, UI build | pytest + Next build + CI | PASS 목표 |
| V3 민감도·강건성 | λ, p(bind), sigma, correlation, WACC, route/contract 변화 | sensitivity artifact와 API 비교 | PARTIAL |
| V4 실제 사례 | 실제 asset, quote, timeline을 blind input 후 결과 대조 | 한·일 자동 dry run 완료, 실제 사례 미완료 | OPEN |
| V5 외부 타당도 | holdout 거래/시장 결과, 독립 검토, 다기관 재현 | 없음 | OPEN |

## 자동 검증

PR과 main push에서 다음 순서를 실행한다.

1. lockfile로 Python·Node 의존성 설치
2. ingest와 calibration 재생성
3. s01–s10 전체 모델 실행
4. theory anchor와 ledger 생성·렌더
5. 모든 회귀 테스트
6. Next.js 정적 빌드

필수 cross-artifact assertions:

- underwriting option과 intervention impact의 동일-basis before/after가 일치한다.
- deal risk에는 project basis, underwriting risk에는 enterprise basis가 부착된다.
- project economics에는 illustrative levelized basis가 부착된다.
- direct comparison rule이 artifact와 UI copy에 존재한다.
- release stage가 90점 전에는 외부 공개 상태로 승격되지 않는다.

## 내부 파일럿 프로토콜

각 파일럿은 `PILOT_CASE_TEMPLATE.md`를 복제해 다음 순서로 진행한다.

1. 분석 전에 투자 질문, 기준일, 허용 근거, 결정 gate를 고정한다.
2. analyst A가 입력 provenance와 status를 작성한다.
3. analyst B가 결론을 보지 않고 동일 입력으로 rerun한다.
4. CAP 결론을 기존 IC/treasury 판단과 비교하되, 차이를 CAP 정답으로 간주하지 않는다.
5. 숫자 차이를 data, basis, formula, decision-policy 차이로 분류한다.
6. decision-changing assumption과 추가 데이터의 가치(VoI)를 기록한다.
7. 오류·누락·사용자 오해를 severity로 분류하고 owner/date를 배정한다.

## 20 → 40 승격 표본

- 최소 2건: 한국 1건, 일본 1건
- 최소 1건은 철강, 가능하면 1건은 석유화학
- 실제 asset register 또는 확인 가능한 public asset data
- 실제 또는 문서화된 indicative quote 최소 1개
- analyst blind rerun 결과 일치
- 각 사례에서 최소 3개 핵심 가정의 one-way 및 joint stress

## 오류 예산

- P0: basis 혼동, 잘못된 ADVANCE, 다른 기업/국가 입력 사용 — 0건 허용
- P1: NPV/DSCR/gap 5% 초과 재현 불일치, lineage 누락 — 공개 전 0건
- P2: 비핵심 표시·rounding·copy 오류 — owner와 수정일이 있으면 내부 파일럿 허용

## 검증 결과 기록

각 실행은 artifact hash, commit, config hash, 입력 provenance, 실행자, 실행일, 테스트 결과를 남긴다.
결론이 바뀐 경우 바뀐 입력과 gate를 diff로 기록한다. “전반적으로 비슷함”은 검증 결과가 아니다.
