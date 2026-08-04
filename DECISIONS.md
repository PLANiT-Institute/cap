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

Status: **OPEN 3 (X1, X3, X10 — data pending) · RESOLVED 8** (updated 2026-08-04)

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

### X2. Process boundary for power intensity `RESOLVED (2026-07-29)`

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

### X4. Japanese WACC `RESOLVED (2026-07-29)`

| | |
|---|---|
| Current | `config/firms.csv` JP 4.0% (band 3–4%) |
| Alternative | **5.75%** — reflects Nippon Steel's doubled interest-bearing debt (5.3tn yen), blended 2.5–3.5% survey midpoint |
| Evidence | external research, Day 3 (2026-07-22) |
| Impact | `PAPER_DIFF.md` already flags "JP WACC 4% distorts Nippon's H₂ share". Adoption moves all three Japanese firms' anatomies |
| Recommendation | **Adopt 5.75%** — more recent, more specific. Record the shifts in PAPER_DIFF on adoption |

---

## Tier 2 — framing and scope

### X5. ρ(H₂, power) `RESOLVED (2026-07-29)`

Current 0.70 (power is 55–70% of LCOH; banded) vs alternative 0.35 (in-house
electrolysis assumption). The factor-of-two difference feeds σ_B directly, and
the strength of the "super-additive σ-compression" differentiation claim hangs
on it.

**Recommendation**: declare the reference technology scenario as **externally
purchased hydrogen**, keep 0.70, and carry 0.35 as the in-house-electrolysis
sensitivity. Must stay consistent with X2 (`external_h2`).

### X6. Reference date for carbon prices in prose `RESOLVED (2026-07-29)`

KAU ranged over a factor of four in seven years — $25 (2019–20) → $6.6 (2025) →
$11 (H1 2026) (`PAPER_DIFF.md`, update 8). The multiple against the switching
break-even (~$50/tCO₂) moves between 1/7 and 1/3.3 depending on the date chosen.

**Recommendation**: make the reference date mandatory in any document. Config
uses the 2026-06-30 close ($14.93, measured); put the yearly averages table in
an appendix.

### X7. Japanese required-pathway benchmark `RESOLVED (2026-07-29)`

Korea uses GCAM-KAIST NZ2050_limCCS; Japan uses TZ-OSeMOSYS-STEEL — a separate
IAM, leaving the single-IAM frame. Needs sign-off.

**Recommendation**: approve, with the explicit sentence "comparability is
preserved by normalizing through state variables", and extend
`t_required_source` so the artifact records the choice.

### X8. Standing of λ_k (per-driver risk prices) `RESOLVED (2026-07-29)`

`outputs/lambda_k_sensitivity.json` is currently side-robustness. But A5
(uniform λ) has zero supporting papers and seven against, with Ready (2018)
reporting **opposite signs** across components (`PAPER_DIFF.md`, D1).

**Recommendation**: **promote λ_k to a headline result** — report shares under
uniform λ and λ_k side by side. POSCO's carbon share moves 31.6% → 39.8%
(+8.2pp), so the results prose changes.

---

### X9. Carbon-price process in the LSM `RESOLVED (2026-08-03)`

| | |
|---|---|
| Problem | μ_carbon (0.086) entered as a scenario anchor (ln(ℓ̄/spot)/15y, PAPER_DIFF 갱신 2026-07-22) and was propagated into the exercise value by the drift-consistency fix (갱신 5). Net effect: a **perpetual compound growth forecast the project never made**. Simulated KR carbon mean reaches ~$300 by 2061 vs scenario max $85; μ > WACC for every priced firm except Hyundai (δ = r − μ < 0, supercritical waiting); σ↑ **accelerates** τ* (12/12 seeds, all three τ definitions); σ-cutting contracts (H₂ CfD) delay τ* by collapsing p_exercised (0.74→0.58) — opposite sign to theory/01·10; s12 meanwhile assumes `dp_delta = +0.05` (the opposite regime). Full audit: `FORMULA_LEDGER_2026-08-03.md` §D (R-1, R-2, R-5) |
| Decision | Replace the perpetual GBM drift with a **scenario-anchored convergence path**: μ_t = ln(target/spot)/T_anchor for t ≤ anchor year, **0 after** — target and anchor horizon derived from the scenario table (the SSOT for price levels, per the calculator principle). μ_carbon is demoted from parameter to derived value. `dp_delta` is deleted; s12 derives δ from the same path so both lanes live in one world |
| Rejected (a) | Keep the physical perpetual drift and headline "expectation-driven waiting" — rejected: it treats a mistranslation of a *level* scenario into a *growth* forecast as an economic finding. CAP forecasts no returns; scenarios drive levels |
| Rejected (b) | Risk-adjusted drift (μ − risk premium) — rejected for now: imports an unidentified risk-price estimate (λ identification is OPEN); revisit in 2차 연구 if contract-price data arrives |
| Blocks | S1 implementation; the sign of every intervention timing effect; View 1 waterfall (W4); theory/01·10 WEDGE prose |
| Numeric shift | Pending implementation — τ*, wedge, intervention_impacts, level_wedge all recompute. Record in PAPER_DIFF on rerun (rule 8: no silent reconciliation) |

