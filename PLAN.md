# CAP 재구축 계획 — Claude Code 실행 지시서

> **프로젝트**: CAP (Carbon-transition Asset Pricing) — 한·일 철강 transition-risk premium의 anatomy
> **목표**: 논문의 모든 수치가 재현 가능한 파이프라인에서 나오고, 파라미터는 전부 config 파일에 살고, 결과는 Vercel에 배포되며, 이론(.md)과 모델 출력이 서로를 참조하는 살아있는 리포지토리.
> **원칙 세 줄**: ① 코드에 숫자를 쓰지 않는다(모든 파라미터는 config에서 온다). ② 모든 출력은 JSON artifact로 떨어지고 웹은 그것만 읽는다. ③ 이론 문서의 모든 주장은 anchor ID를 갖고, config와 코드가 그 ID를 역참조한다.

---

## 0. 리포지토리 구조

```
cap/
├── CLAUDE.md                  # 이 계획의 요약 + 작업 규칙 (Claude Code가 항상 읽는 파일)
├── PLAN.md                    # 본 문서
├── data/
│   ├── raw/                   # 원본 그대로 (수정 금지, 읽기 전용 취급)
│   ├── processed/             # ingest 산출물 (parquet/csv, 스크립트로만 생성)
│   └── DATA_PROVENANCE.md     # 파일별 출처·수집일·라이선스·해시
├── config/
│   ├── calibration.xlsx       # 마스터 캘리브레이션 북 (§2 시트 구조)
│   ├── firms.csv              # 기업·고로 레지스트리
│   ├── routes.csv             # 기술 route별 감응도 벡터 a
│   ├── scenarios.csv          # 탄소 policy-jump 시나리오 {수준, 확률}
│   └── schema/                # 각 config의 pandera/JSON-schema 검증 정의
├── model/                     # Python (uv 관리)
│   ├── s01_ingest.py
│   ├── s02_calibrate.py
│   ├── s03_lsm.py             # 교환옵션 LSM → τ*, wedge, σ_B 선형성 체크
│   ├── s04_anatomy.py         # Euler 분해 → driver shares
│   ├── s05_robustness.py      # σ×R×carbon grid, λ×p_bind 불변성 데모
│   ├── s06_contracts.py       # CfD/PPA/보조금 waterfall, Δπ
│   └── lib/                   # 순수 함수만 (config 로드는 s0*에서만)
├── outputs/                   # 단계별 JSON artifact (figure 1개 = JSON 1개)
│   └── manifest.json          # 실행 시각, config 해시, git SHA, seed
├── theory/                    # 이론 문서 (§4)
│   ├── 00_axioms.md
│   ├── 01_wedge.md
│   ├── 02_variance_premium.md
│   ├── 03_proposition1.md
│   ├── 04_carbon_jump.md
│   ├── 05_contracts_identification.md
│   └── LEDGER.md              # proven vs conditional 원장 (자동 생성 섹션 포함)
├── web/                       # Next.js (App Router) → Vercel
└── Makefile                   # make all = ingest→…→web build
```

---

## Phase 1 — 데이터 수집·정리 (기존 폴더 이관)

데이터는 이미 로컬 폴더에 있다. 이 단계의 일은 **수집이 아니라 등록**이다.

1. 기존 폴더의 파일을 `data/raw/`로 복사하고, 파일마다 `DATA_PROVENANCE.md`에 한 줄 등록: 파일명, 내용, 출처, 수집일, 단위, SHA256. 출처 불명 파일은 `UNKNOWN`으로 표시하고 진행을 막지 않되 LEDGER에 자동 반영.
2. `s01_ingest.py`: raw → `data/processed/` 표준화. 규칙 — 날짜는 ISO, 통화는 USD 기준 컬럼 + 원통화 컬럼 병기, 결측은 NaN 유지(임의 보간 금지). 각 산출물에 pandera 스키마 검증.
3. **신규 수집 2건 (논문 피드백에서 나온 최우선 보완)**:
   - KAU 일별 시계열 (KRX 배출권시장 공개 데이터) → σ_carbon-diffusion을 banded에서 **measured**로 승격
   - SMP 시계열 (전력거래소) → ρ(elec, carbon)을 실측 상관으로 승격
   - JEPX 현물 (가능하면) → σ_elec(JP) 검증
