"use client";
// The tool. Sector → firm → three panels:
// ① your premium (size conditional, mix proven) ② why it exists (required vs current)
// ③ how to hedge it (contract → bps retired). All data precomputed server-side.
import { useState } from "react";
import PremiumFan from "./PremiumFan";
import tokens from "../tokens.json";

const DRIVERS = ["carbon", "h2", "elec", "capex"] as const;
const DRIVER_LABEL: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  capex: "Capital",
};
const INSTRUMENT: Record<string, string> = {
  carbon: "Carbon CfD",
  h2: "Hydrogen CfD (CHPS-style)",
  elec: "Power purchase agreement",
  capex: "Capital subsidy / concessional finance",
};

export type SteelFirm = {
  firm_id: string;
  firm: string;
  country: string;
  cluster: string;
  shares: Record<string, number>;
  shares_reform: Record<string, number>;
  premium_bps: number;
  premium_reform_bps: number;
  grid: { lambda: number; p_bind: number; premium_bps: number }[];
  waterfall: { step: string; label: string; premium_bps: number; cut_bps: number }[];
  waterfall_reform: { step: string; label: string; premium_bps: number; cut_bps: number }[];
  assets: {
    asset_id: string;
    facility: string;
    tau_star: number | null;
    t_gcam: number;
    wedge: number | null;
    intensity: number;
  }[];
  residual_intensity: number;
};

