# ARCHITECTURE — how data moves through this repository

Read this first. It explains **what produces what, and where the build stops**.
Individual claims live in `theory/` (anchored), terms in [GLOSSARY.md](GLOSSARY.md),
the ingest contract in [DATA_INTERFACE.md](DATA_INTERFACE.md), and the promotion
workflow from the external knowledge base in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 1. One-page summary

```
             ┌─ config/sheets/*.csv ─┐
             │  config/*.csv         │  ← parameters (every number lives here)
             └───────────┬───────────┘
                         │  make calibration
data/raw/                ▼
  <dataset>/*.csv  →  config/calibration.xlsx (build artifact)
      │                  │
      │ make ingest      │
      ▼                  ▼
data/processed/*.parquet ──→ s02 CalibrationSet ──→ s03 … s13 ──→ outputs/*.json
                                                                      │
                                     theory/*.md ──{{substitution}}───┤
                                                                      ▼
                                                            web/content/ → web/out
```

Three principles govern the whole picture:

1. **No numeric literals in code.** Every parameter comes from `config/`.
   `s02_calibrate.py` builds one validated `CalibrationSet`; every later stage
   receives only that object. (Exceptions: mathematical identities like 0 and 1,
   and array indices.)
2. **Every output is a JSON artifact.** One figure = one JSON. The web layer
   computes nothing; it only reads.
3. **Every theoretical claim carries an anchor ID, and config back-references it.**
   If the two-way check breaks, the build fails.

---

## 2. Stages

### Input layer

| Location | Contents | Edited by |
|---|---|---|
| `data/raw/<dataset>/` | Imported source CSVs. **Read-only — never modified in place** | humans (import only) |
| `data/provenance.yaml` | Per-pattern registry: source, collection date, units, license (23 patterns) | humans |
| `config/sheets/*.csv` | σ, ρ, pricing, LSM engine parameters — **the editing SSOT** | humans |
| `config/firms.csv` | Asset registry (capacity, reline year, intensity, route, WACC, EV) | humans |
| `config/routes.csv` | Sensitivity vector *a* per route (input intensities, base prices, capex) | humans |
| `config/scenarios.csv` | Carbon scenarios per country (level, probability, binding flag) | humans |
| `config/interventions.csv` | Contract/policy interventions as parameter transformations (coverage, tenor, basis band) | humans |
| `config/transaction_assumptions.csv` | Deal-screening assumptions (debt share, DSCR, PD, …) | humans |
| `config/calibration.xlsx` | **Build artifact.** Assembled from sheets by `make calibration`. Not tracked by git | machine |

### Processing stages

| Stage | What it does | Key outputs |
|---|---|---|
| `s01_ingest` | raw → processed. ISO dates, USD plus original currency, **missing values stay NaN (no interpolation)**, pandera validation. Builds time-series parquet when KAU/SMP/JEPX files exist | `data/processed/*.parquet` |
| `s02_calibrate` | config + processed → one validated `CalibrationSet`. Splits carbon into country factors, derives `p_bind`, resolves `T_required` in country×route pools, and tags source/pathway kind/headline eligibility per asset | `calibration_resolved.json` |
| `s03_lsm` | Exchange-option LSM → asset-level τ\* (base and per intervention), wedge = τ\* − T_required, WACC-equalized variants | `tau_star`, `wedge`, `sigma_linearity` |
| `s04_anatomy` | Euler decomposition of transition-cost uncertainty. Carbon uses the matched conditional pair `E[level|bind]` and `sigma_binding`, then multiplies `p_bind` once | `shares_by_firm`, `cost_vs_risk`, `premium_levels`, `stranding` |
| `s05_robustness` | Share envelopes over σ·ρ band draws, λ×p_bind grid invariance (P1 demo), cluster separation, per-driver λ_k sensitivity | `share_envelopes`, `lambda_invariance`, `cluster_separation`, `lambda_k_sensitivity` |
| `s06_interventions` | Interventions change τ\*, pathways, anatomy, and level **together**. Basis solved as a lo/hi band | `intervention_impacts` |
| `s07_pathways` | Emission pathways per firm (BAU / private / required / per intervention) and the cumulative alignment gap | `emissions_pathways_by_firm`, `condition_gap` |
| `s13_gap_pricing` | Explicit reduced-form bridge: annual physical gap → country scenario-loss distribution → separate gap-linked risk charge. `p_bind` is embedded in scenario probabilities and is not multiplied again | `alignment_gap_loss` |
| `s08_underwriting` | Investor view (model-implied spread, λ×p_bind sensitivity surface) and corporate-finance view (contract priorities) | `transition_underwriting` |
| `s09_deal_screening` | Pre-deal screen — NPV, IRR, DSCR, required green premium per route and intervention | `deal_screening` |
| `s10_result_contract` | Emits the metric/basis/evidence contract as an artifact | `result_contract` |
| `s11_pilot_cases` | Regenerates POSCO/NIPPON dry-run evidence packs; verifies deterministic replay | `pilot_cases`, `outputs/pilots/*.md` |
| `run_all` | Runs s02–s13 in dependency order, then writes `manifest.json` (run time, git SHA, dirty flag, config/code/data hashes, seed) | `manifest` |

