# CONTRIBUTING — how work outside becomes canon inside

CAP's exploration happens in an external knowledge base (literature collection,
brainstorming notes, meeting material, draft analyses — maintained by PLANiT
Institute). This repository is the canon: theory, parameters, code, artifacts.
This document is the **promotion contract** between the two.

The one rule behind everything here: **exploration is free; promotion goes
through a gate.** Nothing enters `theory/` or `config/` without passing the lane
it belongs to.

```
knowledge base (explore)          this repo (canon)
──────────────────────            ─────────────────────────────
literature PDFs, notes    ──►     References/<key>.md + refs.bib      (lane L)
parameter research        ──►     DECISIONS.md → config/*.csv          (lane P)
datasets, time series     ──►     data/raw/<dataset>/*.csv             (lane D)
new claims, model ideas   ──►     theory/*.md anchors (+ code + tests) (lane T)
```

---

## Lane D — datasets

Fully specified in [DATA_INTERFACE.md](DATA_INTERFACE.md). Short form:

1. Upstream, keep one workbook per dataset (`CAP_DS_<name>.xlsx`, sheets
   `raw` / `clean` / `export`).
2. Export the `export` sheet as `<dataset>_YYYY-MM-DD.csv` into
   `data/raw/<dataset>/`.
3. Register the pattern in `data/provenance.yaml` with a source label
   (`planit_internal` / `public_market` / `licensed`).
4. `make ingest`. Done. Some σ parameters promote to `measured` automatically
   when their series arrive.

Never import: PDFs, original workbooks, meeting material, anything `licensed`.

## Lane P — parameters

A parameter value changes **only through a decision record.**

1. Register the candidate in [DECISIONS.md](DECISIONS.md): current value,
   proposed value, evidence, what it blocks, recommendation. Status `OPEN`.
2. The author resolves it. The entry becomes `RESOLVED (date)` and keeps the
   **rejected alternative and the reason** — discarded options are intellectual
   assets, not clutter.
3. Apply the change in `config/` (the editing SSOT is `config/sheets/*.csv` and
   the `config/*.csv` registries).
4. Run `make all`. Record every resulting numeric shift in
   [PAPER_DIFF.md](PAPER_DIFF.md) — **never reconcile silently.** A shift may be
   a finding.

A change that skips DECISIONS.md is not a promotion; it is drift with better
manners.

## Lane L — literature

The failure mode this lane exists to stop is real and recorded: two citations
were found to assert results **absent from the papers cited**
(`PAPER_DIFF.md`, D8 and D18). Both were plausible and useful — that is exactly
why they survived until full-text verification.

1. PDFs stay in the knowledge base. The repo takes a **note**, not the file:
   `References/<key>.md`.
2. Every note carries a verification stamp:
   - `CONFIRMED` — bibliography *and* the cited result checked against full text
   - `PARTIAL` — some claims verified, some not (say which)
   - `UNVERIFIABLE` — paywalled or inaccessible; bibliography checked only
   - `WRONG` — checked and found not to support the claim (keep the note; it is
     a result)
3. Register the entry in `theory/refs.bib`. If a survey found **no support** for
   an axiom, encode that too (`% unsupported: <anchor>`) — absence of support is
   a finding, and `make check-anchors` will print it on every build.
4. **Theory documents may cite `CONFIRMED` (or explicitly scoped `PARTIAL`)
   notes only.** Abstract-based summaries may live in `refs.bib` as a map of the
   field, but they support no claim.
5. When verification changes a note's verdict, update the theory text that cited
   it in the same commit, and record the correction in PAPER_DIFF.

## Lane T — theory and model claims

The heaviest lane. A claim from the notes becomes canon when all of the
following hold:

1. **It has an anchor.** A stable `{#anchor-id}` in the right `theory/*.md`,
   with an explicit status (`AXIOM` / `CLAIM` / `IDENTITY` / `INTERPRETATION` /
   `OPEN`), and honest `challenged-by` links if a referee note disputes it.
2. **Config points at it.** Any parameter the claim justifies carries it as
   `theory_anchor`. `make check-anchors` enforces both directions.
3. **If it computes, it is a stage.** Executable claims enter `model/` as a
   numbered stage with parameters from config (no literals), a new `basis_id`
   in the result contract if the quantity is not comparable to existing ones,
   and a structural regression test.
4. **Numbers in prose are substitutions.** `{{...}}` placeholders, filled by
   `make render-theory` — so the text updates when the model does.
5. **Its lineage is recorded.** If the claim supersedes an earlier framing, the
   earlier framing is archived in the knowledge base with a tombstone, and the
   succession is noted here (a dedicated lineage document is planned).

If a promoted claim later fails — a citation collapses, a rerun moves the
numbers, a referee point lands — it is **not deleted**. Its status changes, the
challenge is linked, and PAPER_DIFF records what happened. This repo's credibility
comes from visible self-correction, not from a clean surface.

---

## Cadence

A practical rhythm that has worked:

- **Explore daily, promote weekly.** Notes accumulate freely; once a week, sweep
  them for candidates and file DECISIONS/References entries.
- **One decision session** resolves open DECISIONS items in a batch — most need
  minutes, not meetings.
- **Every promotion ends with `make all` green.** If the gates fail, the
  promotion is not done.

## Language

Repository documents — interface docs, decision records, commit messages,
reference notes — are written in **English**: the repo is read by people outside
the project. Exploration notes in the knowledge base may be in any language;
what gets promoted gets translated at the gate.
