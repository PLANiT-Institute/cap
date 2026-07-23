import { artifact } from "../../lib/data";

const SIGMA_LABEL: Record<string, string> = {
  carbon_diffusion: "Carbon (diffusion)",
  h2: "Hydrogen",
  elec_kr_regulated: "Electricity KR (regulated tariff)",
  elec_kr_smp: "Electricity KR (SMP)",
  elec_jp: "Electricity JP",
  feedstock: "Naphtha / circular feedstock",
  capex: "Capital cost",
};

export default function MethodPage() {
  const cal = artifact("calibration_resolved");
  const linearity = artifact("sigma_linearity");
  const manifest = artifact("manifest");
  const d = cal.derived;

  return (
    <main className="page page--dark">
      <h1>Method, in one page</h1>
      <p style={{ fontSize: 14, color: "#b6c2d4", maxWidth: 720 }}>
        CAP maps the gap between privately optimal and required decarbonization pathways into a
        conditional distribution of transition cash-flow losses, decomposes its sources, and
        evaluates which interventions change both transition timing and residual risk.
      </p>

      <h2>One engine, three decision views</h2>
      <p style={{ fontSize: 14, color: "#b6c2d4", maxWidth: 720 }}>
        <b>Pathways</b> asks whether an intervention changes transition timing and cumulative
        emissions. <b>Underwrite</b> asks which technology-linked uncertainty remains, how the
        conditional charge changes after a contract, and what that change equals when normalized
        to enterprise value. <b>Deal &amp; investment</b> keeps project value, debt service,
        climate depth and residual risk as separate gates. The bps output is not an observed credit
        spread or a credit rating.
      </p>

      <h2>The deal screen</h2>
      <p style={{ fontSize: 14, color: "#b6c2d4", maxWidth: 720 }}>
        The transaction view converts each route and intervention into a firm-scale screening NPV,
        level-cash-flow IRR, debt-service coverage ratio, required low-carbon product premium and
        route-relevant break-even carbon, hydrogen or feedstock price. It then keeps expected value, residual conditional risk and
        climate depth as separate gates. Non-configured routes are never presented as technically
        feasible without additional evidence. Each instrument also exposes its modeled price,
        volume coverage, tenor and the clauses that must be diligenced before signature; these are
        screening terms, not an executable offer.
      </p>

      <h2>Efficient frontier definition</h2>
      <p style={{ fontSize: 14, color: "#b6c2d4", maxWidth: 720 }}>
        The contract frontier is the non-dominated set on two separate axes: higher
        counterparty-adjusted incremental NPV and lower residual conditional transition-risk
        charge. A point remains on the frontier when no other modeled instrument improves one
        dimension without weakening the other. This is a transaction-screening Pareto frontier,
        not a market-calibrated mean–variance portfolio frontier.
      </p>

      <h2>The causal chain the dashboard follows</h2>
      <ol className="method-steps">
        <li>
          <b>Pathways first.</b> Asset-level annual emissions under four pathways: BAU, privately
          optimal (real-option timing τ*, least-squares Monte Carlo), required (T_required from a
          route-specific deployment pool — currently a <i>provisional surrogate</i>, not an
          empirically identified firm mandate), and with interventions.
        </li>
        <li>
          <b>Condition gap.</b> The core state variable: cumulative excess emissions Σ max(E_private
          − E_required, 0), plus per-asset timing gaps. Capacity and intensity weighted — not just
          years.
        </li>
        <li>
          <b>Interventions as parameter transformations.</b> H₂ CfD, PPA, circular-feedstock
          offtake, capex subsidy, carbon reform and concessional finance — each transforms prices, volatilities, capex or scenarios
          (coverage, tenor and basis risk retained; first-order approximation) and re-solves τ*.
          Residual risk never hits zero by construction.
        </li>
        <li>
          <b>Residual anatomy.</b> Euler decomposition of remaining transition-cost variance —{" "}
          <i>model-conditional mix</i>: invariant to the scalar pricing scale λ·p_bind (an identity,
          Proposition 1) but conditional on the exposure model, scenarios, switch timing and
          calibration. Not an empirically identified market-premium decomposition.
        </li>
        <li>
          <b>Conditional risk charge, last.</b> bps and $/t shown only with their conditioning: λ,
          k, EV estimate, WACC, scenario set, derived p_bind.
        </li>
      </ol>

      <h2>Sector boundary</h2>
      <p style={{ fontSize: 14, color: "#b6c2d4", maxWidth: 720 }}>
        Steel and petrochemicals use the same CAP equations but different asset registries,
        technology routes and exposure vectors. Petrochemicals adds a feedstock driver and three
        route cases: electrified cracking, cracker plus CCUS and circular olefins. Its current NCC
        firms and required transition dates are provisional archetypes, not company estimates or
        validated mandates.
      </p>

      <h2>Carbon structure (per country)</h2>
      <table>
        <thead>
          <tr><th>Factor</th><th>ℓ_bind $/t</th><th>p_bind (derived)</th><th>σ reform-priced</th><th>Jump var share</th></tr>
        </thead>
        <tbody className="mono">
          {["KR", "JP"].map((c) => (
            <tr key={c}>
              <td>carbon_{c.toLowerCase()}</td>
              <td>{d.l_bind[c].toFixed(1)}</td>
              <td>{d.p_bind[c].toFixed(2)}</td>
              <td>{d.sigma_carbon_reform[c].toFixed(2)}</td>
              <td>{(d.carbon_variance_decomposition[c].jump_share * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ fontSize: 13, color: "#94a3b8" }}>
        p_bind is <b>derived</b>: Σ prob(binding scenarios) — Option A; it is not a free parameter.
        CBAM rows are tagged as a common factor across both markets. Jumps share the diffusion's
        correlation and annual σ — an approximation; Merton-style jump-risk pricing is OPEN.
      </p>

      <h2>Parameters</h2>
      <table>
        <thead>
          <tr><th>Volatility σ</th><th>Value</th><th>Band</th><th>Status</th></tr>
        </thead>
        <tbody className="mono">
          {cal.sigmas.map((s: any) => (
            <tr key={s.driver}>
              <td style={{ fontFamily: "var(--font-body)" }}>{SIGMA_LABEL[s.driver] ?? s.driver}</td>
              <td>{s.value.toFixed(3)}</td>
              <td>[{s.band_lo.toFixed(2)}, {s.band_hi.toFixed(2)}]</td>
              <td><span className={`badge badge--${s.status}`}>{s.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      <table style={{ marginTop: 20 }}>
        <thead>
          <tr><th>Pricing</th><th>Value</th><th>Status</th></tr>
        </thead>
        <tbody className="mono">
          {Object.entries(cal.pricing).map(([p, o]: [string, any]) => (
            <tr key={p}>
              <td>{p}</td>
              <td>{o.value}</td>
              <td><span className={`badge badge--${o.status}`}>{o.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Epistemic status of results</h2>
      <table>
        <thead><tr><th>Level</th><th>What sits there</th></tr></thead>
        <tbody style={{ fontSize: 13 }}>
          <tr><td className="mono">IDENTITY</td><td>Share sum = 1; scalar λ·p_bind cancellation (all of Prop 1)</td></tr>
          <tr><td className="mono">MODEL_CONDITIONAL</td><td>Driver shares, τ*, cluster separation, intervention deltas</td></tr>
          <tr><td className="mono">SCENARIO_CONDITIONAL</td><td>Risk charge (bps, $/t), ℓ_bind, derived p_bind</td></tr>
          <tr><td className="mono">EMPIRICAL</td><td>σ carbon-diffusion (KAU daily), annual reference prices</td></tr>
          <tr><td className="mono">PROVISIONAL</td><td>T_required (GCAM surrogate; route pools rescaled)</td></tr>
          <tr><td className="mono">OPEN</td><td>SDF/β′λ identification, jump-risk pricing, p_bind in exercise policy</td></tr>
        </tbody>
      </table>
      <p style={{ fontSize: 13, marginTop: 12 }}>
        Option-value linearity in σ: R² = {linearity.r_squared.toFixed(2)}. Every artifact carries a{" "}
        <code>claims</code> block with per-result status and input dependencies; the manifest records
        git SHA{manifest.git_dirty ? " (working tree dirty)" : ""}, code/config/data hashes and seed.
      </p>

      <h2>Use it as a tool</h2>
      <pre className="code-block">{`from model.api import compute

compute({
  "pricing": {"lambda": 0.6},
  "carbon_scenarios_kr": [
    {"scenario": "SQ",     "level_usd": 12, "prob": 0.5, "binds": 0},
    {"scenario": "REFORM", "level_usd": 60, "prob": 0.5, "binds": 1},
  ],
  "interventions": ["h2_cfd", "carbon_reform"],
}, mode="full_counterfactual")
# → re-solved LSM τ* + pathway/gap + model-conditional shares + conditional risk charge

# Use mode="fixed_exposure" only when the transition path must stay fixed.`}</pre>
      <p className="mono" style={{ fontSize: 12, color: "#94a3b8" }}>
        MCP server will wrap the same call. Full research docs (Korean), axioms, referee notes,
        provenance: <a href="https://github.com/PLANiT-Institute/cap">github.com/PLANiT-Institute/cap</a>
      </p>
    </main>
  );
}
