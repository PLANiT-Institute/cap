# CAP dry-run pilot — Nippon Steel H₂ DRI

> **INTERNAL RESEARCH PREVIEW.** This is an automated dry run using banded asset data, illustrative terms and a surrogate required pathway. It is not an actual transaction pilot.

## Decision summary

- Verdict: **FID_HOLD**
- Selected support: H2 CfD (CHPS-style)
- Project NPV: −$28,319.4m
- Gross incremental project NPV before counterparty EL: $6,442.8m
- Counterparty-adjusted incremental NPV: $5,901.8m
- Required contracted premium: $277.3/t
- Annual CFADS shortfall: $2,218.3m

## Basis separation

- Enterprise transition-window charge: 11.06 bps (`enterprise_transition_window.reform_priced.full_counterfactual.ev_normalized`)
- Project-from-base-year charge: 12.39 bps (`project_from_base_year.reform_priced.fixed_commissioning.ev_normalized`)
- These bps values are not directly comparable; only within-basis before/after deltas are effects.

## Replay and 40-point gates

- Automated deterministic replay: PASS
- Traceable asset sources: PASS
- Executable quote: OPEN
- Empirical required path: OPEN
- Independent analyst blind rerun: OPEN
- Eligible for 40/100: **NO**

The machine-readable stress results and input evidence are in `outputs/pilot_cases.json`.
