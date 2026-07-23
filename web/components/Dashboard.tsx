"use client";
// Pathway-first decision system (개편 §6):
// ① 감축경로 ② 자산 타임라인 ③ why the gap ④ residual anatomy ⑤ conditional charge
import Link from "next/link";
import { useEffect, useState } from "react";
import PathwayPanel from "./PathwayPanel";
import PremiumFan from "./PremiumFan";
import { readScenarioQuery, replaceScenarioQuery, scenarioHref } from "../lib/scenarioUrl";
import tokens from "../tokens.json";

const DRIVERS = ["carbon", "h2", "elec", "feedstock", "capex"] as const;
const DRIVER_LABEL: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  feedstock: "Feedstock",
  capex: "Capital",
};

const SECTOR_LABEL: Record<string, string> = {
  steel: "Steel",
  petrochemicals: "Petrochemicals",
};

function semanticClass(value: number, threshold = 0.05) {
  if (value < -threshold) return "semantic-good";
  if (value > threshold) return "semantic-bad";
  return "semantic-neutral";
}

export default function Dashboard({ data }: { data: any }) {
  const firms = data.firms as any[];
  const [firmId, setFirmId] = useState(firms.find((f: any) => f.firm_id === "POSCO")?.firm_id ?? firms[0].firm_id);
  const selectedFirm = firms.find((x) => x.firm_id === firmId)!;
  const [sector, setSector] = useState(selectedFirm.sector);
  const [iv, setIv] = useState<string | null>("package");
  const [returnMode, setReturnMode] = useState("investor");
  const [returnRoute, setReturnRoute] = useState(selectedFirm.route);
  const [returnIntervention, setReturnIntervention] = useState<string | undefined>("package");
  const colors = tokens.drivers as Record<string, string>;

  const f = selectedFirm;
  const visibleFirms = firms.filter((candidate) => candidate.sector === sector);
  const visibleInterventions = data.interventions.filter((intervention: any) => (
    (intervention.applicable_sector === "all" || intervention.applicable_sector === f.sector)
    && (intervention.applicable_route === "all" || intervention.applicable_route === f.route)
  ));
  const impact = iv && f.impacts ? f.impacts[iv] : null;
  const provisional = data.t_required_source === "surrogate";
  const yearMin = data.years[0];
  const yearMax = data.years[data.years.length - 1];
  const yearX = (y: number) =>
    ((Math.min(Math.max(y, yearMin), yearMax) - yearMin) / (yearMax - yearMin)) * 100;

  const shares = impact ? impact.residual.shares : f.shares_reform;
  const charge = impact ? impact.residual.risk_charge_bps : f.levels?.premium_reform_bps;
  const interventionLabel = iv
    ? data.interventions.find((intervention: any) => intervention.id === iv)?.label ?? iv
    : "No intervention";
  const underwriteHref = scenarioHref("/", {
    firm: firmId,
    mode: returnMode,
    intervention: returnIntervention,
    route: returnRoute,
  });

  useEffect(() => {
    const query = readScenarioQuery();
    const nextFirm = firms.find((candidate) => candidate.firm_id === query.firm)
      ?? firms.find((candidate) => candidate.firm_id === "POSCO")
      ?? firms[0];
    const nextMode = query.mode === "treasury" || query.mode === "deal" ? query.mode : "investor";
    const nextIntervention = query.intervention !== "base"
      && data.interventions.some((candidate: any) => candidate.id === query.intervention)
      && nextFirm.impacts?.[query.intervention!]
      ? query.intervention!
      : nextFirm.impacts?.package
        ? "package"
        : null;
    setFirmId(nextFirm.firm_id);
    setSector(nextFirm.sector);
    setIv(nextIntervention);
    setReturnMode(nextMode);
    setReturnRoute(query.route ?? nextFirm.route);
    setReturnIntervention(query.intervention ?? nextIntervention ?? undefined);
    replaceScenarioQuery({
      firm: nextFirm.firm_id,
      mode: nextMode,
      intervention: query.intervention ?? nextIntervention ?? undefined,
      route: query.route ?? nextFirm.route,
    });
  // URL state is intentionally hydrated once; later changes flow through the handlers below.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function selectSector(nextSector: string) {
    const nextFirm = firms.find((candidate) => candidate.sector === nextSector);
    if (!nextFirm) return;
    setSector(nextSector);
    setFirmId(nextFirm.firm_id);
    setIv("package");
    setReturnRoute(nextFirm.route);
    setReturnIntervention("package");
    replaceScenarioQuery({ firm: nextFirm.firm_id, mode: returnMode, intervention: "package", route: nextFirm.route });
  }

  function selectFirm(nextFirmId: string) {
    const nextFirm = firms.find((candidate) => candidate.firm_id === nextFirmId);
    if (!nextFirm) return;
    setFirmId(nextFirmId);
    setIv("package");
    setReturnRoute(nextFirm.route);
    setReturnIntervention("package");
    replaceScenarioQuery({ firm: nextFirmId, mode: returnMode, intervention: "package", route: nextFirm.route });
  }

  function selectIntervention(nextIntervention: string | null) {
    setIv(nextIntervention);
    setReturnIntervention(nextIntervention ?? "base");
    replaceScenarioQuery({
      firm: firmId,
      mode: returnMode,
      intervention: nextIntervention ?? "base",
      route: returnRoute,
    });
  }

  return (
    <div className="dash">
      <div className="dash__controls">
        <div className="seg seg--sector" role="tablist" aria-label="Sector">
          {Object.keys(SECTOR_LABEL).filter((candidate) => firms.some((firm) => firm.sector === candidate)).map((candidate) => (
            <button key={candidate} className={candidate === sector ? "on" : ""} onClick={() => selectSector(candidate)}>{SECTOR_LABEL[candidate]}</button>
          ))}
        </div>
        <div className="seg" role="tablist" aria-label="Firm">
          {visibleFirms.map((s) => (
            <button key={s.firm_id} className={s.firm_id === firmId ? "on" : ""} onClick={() => selectFirm(s.firm_id)}>
              {s.firm}
            </button>
          ))}
        </div>
        <div className="seg" role="tablist" aria-label="Intervention">
          <button className={iv === null ? "on" : ""} onClick={() => selectIntervention(null)}>
            no intervention
          </button>
          {visibleInterventions.map((i: any) => (
            <button key={i.id} className={iv === i.id ? "on" : ""} onClick={() => selectIntervention(i.id)} title={i.label}>
              {i.short}
            </button>
          ))}
        </div>
      </div>

      <section className="scenario-strip" aria-label="Current scenario" aria-live="polite">
        <b>Current scenario</b>
        <dl>
          <div><dt>Company</dt><dd>{f.firm}</dd></div>
          <div><dt>Route</dt><dd className="mono">{returnRoute.replaceAll("_", " ")}</dd></div>
          <div><dt>Selected term</dt><dd>{interventionLabel}</dd></div>
          <div><dt>Regime</dt><dd>reform-priced</dd></div>
        </dl>
        <Link href={underwriteHref}>Back to underwriting →</Link>
      </section>

      {/* ── ① 감축경로 ── */}
      <section className="panel" style={{ marginBottom: 18 }}>
        <h2>① Decarbonization pathways — the cause</h2>
        <p className="panel__lede">
          What the firm would do on its own (private optimal, from real-option timing) vs what the
          sector pathway requires. The shaded area is the <b>condition gap</b> — cumulative excess
          emissions {f.gap.cumulative_alignment_gap_mtco2.toFixed(0)} MtCO₂
          {f.gap.first_misalignment_year ? `, misaligned from ${f.gap.first_misalignment_year}` : ""}.
        </p>
        <PathwayPanel
          firm={{ ...f.pathway, cum_gap_by_year: f.gap.cumulative_gap_by_year_mtco2 }}
          years={data.years}
          selectedIv={iv}
          provisional={provisional}
          singleAsset={f.assets.length === 1 ? f.assets[0] : undefined}
        />
        {provisional && (
          <p className="panel__foot">{data.required_disclaimer}</p>
        )}
      </section>

      {/* ── ② 자산 타임라인 ── */}
      <section className="panel" style={{ marginBottom: 18 }}>
        <h2>② Asset timeline — where the gap lives</h2>
        <div className="gap-rows">
          <div className="gap-rows__scale mono">
            {[2030, 2040, 2050, 2060].map((y) => (
              <span key={y} style={{ left: `${yearX(y)}%` }}>{y}</span>
            ))}
          </div>
          {f.assets.map((a: any) => {
            const tauIv = iv ? a.tau_interventions?.[iv] : null;
            const stranding = a.category === "no_feasible_route";
            return (
              <div key={a.asset_id} className="gap-row">
                <span className="gap-row__label">
                  {a.facility}
                  <em>
                    {a.capacity_mt}Mt · {a.intensity_tco2_t}t/t · {stranding ? "stranding/closure" : a.route}
                    {a.t_required_status === "PROVISIONAL" ? " · prov." : ""}
                  </em>
                </span>
                <div className="gap-row__track">
                  {[2030, 2040, 2050, 2060].map((y) => (
                    <i key={y} className="gap-row__grid" style={{ left: `${yearX(y)}%` }} />
                  ))}
                  {stranding ? (
                    <span className="gap-row__strand mono">no feasible priced route — stranding branch, not in deployment pool</span>
                  ) : (
                    <>
                      {a.tau_star_year != null && a.t_required != null && (
                        <div
                          className={`gap-row__span ${a.timing_gap_years > 0 ? "late" : "early"}`}
                          style={{
                            left: `${Math.min(yearX(a.tau_star_year), yearX(a.t_required))}%`,
                            width: `${Math.abs(yearX(a.tau_star_year) - yearX(a.t_required))}%`,
                          }}
                        />
                      )}
                      {a.t_required != null && (
                        <b className="gap-row__gcam" style={{ left: `${yearX(a.t_required)}%` }} title={`required ${a.t_required}`} />
                      )}
                      {a.tau_star_year != null ? (
                        <b className="gap-row__tau" style={{ left: `${yearX(a.tau_star_year)}%` }} title={`τ* ${a.tau_star_year.toFixed(0)}`} />
                      ) : (
                        <span className="gap-row__never mono">no private transition in horizon</span>
                      )}
                      {tauIv != null && (
                        <b className="gap-row__iv" style={{ left: `${yearX(tauIv)}%` }} title={`τ* with ${iv}: ${tauIv.toFixed(0)}`} />
                      )}
                    </>
                  )}
                </div>
                <span className="gap-row__wedge mono">
                  {a.timing_gap_years == null ? "—" : `${a.timing_gap_years > 0 ? "+" : ""}${a.timing_gap_years.toFixed(0)}y`}
                </span>
              </div>
            );
          })}
        </div>
        <div className="gap-legend">
          <span><b className="dot dot--tau" /> τ* private</span>
          <span><b className="dot dot--gcam" /> T_required{provisional ? " (provisional)" : ""}</span>
          <span><b className="dot dot--iv" /> τ* with intervention</span>
          <span><b className="dot dot--late" /> waiting past requirement</span>
        </div>
      </section>

      <div className="panel-grid">
        {/* ── ③ why the gap ── */}
        <section className="panel">
          <h2>③ Why the gap exists — what moves it</h2>
          <p className="panel__lede">
            Each intervention transforms parameters (contract price, coverage, tenor, capex,
            discount rate, carbon scenarios) and re-solves transition timing. Effect on τ* and
            cumulative gap, standalone:
          </p>
          <table className="iv-table">
            <thead>
              <tr><th>Intervention</th><th>Δτ*</th><th>Δcum. gap</th><th>Δcharge</th><th>Decision read</th></tr>
            </thead>
            <tbody>
              {visibleInterventions.map((i: any) => {
                const im = f.impacts[i.id];
                if (!im) return null;
                return (
                  <tr key={i.id} className={iv === i.id ? "sel" : ""} onClick={() => selectIntervention(i.id)}>
                    <td>{i.label}</td>
                    <td className={`mono ${semanticClass(im.delta.tau_star_years)}`}>{im.delta.tau_star_years > 0 ? "+" : ""}{im.delta.tau_star_years.toFixed(1)}y</td>
                    <td className={`mono ${semanticClass(im.delta.cumulative_gap_mtco2)}`}>{im.delta.cumulative_gap_mtco2 > 0 ? "+" : ""}{im.delta.cumulative_gap_mtco2.toFixed(0)} Mt</td>
                    <td className={`mono ${semanticClass(im.delta.risk_charge_bps)}`}>{im.delta.risk_charge_bps > 0 ? "+" : ""}{im.delta.risk_charge_bps.toFixed(1)} bps</td>
                    <td className="iv-table__read">
                      <span className={`meaning-badge ${semanticClass(im.delta.cumulative_gap_mtco2)}`}>
                        {im.delta.cumulative_gap_mtco2 < -0.05 ? "alignment ↑" : im.delta.cumulative_gap_mtco2 > 0.05 ? "alignment ↓" : "alignment —"}
                      </span>
                      <span className={`meaning-badge ${semanticClass(im.delta.risk_charge_bps)}`}>
                        {im.delta.risk_charge_bps < -0.05 ? "charge ↓" : im.delta.risk_charge_bps > 0.05 ? "charge ↑" : "charge —"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="panel__foot">
            A reduction in modeled charge does not guarantee an earlier transition. Carbon reform
            can close the gap while <b>raising</b> the priced carbon burden. Read Δτ*, Δgap and
            Δcharge as separate gates; sequential attribution is order-dependent and the artifact
            also reports order-averaged (Shapley) contributions.
          </p>
        </section>

        {/* ── ④ residual anatomy ── */}
        <section className="panel">
          <h2>④ Residual risk anatomy {iv ? `— with ${iv}` : ""}</h2>
          <p className="panel__lede">
            What uncertainty remains under the selected pathway and intervention. Coverage, tenor
            and basis risk keep this from ever reaching zero.
          </p>
          <div className="mix-readout">
            {DRIVERS.filter((d) => shares[d] > 0.004).map((d) => (
              <div key={d} className="mix-readout__row">
                <i style={{ background: colors[d] }} />
                <span>{DRIVER_LABEL[d]}</span>
                <b className="mono">{(shares[d] * 100).toFixed(0)}%</b>
              </div>
            ))}
          </div>
          <div className="mix-bar" style={{ height: 16, marginTop: 10 }}>
            {DRIVERS.map((d) =>
              shares[d] > 0.004 ? <div key={d} style={{ width: `${shares[d] * 100}%`, background: colors[d] }} /> : null
            )}
          </div>
          <p className="proven" style={{ marginTop: 10 }}>
            model-conditional mix · invariant to scalar λ and p_bind (P1) — conditional on the
            exposure model and calibration
          </p>
        </section>
      </div>

      {/* ── ⑤ conditional charge ── */}
      <section className="panel" style={{ marginTop: 18 }}>
        <h2>⑤ Conditional risk charge — the last step, not the first</h2>
        <div className="premium-head">
          <div>
            <div className="big-bps mono">
              {charge?.toFixed(1)}
              <small> bps</small>
            </div>
            <div className="premium-sub">
              <span className="cond">SCENARIO_CONDITIONAL</span> — conditional on assumed λ{" "}
              {data.pricing.lambda} · k {data.pricing.k} · EV estimate · WACC{" "}
              {(f.levels.wacc * 100).toFixed(1)}% · derived p_bind {f.levels.p_bind.toFixed(2)} (Σ
              prob of binding scenarios) · reform-priced carbon regime. Not an empirically
              identified market risk premium.
            </div>
          </div>
        </div>
        <PremiumFan
          grid={f.grid}
          shares={f.shares_reform}
          firm={f.firm}
          baseCase={{ lambda: data.pricing.lambda, p_bind: f.levels.p_bind, premium_bps: f.levels.premium_reform_bps }}
        />
        <p className="panel__foot">
          $/t view (EV-independent): {f.levels.premium_reform_usd_t.toFixed(1)} $/t · WACC-equalized:{" "}
          {f.levels.premium_reform_bps_wacc_eq.toFixed(1)} bps · manifest{" "}
          {data.manifest.config_sha256.slice(0, 12)}
          {data.manifest.git_dirty ? " · working tree DIRTY" : ""} · T_required{" "}
          {data.t_required_source}
        </p>
      </section>
    </div>
  );
}
