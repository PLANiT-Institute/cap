import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { artifact, provenanceMd } from "../../lib/data";
import StatusBadge from "../../components/StatusBadge";

// /data — annual reference prices + provenance table
export default function DataPage() {
  const ref = artifact("reference_prices");
  return (
    <main className="page">
      <h1>Reference prices (annual)</h1>
      <p style={{ maxWidth: 680, fontSize: 14, color: "#475569" }}>
        These are not model parameters — CAP is a calculator, and price levels and paths are driven
        by scenarios in config. The series below are measured references for comparison.
      </p>
      <h2 style={{ fontSize: 18 }}>
        KAU — Korean allowance (carbon) <StatusBadge status="measured" />
      </h2>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "right" }}>Year</th>
            <th style={{ textAlign: "right" }}>Mean KRW/t</th>
            <th style={{ textAlign: "right" }}>Mean USD/t</th>
            <th style={{ textAlign: "right" }}>Obs</th>
          </tr>
        </thead>
        <tbody>
          {ref.carbon_kr_annual.map((r: any) => (
            <tr key={r.year} className="mono" style={{ fontSize: 13 }}>
              <td style={{ textAlign: "right" }}>{r.year}</td>
              <td style={{ textAlign: "right" }}>{r.mean_krw.toLocaleString()}</td>
              <td style={{ textAlign: "right" }}>{r.mean_usd}</td>
              <td style={{ textAlign: "right" }}>{r.n_obs}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ fontSize: 12, color: "#64748b" }}>{ref.carbon_source}</p>
      <h2 style={{ fontSize: 18 }}>
        Electricity — base levels <StatusBadge status="banded" />
      </h2>
      <ul style={{ fontSize: 13.5 }}>
        {ref.elec_base.map((e: any) => (
          <li key={e.series}>
            {e.series}: {e.base_2026_usd_mwh} USD/MWh — {e.source}{" "}
            <em style={{ color: "#64748b" }}>
              (annual series will replace this once SMP/JEPX data lands)
            </em>
          </li>
        ))}
      </ul>
      <hr style={{ margin: "32px 0", border: "none", borderTop: "1px solid #e2e8f0" }} />
      <h2 style={{ fontSize: 18 }}>Provenance</h2>
      <p style={{ fontSize: 13, color: "#64748b" }}>
        Every raw file is registered with source, collection date, and SHA256 — the build fails on
        unregistered files. Table is machine-generated (Korean annex).
      </p>
      <article style={{ lineHeight: 1.7, fontSize: 13, overflowX: "auto" }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{provenanceMd()}</ReactMarkdown>
      </article>
    </main>
  );
}
