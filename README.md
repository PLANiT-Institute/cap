# CAP — Carbon-transition Asset Pricing

> **Canonical-source declaration.** This repository is the single source of
> truth (SSOT) for CAP's logic, theory, parameters, and code. Documents in the
> external working folder are exploration, evidence, and drafts; nothing is
> canonical until it has been promoted into `theory/` or `config/` through the
> gates in [CONTRIBUTING.md](CONTRIBUTING.md). Computation runs only in this repo.
>
> The repo is self-contained — no file references an external storage path.
> External data arrives as CSV imports under `data/raw/` and is recorded in
> provenance by source label and SHA256 only. Pipeline structure:
> [ARCHITECTURE.md](ARCHITECTURE.md) · import/citation contract:
> [DATA_INTERFACE.md](DATA_INTERFACE.md) · terms: [GLOSSARY.md](GLOSSARY.md) ·
> open judgement calls: [DECISIONS.md](DECISIONS.md).

**Transition-risk underwriting + pathway decision system** for 11 blast
furnaces across 5 Korean/Japanese steelmakers, plus 2 Korean/Japanese
petrochemical NCC archetypes. Petrochemical asset, feedstock, and route figures
are explicitly `assumed/provisional` inputs, not company measurements.

> CAP maps the gap between privately optimal and required decarbonization
> pathways into a separate reduced-form scenario-loss distribution, independently
> decomposes transition-cost uncertainty, and evaluates which interventions
> change timing and each risk basis. The two charges are not added without a
> joint covariance model.

The causal chain: asset registry → privately optimal pathway (τ\*, LSM) →
required pathway (T_required) → **condition gap** (cumulative excess
emissions) → interventions (parameter transformations) → τ\* and pathways
recomputed → residual-risk anatomy → **conditional risk charge**. The level
(bps) is the conditional last step, not the starting point. The current
implementation does not claim empirical identification of a market risk
premium (P1 covers only the scalar λ·p_bind cancellation identity).

The product translates one computation engine into investor, corporate-finance,
and transaction views:

- **`/underwrite` — CAP Transition Risk Underwriter**: technology route → risk
  anatomy → model-implied conditional spread → residual risk before/after
  contracts. Relative value and λ×p_bind sensitivity for investors, contract
  priorities for corporate finance, and route NPV/IRR/DSCR, required green
  premium, break-even prices, and a cross-sector risk map for transactions.
- **`/` — CAP Pathways**: private vs required pathways, cumulative condition
  gap, and the actual investment-timing and emission-pathway effects of
  interventions.

Underwriter bps are not observed bond or loan spreads, and annual USD figures
are not forecasts of realized financing savings. They are the same conditional
risk charge applied to EV for comparison. Until contract-price data arrives,
rankings are **benefit-only**.

Three principles: ① no numeric literals in code ② every output is a JSON
artifact ③ every theoretical claim carries an anchor ID that config
back-references. Details: [PLAN.md](PLAN.md) · [CLAUDE.md](CLAUDE.md) ·
financial-product scope and data gates: [FINANCIAL_TOOL.md](FINANCIAL_TOOL.md)

The release stage is **INTERNAL_RESEARCH_PREVIEW**. The 10→20 implementation
bar is [MILESTONE_20.md](MILESTONE_20.md), number-comparison rules are
[RESULT_CONTRACT.md](RESULT_CONTRACT.md), research limits are
[MODEL_CARD.md](MODEL_CARD.md), and the validation protocol is
[VALIDATION_PLAN.md](VALIDATION_PLAN.md). External release is blocked until
the 90-point gate in [PUBLIC_RELEASE_CHECKLIST.md](PUBLIC_RELEASE_CHECKLIST.md);
real cases are recorded via [PILOT_CASE_TEMPLATE.md](PILOT_CASE_TEMPLATE.md).

The current implementation level is **30/100, pilot-ready dry run**: the
POSCO/NIPPON cases replay automatically from identical inputs and produce
decision/basis/stress/provenance packs. Status and the 40-point blockers are
in [MILESTONE_30.md](MILESTONE_30.md); generated packs live in
`outputs/pilot_cases.json` and `outputs/pilots/*.md`. With no real transaction
case and no executable quote, 40 points are not claimed.

## One-command reproduction

```bash
uv sync                 # Python deps (once)
(cd web && npm install) # web deps (once)
make all                # ingest → calibration → model → anchors → ledger → theory → test → web
```

Individual stages: `make ingest` / `make model` / `make check-anchors` /
`make ledger` / `make render-theory` / `make test` / `make web`

Deploy: `make web && cd web && npx vercel deploy` (root `vercel.json` builds web/ only).

## Layout

