# CAP STATUS — 구현 수준·게이트·공개 통제 (단일 문서)

> MILESTONE_20 · MILESTONE_30 · PUBLIC_RELEASE_CHECKLIST를 이 문서로 통합 (2026-08-03).
> 원문은 `archive/2026-08_final_update/`에 보존. 갱신 규칙: 수준이 바뀔 때만 이 문서를 고친다.

## 릴리스 단계

**`INTERNAL_RESEARCH_PREVIEW`** — 모든 화면·산출물에 이 상태를 표시한다.
외부 공개 최소선은 90/100이며, 아래 §90점 blocker 중 하나라도 미통과면 fail-closed.

## 현재 수준: 30/100 — pilot-ready dry run

| 게이트 | 상태 | 증거 |
|---|---|---|
| 의미 계약 (metric_id·basis_id·evidence_grade, 교차 basis 비교 금지) | PASS | `outputs/result_contract.json`, 회귀 테스트 |
| 투자자 첫 화면 = FID 결론·절대 NPV·필요 프리미엄·CFADS | PASS | Investor Decision Summary |
| 연구 경계 표시 (시나리오 조건부·surrogate·illustrative) | PASS | evidence badge, `MODEL_CARD.md` |
| 재현성 CI (lockfile 기반 전체 파이프라인) | PASS | `.github/workflows/ci.yml` |
| 한·일 동일 워크플로 자동 재실행 (canonical SHA256 일치) | PASS | POSCO·NIPPON dry-run 결과팩 |
| 실제 executable quote | **OPEN** | 현행 계약 조건은 assumed screening terms |
| 검증된 required path | **OPEN** | `T_required = surrogate` (pro-rata 배분, assumed) |
| 독립 분석가 blind rerun | **OPEN** | 자동 replay ≠ 독립 검토 |
| 실제 거래 사례 | **OPEN** | dry run ≠ IC/treasury case |

40점은 위 OPEN 4건이 남아 있는 한 주장하지 않는다.

## 90점 외부 공개 blocker (fail-closed 요약)

- **모델**: T_required 검증 출처 교체, holdout backtest, 독립 재현, joint stress·decision
  reversal boundary 공개, calibration 감사 가능성, claim ledger 일치.
- **투자자 안전**: gate 분리 표시(NPV·DSCR·기술·심도), illustrative ≠ executable 구분,
  observed spread·rating·advice 표현 금지, basis 혼동 방지, 정밀도≠확실성 명시.
- **데이터·법률**: 사용권한·라이선스·provenance 승인, 비공개 데이터 분리·감사로그,
  법률·투자자문·경쟁법 검토, dependency/secret scan, 결과팩 hash 포함.
- **품질·운영**: clean-checkout CI, UI QA, 부분 실패의 명시적 실패 처리, owner 지정,
  incident·rollback 리허설, 재보정 주기, 승인 기록.

## 다음 구조 변경

없다 — `RESTRUCTURE_2026-08.md`가 마지막 구조 계획이며, 이후는 데이터 수정과
2차 프로젝트(merit-order 배분, λ 역산, WACC 고정점, 과점 행사)뿐이다.
