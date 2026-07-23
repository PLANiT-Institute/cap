import { artifact } from "../../lib/data";

function money(value: number) {
  const sign = value < 0 ? "−" : "";
  const abs = Math.abs(value);
  return abs >= 1000 ? `${sign}$${(abs / 1000).toFixed(1)}bn` : `${sign}$${abs.toFixed(0)}m`;
}

function gateLabel(value: boolean) {
  return value ? "PASS" : "OPEN";
}

export default function PilotsPage() {
  const pilots = artifact("pilot_cases");

  return (
    <main>
      <section className="pilot-head">
        <div>
          <p className="eyebrow">CAP evidence packs</p>
          <span className="evidence-tag evidence-tag--illustrative">{pilots.capability_stage.replaceAll("_", " ")}</span>
          <h1>Two repeatable cases. <em>Not two validated deals.</em></h1>
          <p>
            POSCO and Nippon Steel run through the same decision, basis, stress and provenance
            workflow. Exact automated replay passes; actual cases, quotes, required pathways and
            independent analyst review still block 40/100.
          </p>
        </div>
      </section>

      <div className="pilot-page">
        <section className="pilot-status">
          <div><span>Current capability</span><b>30/100 · pilot-ready dry run</b></div>
          <div><span>40-point status</span><b className="bad">NOT ACHIEVED</b></div>
          <div><span>Release stage</span><b>internal research preview</b></div>
        </section>

        <div className="pilot-grid">
          {pilots.cases.map((pilot: any) => {
            const decision = pilot.decision_summary;
            const enterprise = pilot.basis_separation.enterprise_transition_window;
            const project = pilot.basis_separation.project_from_base_year;
            const gates = pilot.forty_point_gates;
            return (
              <article className="pilot-card" key={pilot.case_id}>
                <div className="pilot-card__head">
                  <div>
                    <p className="eyebrow">{pilot.country} · {pilot.route.replaceAll("_", " ")}</p>
                    <h2>{pilot.firm}</h2>
                  </div>
                  <span className="deal-ic-status fail">FID hold</span>
                </div>
                <p className="pilot-question">{pilot.decision_question}</p>

                <div className="pilot-metrics">
                  <div><span>Absolute project NPV</span><b>{money(decision.project_npv_usd_m)}</b></div>
                  <div><span>CP-adjusted ΔNPV</span><b>{money(decision.counterparty_adjusted_incremental_npv_usd_m)}</b></div>
                  <div><span>Required premium</span><b>${decision.required_green_premium_usd_t.toFixed(0)}/t</b></div>
                  <div><span>CFADS shortfall</span><b>{money(decision.annual_cfads_shortfall_usd_m)}/yr</b></div>
                </div>

                <div className="pilot-basis">
                  <div>
                    <span>Enterprise transition window</span>
                    <b>{enterprise.before_bps.toFixed(1)} → {enterprise.after_bps.toFixed(1)} bps</b>
                    <small>{enterprise.basis_id}</small>
                  </div>
                  <div>
                    <span>Project from base year</span>
                    <b>{project.before_bps.toFixed(1)} → {project.after_bps.toFixed(1)} bps</b>
                    <small>{project.basis_id}</small>
                  </div>
                  <p>Within-basis deltas are effects. The two resulting bps levels are not directly comparable.</p>
                </div>

                <div className="pilot-stress">
                  <h3>Green-premium reversal</h3>
                  {pilot.stress_results.transaction.green_premium.map((point: any) => (
                    <div key={point.green_premium_usd_t}>
                      <span>${point.green_premium_usd_t.toFixed(0)}/t</span>
                      <b>{money(point.project_npv_usd_m)}</b>
                      <em className={point.decision === "INVESTABLE_SCREEN" ? "pass" : "fail"}>
                        {point.decision === "INVESTABLE_SCREEN" ? "advance" : "hold"}
                      </em>
                    </div>
                  ))}
                </div>

                <div className="pilot-replay">
                  <span>Automated replay SHA256</span>
                  <b className="mono">{pilot.reproducibility.run_a_sha256.slice(0, 16)}…</b>
                  <em>{pilot.reproducibility.exact_match ? "exact match" : "mismatch"}</em>
                  <small>Automated replay is not an independent analyst review.</small>
                </div>

                <div className="pilot-gates">
                  <h3>40-point evidence gates</h3>
                  {[
                    ["Traceable asset sources", gates.traceable_asset_sources],
                    ["Deterministic replay", gates.automated_deterministic_replay],
                    ["Executable quote", gates.executable_quote],
                    ["Empirical required path", gates.empirical_required_path],
                    ["Independent blind rerun", gates.independent_analyst_blind_rerun],
                    ["Actual transaction case", gates.actual_transaction_case],
                  ].map(([label, pass]: any) => (
                    <div key={label}><span>{label}</span><b className={pass ? "pass" : "open"}>{gateLabel(pass)}</b></div>
                  ))}
                </div>
              </article>
            );
          })}
        </div>

        <section className="uw-disclaimer">
          <b>Decision boundary</b>
          <span>These packs prove repeatable workflow execution, not transaction validity. Replace banded assets, assumed contract terms and the surrogate required path before a 40/100 claim.</span>
        </section>
      </div>
    </main>
  );
}
