# GLOSSARY — terms

Written to be readable without equations. Precise definitions live at the
corresponding anchors in `theory/`.

---

## The sentence this model tries to produce

> "The uncertainty this firm must carry through its transition is **carbon C% ·
> hydrogen H% · power E% · feedstock F% · capital K%**, and each component can
> be addressed separately through real, existing contracts."

Four steps build that sentence: **when does the firm switch (τ\*) → how late is
that (wedge) → what is the risk made of (anatomy) → how much is it (risk charge).**

---

## Core terms

### τ\* (tau-star) — privately optimal switch year

The year switching becomes attractive **on the firm's own numbers**, computed by
a real-options model (LSM) over 4,000 simulated price paths.

If switching today loses money, waiting is rational. A far-off τ\* is therefore
evidence of rationality, not of failure. Some assets have no τ\* within the
35-year horizon at all — privately, never switching is the better policy.

⚠️ Current τ\* solves each asset **in isolation.** Under oligopolistic
competition exercise moves earlier, so the current estimate is likely an
**upper bound** (`theory/08_referee_notes.md`, R8).

### T_required — required switch year

The year a climate scenario (GCAM et al.) requires that asset to switch. Comes
from the carbon budget, not the firm's profit.

⚠️ Currently read off a surrogate curve, hence `provisional`. Read it as: **the
existence of the gap is robust; its size is not settled.**

### wedge — the timing gap

`wedge = τ* − T_required`. The distance between "when it is rational to wait
until" and "when waiting stops being acceptable". This is the exposure CAP
measures — *rational today, exposed tomorrow*.

### condition gap / cumulative alignment gap

The wedge measured not in years but in **cumulative excess emissions (MtCO₂)**,
weighting capacity and intensity. More informative than "years late", and the
model's central state variable.

### anatomy — the composition of the risk

The **uncertainty** of transition cost split by driver, via Euler variance
decomposition. The output reads like "hydrogen 63.8%, carbon 31.6%, power 4.4%".

### mix vs level

The distinction this model cares most about.

| | mix (composition) | level |
|---|---|---|
| What | shares by driver | how many bps |
| Example | hydrogen 63.8% | 15.7 bps |
| Property | unchanged when λ·p_bind change | scales one-for-one with them |
| Read as | comparatively robust | conditional on assumptions |

Double λ and the level doubles while the mix holds to six decimal places: a
scalar multiplying every driver cancels in a ratio. That is **Proposition 1**,
and it is why this project leads with "what is the risk" rather than "how many
bps".

⚠️ P1 protects the mix **against λ only.** σ and ρ enter both mix and level and
enjoy no invariance. And P1 itself is a homogeneity identity, not a
methodological contribution — the novelty claim was withdrawn
(`PAPER_DIFF.md`, D2).

### risk charge (bps)

The premium an investor would require for transition uncertainty, normalized by
enterprise value in basis points.

⚠️ **Not an observed bond or loan spread.** It is a conditional risk charge
normalized by EV for comparison, not a forecast of realized financing costs.

### σ_B (sigma-B)

The present-valued standard deviation of transition cost B — exposure size
times volatility. The risk charge is **exactly proportional** to it.

### λ (lambda) — the price of risk

Compensation demanded per unit of uncertainty; a Sharpe-ratio-like loading.
Currently **assumed** at 0.40, awaiting empirical calibration.

⚠️ The assumption that one λ serves every driver (axiom A5) has **zero
supporting papers and seven against** (`PAPER_DIFF.md`, D1); Ready (2018) even
reports opposite signs across components. With per-driver λ_k, POSCO's carbon
share moves 31.6% → 39.8%.

### p_bind — probability the budget binds

The probability the carbon budget becomes binding. Not a free parameter — it is
**derived** as the probability mass of binding scenarios. Korea 0.55, Japan 0.50.

### ℓ_bind (l-bind) — the binding carbon price

The conditional mean carbon price given binding: Korea $53.18, Japan $46.50.
Carbon exposure is priced at this, not at spot ($14.93).

### LEVEL / WEDGE (capitalized) — the other cut

The same "why wait" question, cut by **level and volatility** instead of by
driver.

- **LEVEL**: the net loss that remains even with zero uncertainty — switching
  today simply loses money.
- **WEDGE**: the value of waiting created by uncertainty; removing volatility
  removes it.

The policy implication matters: cutting volatility alone leaves LEVEL standing,
and no switch happens. Instruments that lift the level and instruments that cut
volatility are **both** required.

⚠️ LEVEL/WEDGE rests on a perpetual-option closed form — an **approximation**.
The definition of record is the LSM τ\*; this cut is for intuition and checking.

### route — technology pathway

`h2_dri` (hydrogen direct reduction), `scrap_eaf` (scrap electric-arc),
`ng_dri` (gas direct reduction); petrochemicals: `e_cracker` / `ccus_cracker` /
`circular_olefins`.

The route fixes the sensitivity vector. Scrap and gas routes have hydrogen
sensitivity **zero by construction**, so hydrogen never appears in those firms'
anatomies.

### intervention

H₂ CfD, PPA, capex subsidy, carbon reform, concessional finance, … Modelled
**not as switches that zero out σ but as parameter transformations** — coverage,
tenor, and basis risk remain. The model never claims "fully contracted → 0 bps".

⚠️ Basis is a **band**, not a point. At the literature's worst basis, the H₂
CfD's risk reduction falls below half and the PPA's essentially vanishes
(`PAPER_DIFF.md`, D14).

---

## Evidence grades

Attached per result; when several apply, **the most restrictive is shown nearest
the result.**

| Grade | Meaning |
|---|---|
| `IDENTITY` | mathematical identity; assumption-free (e.g. shares sum to 1) |
| `MODEL_CONDITIONAL` | conditional on model structure (e.g. anatomy) |
| `SCENARIO_CONDITIONAL` | conditional on scenarios and assumptions (e.g. risk charge) |
| `EMPIRICAL` | grounded in observation |
| `PROVISIONAL` | surrogate-based (e.g. T_required) |
| `OPEN` | unresolved |

## Parameter status

| status | Meaning |
|---|---|
| `measured` | computed from observed series or filings |
| `banded` | sourced, but a range |
| `assumed` | set without evidence |
| `derived` | computed from other parameters |
| `provisional` | surrogate |

---

## Easily confused

**"Expensive" and "risky" are different.** Capex is 7.1% of POSCO's transition
cost but 0.26% of its risk. A large but certain outlay is debt, not risk. That
is axiom A1.

**variance share ≠ premium share.** A variance-based composition must not be
read as a risk-premium composition; jump and tail premia are priced separately
(`PAPER_DIFF.md`, D7).

**bps are comparable only on the same basis.** Enterprise transition-window and
project-at-commissioning share a unit, not an object.

**Anatomy is gross exposure.** Revenue-side channels — green-steel premia, CBAM
export pricing — are out of scope for now (R6).
