# CAP Joint Risk Premium

> Combine CAP transition-cost and alignment-gap premiums through an explicit shared-carbon covariance without double counting.

## Portfolio readout

- EV-weighted transition component: **16.71 bps**
- EV-weighted gap component: **5.75 bps**
- EV-weighted combined premium: **20.73 bps**
- Perfect-positive component-sum upper: **22.46 bps**

The combined value is a PROVISIONAL model-conditional issuer charge, not an observed spread. The portfolio number is an EV-weighted average; it is not a portfolio risk measure.

## Firms

| Firm | Transition | Gap | rho(T,G) | Independence | Combined | Positive upper | No-tradeoff option | Combined cut |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| JFE Steel | 23.99 | 6.70 | 0.999 | 24.91 | 30.68 | 30.69 | Long-term PPA | 0.08 |
| Japan NCC archetype | 17.88 | 2.01 | 0.318 | 17.99 | 18.61 | 19.88 | Long-term PPA | 0.07 |
| Kobe Steel | 15.84 | 0.15 | 1.000 | 15.84 | 15.99 | 15.99 | CAPEX subsidy | 0.00 |
| Korea NCC archetype | 16.42 | 1.60 | 0.339 | 16.49 | 17.02 | 18.01 | Long-term PPA | 0.06 |
| Nippon Steel | 11.33 | 7.14 | 0.422 | 13.39 | 15.73 | 18.46 | Long-term PPA | 0.31 |
| POSCO | 19.34 | 7.63 | 0.628 | 20.79 | 24.86 | 26.98 | CAPEX subsidy | 0.48 |

## Publication controls

- `p_bind` is not applied to the gap component a second time.
- Component sum is reported only as the perfect-positive-correlation upper bound.
- `T_required` remains surrogate-conditioned, so the combined result remains PROVISIONAL.
- Core and web promotion remain blocked pending structural simulation and explicit approval.