| Path | Contents |
|---|---|
| `data/raw/` | Sources (never modified) — every file registered in `data/DATA_PROVENANCE.md` (SHA256); unregistered files fail ingest |
| `data/processed/` | Parquet produced by `model/s01_ingest.py` |
| `config/` | **Every parameter** — `firms.csv`, `routes.csv`, `scenarios.csv`, `interventions.csv`, and the editing SSOT `config/sheets/*.csv` (`calibration.xlsx` is assembled by `make calibration`, untracked) |
| `model/` | s01 ingest → s02 CalibrationSet → s03 LSM → s04 anatomy → s05 robustness → s06 intervention impacts → s07 pathways & condition gap → s13 explicit gap-loss bridge → s08 underwriting → s09 deal screening → s10 result contract → s11 pilots → s12 LEVEL/WEDGE closed-form lane |
| `outputs/` | one figure = one JSON + `manifest.json` (config hash, git SHA, seed). Fixed inputs make numerical artifacts deterministic; manifest run time is expected to change |
| `theory/` | theory documents — anchors `{#id}` + live values `{{key}}` (auto-refreshed on rerun). `LEDGER.md` generated by `make ledger` |
| `References/` | full-text-verified literature notes with verdicts (CONFIRMED / PARTIAL / UNVERIFIABLE / WRONG) |
| `subprojects/` | isolated decision-layer experiments that consume core artifacts without changing the core model; currently `transition_decision_bridge/` |
| `web/` | Next.js SSG — no computation; renders `outputs/*.json` with measured/banded/assumed badges |

## Ledger logic (one line)

Shares are **identity-invariant** to scalar λ·p_bind (P1) but
**model-conditional** on the exposure model, scenarios, and switch timing;
absolute levels are **scenario-conditional risk charges**. Each artifact's
`claims` block records per-result status (IDENTITY / MODEL_CONDITIONAL /
SCENARIO_CONDITIONAL / EMPIRICAL / PROVISIONAL / OPEN) and parameter
dependencies; the manifest records dirty state before and after generation plus code/config/data
hashes. T_required is a provisional surrogate — not an empirically identified
corporate obligation.

## The calculator principle

CAP is a calculator — scenarios and parameters in, anatomy and levels out.
Price levels and paths are driven by scenarios (config); observed series are
used only for σ·ρ calibration and the annual reference table
(`outputs/reference_prices.json`, web `/data`). `config/scenarios.csv` accepts
non-carbon drivers (elec_kr / elec_jp) through its driver column.

Programmatic entry points:

```python
from model.api import compute

scenario = {
    "pricing": {"lambda": 0.6},
    "carbon_scenarios_kr": [
        {"scenario": "REFORM", "level_usd": 60, "prob": 1.0, "binds": 1},
    ],
}
compute(scenario, mode="fixed_exposure")       # τ* held: fast price/risk sensitivity
compute(scenario, mode="full_counterfactual")  # LSM τ*, pathways, condition gap recomputed
```

The two modes answer different questions. `fixed_exposure` stresses price
terms on an unchanged technology path and must not be read as a pathway
effect. `full_counterfactual` is for research and policy analysis: expected
carbon-price shifts enter the LSM drift and private switch years and
cumulative alignment gaps are re-solved. Neither mode changes T_required
itself, and its surrogate status stays displayed.

Transaction-term overrides (file-invariant):

```python
from model.api import screen_transaction

screen_transaction({
    "firm_id": "POSCO",
    "route": "h2_dri",
    "interventions": ["h2_cfd"],
    "terms": {"green_premium_usd_t": 240, "debt_share": 0.5},
})  # → NPV, IRR, DSCR, required premium, residual charge before/after
```

The default transaction profile is an explicit assumption set
(`config/transaction_assumptions.csv`), not a market quote. Alternative routes
pass a separate decarbonization-depth gate against the configured route, and
technology/feedstock/infrastructure feasibility stays `OPEN`. Modelled
contract prices, coverage, and tenor — and the must-have clauses before any
signature — are auditable in `config/interventions.csv`; nothing is an
executable offer or a lender term sheet. The web's contract efficient frontier
is the non-dominated set by counterparty-adjusted ΔNPV and residual
conditional risk charge — not an observed mean–variance frontier.

Petrochemicals are computed separately across `e_cracker`, `ccus_cracker`,
and `circular_olefins` with their own feedstock, power, carbon, and CAPEX
exposures — not steel numbers with new labels. At this stage NCC capacity, EV,
WACC, feedstock prices, CAPEX, and T_required are archetype assumptions; before
any corporate decision they must be replaced with actual cracker trains, feed
slates, yields, energy balances, turnarounds, and contract quotes.

File-invariant: neither computation mode touches config or outputs. The
default mode is `fixed_exposure` for compatibility; pathway conclusions must
state `full_counterfactual` explicitly.

---

*Theory documents (`theory/*.md`) are currently in Korean; an English
migration is tracked as an open ticket. Interface documents, decision records,
and commit messages are in English (see CONTRIBUTING.md, Language).*
