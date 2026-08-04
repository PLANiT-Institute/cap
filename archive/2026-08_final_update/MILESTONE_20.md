# CAP 10 → 20 내부 파일럿 마일스톤

## 결론

20점의 의미는 기능 수가 두 배가 되는 것이 아니다. **서로 다른 숫자의 의미가 분리되고,
투자자가 먼저 결론을 읽으며, 연구자가 같은 결론을 재생성·반증할 수 있는 상태**다.
이 단계는 외부 공개가 아니라 `INTERNAL_RESEARCH_PREVIEW`다. 외부 공개 최소선은 90점이며
그 전에는 모든 화면과 산출물에 내부 연구 프리뷰 상태를 유지한다.

## 다섯 번의 검토

| 검토 | 10점 상태의 핵심 결함 | 20점에서 강제할 변화 | 통과 증거 |
|---|---|---|---|
| 1. 의미 계약 | 같은 `bps`가 기업 transition window와 base-year 프로젝트를 오가며 보임 | 모든 핵심 결과에 `metric_id`, `basis_id`, `evidence_grade` 부착. 두 ID가 모두 같을 때만 직접 비교 | `outputs/result_contract.json`, result-contract 회귀 테스트 |
| 2. 투자자 관점 | 위험 수치가 앞에 있고 실제 HOLD/필요 프리미엄/NPV는 아래에 있음 | 첫 화면에 FID 결론, 절대 NPV, 필요 프리미엄, CFADS 부족액, 증분가치 표시 | Investor Decision Summary와 deal gate |
| 3. 연구 관점 | 조건부·대리변수·가정의 경계가 문장에 흩어짐 | 시나리오 조건부, provisional required path, illustrative terms를 결과 가까이에 표시 | evidence badge, Model Card, Validation Plan |
| 4. 재현성 | 로컬 `make all`은 있으나 변경마다 자동 강제되지 않음 | lockfile 기반 CI에서 전체 파이프라인·회귀·정적 웹 빌드 실행 | `.github/workflows/ci.yml` |
| 5. 공개 통제 | 내부 연구물과 공개 가능 산출물의 문턱이 불명확 | 20/90/100 게이트와 fail-closed 공개 체크리스트 운영 | `PUBLIC_RELEASE_CHECKLIST.md`, 파일럿 템플릿 |

## 20점 출구 기준

- [x] 기업 위험, 고정노출 스트레스, 프로젝트 위험, 프로젝트 경제성, alignment gap의 basis가 기계가독 형태로 분리된다.
- [x] 투자자 화면의 첫 결론이 HOLD/ADVANCE와 절대 경제성이다.
- [x] alignment gap에 `≈`와 `PROVISIONAL` 표시가 붙는다.
- [x] 프로젝트 bps와 기업 bps의 직접 비교 금지가 UI와 artifact에 동시에 존재한다.
- [x] 거래 경제성은 lender-grade valuation이 아닌 levelized illustrative screen으로 표시된다.
- [x] 모델 전체 실행, anchor, theory render, 회귀 테스트, Next.js build가 CI의 필수 단계다.
- [x] 90점 외부 공개 체크리스트와 파일럿 증거 수집 양식이 존재한다.
- [x] 한국·일본 dry-run 결과팩을 동일 파이프라인으로 생성하고 자동 재실행한다. 이 항목이 30점 진입 조건이다.
- [ ] 최소 2건의 실제 내부 파일럿을 완료한다. 실제 사례·quote·독립 rerun은 40점 진입 조건이다.

후속 구현 상태: [MILESTONE_30.md](MILESTONE_30.md)의 한·일 자동 dry run까지 완료했다.
실제 파일럿은 여전히 40점 진입 gate이며 자동 replay로 대체하지 않는다.

## 20 → 90 → 100

| 수준 | 제품 상태 | 필수 승격 조건 |
|---|---|---|
| 20 | 내부 연구 프리뷰 | 의미 계약, 투자결정 요약, evidence 표시, 재현·CI, 공개 게이트 |
| 40 | 반복 가능한 내부 파일럿 | 한국·일본 각 1건 이상 실제 asset/quote 입력, analyst blind rerun, 입력 provenance 완결 |
| 60 | 검증된 의사결정 보조 | holdout backtest, 민감도·오류 예산, 독립 모델 검토, 사용자 의사결정 시간/오판 측정 |
| 75 | 제한된 파트너 베타 | 권한·감사로그, 버전 고정 결과팩, 법률·데이터 라이선스 검토, red-team 완료 |
| 90 | 외부 공개 가능 | 공개 체크리스트 전 항목 PASS, surrogate 핵심 결론 제거 또는 전면 비수치화, 외부 재현 패키지 |
| 100 | 기관급 표준 | 다기관 반복검증, 모델 리스크 위원회, 지속 모니터링·재보정 SLA, 독립 assurance |

점수는 마케팅 수치가 아니라 게이트다. 앞 단계의 필수 조건이 하나라도 실패하면 상위 단계로
표시하지 않는다.