4. GCAM raw pathway는 미확보 상태 그대로 인정: `data/raw/gcam/MISSING.md`에 무엇이 필요한지 명세하고, 현행 logistic surrogate를 `s02`의 명시적 fallback으로 구현 (surrogate 사용 시 manifest에 `t_gcam_source: "surrogate"` 기록).

**완료 기준**: `make ingest`가 raw를 건드리지 않고 processed를 전부 재생성하며, provenance에 미등록된 raw 파일이 있으면 실패한다.

---

## Phase 2 — Config 구동 분석 프레임워크 (하드코딩 제로)

### 2.1 calibration.xlsx 시트 구조 (논문 Table 1의 기계가독 버전)

| 시트 | 내용 | 필수 컬럼 |
|---|---|---|
| `sigmas` | 드라이버별 변동성 | driver, value, band_lo, band_hi, **status**(measured/banded/assumed), source, confidence, theory_anchor |
| `correlations` | ρ 행렬 (long form) | driver_i, driver_j, value, band_lo, band_hi, status, source, theory_anchor |
| `pricing` | λ, p_bind, k | param, value, status(=assumed), theory_anchor |
| `lsm` | seed, n_paths, horizon, basis 차수, band grid | param, value |
| `carbon_jump` | (scenarios.csv와 동일 스키마, 우선순위는 csv) | scenario, level_usd, prob, anchor_note |

**핵심 규칙**
- 모델 코드 어디에도 숫자 리터럴 금지. `s02_calibrate.py`가 xlsx/csv를 읽어 검증된 `CalibrationSet` 객체 하나로 만들고, 이후 단계는 그 객체만 받는다.
- 모든 파라미터 행은 `status`와 `theory_anchor`(§4 참조)가 필수. status가 `assumed`인 파라미터가 결과 수준에 들어가면 출력 JSON에 `conditional_on: [...]` 배열이 자동으로 붙는다 — 논문 §5 원장이 **데이터 구조로** 존재하게 하는 장치.
- σ·ρ의 band는 grid 실행의 입력: `s05`가 band 안에서 draw하여 share envelope 생성.

### 2.2 모델 단계별 산출 (각 단계 = JSON artifact)

| 단계 | 산출 JSON | 논문 대응 |
|---|---|---|
| s03 LSM | `tau_star.json`, `wedge.json`, `sigma_linearity.json` | Fig 2, §3.4 R²=0.99 체크 |
| s04 Anatomy | `shares_by_firm.json`, `cost_vs_risk.json` | Fig 3, Fig 4 |
| s05 Robustness | `share_envelopes.json`, `lambda_invariance.json`, `cluster_separation.json` | Fig 5, Fig 8, Prop 1 수치 데모 |
| s06 Contracts | `waterfall.json`, `delta_pi_ranking.json` | Fig 6 |

**논문 피드백 반영 태스크 (신규)**
- `s05`에 **driver별 λ_k 감응도** 모듈 추가: λ 벡터를 config에서 받아 s_k = λ_k·RC_k/Σλ_j·RC_j 재계산, 균일 λ 대비 share 변화를 리포트 (심사 대비 robustness).
- `s03`에 p_bind가 행사정책에 들어가는 변형(τ*(p_bind)) 실험 플래그 — 기본 off, LEDGER에 미구현/구현 상태 자동 표기.
- Hyundai 처리 일관화: `firms.csv`에 `category` 컬럼(priced_route / no_feasible_route) 추가, `no_feasible_route` 자산은 anatomy 출력에서 자동 제외되고 stranding 출력으로 분리 — Fig 3와 §4.6의 모순을 데이터 수준에서 차단.

**완료 기준**: `make model`이 config만 바꿔서 (코드 수정 없이) 전체 결과를 재생성하고, `outputs/manifest.json`의 config 해시가 바뀐다. seed 고정 시 JSON diff가 0.

---

## Phase 3 — Vercel 배포 (web/)

1. **Next.js App Router + 정적 생성(SSG)**. 웹은 계산하지 않는다 — `outputs/*.json`을 빌드 타임에 읽어 렌더만 한다. 모델 재실행 → JSON 갱신 → `git push` → Vercel 자동 재배포가 전체 루프.
2. 페이지 구성:
   - `/` — 핵심 결과: 두 클러스터 100% 누적막대 (Fig 3), 한 문단 요약
   - `/anatomy/[firm]` — 기업별 상세: share, envelope, waterfall
   - `/wedge` — 고로별 덤벨 (Fig 2), WACC-equalized 토글
   - `/theory/[slug]` — §4의 이론 문서 렌더
   - `/ledger` — proven/conditional 원장 (config status에서 자동 생성)
   - `/data` — provenance 테이블
