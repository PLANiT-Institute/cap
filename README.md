# CAP — Carbon-transition Asset Pricing

**Transition-risk underwriting + pathway decision system** — 한·일 철강 5사 11개 고로와
한·일 석유화학 NCC archetype 2개. 석유화학 자산·원료·경로 수치는 현재 명시적
`assumed/provisional` 입력이며 기업 실측치가 아니다.

> CAP maps the gap between privately optimal and required decarbonization pathways
> into a conditional distribution of transition cash-flow losses, decomposes its
> sources, and evaluates which interventions change both transition timing and
> residual risk.

인과사슬: 자산 구성 → 사적 최적 경로(τ*, LSM) → 요구 경로(T_required) →
**condition gap**(누적 초과배출) → 개입(파라미터 변환) 후 τ*·경로 재계산 →
잔여 위험 anatomy → **conditional risk charge**. 수준(bps)은 마지막 단계의
조건부 결과이지 출발점이 아니다. 현재 구현은 시장위험프리미엄의 실증 식별을
주장하지 않는다 (P1은 scalar λ·p_bind 소거 항등까지만).

제품은 같은 계산엔진을 투자자·기업재무·거래 화면으로 번역한다.

- **`/underwrite` — CAP Transition Risk Underwriter**: 기술 route → 위험 anatomy →
  model-implied conditional spread → 계약 전후 잔여위험. 투자자용 상대가치·λ×p_bind
  민감도, 기업 재무용 계약 우선순위, 그리고 거래용 route NPV·IRR·DSCR·필요 green
  premium·break-even 가격과 sector 간 위험지도를 제공한다.
- **`/` — CAP Pathways**: 사적 경로와 요구 경로, 누적 condition gap, 개입의 실제
  투자시점·배출경로 효과를 본다.

Underwriter의 bps는 관측 채권·대출 스프레드가 아니며, 연간 USD 값도 실현될
금융비용 절감 예측이 아니다. 동일한 conditional risk charge를 EV에 적용한 비교용
환산치다. 계약가격 데이터가 들어오기 전 순위는 **benefit-only**이다.

세 원칙: ① 코드에 숫자를 쓰지 않는다 ② 모든 출력은 JSON artifact ③ 이론의 모든
주장은 anchor ID를 갖고 config가 역참조한다. 상세: [PLAN.md](PLAN.md) · [CLAUDE.md](CLAUDE.md)
· 금융제품 범위와 데이터 게이트: [FINANCIAL_TOOL.md](FINANCIAL_TOOL.md)

현재 release stage는 **INTERNAL_RESEARCH_PREVIEW**다. 10→20 구현·평가 기준은
[MILESTONE_20.md](MILESTONE_20.md), 숫자 비교 규칙은 [RESULT_CONTRACT.md](RESULT_CONTRACT.md),
연구 한계는 [MODEL_CARD.md](MODEL_CARD.md), 검증 프로토콜은 [VALIDATION_PLAN.md](VALIDATION_PLAN.md)를
따른다. 외부 공개는 [PUBLIC_RELEASE_CHECKLIST.md](PUBLIC_RELEASE_CHECKLIST.md)의 90점 gate를
통과하기 전까지 금지하며, 실제 사례는 [PILOT_CASE_TEMPLATE.md](PILOT_CASE_TEMPLATE.md)로 기록한다.

현재 구현 수준은 **30/100 pilot-ready dry run**이다. POSCO·NIPPON 사례를 동일 입력으로
자동 재실행하고 decision/basis/stress/provenance pack을 생성한다. 상세 상태와 40점 blocker는
[MILESTONE_30.md](MILESTONE_30.md), 생성 결과는 `outputs/pilot_cases.json`과
`outputs/pilots/*.md`에 있다. 실제 거래사례와 executable quote가 없으므로 40점 달성으로
표시하지 않는다.

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
| `model/` | s01 ingest → s02 CalibrationSet → s03 LSM → s04 anatomy → s05 robustness → s06 intervention impacts → s07 pathways·condition gap → s08 investor/treasury underwriting → s09 deal & technology screening |
| `outputs/` | figure 1개 = JSON 1개 + `manifest.json` (config 해시·git SHA·seed). seed 고정 시 diff 0 |
| `theory/` | 이론 문서 — anchor `{#id}` + 라이브 수치 `{{키}}` (모델 재실행 시 자동 갱신). `LEDGER.md`는 `make ledger` 자동 생성 |
| `web/` | Next.js SSG — 계산 없음, `outputs/*.json`만 렌더. 상태 배지 measured/banded/assumed·conditional |

## 원장 논리 (한 줄)

