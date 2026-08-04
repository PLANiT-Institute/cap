# CAP 90점 외부 공개 체크리스트

## Fail-closed 원칙

아래 blocker 중 하나라도 미통과면 release stage는 `INTERNAL_RESEARCH_PREVIEW` 또는 제한된
partner beta에 머문다. 체크되지 않은 항목은 실패로 간주한다.

## A. 모델·연구 타당성

- [ ] 핵심 기업의 `T_required`가 검증 가능한 출처로 교체되거나 수치 결론에서 제거됐다.
- [ ] 실제 사례 holdout backtest가 사전 정의된 기준으로 완료됐다.
- [ ] 독립 검토자가 exposure, covariance, LSM, transaction model을 재현했다.
- [ ] 주요 가정 joint stress와 decision reversal boundary가 공개된다.
- [ ] calibration window, 결측 처리, 통화·단위 변환이 감사 가능하다.
- [ ] 모든 public claim이 claim ledger와 일치한다.

## B. 투자자 안전성

- [ ] ADVANCE/HOLD가 NPV, DSCR, 기술타당성, 기후심도 gate를 분리해 보여준다.
- [ ] illustrative term이 executable quote로 오인되지 않는다.
- [ ] observed spread, credit rating, investment advice 표현이 제거됐다.
- [ ] 기업 basis와 프로젝트 basis를 사용성 테스트에서 혼동하지 않는다.
- [ ] 소수점 precision과 추정 uncertainty의 차이를 명시한다.

## C. 데이터·법률·보안

- [ ] 모든 데이터의 사용권한, 라이선스, provenance, 보존정책이 승인됐다.
- [ ] 기업 비공개·개인·계약 데이터를 분리하고 접근권한과 감사로그가 있다.
- [ ] 법률, 투자자문, 신용평가, 경쟁법 관점 검토가 완료됐다.
- [ ] dependency/SBOM/secret scan과 취약점 대응 owner가 있다.
- [ ] 결과팩에 재현에 필요한 버전과 hash가 포함된다.

## D. 제품 품질

- [ ] CI가 clean checkout에서 전체 파이프라인을 통과한다.
- [ ] 브라우저·모바일·접근성·인쇄/PDF 결과팩 QA가 완료됐다.
- [ ] 빈 값, stale artifact, 부분 실패가 조용히 정상 결과로 표시되지 않는다.
- [ ] 계산 timeout/오류/지원하지 않는 조합이 명확한 실패 상태를 낸다.
- [ ] 공개 문서와 실제 UI가 같은 release stage와 제한을 표시한다.

## E. 운영·책임

- [ ] 모델 owner, 데이터 owner, 제품 owner, 승인자가 지정됐다.
- [ ] incident, correction, model rollback 절차가 리허설됐다.
- [ ] 재보정 주기와 data drift/decision drift threshold가 정해졌다.
- [ ] 사용자 피드백·오해·오판을 수집하는 절차가 있다.
- [ ] 90점 승인일, 승인자, 근거 artifact가 기록됐다.

## 승인 기록

| 항목 | 값 |
|---|---|
| Release candidate | 미지정 |
| Artifact/config hash | 미지정 |
| Validation report | 미지정 |
| Independent reviewer | 미지정 |
| Approval date | 미지정 |
| Decision | **NOT CLEARED** |
