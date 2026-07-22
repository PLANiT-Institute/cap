import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import { artifact } from "../../lib/data";
import tokens from "../../tokens.json";

export default function SectorsPage() {
  const stranding = artifact("stranding");
  const shares = artifact("shares_by_firm");
  const manifest = artifact("manifest");
  const petchem = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), "content", "sample_petchem.json"), "utf-8")
  );
  const colors = tokens.drivers as Record<string, string>;

  return (
    <main className="page">
      <h1>Sectors</h1>
      <p style={{ maxWidth: 680, color: "#475569" }}>
        The anatomy is sector-agnostic machinery: discrete technology routes, four stochastic
        drivers, contract identification. Steel runs live; petrochemicals is scoped with sample
        structure; the roadmap follows wherever routes are discrete and hedgeable.
      </p>

      <h2>
        Steel <span className="badge badge--measured">LIVE</span>
      </h2>
      <p style={{ fontSize: 14, color: "#475569" }}>
        {shares.firms.length} firms in the anatomy (
        {shares.firms.map((f: any, i: number) => (
          <span key={f.firm_id}>
            {i > 0 && ", "}
            <Link href={`/anatomy/${f.firm_id}`}>{f.firm}</Link>
          </span>
        ))}
        ), 11 blast furnaces priced. Pipeline: config → LSM → anatomy → robustness → contracts, seed{" "}
        {manifest.seed}, config {manifest.config_sha256.slice(0, 12)}.
      </p>

      <h3>Stranding annex — no feasible route</h3>
      <p style={{ fontSize: 14, color: "#475569", maxWidth: 640 }}>
        Assets whose required abatement depth exceeds every priced route are excluded from the
        anatomy and reported separately — pricing them with a route they cannot take would fake
        precision.
      </p>
      <table>
        <thead>
          <tr>
            <th>Asset</th>
            <th>Firm</th>
            <th>Facility</th>
            <th>Capacity (Mt/yr)</th>
            <th>Intensity (tCO₂/t)</th>
          </tr>
        </thead>
        <tbody>
          {stranding.assets.map((a: any) => (
            <tr key={a.asset_id}>
              <td className="mono">{a.asset_id}</td>
              <td>{a.firm}</td>
              <td>
                {a.facility} {a.bf_number}
              </td>
              <td>{a.crude_steel_mt_yr}</td>
              <td>{a.emission_intensity_tco2_t}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ marginTop: 48 }}>
        Petrochemicals <span className="badge badge--banded">SAMPLE</span>
      </h2>
      <p style={{ fontSize: 14, color: "#475569", maxWidth: 640 }}>
        {petchem.note}
      </p>
      <p style={{ fontSize: 14, color: "#475569", maxWidth: 640 }}>{petchem.asset_base}</p>
      <table>
        <thead>
          <tr>
            <th>Firm</th>
            <th>Route (the bet)</th>
            <th>Illustrative anatomy</th>
          </tr>
        </thead>
        <tbody>
          {petchem.firms.map((f: any) => {
            const route = petchem.routes.find((r: any) => r.route === f.route);
            return (
              <tr key={f.firm}>
                <td>
                  {f.firm} <span className="mono" style={{ color: "#94a3b8" }}>({f.country})</span>
                </td>
                <td style={{ fontSize: 13 }}>{route.bet}</td>
                <td style={{ minWidth: 180 }}>
                  <div className="mini-bar" style={{ height: 14 }}>
                    {Object.entries(f.shares).map(([d, v]: [string, any]) => (
                      <div key={d} style={{ width: `${v * 100}%`, background: colors[d] }} />
                    ))}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mono" style={{ fontSize: 12, color: "#b45309" }}>
        All petrochemical numbers are illustrative placeholders for scoping — not model output.
      </p>

      <h2 style={{ marginTop: 48 }}>
        Roadmap <span className="badge" style={{ background: "#64748b" }}>NEXT</span>
      </h2>
      <p style={{ fontSize: 14, color: "#475569", maxWidth: 640 }}>
        Cement, aluminum, shipping fuel. The calculator core (<code>model/api.py</code>) accepts new
        sectors as config: an asset registry, route sensitivity vectors, and scenario sets — no new
        code.
      </p>
    </main>
  );
}
