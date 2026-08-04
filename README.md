# CAP — Capital Allocation Pathway

> **Name note (2026-08-03).** CAP has always been the Capital Allocation
> Pathway project (knowledge-base reset 2026-06-09). The expansion
> "Carbon-transition Asset Pricing" was introduced at the 2026-07-22 repo
> rebuild around the paper's anatomy frame and is retired: asset pricing is
> one translation layer of this engine, not its identity. Final plan:
> [RESTRUCTURE_2026-08.md](RESTRUCTURE_2026-08.md) · review:
> [REVIEW_2026-08.md](REVIEW_2026-08.md).

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

## The question

**Why does transition capital not flow to net zero, when and how much is
needed, and what moves it?** Computed bottom-up for 11 blast furnaces across
5 Korean/Japanese steelmakers — a **partial fleet**, about one third of those
firms' crude steel (21–48% by firm), so enterprise-value basis points are not
comparable across firms; use $/t and deltas (see `DECISIONS.md` X12). Plus 2
petrochemical NCC archetypes kept as explicitly `assumed/provisional`
calculation examples, not measurements.

The causal chain: asset registry → privately optimal switch timing (τ\*, LSM)
→ required pathway (T_required, surrogate; sector pool allocated pro-rata by
capacity under the reline investment-window constraint) → **condition gap**
(cumulative excess emissions) → why capital waits (**LEVEL** = break-even
shortfall · **WEDGE** = the extra waiting created by uncertainty through the
m(σ) hurdle) → interventions as parameter transformations → τ\*, pathways and
residual-risk anatomy recomputed → investor translation (conditional bps).
The bps level is the conditional last step, not the starting point; waiting
does not remove risk — it accumulates it as the gap.

## Three views, one engine

1. **LEVEL / WEDGE** — why and how late capital moves; emission effects of
   interventions attributed by lever class (LEVEL levers / σ-cutting contract
   levers / dual), order-averaged.
2. **Risk anatomy** — what the uncertainty is made of, by driver, shown as
   bands; each component carries its contract name and decision owner
   (joint / public / lender). On the private path every firm now reads as a
   *concentration* in carbon policy, because the pre-switch carbon leg runs to
   τ*≈2050 and dominates; the *composition* reading (hydrogen-dominated) belongs
   to the post-transition world, i.e. under a required path or an intervention
   package (see `PAPER_DIFF.md` update 13). Non-transitioning firms are a
   *concentration* for a second reason (single carbon-policy
   exposure no private contract can touch).
3. **Investor translation** — σ_B, Δσ, Δbps, rankings and deal gates are
   engine outputs; the pricing scale (λ, k, p_bind, EV) is the user's input
   (`model/api.py compute`, defaults = config with status badges). Levels are
   quoted only with their conditionality; Δ and rank are robust to the scale.

Three principles: ① no numeric literals in code ② every output is a JSON
artifact ③ every theoretical claim carries an anchor ID that config
back-references. Details: [PLAN.md](PLAN.md) (original build spec) ·
[CLAUDE.md](CLAUDE.md) · [RESTRUCTURE_2026-08.md](RESTRUCTURE_2026-08.md)
(final update plan).

Release stage, implementation level (30/100), gates and external-release
blockers: **[STATUS.md](STATUS.md)**. Number-comparison rules:
[RESULT_CONTRACT.md](RESULT_CONTRACT.md) · research limits:
[MODEL_CARD.md](MODEL_CARD.md) · validation protocol:
[VALIDATION_PLAN.md](VALIDATION_PLAN.md) · real cases via
[PILOT_CASE_TEMPLATE.md](PILOT_CASE_TEMPLATE.md). Underwriter bps are not
observed bond or loan spreads; rankings are benefit-only until contract-price
data arrives.

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
| `archive/` | superseded records, code and data — each batch carries a `TOMBSTONE.md`; never cite as current evidence |
| `web/` | Next.js SSG — no computation; renders `outputs/*.json` with measured/banded/assumed badges |

## Ledger logic (one line)

Shares are **identity-invariant** to scalar λ·p_bind (P1) but
**model-conditional** on the exposure model, scenarios, and switch timing;
absolute levels are **scenario-conditional risk charges**. Each artifact's
`claims` block records per-result status (IDENTITY / MODEL_CONDITIONAL /
SCENARIO_CONDITIONAL / EMPIRICAL / PROVISIONAL / OPEN) and parameter
dependencies; the manifest records dirty state before and after generation
plus code/config/data hashes. T_required is a provisional surrogate — not an
empirically identified corporate obligation.

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
executable offer or a lender term sheet.

Petrochemicals are computed separately across `e_cracker`, `ccus_cracker`,
and `circular_olefins` with their own feedstock, power, carbon, and CAPEX
exposures. NCC capacity, EV, WACC, feedstock prices, CAPEX, and T_required
are archetype assumptions; the final plan (W1) schedules their demotion from
headline outputs to calculation examples.

File-invariant: neither computation mode touches config or outputs. The
default mode is `fixed_exposure` for compatibility; pathway conclusions must
state `full_counterfactual` explicitly.

---

*Theory documents (`theory/*.md`) are currently in Korean; an English
migration is tracked as an open ticket. Interface documents, decision records,
and commit messages are in English (see CONTRIBUTING.md, Language).*
