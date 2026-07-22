# CAP — Carbon-transition Asset Pricing

한·일 철강 5사 11개 고로의 transition-risk premium **anatomy**. 논문의 모든 수치가
재현 가능한 파이프라인에서 나오고, 파라미터는 전부 config에 살고, 결과는 Vercel에
배포되며, 이론(.md)과 모델 출력이 서로를 참조한다.

세 원칙: ① 코드에 숫자를 쓰지 않는다 ② 모든 출력은 JSON artifact ③ 이론의 모든
주장은 anchor ID를 갖고 config가 역참조한다. 상세: [PLAN.md](PLAN.md) · [CLAUDE.md](CLAUDE.md)

## 원커맨드 재현

```bash
uv sync                 # Python 의존성 (최초 1회)
(cd web && npm install) # 웹 의존성 (최초 1회)
make all                # ingest → calibration → model → anchors → ledger → theory → test → web
```

개별 단계: `make ingest` / `make model` / `make check-anchors` / `make ledger` /
`make render-theory` / `make test` / `make web`

배포: `make web && cd web && npx vercel deploy` (루트 `vercel.json`이 web/만 빌드).

## 구조

| 경로 | 내용 |
|---|---|
| `data/raw/` | 원본 (수정 금지) — 전 파일 `data/DATA_PROVENANCE.md` 등록 (SHA256), 미등록 시 ingest 실패 |
| `data/processed/` | `model/s01_ingest.py` 산출 parquet |
| `config/` | **모든 파라미터** — `calibration.xlsx`(sigmas·correlations·pricing·lsm·carbon_jump), `firms.csv`, `routes.csv`, `scenarios.csv`. 편집 정본은 `config/sheets/*.csv` (xlsx는 `make calibration`으로 조립) |
| `model/` | s01 ingest → s02 CalibrationSet → s03 LSM(τ*, wedge) → s04 anatomy(Euler shares) → s05 robustness(envelope, λ 불변성, λ_k) → s06 contracts(waterfall, Δπ) |
| `outputs/` | figure 1개 = JSON 1개 + `manifest.json` (config 해시·git SHA·seed). seed 고정 시 diff 0 |
| `theory/` | 이론 문서 — anchor `{#id}` + 라이브 수치 `{{키}}` (모델 재실행 시 자동 갱신). `LEDGER.md`는 `make ledger` 자동 생성 |
| `web/` | Next.js SSG — 계산 없음, `outputs/*.json`만 렌더. 상태 배지 measured/banded/assumed·conditional |

## 원장 논리 (한 줄)

anatomy(driver share·클러스터·서열)는 **proven** — λ·p_bind에 1차 동차성으로 불변
(Prop 1, `outputs/lambda_invariance.json`이 살아있는 데모). 절대 bps는 **conditional** —
status=assumed 파라미터가 들어간 artifact엔 `conditional_on`이 자동으로 붙는다.

## 계산기 (툴 원칙)

CAP은 계산기다 — 시나리오·파라미터 in, anatomy·수준 out. 가격 수준·경로는
시나리오(config)가 구동하고, 실측 시계열은 σ·ρ 캘리브레이션과 연단위 레퍼런스
(`outputs/reference_prices.json`, 웹 /data)에만 쓴다. `config/scenarios.csv`는
driver 컬럼으로 탄소 외 전력(elec_kr/elec_jp) 시나리오도 받는다.

프로그램 진입점 (향후 MCP 서버가 감쌀 시임):

```python
from model.api import compute
compute({"pricing": {"lambda": 0.6},
         "carbon_scenarios": [{"scenario": "REFORM", "level_usd": 60, "prob": 1.0, "binds": 1}]})
```

파일 불변 — config·outputs 안 건드리고 메모리에서 계산 (τ*는 최근 `make model` 고정).

## 미확보 데이터 (도착 시 자동 승격)

`data/raw/{kau,smp,jepx,gcam}/MISSING.md` — 파일을 해당 폴더에 넣고 provenance 등록 후
`make all` 하면 σ·ρ가 measured로 승격되고 surrogate가 교체된다.

## 논문 대조

[PAPER_DIFF.md](PAPER_DIFF.md) — σ 0.40→0.88 검산·불변성·클러스터 분리는 재현,
share 수준 수치는 노출 창 정의 차이로 이동 (조용히 맞추지 않고 기록).
