import fs from "node:fs";
import path from "node:path";
import { artifact } from "../lib/data";
import Dashboard, { SteelFirm } from "../components/Dashboard";

export default function Home() {
  const shares = artifact("shares_by_firm");
  const levels = artifact("premium_levels");
  const cal = artifact("calibration_resolved");
  const inv = artifact("lambda_invariance");
  const wf = artifact("waterfall");
  const wedge = artifact("wedge");
  const petchem = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), "content", "sample_petchem.json"), "utf-8")
  );
  const manifest = artifact("manifest");

  const steel: SteelFirm[] = shares.firms.map((f: any) => {
    const level = levels.firms.find((l: any) => l.firm_id === f.firm_id);
    const firmWf = wf.firms.find((w: any) => w.firm_id === f.firm_id);
    const assets = wedge.assets
      .filter((a: any) => a.firm_id === f.firm_id && a.category === "priced_route")
      .map((a: any) => ({
        asset_id: a.asset_id,
        facility: a.facility,
        tau_star: a.tau_star_year,
        t_gcam: a.t_gcam,
        wedge: a.wedge_years,
        intensity: a.emission_intensity_tco2_t,
      }));
    return {
      firm_id: f.firm_id,
      firm: f.firm,
      country: f.country,
      cluster: f.cluster,
      shares: f.shares,
      shares_reform: f.shares_reform,
      premium_bps: level.premium_bps,
      premium_reform_bps: level.premium_reform_bps,
      grid: inv.grid.filter((g: any) => g.firm_id === f.firm_id),
      waterfall: firmWf.steps,
      waterfall_reform: firmWf.steps_reform,
      assets,
      residual_intensity: f.residual_intensity_tco2_t,
    };
  });

  return (
    <main>
      <section className="tool-head">
        <div className="tool-head__inner">
          <h1>
            Price the transition. <em>Then hedge it.</em>
          </h1>
          <p>
            A pricing tool for heavy-industry transition risk: pick an asset base, see the premium
            and what it is made of, see why it exists, and see which contract retires each slice.
            Steel runs live; petrochemicals is the next sector.
          </p>
          <p className="mono tool-head__meta">
            pipeline {manifest.config_sha256.slice(0, 12)} · seed {manifest.seed} · T_GCAM{" "}
            {manifest.t_gcam_source} · σ_carbon measured from KAU
          </p>
        </div>
      </section>
      <Dashboard
        steel={steel}
        petchem={petchem}
        pricing={{ lambda: cal.pricing.lambda.value, p_bind: cal.pricing.p_bind.value }}
        sigma={{
          base: cal.sigmas.find((s: any) => s.driver === "carbon_diffusion").value,
          reform: cal.derived.sigma_carbon_reform,
        }}
      />
    </main>
  );
}
