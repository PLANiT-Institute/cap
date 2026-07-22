import { artifact, DRIVER_LABELS } from "../../../lib/data";
import { EnvelopeBars, WaterfallBars } from "../../../components/charts";
import ConditionalNote from "../../../components/ConditionalNote";
import StatusBadge from "../../../components/StatusBadge";

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
    <>
      <h1>
        {f.firm} <small style={{ color: "#64748b" }}>({f.route} · {f.cluster})</small>
      </h1>

      <h2>Driver shares (risk vs cost)</h2>
      <table style={{ borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          <tr>
            {["driver", "risk share", "reform-priced", "cost share"].map((h) => (
              <th key={h} style={{ textAlign: "left", padding: "4px 12px", borderBottom: "1px solid #cbd5e1" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.keys(f.shares).map((d) => (
            <tr key={d}>
              <td style={{ padding: "4px 12px" }}>{DRIVER_LABELS[d]}</td>
              <td style={{ padding: "4px 12px" }}>{(f.shares[d] * 100).toFixed(1)}%</td>
              <td style={{ padding: "4px 12px" }}>{(f.shares_reform[d] * 100).toFixed(1)}%</td>
              <td style={{ padding: "4px 12px" }}>{(cvr.cost_shares[d] * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <ConditionalNote conditional={shares.conditional_on} />

      <h2>Share envelope (σ·ρ band draws)</h2>
      <EnvelopeBars
        rows={Object.entries(env.envelope).map(([driver, e]: [string, any]) => ({
          driver,
          ...e,
        }))}
      />

      <h2>계약 waterfall</h2>
      <WaterfallBars
        steps={firmWf.steps.map((s: any) => ({ label: s.label, premium_bps: s.premium_bps }))}
      />
      <ConditionalNote conditional={wf.conditional_on} />

      <h2>수준 (conditional)</h2>
      <p style={{ fontSize: 14 }}>
        π = {level.premium_bps.toFixed(1)} bps
        <StatusBadge status="assumed" /> · reform-priced{" "}
        {level.premium_reform_bps.toFixed(1)} bps · σ_B ${level.sigma_b_usd_bn.toFixed(2)}bn
      </p>
      <ConditionalNote conditional={levels.conditional_on} />
    </>
  );
}