3. 차트는 recharts (기존 논문 도식과 동일한 navy/slate 팔레트 — 색상 토큰도 `web/tokens.json` 한 곳에).
4. 모든 수치 옆에 상태 배지: `measured` / `banded` / `assumed·conditional` — pricing 시트의 status가 그대로 UI까지 흐른다.
5. Vercel 설정: 모노레포 루트에서 `web/`만 빌드, `outputs/`는 빌드에 포함(정적 import). 환경변수·서버 비밀 없음(전부 정적) → 프리뷰 배포를 협업자 리뷰 링크로 사용.

**완료 기준**: `vercel --prod` 없이도 `make web && npx vercel deploy`로 배포되고, config에서 λ를 바꾸면 사이트의 bps 수준은 바뀌되 share는 불변임이 눈으로 확인된다 (Prop 1의 살아있는 데모).

---

## Phase 4 — 이론 .md ↔ 모델 상호작용

이론이 죽은 문서가 되지 않게 하는 양방향 장치 두 개.

### 4.1 이론 → 모델: anchor 시스템

각 이론 문서의 주장 블록에 ID를 단다:

```md
<!-- theory/03_proposition1.md -->
## 공리 A2 {#axiom-uniform-lambda}
단일 λ가 네 드라이버에 공통이다. 이 공리가 깨지면 share 불변성이 깨진다.
status: AXIOM · challenged-by: referee-note-1
```

- config의 모든 파라미터 행은 `theory_anchor`로 이 ID를 참조해야 한다 (예: λ 행 → `#axiom-uniform-lambda`).
- `make check-anchors`: config가 참조하는 anchor가 실제 md에 존재하는지, 역으로 어떤 공리도 config에서 고아가 아닌지 검증. 깨지면 CI 실패.

### 4.2 모델 → 이론: 라이브 수치 주입

이론 md 안에서 계산값을 하드코딩하지 않고 참조한다:

```md
POSCO의 탄소 share는 {{shares.POSCO.carbon}}이며, reform-priced에서 {{shares_reform.POSCO.carbon}}로 상승한다.
```

- 웹 빌드 시 `outputs/*.json`에서 치환 (간단한 remark 플러그인 하나). 모델을 다시 돌리면 이론 문서의 숫자가 **자동으로** 따라온다 — 논문 개정 때 본문 숫자 불일치가 원천 차단됨.
- `LEDGER.md`의 proven/conditional 표는 손으로 쓰지 않는다: `sigmas`/`pricing` 시트의 status 컬럼에서 스크립트가 생성한 섹션 + 손으로 쓰는 해설 섹션의 2층 구조.

### 4.3 작업 루프

이론을 고치면(공리 추가·수정) → anchor 체크가 config 갱신을 요구 → 모델 재실행 → 이론 문서의 라이브 수치 갱신 → Vercel 재배포. **이론과 숫자가 어긋난 상태로는 빌드가 통과하지 않는다.**

---

## 실행 순서 (Claude Code 작업 단위)

1. 스캐폴딩: 디렉토리, Makefile, uv 프로젝트, CLAUDE.md (이 문서 요약 + "숫자 리터럴 금지" 규칙 명기)
2. Phase 1: 기존 폴더 이관 + provenance + ingest + KAU/SMP 신규 수집
3. Phase 2: calibration.xlsx 스키마 → s02~s06 순서대로, 단계마다 논문 수치와 대조 (Fig 3의 share, 0.40→0.88 검산 등 회귀 테스트로 고정)
4. Phase 4의 anchor/치환 시스템 (웹보다 먼저 — md 구조가 웹 렌더의 입력이므로)
5. Phase 3: 웹 + Vercel
6. 마지막: `make all` 원커맨드 재현 + README

각 Phase 완료 시 논문 원본 수치와의 diff 리포트를 남길 것. 불일치는 버그가 아니라 발견일 수 있으니(기존 repo의 하드코딩이 원인일 가능성) 조용히 맞추지 말고 기록할 것.
