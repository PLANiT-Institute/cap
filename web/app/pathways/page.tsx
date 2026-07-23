import { artifact } from "../../lib/data";
import Dashboard from "../../components/Dashboard";

const IV_SHORT: Record<string, string> = {
  h2_cfd: "H₂ CfD",
  ppa: "PPA",
  feedstock_hedge: "feed collar",
  circular_feedstock: "feedstock",
  capex_subsidy: "capex",
  carbon_reform: "reform",
  concessional: "conc.fin",
  package: "package",
};

export default function PathwaysPage() {
  const pathways = artifact("emissions_pathways_by_firm");
  const gaps = artifact("condition_gap");
  const impacts = artifact("intervention_impacts");
  const shares = artifact("shares_by_firm");
  const levels = artifact("premium_levels");
  const inv = artifact("lambda_invariance");
  const tau = artifact("tau_star");
  const cal = artifact("calibration_resolved");
  const manifest = artifact("manifest");

  const ivMeta = cal.interventions.map((row: any) => ({
    id: row.intervention_id,
    label: row.label,
    short: IV_SHORT[row.intervention_id] ?? row.intervention_id,
    applicable_sector: row.applicable_sector,
    applicable_route: row.applicable_route,
  }));

  const firms = shares.firms.map((share: any) => {
    const firmId = share.firm_id;
    const pathway = pathways.firms.find((row: any) => row.firm_id === firmId);
    const gap = gaps.firms.find((row: any) => row.firm_id === firmId);
    const impact = impacts.firms.find((row: any) => row.firm_id === firmId);
    const level = levels.firms.find((row: any) => row.firm_id === firmId);
    const assets = gap.assets.map((asset: any) => ({
      ...asset,
      tau_interventions: Object.fromEntries(
        Object.entries(tau.interventions).map(([interventionId, values]: [string, any]) => [
          interventionId,
          values[asset.asset_id],
        ]),
      ),
    }));
    return {
      firm_id: firmId,
      firm: share.firm,
      sector: share.sector,
      route: share.route,
      shares: share.shares,
      shares_reform: share.shares_reform,
      pathway,
      gap,
      assets,
      impacts: impact?.interventions ?? {},
      levels: level,
      grid: inv.grid.filter((row: any) => row.firm_id === firmId),
    };
  });

  return (
    <main>
      <section className="tool-head tool-head--pathways">
        <div className="tool-head__inner">
          <p className="eyebrow">Underwriting evidence · pathway drill-down</p>
          <h1>Why this charge exists.</h1>
          <p>
            Trace the selected company’s conditional risk charge back to the gap between its
            privately optimal and required decarbonization pathways, then test which intervention
            changes timing, alignment and residual risk.
          </p>
          <p className="tool-head__meta">
            Pipeline <span className="mono">{manifest.config_sha256.slice(0, 12)}</span>
            {manifest.git_dirty ? " · DIRTY" : ""} · T_required {manifest.t_required_source} (provisional)
          </p>
        </div>
      </section>
      <Dashboard
        data={{
          firms,
          years: pathways.years,
          t_required_source: pathways.t_required_source,
          required_disclaimer: pathways.required_disclaimer,
          interventions: ivMeta,
          pricing: {
            lambda: cal.pricing.lambda.value,
            k: cal.pricing.k.value,
          },
          manifest,
        }}
      />
    </main>
  );
}
