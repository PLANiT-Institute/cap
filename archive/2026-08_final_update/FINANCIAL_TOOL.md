# CAP Transition Risk Underwriter

## Product thesis

CAP is not an ESG score and does not claim to observe a market spread. It translates a
technology route into transition-cost exposures, decomposes their uncertainty, and tests which
contracts change the resulting conditional risk charge.

The shared question for both sides of a financing transaction is:

> Which technology creates which risk, and which contract reallocates that risk most efficiently?

## Two user views, one calculation

### Investor underwriting

- model-implied conditional spread (bps)
- PV transition-cost uncertainty and uncertainty / enterprise value
- annual risk-charge equivalent (spread × EV)
- technology-linked risk anatomy and dominant driver
- cross-sector allocation map and relative-value comparison across priced-route firms
- fixed-exposure sensitivity to scalar `lambda × p_bind`
- contract-adjusted spread and residual risk

### Corporate treasury

- contract terms actually used by the model: target driver, coverage, tenor and basis risk
- contract coverage and maturity ladder
- risk-charge and transition-cost sigma before/after each intervention
- annual risk-charge equivalent of the modeled bps change
- residual charge ratio and residual risk anatomy
- separate classification of de-risking and pathway-alignment effects
- order-averaged (Shapley) attribution for the integrated package

### Deal and investment

- firm-scale route CAPEX, project NPV and level-cash-flow IRR
- debt amount, level debt service, DSCR and target-DSCR gate
- low-carbon product premium required to pass both NPV and DSCR
- break-even carbon, hydrogen and feedstock prices where route-relevant
- gross and counterparty-adjusted incremental contract value
- value-versus-risk Pareto set and the first bilateral contract to negotiate
- technology-route comparison with separate decarbonization-depth and feasibility gates

Investor and treasury views are generated from `outputs/transition_underwriting.json`; deal and
technology screening is generated from `outputs/deal_screening.json`. The web performs no
calculation.

## Sector libraries

- **Steel:** H₂-DRI, scrap-EAF and NG-DRI with carbon, hydrogen, electricity and CAPEX drivers.
- **Petrochemicals (provisional archetypes):** electrified steam cracking, cracker + CCUS and
  circular olefins with carbon, electricity, feedstock and CAPEX drivers. Firm attributes,
  technology economics and required pathways are assumptions until train-level data are supplied.

## Decision boundaries

1. **Not an observed credit spread.** The bps value remains conditional on assumed `lambda`, `k`,
   scenario probabilities, EV, the exposure model and calibration.
2. **Not a financing-savings forecast.** USD/year applies the bps change to EV using the same
   normalization as the model. It is a comparison measure.
3. **Illustrative transaction profile.** The current deal screen includes explicit zero fees and a
   visible 1% annual counterparty-PD stress. These are not executable quotes. The result is a term
   negotiation screen, not proof of cost effectiveness.
4. **Alignment is a separate dimension.** A contract can reduce risk while delaying the modeled
   transition; carbon reform can improve alignment while increasing the risk charge.
5. **No-feasible-route is not underwritten as a normal transition.** It remains in the stranding
   branch rather than being forced into the priced-route portfolio.

## Calculation boundary: price stress versus path counterfactual

The callable model exposes two deliberately separate calculations.

| Mode | Investor use | Research use | Prohibited interpretation |
|---|---|---|---|
| `fixed_exposure` | Reprice an unchanged technology and transition path under different risk-price assumptions | Hold exposure constant for comparative statics and the scalar-invariance demonstration | A change in policy input did not cause a modeled transition response |
| `full_counterfactual` | Test whether a scenario or intervention changes the private transition date and alignment gap as well as the charge | Re-run LSM, asset pathways and condition gap in memory under the new parameter set | The provisional T_required became an empirically identified mandate |

`compute()` defaults to `fixed_exposure` only for backward compatibility. Any investment memo
that discusses timing, alignment or emissions consequences must request `full_counterfactual` and
must report `path_recomputed: true`. Both modes remain scenario-conditional and write neither
config nor artifacts.

## Data gates for a transaction-ready version

| Gate | Required data | Product unlocked |
|---|---|---|
| Contract cost | quoted CfD/PPA premium, strike, volume, fees | true cost-versus-risk frontier |
| Counterparty risk | rating/PD, collateral, termination and replacement terms | CVA-adjusted residual risk |
| Debt structure | debt amount, tenor, amortization, covenants, DSCR | loan-specific rather than EV-normalized spread |
| Market validation | bond/loan spread, CDS and event observations | empirical calibration of `lambda` and backtest |
| Tail distribution | driver return histories and jump calibration | cash-flow-at-risk and expected shortfall |
| Private asset data | route volumes, commissioning plan, ramp-up and utilization | transaction-grade exposure vector |

## Build sequence

### Implemented: research MVP

- reproducible underwriting artifact (`model/s08_underwriting.py`)
- callable API fields for sigma, annual charge equivalent and dominant driver
- separate fixed-exposure and full-counterfactual API modes; the latter re-solves LSM τ*, pathways
  and condition gap without mutating artifacts
- investor and corporate treasury web modes (`/underwrite`)
- contract-adjusted residual risk, benefit ranking and package attribution
- scalar pricing sensitivity and portfolio comparison
- explicit epistemic labels and regression coverage

### Implemented: pre-deal screening MVP

1. Separate transaction assumption schema and visible quote status.
2. In-memory overrides for green premium, debt share, fees and counterparty assumptions.
3. Route and intervention NPV·IRR·DSCR·break-even calculations.
4. Simple lifetime counterparty expected-loss adjustment.
5. Climate-depth gate and OPEN feasibility status for alternative technologies.
6. Auditable modeled commercial cores and must-have diligence clauses for each contract/support instrument.
7. Interactive contract Pareto frontier, technology capital-allocation map, risk-transfer anatomy and separate investment-committee gates.

The displayed efficient frontier is non-dominated on higher counterparty-adjusted incremental
NPV and higher modeled risk-charge reduction. It is a transaction frontier, not a calibrated
mean–variance securities frontier, and does not convert heterogeneous gates into a composite score.

### Next: executable deal-room MVP

1. Replace screening assumptions with actual lender and contract term sheets.
2. Add construction drawdown, ramp-up, tax, working capital and terminal value.
3. Model contract cash settlement by year rather than a levelized window approximation.
4. Add counterparty migration, collateral calls, replacement cost and liquidity.
5. Export an assumption-audited underwriting memo for lender and issuer review.

### Later: portfolio and market layer

1. Versioned deal snapshots and monitoring alerts.
2. Portfolio aggregation with cross-firm correlations rather than naive summation.
3. Market-spread calibration and event-study validation.
4. API/MCP wrapper over the same pure calculation entry point.
5. Add cement, shipping and other hard-to-abate sector libraries; replace the petrochemical
   archetypes with train-level calibrated assets.

## Success criterion

The research MVP is successful when both parties can explain the same result. The transaction
version is successful only when a verified contract changes a real financing term sheet. A higher
dashboard usage count is not the north-star metric.
