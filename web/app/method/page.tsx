import { artifact } from "../../lib/data";

// One page, English, everything an analyst needs — full research docs live in the repo.
const SIGMA_LABEL: Record<string, string> = {
  carbon_diffusion: "Carbon (diffusion)",
  h2: "Hydrogen",
  elec_kr_regulated: "Electricity KR (regulated tariff)",
  elec_kr_smp: "Electricity KR (SMP)",
  elec_jp: "Electricity JP",
  capex: "Capital cost",
};

export default function MethodPage() {
  const cal = artifact("calibration_resolved");
  const linearity = artifact("sigma_linearity");
  const manifest = artifact("manifest");

  return (
    <main className="page page--dark">
      <h1>Method, in one page</h1>

      <h2>What the tool does</h2>
      <ol className="method-steps">
        <li>
          <b>Why a premium exists.</b> Waiting to decarbonize is privately optimal (real options,
          least-squares Monte Carlo, τ*). A finite carbon budget forces the switch anyway (GCAM
          pathway, T_GCAM). Waiting past the required date is priced exposure.
        </li>
        <li>
          <b>What the premium is.</b> The transition cost is linear in four stochastic drivers —
          carbon policy, hydrogen, electricity, capital. The premium prices its <i>variance</i>, not
          its mean: π = k · λ · p_bind · σ_B.
        </li>
        <li>
          <b>What is proven vs assumed.</b> Driver shares s_k are a function of the firm's physical
          position and the covariances only — λ and p_bind cancel by homogeneity (Proposition 1,
          verified to machine precision on a {"6×8"} grid). Absolute bps are conditional and always
          labeled.
        </li>
        <li>
          <b>Carbon is diffusion + policy jumps.</b> σ²_carbon = σ²_diff + Σ p_j(ℓ_j−ℓ̄)²/ℓ̄².
          Scenarios (status-quo / MSR reform / CBAM linkage) lift σ from{" "}
          {cal.sigmas.find((s: any) => s.driver === "carbon_diffusion").value.toFixed(2)} to{" "}
          {cal.derived.sigma_carbon_reform.toFixed(2)} — the dashboard switch.
        </li>
        <li>
          <b>Contracts identify the decomposition.</b> Each driver is separately hedgeable — H₂
          CfD, carbon CfD, PPA, capital subsidy — which is what makes the split real rather than an
          accounting fiction.
        </li>
      </ol>

      <h2>Parameters</h2>
      <table>
        <thead>
          <tr>
            <th>Volatility σ</th>
            <th>Value</th>
            <th>Band</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody className="mono">
          {cal.sigmas.map((s: any) => (
            <tr key={s.driver}>
              <td style={{ fontFamily: "var(--font-body)" }}>{SIGMA_LABEL[s.driver] ?? s.driver}</td>
              <td>{s.value.toFixed(3)}</td>
              <td>
                [{s.band_lo.toFixed(2)}, {s.band_hi.toFixed(2)}]
              </td>
              <td>
                <span className={`badge badge--${s.status}`}>{s.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <table style={{ marginTop: 20 }}>
        <thead>
          <tr>
            <th>Pricing</th>
            <th>Value</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody className="mono">
          {["lambda", "p_bind", "k", "carbon_base_kr", "carbon_base_jp"].map((p) => (
            <tr key={p}>
              <td>{p}</td>
              <td>{cal.pricing[p].value}</td>
              <td>
                <span className={`badge badge--${cal.pricing[p].status}`}>{cal.pricing[p].status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <table style={{ marginTop: 20 }}>
        <thead>
          <tr>
            <th>Carbon scenario</th>
            <th>Level $/t</th>
            <th>Prob</th>
            <th>Budget binds</th>
          </tr>
        </thead>
        <tbody className="mono">
          {cal.scenarios.map((s: any) => (
            <tr key={s.scenario}>
              <td>{s.scenario}</td>
              <td>{s.level_usd}</td>
              <td>{s.prob}</td>
              <td>{s.binds ? "yes" : "no"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p style={{ fontSize: 13, marginTop: 16 }}>
        <span className="badge badge--measured">measured</span> from time series (KAU daily via
        ICAP) · <span className="badge badge--banded">banded</span> literature range ·{" "}
        <span className="badge badge--assumed">assumed</span> — flows into <i>conditional</i> levels
        only, never into the mix. Option-value linearity in σ: R² ={" "}
        {linearity.r_squared.toFixed(2)}.
      </p>

      <h2>Use it as a tool</h2>
      <p style={{ fontSize: 14 }}>
        The model core is a pure calculator — overrides in, anatomy out, no files touched. An MCP
        server will expose the same call so analysts can run scenarios from their own tools.
      </p>
      <pre className="code-block">{`from model.api import compute

compute({
  "pricing": {"lambda": 0.6},
  "carbon_scenarios": [
    {"scenario": "SQ",     "level_usd": 12, "prob": 0.5, "binds": 0},
    {"scenario": "REFORM", "level_usd": 60, "prob": 0.5, "binds": 1},
  ],
})  # → firm-level shares + premium range`}</pre>

      <p className="mono" style={{ fontSize: 12, color: "#94a3b8" }}>
        Full research documentation, axioms, referee notes, data provenance:{" "}
        <a href="https://github.com/PLANiT-Institute/cap">github.com/PLANiT-Institute/cap</a> ·
        pipeline {manifest.config_sha256.slice(0, 12)} · seed {manifest.seed}
      </p>
    </main>
  );
}
