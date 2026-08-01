# DATA_INTERFACE — the contract for data in and out

The contract between this repository and the outside world. The overall pipeline
is in [ARCHITECTURE.md](ARCHITECTURE.md); how findings (not just data) get
promoted into the repo is in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 0. Two-line summary

- **In**: external work arrives as a single CSV per dataset under
  `data/raw/<dataset>/`, registered in `data/provenance.yaml` with a source
  label. Unregistered files fail `make ingest`.
- **Out**: `outputs/*.json` is the public API. Compare two numbers only when
  both `metric_id` and `basis_id` match.

---

## 1. The repository is self-contained

**No file references an external storage path.** Absolute paths, cloud-drive
URLs, and personal home directories appear nowhere in code, config, or docs —
mounts differ across machines and paths rot silently.

External provenance is recorded **by label only**:

| Label | Meaning | File imported? |
|---|---|---|
| `planit_internal` | PLANiT Institute internal analysis (external project) | yes |
| `public_market` | public market series and filings (KAU, JEPX, DART, EDINET, …) | yes |
| `licensed` | material that cannot be redistributed | **no** — schema and hash only |

For `licensed` material, do not import the file. Describe the needed columns and
the acquisition path in `data/raw/<dataset>/MISSING.md`. The pipeline proceeds,
leaving the affected parameter `banded` or `assumed`.

---

## 2. Inbound — the import procedure

### 2.1 Upstream: one dataset = one workbook

In the external working folder, each dataset is maintained as one spreadsheet
(`CAP_DS_<name>.xlsx`) with three standard sheets:

| Sheet | Contents |
|---|---|
| `raw` | The source as received. Never edited |
| `clean` | Cleaning steps (unit conversion, outlier flags, notes) |
| `export` | The final shape headed for the repo. **Only this sheet becomes a CSV** |

### 2.2 Import

1. Save the `export` sheet as `<dataset>_YYYY-MM-DD.csv`.
2. Place it in `data/raw/<dataset>/`.
3. Register the pattern in `data/provenance.yaml`:

```yaml
  - pattern: "intensities/intensities_*.csv"
    contents: "input intensities per route (H2 kg/t, power MWh/t, residual tCO2/t)"
    source: "planit_internal"
    collected: "2026-07-29"
    units: "kg/t, MWh/t, tCO2/t"
    license: "internal analysis, research use"
```

4. Run `make ingest` — provenance and schema checks pass, and
   `data/processed/` gains a parquet. For parameter and intensity candidates,
   this is an **evidence-only** parquet: it does not change model results.
5. Review conflicts in `DECISIONS.md`; only an explicit decision may promote
   selected values into `config/sheets/*.csv` or `config/routes.csv`. That
   config change, followed by `make all`, is what changes artifacts and theory.

`data/processed/candidate_input_contract.json` records this distinction in a
machine-readable form. Importing a workbook export and changing the model are
two separate gates; provenance registration is never treated as consumption.

### 2.3 The filename is the version

When a newer dated file arrives, move the old one to `data/archive/`.
`outputs/manifest.json` pins `raw_data_sha256`, so reproducibility survives.
Never overwrite values inside a file — history disappears.

### 2.4 Intensity data requires `process_boundary`

Power and hydrogen intensities are **incomparable without an explicit process
boundary.** In practice, four published power intensities measured four
different things (`PAPER_DIFF.md`, D17 correction):

| Value | Source | Boundary |
|---|---|---|
| 0.8 MWh/t | LBL Green Steel | externally sourced H₂, electrolyser excluded |
| 3.6 MWh/t | IRENA / Lhyfe | electrolyser included |
| 3.48 MWh/t | Vogl et al. 2018 | full chain |
| 0.135 MWh/t-DRI | IEEJ (shibata2023) | reduction stage only |

Every row of an intensity dataset therefore carries:

```
process_boundary ∈ { external_h2, incl_electrolyser, full_chain, reduction_stage_only }
```

**Values with different boundaries never share a column.** Aligning boundaries
comes before hunting for country-specific values.