### Output layer

- `outputs/*.json` — **the public API.** Web, paper, and slides all read numbers
  from here.
- `theory/*.md` — theory documents using `{{shares.POSCO.carbon}}`-style
  placeholders. `make render-theory` fills them from artifacts into
  `web/content/theory/`. **Numbers are never typed by hand** — rerunning the
  model updates the documents.
- `web/` — Next.js App Router, SSG. Reads JSON only.

> `web/content/theory/` is generated **but committed**: the Vercel build runs
> only `cd web && npm run build` and never `render_theory`, so the rendered
> files are deployment inputs. By contrast `config/calibration.xlsx` changes
> its bytes on every reassembly (zip metadata) even when no cell changes, so it
> is excluded from git, from the manifest hashes, and from the pilot fingerprint.

---

## 3. Validation gates — where the build stops

| Gate | Command | Failure condition |
|---|---|---|
| provenance | `make ingest` | Any file in `data/raw/` that matches no pattern in `provenance.yaml` |
| schema | `make ingest` | pandera violation (type, range, uniqueness) |
| anchors, both ways | `make check-anchors` | A parameter citing a non-existent anchor, or an orphan axiom no config references |
| regression | `make test` | Structural property violated — shares sum to 1, λ invariance, composition collapse under negative correlation, basis-band monotonicity, … |
| substitution | `make render-theory` | Unresolved `{{...}}` left in a theory document |

CI (`.github/workflows/ci.yml`) runs the full `make all` on every push and PR.
Any failure blocks the merge.

---

## 4. Status propagation — what you may believe

Every parameter carries a `status`:

| status | meaning |
|---|---|
| `measured` | computed directly from observed series or filings |
| `banded` | sourced, but a range rather than a point |
| `assumed` | set without evidence — an explicit assumption |
| `derived` | computed from other parameters (e.g. `p_bind`) |
| `provisional` | surrogate — not empirically identified (e.g. `T_required`) |

Status propagates into each artifact's `conditional_on` array and through to the
web UI badges. No artifact ever gets a blanket "proven" label. Result-level
evidence grades follow [RESULT_CONTRACT.md](RESULT_CONTRACT.md) —
`IDENTITY` / `MODEL_CONDITIONAL` / `SCENARIO_CONDITIONAL` / `EMPIRICAL` /
`PROVISIONAL` / `OPEN` — and when several grades apply, **the most restrictive
one is displayed nearest the result.**

**Two numbers are comparable only when both `metric_id` and `basis_id` match.**
Enterprise transition-window bps and project-at-commissioning bps are different
objects that happen to share a unit.

---

## 5. Reproduction

```bash
uv sync                  # Python deps (once)
(cd web && npm install)  # web deps (once)
make all                 # ingest → calibration → model → anchors → ledger → theory → test → web
```

Individual stages: `make ingest` / `make calibration` / `make model` /
`make check-anchors` / `make ledger` / `make render-theory` / `make test` / `make web`

The `seed` is pinned in `config/sheets/lsm.csv`, so identical inputs make the
numerical artifacts deterministic. `outputs/manifest.json` itself includes a
run timestamp and is therefore expected to differ. It records the git SHA,
dirty state before and after artifact generation, and config/code/data hashes.

Programmatic access is `model/api.py`:

- `compute(overrides, mode=...)` — `fixed_exposure` (τ\* held, price sensitivity
  only) or `full_counterfactual` (τ\*, pathways, and gaps recomputed). Neither
  mode writes files.
- `screen_transaction({...})` — deal-term overrides.

---

## 6. Boundaries of this repository

- The repo is **self-contained**. No file references an external storage path.
  External data arrives as CSV imports with label-only provenance
  ([DATA_INTERFACE.md](DATA_INTERFACE.md)).
- Bulk source material and literature PDFs stay outside. The repo keeps only the
  imported CSVs, provenance records, and verified literature notes
  (`References/`).
- Open judgement calls are collected in [DECISIONS.md](DECISIONS.md).
- Discrepancies — against the original paper, or surfaced by literature
  verification — are recorded in [PAPER_DIFF.md](PAPER_DIFF.md). **We do not
  silently reconcile**: a mismatch may be a finding, not a bug.
