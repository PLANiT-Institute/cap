# DECISIONS — the record of judgement calls

The **single collection point for every item that needs an author's judgement.**
Any change to a parameter value or to the standing of a claim passes through
here (lane P in [CONTRIBUTING.md](CONTRIBUTING.md)).

Rules:

1. Open items are registered `OPEN` with options, recommendation, evidence, and
   what they block.
2. On resolution the entry becomes `RESOLVED (YYYY-MM-DD)` and keeps the
   **rejected alternative and the reason for rejecting it.** Discarded options
   are intellectual assets; they are not deleted.
3. If a decision moves numbers: run `make all` and record every shift in
   [PAPER_DIFF.md](PAPER_DIFF.md) (rule 8 — never reconcile silently).
4. Only full-text-verified literature may serve as decision evidence.
   Abstract-based summaries stay in `refs.bib` as a map, not as support
   (the lesson of `PAPER_DIFF.md` D8 and D18).

Status: **OPEN 8 · RESOLVED 0** (registered 2026-07-29)

---

## Tier 1 — large impact; currently blocking parameter migration

### X1. Hydrogen intensity for H₂-DRI `OPEN`

| | |
|---|---|
| Current | `config/routes.csv` `q_h2_kg_t = 60` (Midrex Tech Sheet 2023, vendor figure) |
| Alternative | KEEI research report 22-03 (kang2022): **89.6 kg/t crude steel** — **+49%** |
| Evidence | `PAPER_DIFF.md` D21 |
| Blocks | POSCO/NIPPON H₂ shares, σ_B, risk charges. Hydrogen is 63.8% of POSCO's risk on current figures |
| Recommendation | **Boundary check first.** KEEI states "per t crude steel", Midrex "per t steel"; equivalence unconfirmed. If confirmed as same-boundary and Korea-specific, candidate for `measured` promotion. Expect the anatomy to move |
| Prerequisite | X2 (boundary definitions) |

### X2. Process boundary for power intensity `OPEN`

| | |
|---|---|
| Problem | Four published values measure four different things yet get compared |
| Values | 0.8 MWh/t (LBL, **external H₂, electrolyser excluded** — current config) / 3.6 (IRENA·Lhyfe, electrolyser included) / 3.48 (Vogl 2018, full chain) / 0.135 MWh/t-DRI (IEEJ shibata2023, **reduction stage only**) / 0.55 (KEEI kang2022) |
| Evidence | `PAPER_DIFF.md` D17 correction |
| Recommendation | Adopt the `process_boundary` field (`external_h2` / `incl_electrolyser` / `full_chain` / `reduction_stage_only`), state which boundary the model prices, then compare within that boundary only. The model assumes externally sourced hydrogen, so retaining the `external_h2` family is likely the consistent choice |
| Blocks | X1, X3, and every cross-country comparison sentence of the form "Korea is worse off than Europe" |

### X3. Residual intensity for H₂-DRI / dEmis `OPEN`

| | |
|---|---|
| Current | `residual_intensity_tco2_t = 0.10` (IEA ETP 2024) → avoided ≈ 2.0 tCO₂/t |
| Alternative | 0.5 (KEEI family) → dEmis 1.65 |
| Impact | Carbon exposure moves 18%; feeds the LEVEL gap and the carbon share directly |
| Recommendation | Re-verify sources; check whether the difference is a definition issue (indirect power emissions included or not) |

### X4. Japanese WACC `OPEN`

| | |
|---|---|
| Current | `config/firms.csv` JP 4.0% (band 3–4%) |
| Alternative | **5.75%** — reflects Nippon Steel's doubled interest-bearing debt (5.3tn yen), blended 2.5–3.5% survey midpoint |
| Evidence | external research, Day 3 (2026-07-22) |
| Impact | `PAPER_DIFF.md` already flags "JP WACC 4% distorts Nippon's H₂ share". Adoption moves all three Japanese firms' anatomies |
| Recommendation | **Adopt 5.75%** — more recent, more specific. Record the shifts in PAPER_DIFF on adoption |

---

## Tier 2 — framing and scope

### X5. ρ(H₂, power) `OPEN`

Current 0.70 (power is 55–70% of LCOH; banded) vs alternative 0.35 (in-house
electrolysis assumption). The factor-of-two difference feeds σ_B directly, and
the strength of the "super-additive σ-compression" differentiation claim hangs
on it.

**Recommendation**: declare the reference technology scenario as **externally
purchased hydrogen**, keep 0.70, and carry 0.35 as the in-house-electrolysis
sensitivity. Must stay consistent with X2 (`external_h2`).

### X6. Reference date for carbon prices in prose `OPEN`

KAU ranged over a factor of four in seven years — $25 (2019–20) → $6.6 (2025) →
$11 (H1 2026) (`PAPER_DIFF.md`, update 8). The multiple against the switching
break-even (~$50/tCO₂) moves between 1/7 and 1/3.3 depending on the date chosen.

**Recommendation**: make the reference date mandatory in any document. Config
uses the 2026-06-30 close ($14.93, measured); put the yearly averages table in
an appendix.

### X7. Japanese required-pathway benchmark `OPEN`

Korea uses GCAM-KAIST NZ2050_limCCS; Japan uses TZ-OSeMOSYS-STEEL — a separate
IAM, leaving the single-IAM frame. Needs sign-off.

**Recommendation**: approve, with the explicit sentence "comparability is
preserved by normalizing through state variables", and extend
`t_required_source` so the artifact records the choice.

### X8. Standing of λ_k (per-driver risk prices) `OPEN`

`outputs/lambda_k_sensitivity.json` is currently side-robustness. But A5
(uniform λ) has zero supporting papers and seven against, with Ready (2018)
reporting **opposite signs** across components (`PAPER_DIFF.md`, D1).

**Recommendation**: **promote λ_k to a headline result** — report shares under
uniform λ and λ_k side by side. POSCO's carbon share moves 31.6% → 39.8%
(+8.2pp), so the results prose changes.

---

## Tier 3 — deferrable

- **Paper spine**: whether anatomy is the main text and LEVEL/WEDGE the policy
  section.
- **Source for rotation non-invariance**: R7's point stands but its citation was
  corrected; Meucci (2009) is the candidate source, unverified
  (`PAPER_DIFF.md`, D18).
- **Quantifying R8 (oligopolistic exercise)**: direction is clear — competition
  pulls τ\* earlier, shrinking wedge and condition gap, so **current estimates
  are upper bounds**. Magnitude unmeasured.
- **Full texts for the 5 UNVERIFIABLE references**: dixit1994, flora2023,
  meyer1987, roncalliweisang2016 (artzneretal1999 since obtained).

---

## Resolution log

| Date | ID | Decision | Rejected alternative | Numeric shift |
|---|---|---|---|---|
| — | — | (none yet) | | |