export default function Dashboard({
  steel,
  petchem,
  pricing,
  sigma,
}: {
  steel: SteelFirm[];
  petchem: any;
  pricing: { lambda: number; p_bind: number };
  sigma: { base: number; reform: number };
}) {
  const [sector, setSector] = useState<"steel" | "petchem">("steel");
  const [firmId, setFirmId] = useState(steel[0].firm_id);
  const [reform, setReform] = useState(true);
  const colors = tokens.drivers as Record<string, string>;

  const f = steel.find((x) => x.firm_id === firmId)!;
  const shares = reform ? f.shares_reform : f.shares;
  const bps = reform ? f.premium_reform_bps : f.premium_bps;
  const gridScale = reform ? f.premium_reform_bps / f.premium_bps : 1;
  const dominant = DRIVERS.reduce((a, b) => (shares[a] >= shares[b] ? a : b));
  const yearMin = 2026;
  const yearMax = 2062;
  const yearX = (y: number) => ((Math.min(Math.max(y, yearMin), yearMax) - yearMin) / (yearMax - yearMin)) * 100;

  return (
    <div className="dash">
      {/* ── controls ── */}
      <div className="dash__controls">
        <div className="seg" role="tablist" aria-label="Sector">
          <button className={sector === "steel" ? "on" : ""} onClick={() => setSector("steel")}>
            Steel <em className="live">LIVE</em>
          </button>
          <button className={sector === "petchem" ? "on" : ""} onClick={() => setSector("petchem")}>
            Petrochemicals <em className="sample">SAMPLE</em>
          </button>
        </div>
        {sector === "steel" && (
          <>
            <div className="seg" role="tablist" aria-label="Firm">
              {steel.map((s) => (
                <button key={s.firm_id} className={s.firm_id === firmId ? "on" : ""} onClick={() => setFirmId(s.firm_id)}>
                  {s.firm}
                </button>
              ))}
            </div>
            <label className="reform-ctl">
              <input type="checkbox" checked={reform} onChange={(e) => setReform(e.target.checked)} />
              <span>
                price the carbon-policy reform{" "}
                <b className="mono">σ {reform ? sigma.reform.toFixed(2) : sigma.base.toFixed(2)}</b>
              </span>
            </label>
          </>
        )}
      </div>

      {sector === "petchem" ? (
        /* ── petrochemicals: structure loaded, pricing pending ── */
        <div className="panel-grid">
          <section className="panel" style={{ gridColumn: "1 / -1" }}>
            <h2>
              Petrochemicals — sample structure <span className="tag tag--sample">SAMPLE</span>
            </h2>
            <p className="panel__lede">{petchem.note}</p>
            <p className="panel__lede">{petchem.asset_base}</p>
            <div className="petchem-grid">
              {petchem.firms.map((p: any) => (
                <div key={p.firm} className="petchem-card">
                  <div className="petchem-card__head">
                    <b>{p.firm}</b>
                    <span className="mono">{p.country}</span>
                  </div>
                  <div className="mix-bar">
                    {DRIVERS.map((d) =>
                      p.shares[d] > 0 ? (
                        <div key={d} style={{ width: `${p.shares[d] * 100}%`, background: colors[d] }} />
                      ) : null
                    )}
                  </div>
                  <p>{petchem.routes.find((r: any) => r.route === p.route)?.bet}</p>
                </div>
              ))}
            </div>
            <p className="mono" style={{ color: "var(--molten-soft)", fontSize: 12 }}>
              Illustrative mix only — the pricing pipeline for this sector has not been run. Same
              machinery as steel: asset registry + route sensitivities + scenarios in, premium out.
            </p>
          </section>
        </div>
      ) : (
        <div className="panel-grid">
          {/* ── ① your premium ── */}
          <section className="panel panel--premium">
            <h2>① Your premium</h2>
            <div className="premium-head">
              <div>
                <div className="big-bps mono">
                  {bps.toFixed(1)}
                  <small> bps</small>
                </div>
                <div className="premium-sub">
                  base case (λ {pricing.lambda} · p_bind {pricing.p_bind}) ·{" "}
                  <span className="cond">level conditional</span>
                </div>
              </div>
              <div className="mix-readout">
                {DRIVERS.filter((d) => shares[d] > 0.005).map((d) => (
                  <div key={d} className="mix-readout__row">
                    <i style={{ background: colors[d] }} />
                    <span>{DRIVER_LABEL[d]}</span>
                    <b className="mono">{(shares[d] * 100).toFixed(0)}%</b>
                  </div>
                ))}
                <div className="proven">mix proven — invariant to λ · p_bind</div>
              </div>
            </div>
            <PremiumFan
              grid={f.grid.map((g) => ({ ...g, premium_bps: g.premium_bps * gridScale }))}
              shares={shares}
              firm={f.firm}
              baseCase={{ lambda: pricing.lambda, p_bind: pricing.p_bind, premium_bps: bps }}
            />
          </section>

          {/* ── ③ how to hedge ── */}
          <section className="panel">
            <h2>③ How to hedge it</h2>
            <p className="panel__lede">
              Each slice has a real instrument. Start with your dominant slice:{" "}
              <b>{DRIVER_LABEL[dominant]}</b> ({(shares[dominant] * 100).toFixed(0)}%) →{" "}
              <b>{INSTRUMENT[dominant]}</b>.
            </p>
            <ol className="hedge-list">
              {(reform ? f.waterfall_reform : f.waterfall)
                .filter((s) => s.step !== "uncommitted" && s.cut_bps > 0.05)
                .map((s) => {
                  const driver = { h2_cfd: "h2", carbon_cfd: "carbon", ppa: "elec", capex_subsidy: "capex" }[s.step] as string;
                  return (
                    <li key={s.step}>
                      <i style={{ background: colors[driver] }} />
                      <span className="hedge-list__name">{INSTRUMENT[driver]}</span>
                      <span className="hedge-list__cut mono">−{s.cut_bps.toFixed(1)} bps</span>
                    </li>
                  );
                })}
            </ol>
            <div className="hedge-total mono">
              uncommitted {bps.toFixed(1)} bps → fully contracted 0.0 bps
            </div>
            <p className="panel__foot">
              Carbon-policy risk is the sector's common factor — stock selection cannot shed it,
              only a carbon hedge can. Hydrogen risk is elective: dial it with names or an H₂ CfD.
            </p>
          </section>

          {/* ── ② why it exists ── */}
          <section className="panel" style={{ gridColumn: "1 / -1" }}>
            <h2>② Why it exists — required vs current</h2>
            <p className="panel__lede">
              The model compares two dates per furnace: <b className="mono" style={{ color: "#7fa3d0" }}>τ*</b>{" "}
              when switching is privately optimal (real-options, LSM) and{" "}
              <b className="mono" style={{ color: "var(--molten-soft)" }}>T_GCAM</b> when the
              net-zero pathway requires it. Waiting past the required date is rational — and is
              exactly what gets priced. Current intensity {f.assets[0]?.intensity.toFixed(1)} tCO₂/t
              must reach {f.residual_intensity.toFixed(1)} on the firm's route.
            </p>
            <div className="gap-rows">
              <div className="gap-rows__scale mono">
                {[2030, 2040, 2050, 2060].map((y) => (
                  <span key={y} style={{ left: `${yearX(y)}%` }}>
                    {y}
                  </span>
                ))}
              </div>
              {f.assets.map((a) => {
                const t1 = a.tau_star ?? yearMax;
                const left = Math.min(yearX(t1), yearX(a.t_gcam));
                const width = Math.abs(yearX(t1) - yearX(a.t_gcam));
                const late = (a.wedge ?? 0) > 0;
                return (
                  <div key={a.asset_id} className="gap-row">
                    <span className="gap-row__label mono">{a.facility}</span>
                    <div className="gap-row__track">
                      {[2030, 2040, 2050, 2060].map((y) => (
                        <i key={y} className="gap-row__grid" style={{ left: `${yearX(y)}%` }} />
                      ))}
                      <div
                        className={`gap-row__span ${late ? "late" : "early"}`}
                        style={{ left: `${left}%`, width: `${Math.max(width, 0.5)}%` }}
                      />
                      <b className="gap-row__gcam" style={{ left: `${yearX(a.t_gcam)}%` }} title={`required ${a.t_gcam}`} />
                      <b className="gap-row__tau" style={{ left: `${yearX(t1)}%` }} title={`optimal ${t1.toFixed(0)}`} />
                    </div>
                    <span className="gap-row__wedge mono">
                      {a.wedge == null ? "—" : `${a.wedge > 0 ? "+" : ""}${a.wedge.toFixed(0)}y`}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="gap-legend mono">
              <span>
                <b className="dot dot--tau" /> τ* private optimum
              </span>
              <span>
                <b className="dot dot--gcam" /> T_GCAM required
              </span>
              <span>
                <b className="dot dot--late" /> waiting past requirement = priced exposure
              </span>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