share는 scalar λ·p_bind에 **항등 불변**(IDENTITY, P1)이되 노출 모델·시나리오·전환시점에
**model-conditional**; 절대 수준은 **scenario-conditional risk charge**. 각 artifact의
`claims` 블록이 result별 상태(IDENTITY/MODEL_CONDITIONAL/SCENARIO_CONDITIONAL/EMPIRICAL/
PROVISIONAL/OPEN)와 의존 파라미터를 기록하고, manifest가 git dirty·코드/설정/데이터
해시를 담는다. T_required는 provisional surrogate — 실증 식별된 기업 의무가 아니다.

## 계산기 (툴 원칙)

CAP은 계산기다 — 시나리오·파라미터 in, anatomy·수준 out. 가격 수준·경로는
시나리오(config)가 구동하고, 실측 시계열은 σ·ρ 캘리브레이션과 연단위 레퍼런스
(`outputs/reference_prices.json`, 웹 /data)에만 쓴다. `config/scenarios.csv`는
driver 컬럼으로 탄소 외 전력(elec_kr/elec_jp) 시나리오도 받는다.

프로그램 진입점 (향후 MCP 서버가 감쌀 시임):

```python
from model.api import compute

scenario = {
    "pricing": {"lambda": 0.6},
    "carbon_scenarios_kr": [
        {"scenario": "REFORM", "level_usd": 60, "prob": 1.0, "binds": 1},
    ],
}
compute(scenario, mode="fixed_exposure")       # 최근 τ* 고정: 빠른 가격·위험 민감도
compute(scenario, mode="full_counterfactual")  # LSM τ*·pathway·condition gap 재계산
```

두 모드는 의사결정 질문이 다르다. `fixed_exposure`는 투자자가 동일 기술·경로에서
가격조건만 스트레스할 때 쓰며 경로 효과로 해석하지 않는다. `full_counterfactual`은
연구·정책 분석용으로 기대 탄소가격 이동을 LSM drift에 반영해 사적 전환연도와
누적 alignment gap까지 다시 푼다. 두 모드 모두 T_required 자체는 바꾸지 않으며,
현행 surrogate 상태도 그대로 표시한다.

거래조건 override (파일 불변):

```python
from model.api import screen_transaction

screen_transaction({
    "firm_id": "POSCO",
    "route": "h2_dri",
    "interventions": ["h2_cfd"],
    "terms": {"green_premium_usd_t": 240, "debt_share": 0.5},
})  # → NPV·IRR·DSCR·필요 premium·잔여 charge before/after
```

기본 거래 profile은 `config/transaction_assumptions.csv`의 명시적 가정이며 market
quote가 아니다. 대안 route는 configured route와 같은 감축심도를 충족하는지 별도
gate를 통과하고, 기술·원료·인프라 타당성은 `OPEN`으로 남긴다.
계약별 모델 가격·커버리지·기간과 서명 전 필수 조항은 `config/interventions.csv`에서
감사 가능하게 관리하며, 실행 가능한 offer나 lender term sheet로 간주하지 않는다.
웹의 contract efficient frontier는 counterparty-adjusted ΔNPV가 높고 잔여 conditional
risk charge가 낮은 비지배 집합이다. 증권 포트폴리오의 실측 mean–variance frontier가 아니다.

석유화학은 `e_cracker`, `ccus_cracker`, `circular_olefins` 세 경로와 feedstock
가격·전력·탄소·CAPEX 노출을 별도로 계산한다. 철강 수치의 라벨만 바꾼 것이 아니다.
다만 현 단계의 NCC 용량·EV·WACC·원료가격·CAPEX와 T_required는 archetype 가정이므로,
기업 의사결정 전 실제 cracker train, feed slate, yield, energy balance, turnaround와
계약 quote로 교체해야 한다.

파일 불변 — 두 계산 모드 모두 config·outputs를 건드리지 않는다. 기본 모드는 기존
호출과의 호환을 위해 `fixed_exposure`; 경로 결론에는 `full_counterfactual`을 명시한다.

## 미확보 데이터 (도착 시 자동 승격)

`data/raw/{kau,smp,jepx,gcam}/MISSING.md` — 파일을 해당 폴더에 넣고 provenance 등록 후
`make all` 하면 σ·ρ가 measured로 승격되고 surrogate가 교체된다.

## 논문 대조

[PAPER_DIFF.md](PAPER_DIFF.md) — σ 0.40→0.88 검산·불변성·클러스터 분리는 재현,
share 수준 수치는 노출 창 정의 차이로 이동 (조용히 맞추지 않고 기록).
