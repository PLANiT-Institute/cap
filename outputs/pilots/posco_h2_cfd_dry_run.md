# CAP dry-run pilot — POSCO H₂ DRI

> **INTERNAL RESEARCH PREVIEW.** This is an automated dry run using banded asset data, illustrative terms and a surrogate required pathway. It is not an actual transaction pilot.

## Decision summary

- Verdict: **FID_HOLD**
- Selected support: H2 CfD (CHPS-style)
- Project NPV: −$33,620.3m
- Gross incremental project NPV before counterparty EL: $8,291.9m
- Counterparty-adjusted incremental NPV: $7,595.6m
- Required contracted premium: $255.4/t
- Annual CFADS shortfall: $3,555.3m

## Basis separation

- Enterprise transition-window charge: 15.77 bps (`enterprise_transition_window.reform_priced.full_counterfactual.ev_normalized`)
- Project-from-base-year charge: 22.26 bps (`project_from_base_year.reform_priced.fixed_commissioning.ev_normalized`)
- These bps values are not directly comparable; only within-basis before/after deltas are effects.

## Replay and 40-point gates

- Automated deterministic replay: PASS
- Traceable asset sources: PASS
- Executable quote: OPEN
- Empirical required path: OPEN
- Independent analyst blind rerun: OPEN
- Eligible for 40/100: **NO**

The machine-readable stress results and input evidence are in `outputs/pilot_cases.json`.