### X10. Carbon-price anchor source: replace assumed scenario levels with GCAM-KAIST / NGFS `OPEN`

| | |
|---|---|
| Current | X9 anchors the LSM carbon path to `config/scenarios.csv` levels (SQ/MSR/CBAM 12–85 USD, **assumed**) |
| Direction (author, 2026-08-04) | Anchor to a published model path instead — **GCAM-KAIST (Jee-Yeon Uhm group; the same model already used for T_required) first choice**, NGFS scenarios as the fallback/comparison. Put one price path in first, keep the scenario table as the probability mixture over paths |
| Blocks | Data: GCAM-KAIST carbon-price series not in `data/raw/` (provenance rule 5 — no entry without registered source). Need the price output file from the GCAM-KAIST run or an NGFS download |
| Recommendation | Register the raw file via `s01_ingest`, then re-derive mu_carbon; record shifts in PAPER_DIFF (rule 8). Until then X9's derived anchor stays `assumed` |

### X11. Feedstock (scrap/NG/ore) as stochastic driver — scope of the transition frame `RESOLVED (2026-08-04)`

| | |
|---|---|
| Current | Steel feedstock prices are deterministic constants inside `avoided`/`other_opex` (FORMULA_LEDGER R-9); `q_feedstock = 0` for steel rows |
| Decision | **Keep feedstock deterministic** — the project prices the *transition*, not commodity-cost risk (author, 2026-08-04). JFE/KOBE carbon-dominant anatomy is reported as **concentration** (single-driver exposure of non-transitioning firms), not as a degenerate composition. Plan S5 is thereby reduced: no feedstock activation |
| Rejected | Activating q_feedstock per original S5 — rejected: (a) out of the transition frame; (b) its acceptance criterion was mechanically unreachable under S4 anyway (tau* = None for JFE → zero post-switch window, review 2026-08-04) |
| Carried tension | Scrap is the input of the destination route (scrap_eaf), so its price risk is transition-conditional — JFE's cost base is ~88% scrap. Recorded as a known scope limit; revisit only if a referee or the LNG pack forces it (2차) |
| R-8 (annualization) adjudication | After S4 (t_sw = tau*), every firm's carbon leg spans the full horizon (pre- + post-switch), so sigma_B is a full-horizon PV quantity and annuity(WACC, horizon) **is** the matching annualization window. R-8's short-window premise dissolved — no code change; recorded here |

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
| 2026-07-29 | X2 | Adopt `process_boundary` field; the model prices the `external_h2` boundary. Values from other boundaries are reference-only | Hunting country-specific values before aligning boundaries — rejected: it produced the D17 confusion | none (framework) |
| 2026-07-29 | X4 | JP steel WACC 4.0% → **5.75%** (5 assets) | Keeping 4.0% (low-rate-era convention) — rejected: NS interest-bearing debt doubled; survey band 5.0–6.5% | PAPER_DIFF update 10 — Oita τ* leaves the horizon; NIPPON gap +32% |
| 2026-07-29 | X5 | Reference technology = externally purchased H₂; keep ρ(H₂,elec)=0.70; carry 0.35 as in-house-electrolysis sensitivity | Switching to 0.35 as the base — rejected: inconsistent with the `external_h2` boundary (X2) | none (base unchanged) |
| 2026-07-29 | X6 | Carbon-price prose must carry a reference date; config uses the 2026-06-30 KAU close ($14.93) | Undated citation — rejected: the break-even multiple moves 1/7↔1/3.3 with the date | none (rule) |
| 2026-07-29 | X7 | Approve TZ-OSeMOSYS-STEEL as the Japanese required-pathway benchmark, normalized through state variables. Implementation ticket: extend `t_required_source` to record per-country sources | Forcing a single global IAM — rejected: GCAM-KAIST is Korea-specific | none yet (implementation pending) |
| 2026-07-29 | X8 | Promote λ_k to a headline result: report shares under uniform λ and λ_k side by side | Keeping λ_k as side-robustness — rejected: A5 has zero supporting papers, seven against (D1) | presentation change; implementation with s12 |
| 2026-08-03 | X9 | LSM carbon price: scenario-anchored convergence path (drift → 0 after anchor year); μ demoted to derived; `dp_delta` deleted, s12 δ from the same path | (a) keep perpetual physical drift — mistranslates a level scenario into a return forecast; (b) risk-adjusted drift — imports unidentified λ | PAPER_DIFF update 12 — POSCO τ* 2044.6→2050.0, HYUNDAI private transition gone |
| 2026-08-04 | X11 | Steel feedstock stays deterministic (transition frame); JFE/KOBE anatomy = concentration, not composition; S5 reduced to nothing (R-8 dissolved by S4) | Activating q_feedstock (original S5) — out of frame and unreachable under S4 | none (no code change) |

