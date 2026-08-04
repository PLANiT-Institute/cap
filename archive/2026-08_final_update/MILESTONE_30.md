# CAP 30/100 — Pilot-ready dry run

## 현재 결론

CAP은 20점의 의미·검증 계약을 넘어, 동일한 입력으로 한·일 사례를 반복 생성하고 투자·연구
결론, basis, stress, 입력 출처와 재실행 hash를 한 결과팩에 묶는 30점 상태다.

30점은 **실제 파일럿 완료가 아니다.** 현재 POSCO와 NIPPON 결과팩은 repository의 banded
asset registry, assumed intervention/transaction terms, surrogate required path를 사용하는 자동
dry run이다. 따라서 release stage는 계속 `INTERNAL_RESEARCH_PREVIEW`다.

## 구현된 증거

| 항목 | 상태 | 증거 |
|---|---|---|
| 한국·일본 동일 워크플로 | PASS | POSCO, NIPPON H₂ DRI + H₂ CfD 결과팩 |
| 동일 입력 자동 재실행 | PASS | 두 fresh API call의 canonical SHA256 일치 |
| 투자결정 요약 | PASS | 절대 NPV, gross/CP-adjusted ΔNPV, DSCR, CFADS 부족액, 필요 프리미엄 |
| 연구 basis 분리 | PASS | enterprise transition-window와 project-from-base-year 별도 계약 |
| 민감도 | PASS | green premium, debt share, DSCR target, fixed-exposure λ stress |
| 입력 provenance | PASS | asset source/status와 config·upstream artifact fingerprint |
| 실제 executable quote | OPEN | 현 intervention terms는 assumed screening terms |
| 검증된 required path | OPEN | `T_required=surrogate` |
| 독립 분석가 blind rerun | OPEN | 자동 replay는 독립 검토가 아님 |
| 실제 거래사례 | OPEN | dry run이며 실제 IC/treasury case가 아님 |

## 40점 진입에 필요한 입력

1. 한국 또는 일본 실제 사례의 기준일과 투자 질문
2. 확인 가능한 asset register 또는 승인된 public/private asset pack
3. lender 또는 counterparty의 실제/indicative quote 한 건 이상
4. firm-specific required path의 출처와 적용범위
5. 두 번째 분석가의 blind rerun 및 차이 분류
6. construction, ramp, tax, working capital, covenant를 포함한 거래 현금흐름 보강

이 여섯 항목 중 actual case, executable quote, required path, independent rerun은 필수 gate다.
자동 replay가 통과해도 대신할 수 없다.

## 실행

`make model`이 `outputs/pilot_cases.json`과 `outputs/pilots/*.md`를 재생성한다. 웹 `/pilots`는
같은 artifact만 렌더한다. source/config가 바뀌면 fingerprint와 재실행 hash가 함께 바뀐다.
