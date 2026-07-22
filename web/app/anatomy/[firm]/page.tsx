import { artifact } from "../../../lib/data";
import { EnvelopeBars, WaterfallBars } from "../../../components/charts";
import ConditionalNote from "../../../components/ConditionalNote";
import StatusBadge from "../../../components/StatusBadge";

const DRIVER_LABELS: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  capex: "Capital",
};

export function generateStaticParams() {
  return artifact("shares_by_firm").firms.map((f: any) => ({ firm: f.firm_id }));
}

export default async function FirmPage({ params }: { params: Promise<{ firm: string }> }) {
  const { firm } = await params;
  const shares = artifact("shares_by_firm");
  const f = shares.firms.find((x: any) => x.firm_id === firm);
  const env = artifact("share_envelopes").firms.find((x: any) => x.firm_id === firm);
  const wf = artifact("waterfall");
  const firmWf = wf.firms.find((x: any) => x.firm_id === firm);
  const levels = artifact("premium_levels");
  const level = levels.firms.find((x: any) => x.firm_id === firm);
  const cvr = artifact("cost_vs_risk").firms.find((x: any) => x.firm_id === firm);

  return (
    <main className="page">
      <h1>
        {f.firm}{" "}
        <small style={{ color: "#64748b", fontSize: "0.55em" }}>
          {f.route} · {f.cluster === "h2_route" ? "short the hydrogen economy" : "short the grid transition"}
        </small>
      </h1>

      <h2>Driver shares — risk vs cost</h2>
      <p style={{ fontSize: 14, color: "#475569", maxWidth: 620 }}>
        Risk shares decompose the variance of the transition cost (what the premium prices); cost
        shares decompose its mean. They differ — which is the point: averages misstate the anatomy.
      </p>
      <table>
        <thead>
          <tr>
            <th>Driver</th>
            <th>Risk share</th>
            <th>Reform priced</th>
            <th>Cost share</th>
          </tr>
        </thead>
        <tbody>
          {Object.keys(f.shares).map((d) => (
            <tr key={d}>
              <td>{DRIVER_LABELS[d]}</td>
              <td>{(f.shares[d] * 100).toFixed(1)}%</td>
              <td>{(f.shares_reform[d] * 100).toFixed(1)}%</td>
              <td>{(cvr.cost_shares[d] * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <ConditionalNote conditional={shares.conditional_on} />

      <h2>Share envelope (σ·ρ band draws)</h2>
      <EnvelopeBars
        rows={Object.entries(env.envelope).map(([driver, e]: [string, any]) => ({ driver, ...e }))}
      />

      <h2>Contract waterfall</h2>
      <p style={{ fontSize: 14, color: "#475569", maxWidth: 620 }}>
        Each driver is retired by a real instrument, in sequence: H₂ CfD, carbon CfD, PPA, capital
        subsidy. Separately contractible is what makes the decomposition real, not an accounting fiction.
      </p>
      <WaterfallBars
        steps={firmWf.steps.map((s: any) => ({
          label: { "미확약": "Uncommitted", "H₂ CfD (CHPS 낙찰 구조)": "H₂ CfD", "Carbon CfD (탄소 꼬리 절단)": "Carbon CfD", "PPA (전력 고정)": "PPA", "자본보조 (CAPEX 고정)": "Capex subsidy" }[s.label as string] ?? s.step,
          premium_bps: s.premium_bps,
        }))}
      />
      <ConditionalNote conditional={wf.conditional_on} />

      <h2>Level (conditional)</h2>
      <p style={{ fontSize: 14 }}>
        π = {level.premium_bps.toFixed(1)} bps <StatusBadge status="assumed" /> · reform priced{" "}
        {level.premium_reform_bps.toFixed(1)} bps · σ_B ${level.sigma_b_usd_bn.toFixed(2)}bn
      </p>
      <ConditionalNote conditional={levels.conditional_on} />
    </main>
  );
}
