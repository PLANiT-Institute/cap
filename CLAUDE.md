# CAP — Capital Allocation Pathway

한·일 철강 전환자본이 언제·왜 움직이지 않는가의 anatomy — 리스크 프리미엄은 그 번역층.
현행 계획: `RESTRUCTURE_2026-08.md` · 수준·게이트: `STATUS.md` · 역사: `PLAN.md`. 이론: `theory/`.

## 작업 규칙 (위반 시 빌드 실패)

1. **숫자 리터럴 금지** — `model/` 코드에 파라미터 숫자를 쓰지 않는다. 모든 파라미터는
   `config/calibration.xlsx`, `config/firms.csv`, `config/routes.csv`, `config/scenarios.csv`에서 온다.
   `s02_calibrate.py`가 검증된 `CalibrationSet` 하나로 만들고, 이후 단계는 그 객체만 받는다.
   (예외: 0, 1 같은 수학 항등원, 배열 인덱스.)
2. **모든 출력은 JSON artifact** — `outputs/*.json`. 웹(`web/`)은 계산하지 않고 그것만 읽는다.
   figure 1개 = JSON 1개. `outputs/manifest.json`에 실행 시각·config 해시·git SHA·seed 기록.
3. **anchor 시스템** — config의 모든 파라미터 행은 `theory_anchor`로 `theory/*.md`의
   `{#anchor-id}`를 참조해야 한다. `make check-anchors`가 양방향(고아 공리, 근거 없는 파라미터) 검증.
4. **status 전파** — 파라미터마다 `status`(measured/banded/assumed). `assumed` 파라미터가
   결과 수준에 들어가면 출력 JSON에 `conditional_on: [...]`이 자동으로 붙고, 웹 UI 배지까지 흐른다.
5. **`data/raw/` 수정 금지** — 읽기 전용. processed는 `s01_ingest.py`로만 생성.
   provenance 미등록 raw 파일이 있으면 `make ingest` 실패.
6. **결측은 NaN 유지** — 임의 보간 금지. 날짜 ISO, 통화 USD 컬럼 + 원통화 병기.
7. **이론 md의 계산값은 `{{shares.POSCO.carbon}}` 치환** — 하드코딩 금지. 모델 재실행이 문서 숫자를 갱신.
8. **논문 수치와 불일치 발견 시 조용히 맞추지 말 것** — `PAPER_DIFF.md`에 기록. 불일치는 버그가 아니라 발견일 수 있다.

## 명령

```
make ingest        # raw → processed (provenance 검증 포함)
make model         # s02→s06, outputs/*.json 재생성
make check-anchors # 이론↔config 양방향 anchor 검증
make ledger        # theory/LEDGER.md 자동 섹션 재생성
make test          # 회귀 테스트 (σ 0.40→0.88 검산, share 합=1, λ 불변성 등)
make web           # 이론 md 라이브 수치 치환 + Next.js 빌드
make all           # 전부
```

Python은 uv 관리 (`uv run ...`). 웹은 `web/`에서 Next.js App Router, SSG, recharts.
색상 토큰은 `web/tokens.json` 한 곳에만.