### 2.5 What to import, what to keep out

| | |
|---|---|
| Import | tabular CSVs, source time series, values extracted from filings |
| Keep out | bulk binaries, literature PDFs, original workbooks, meeting material, slides |

Literature enters as **notes** in `References/<key>.md` (see
[CONTRIBUTING.md](CONTRIBUTING.md)). Source PDFs stay outside the repo.

---

## 3. Automatic promotion — status changes when series arrive

Some parameters promote from `banded` to `measured` the moment an observed
series is imported. No manual config edit is needed.

| Parameter | Awaited input | Current |
|---|---|---|
| `sigma_carbon_diffusion` | `data/raw/kau/` daily closes | **promoted** (`measured`) |
| `sigma_elec_kr_smp` | `data/raw/smp/` EPSIS series | waiting (`banded`) |
| `sigma_elec_jp` | `data/raw/jepx/` JEPX series | waiting (`banded`) |

Promotions are recorded in `measured_overrides` in `outputs/manifest.json`, and
the affected artifacts' `input_status` follows.

---

## 4. Outbound — how to cite results

### 4.1 `outputs/*.json` is the public API

Web, paper, and slides all read from here. **Numbers are never typed by hand.**
Theory documents use `{{...}}` placeholders filled by `make render-theory`.

### 4.2 The comparison rule — `metric_id` + `basis_id`

The same unit (bps) can measure different objects. Current bases:

| basis_id | What it measures |
|---|---|
| `enterprise_transition_window.reform_priced.full_counterfactual.ev_normalized` | enterprise transition-window risk |
| `enterprise_transition_window.reform_priced.fixed_exposure.ev_normalized` | price stress with the pathway held fixed |
| `project_from_base_year.reform_priced.fixed_commissioning.ev_normalized` | project risk from the base year |
| `project_levelized.expected_scenario.illustrative_terms` | NPV / DSCR / break-even pre-screen |
| `enterprise_private_vs_required.full_counterfactual.provisional_required` | cumulative alignment gap |

**Compare directly only when both `metric_id` and `basis_id` match.** Full rules
in [RESULT_CONTRACT.md](RESULT_CONTRACT.md).

### 4.3 Labels travel with the numbers

- Each artifact's `conditional_on` array says which assumptions a number stands
  on. Carry it along when citing.
- **Do not read `variance share` as `premium share`.** Jump and tail premia are
  large, separately priced components of the total risk premium, so a
  variance-based composition can understate their economic weight
  (`PAPER_DIFF.md`, D7). This warning holds until λ_jump / λ_diffusion are
  separated.
- bps values are not observed bond or loan spreads. They are the same
  conditional risk charge normalized by EV, for comparison only.

### 4.4 Programmatic access

```python
from model.api import compute, screen_transaction

compute(mode="fixed_exposure")        # τ* held; price sensitivity only
compute(mode="full_counterfactual")   # τ*, pathways, gaps recomputed
compute({"sigmas": {"carbon_diffusion": 0.55}})   # override
screen_transaction({"firm_id": "POSCO", "route": "h2_dri", "interventions": ["h2_cfd"]})
```

Neither call writes files. Unknown override keys raise instead of being
silently ignored.

---

## 5. The failures this contract prevents

| Failure | Guard |
|---|---|
| Data of unknown origin slips in | unregistered file fails `make ingest` |
| Paths break across machines | no absolute paths; labels only |
| Intensities with different boundaries compared side by side | mandatory `process_boundary` |
| Document numbers drift from model numbers | `{{substitution}}`; no hand-typed figures |
| bps from different bases in one table | `metric_id` + `basis_id` rule |
| Overwritten values erase history | filename-as-version; old files to `data/archive/` |
| Build-artifact bytes pollute lineage | `calibration.xlsx` excluded from git, hashes, and fingerprints |
| Registered candidate data is mistaken for an active parameter | candidate parquet + `candidate_input_contract.json`; model effect remains `none` until DECISIONS/config promotion |
