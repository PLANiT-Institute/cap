import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import { artifact } from "../lib/data";
import PathwayChart from "../components/PathwayChart";
import PremiumFan from "../components/PremiumFan";
import ReformSwitch from "../components/ReformSwitch";
import tokens from "../tokens.json";

export default function Home() {
  const shares = artifact("shares_by_firm");
  const levels = artifact("premium_levels");
  const cal = artifact("calibration_resolved");
  const pathway = artifact("emission_pathway");
  const sep = artifact("cluster_separation");
  const dpi = artifact("delta_pi_ranking");
  const manifest = artifact("manifest");
  const petchem = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), "content", "sample_petchem.json"), "utf-8")
  );

  const inv = artifact("lambda_invariance");
  const sigmaBase = cal.sigmas.find((s: any) => s.driver === "carbon_diffusion").value;
  const sigmaReform = cal.derived.sigma_carbon_reform;
  const poscoGrid = inv.grid.filter((g: any) => g.firm_id === "POSCO");
  const firms = shares.firms.map((f: any) => ({
    ...f,
    ...levels.firms.find((l: any) => l.firm_id === f.firm_id),
  }));
  const posco = firms.find((f: any) => f.firm_id === "POSCO");
  const maxDelta = dpi.ranking[0];
  const colors = tokens.drivers as Record<string, string>;

  return (
    <main>
      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero__inner">
          <div>
            <p className="eyebrow">CAP — Carbon-transition Asset Pricing</p>
            <h1>
              Transition risk,
              <br />
              <em>taken apart.</em>
            </h1>
            <p className="hero__sub">
              How big is the transition-risk premium? Honest answer: it depends on how dearly the
              market prices the risk — nobody agrees. What it is <em>made of</em> does not depend on
              that at all. CAP proves the mix, prices the range, and names the contract that hedges
              each slice. Steel first: 11 blast furnaces, Korea and Japan.
            </p>
            <div className="hero__stats">
              <div className="stat-chip">
                <b>11</b>
                <span>blast furnaces priced</span>
              </div>
              <div className="stat-chip">
                <b>4</b>
                <span>hedgeable drivers</span>
              </div>
              <div className="stat-chip stat-chip--accent">
                <b>
                  {sigmaBase.toFixed(2)} → {sigmaReform.toFixed(2)}
                </b>
                <span>σ carbon, reform priced</span>
              </div>
            </div>
          </div>
          <PremiumFan
            grid={poscoGrid}
            shares={posco.shares}
            firm="POSCO"
            baseCase={{
              lambda: cal.pricing.lambda.value,
              p_bind: cal.pricing.p_bind.value,
              premium_bps: posco.premium_bps,
            }}
          />
        </div>
      </section>

      {/* ── The flip ── */}
      <section className="band band--paper" id="anatomy">
        <div className="band__inner">
          <p className="eyebrow">The result</p>
          <h2 className="section-title">One switch reprices the sector.</h2>
          <p className="section-lede">
            Korea's carbon market trades thin at ~${cal.pricing.carbon_base_kr.value}. The real risk
            is the discrete policy repricing ahead — market stability reserve, banking reform, CBAM
            linkage. Flip the switch: when reform is priced, carbon becomes the dominant slice of
            every firm's premium. That slice is exposure to the government's own policy path.
          </p>
          <ReformSwitch firms={firms} sigmaBase={sigmaBase} sigmaReform={sigmaReform} />
          <p style={{ fontSize: 13, color: "#64748b", marginTop: 28 }}>
            Two clusters, no overlap (gap {(sep.gap * 100).toFixed(0)}%p across all calibration
            draws): hydrogen-route firms are short the hydrogen economy; scrap/gas-route firms are
            short the grid transition. Hyundai's furnaces sit in a separate{" "}
            <Link href="/sectors">stranding category</Link> — no priced route reaches their required
            depth. Firm detail:{" "}
            {firms.map((f: any, i: number) => (
              <span key={f.firm_id}>
                {i > 0 && " · "}
                <Link href={`/anatomy/${f.firm_id}`}>{f.firm}</Link>
              </span>
            ))}
          </p>
        </div>
      </section>

      {/* ── Wedge teaser ── */}
      <section className="band band--ink">
        <div className="band__inner" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48, alignItems: "center" }}>
          <div>
            <p className="eyebrow">Why a premium exists</p>
            <h2 className="section-title">Rational today. Exposed tomorrow.</h2>
            <p className="section-lede">
              Real-options logic says waiting is privately optimal — and our least-squares Monte
              Carlo confirms it, asset by asset. But a finite carbon budget means the option gets
              exercised for you: the required pathway below bends down whether or not the firm
              moves. The gap between each furnace's private optimum τ* and its required date is the
              exposure this model prices.
            </p>
            <Link href="/wedge" style={{ color: "#f59e0b", fontFamily: "var(--font-mono)", fontSize: 14 }}>
              → See the wedge, furnace by furnace
            </Link>
          </div>
          <PathwayChart pathway={pathway} />
        </div>
      </section>

      {/* ── Audiences ── */}
      <section className="band band--paper">
        <div className="band__inner">
          <p className="eyebrow">What to do with it</p>
          <h2 className="section-title">Three readers, three moves.</h2>
          <p className="section-lede">
            The level of the premium is conditional on the market price of risk. The composition is
            not — and the composition is what tells each reader their fastest move.
          </p>
          <div className="card-grid">
            <div className="card">
              <p className="role">Government</p>
              <h3>Your policy path is the premium.</h3>
              <p>
                With reform priced, carbon policy is {(posco.shares_reform.carbon * 100).toFixed(0)}%
                of POSCO's premium — domestic policy uncertainty, not global markets. Credible reform
                sequencing and carbon contracts-for-difference convert that uncertainty into
                investable certainty.
              </p>
              <p className="takeaway">
                Fastest lever: announce the reform path, then sell certainty via carbon CfDs.
              </p>
            </div>
            <div className="card">
              <p className="role">Corporates</p>
              <h3>Contracts buy the premium back.</h3>
              <p>
                Every driver has a real instrument: H₂ CfD, carbon CfD, PPA, capital subsidy. The
                waterfall shows {maxDelta.firm} can retire {maxDelta.delta_pi_bps.toFixed(0)} bps of
                conditional premium by contracting — commitment, not announcement, is what counts.
              </p>
              <p className="takeaway">
                Fastest lever: sign the contract that kills your dominant slice first.
              </p>
            </div>
            <div className="card">
              <p className="role">Investors</p>
              <h3>Know what you can diversify.</h3>
              <p>
                Carbon-policy risk is the sector's common factor — every firm carries it, so stock
                selection inside the sector cannot shed it; only direct carbon hedges can. Hydrogen
                risk is elective: dial it with names.
              </p>
              <p className="takeaway">
                Fastest lever: hedge carbon directly; express hydrogen views through selection.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Sectors ── */}
      <section className="band band--ink" id="sectors">
        <div className="band__inner">
          <p className="eyebrow">Coverage</p>
          <h2 className="section-title">Steel is the pilot, not the program.</h2>
          <p className="section-lede">
            The anatomy is sector-agnostic: discrete technology routes, four drivers, contract
            identification. Petrochemicals is scoped next — same machinery, new routes.
          </p>
          <div className="card-grid">
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3>Steel</h3>
                <span className="sector-status sector-status--live">LIVE</span>
              </div>
              <p>
                POSCO, Nippon, Hyundai, JFE, Kobe — 11 blast furnaces. Full pipeline: LSM timing,
                anatomy, robustness, contract waterfall.
              </p>
              <p className="mono" style={{ fontSize: 12, color: "#94a3b8" }}>
                config {manifest.config_sha256.slice(0, 12)} · seed {manifest.seed}
              </p>
            </div>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3>Petrochemicals</h3>
                <span className="sector-status sector-status--sample">SAMPLE</span>
              </div>
              <p>{petchem.asset_base}</p>
              {petchem.firms.map((f: any) => (
                <div key={f.firm}>
                  <div className="mono" style={{ fontSize: 11.5, color: "#b6c2d4", marginTop: 8 }}>
                    {f.firm} ({f.country})
                  </div>
                  <div className="mini-bar">
                    {Object.entries(f.shares).map(([d, v]: [string, any]) => (
                      <div key={d} style={{ width: `${v * 100}%`, background: colors[d] }} />
                    ))}
                  </div>
                </div>
              ))}
              <p className="mono" style={{ fontSize: 11, color: "#f59e0b", marginTop: 10 }}>
                Illustrative sample — pipeline not yet run.
              </p>
            </div>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3>Next</h3>
                <span className="sector-status sector-status--roadmap">ROADMAP</span>
              </div>
              <p>
                Cement, aluminum, shipping fuel — anywhere transition routes are discrete and
                contracts exist to hedge them. The calculator core already accepts new sectors as
                config.
              </p>
              <p className="takeaway">Same four drivers. Same proof. New assets.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
