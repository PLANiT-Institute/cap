"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import DealScreen from "./DealScreen";
import { EfficientFrontier, InvestmentCommitteePanel } from "./DealVisuals";
import { ContractCoverageLadder, InvestorPortfolioMap } from "./SectorVisuals";
import { readScenarioQuery, replaceScenarioQuery, scenarioHref } from "../lib/scenarioUrl";
import tokens from "../tokens.json";

const DRIVERS = ["carbon", "h2", "elec", "feedstock", "capex"] as const;
const DRIVER_LABEL: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  feedstock: "Feedstock",
  capex: "Capital cost",
  financing: "Financing",
};
const SECTOR_LABEL: Record<string, string> = {
  steel: "Steel",
  petrochemicals: "Petrochemicals",
};
const CLASS_LABEL: Record<string, string> = {
  dual_benefit: "risk ↓ · alignment ↑",
  de_risking_with_alignment_tradeoff: "risk ↓ · alignment trade-off",
  de_risking_only: "risk ↓",
  alignment_with_risk_tradeoff: "alignment ↑ · risk trade-off",
  risk_increasing: "risk ↑",
  alignment_only: "alignment ↑",
  no_material_model_effect: "no modeled effect",
};
const MATERIAL_RISK_CUT_BPS = 5;

function signed(value: number, digits = 1) {
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function compactMoney(value: number) {
  const sign = value < 0 ? "−" : "";
  const abs = Math.abs(value);
  return abs >= 1000 ? `${sign}$${(abs / 1000).toFixed(1)}bn` : `${sign}$${abs.toFixed(0)}m`;
}

function EvidenceBadge({ children, tone = "scenario" }: { children: React.ReactNode; tone?: string }) {
  return <span className={`evidence-tag evidence-tag--${tone}`}>{children}</span>;
}

function DriverBar({ shares }: { shares: Record<string, number> }) {
  const colors = tokens.drivers as Record<string, string>;
  return (
    <div className="uw-driver-bar" aria-label="Transition risk anatomy">
      {DRIVERS.map((driver) =>
        (shares[driver] ?? 0) > 0 ? (
          <i
            key={driver}
            title={`${DRIVER_LABEL[driver]} ${(shares[driver] * 100).toFixed(1)}%`}
            style={{ width: `${(shares[driver] ?? 0) * 100}%`, background: colors[driver] }}
          />
        ) : null,
      )}
    </div>
  );
}

function RiskAnatomy({ firm, shares, residual = false }: { firm: any; shares: any; residual?: boolean }) {
  const colors = tokens.drivers as Record<string, string>;
  const envelope = firm.underwriting.share_envelope;
  return (
    <div>
      <DriverBar shares={shares} />
      <div className="uw-driver-list">
        {DRIVERS.map((driver) => (
          <div key={driver}>
            <span><i style={{ background: colors[driver] }} />{DRIVER_LABEL[driver]}</span>
            <b className="mono">{((shares[driver] ?? 0) * 100).toFixed(1)}%</b>
            <small>
              {residual ? "residual" : `${((envelope[driver]?.lo ?? 0) * 100).toFixed(0)}–${((envelope[driver]?.hi ?? 0) * 100).toFixed(0)}% base band`}
            </small>
          </div>
        ))}
      </div>
    </div>
  );
}

function SensitivityMatrix({ sensitivity }: { sensitivity: any }) {
  const values = sensitivity.rows.map((r: any) => r.spread_bps);
  const max = Math.max(...values);
  const lookup = useMemo(
    () => new Map(sensitivity.rows.map((r: any) => [`${r.p_bind}|${r.lambda}`, r.spread_bps])),
    [sensitivity],
  );
  return (
    <div className="uw-matrix-wrap">
      <table className="uw-matrix mono">
        <thead>
          <tr>
            <th>p(bind) \ λ</th>
            {sensitivity.lambdas.map((v: number) => <th key={v}>{v.toFixed(2)}</th>)}
          </tr>
        </thead>
        <tbody>
          {sensitivity.p_binds.map((pb: number) => (
            <tr key={pb}>
              <th>{pb.toFixed(2)}</th>
              {sensitivity.lambdas.map((lam: number) => {
                const value = Number(lookup.get(`${pb}|${lam}`));
                const alpha = 0.08 + (value / max) * 0.7;
                const current = Math.abs(pb - sensitivity.base.p_bind) < 1e-9
                  && Math.abs(lam - sensitivity.base.lambda) < 1e-9;
                return (
                  <td
                    key={lam}
                    className={current ? "is-current" : ""}
                    style={{ background: `rgba(217,119,6,${alpha})` }}
                    title={current ? `Current assumptions: λ ${lam.toFixed(2)}, p(bind) ${pb.toFixed(2)}` : undefined}
                  >
                    {value.toFixed(1)}
                    {current && <span>you are here</span>}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChargeRangeKpi({ underwriting }: { underwriting: any }) {
  const range = underwriting.sensitivity.range_bps;
  const base = underwriting.sensitivity.base;
  const position = Math.max(0, Math.min(100, ((base.spread_bps - range.lo) / (range.hi - range.lo)) * 100));
  return (
    <article className="uw-charge-kpi">
      <div className="uw-charge-kpi__head">
        <span>Conditional risk charge</span>
        <b className="mono">{base.spread_bps.toFixed(1)} <small>bps</small></b>
      </div>
      <div className="uw-charge-range" aria-label={`Sensitivity range ${range.lo.toFixed(1)} to ${range.hi.toFixed(1)} basis points; base case ${base.spread_bps.toFixed(1)} basis points`}>
        <i />
        <b style={{ left: `${position}%` }}><span>base</span></b>
        <div className="mono"><span>{range.lo.toFixed(1)}</span><span>{range.hi.toFixed(1)} bps</span></div>
      </div>
      <p className="uw-kpi-caveat">
        Base case sits inside the full λ × p(bind) sensitivity. Exposure and covariance stay fixed;
        this is conditional, not an observed market spread.
      </p>
      <div className="evidence-badges">
        <EvidenceBadge>scenario-conditional</EvidenceBadge>
        <EvidenceBadge tone="basis">enterprise transition-window basis</EvidenceBadge>
      </div>
    </article>
  );
}

function InvestorDecisionSummary({ enterpriseOption, projectOption, profile }: { enterpriseOption: any; projectOption: any; profile: any }) {
  const econ = projectOption.economics;
  const annualCfads = econ.debt.dscr * econ.debt.annual_debt_service_usd_m;
  const cfadsShortfall = Math.max(
    0,
    econ.debt.target_dscr * econ.debt.annual_debt_service_usd_m - annualCfads,
  );
  const advances = econ.investment.decision === "INVESTABLE_SCREEN";

  return (
    <section className={`investor-decision ${advances ? "investor-decision--pass" : ""}`}>
      <div className="investor-decision__main">
        <p className="eyebrow">Investor decision summary · configured route</p>
        <h2>{advances ? "ADVANCE — begin diligence." : "FID HOLD — economics do not clear the screen."}</h2>
        <p>
          Under <b>{projectOption.label}</b>, absolute project NPV remains {compactMoney(econ.investment.project_npv_usd_m)}
          {projectOption.net_incremental_value_usd_m != null ? ` despite ${compactMoney(projectOption.net_incremental_value_usd_m)} of modeled incremental value` : ""}.
          The transaction needs ${econ.break_evens.required_green_premium_usd_t.toFixed(0)}/t of contracted low-carbon product premium
          versus ${profile.green_premium_usd_t.toFixed(0)}/t currently modeled.
        </p>
        <div className="evidence-badges">
          <EvidenceBadge>scenario-conditional</EvidenceBadge>
          <EvidenceBadge tone="provisional">provisional required path</EvidenceBadge>
          <EvidenceBadge tone="illustrative">illustrative transaction terms</EvidenceBadge>
        </div>
      </div>
      <div className="investor-decision__metrics">
        <div><span>Project NPV</span><b className="mono">{compactMoney(econ.investment.project_npv_usd_m)}</b></div>
        <div><span>Required premium</span><b className="mono">${econ.break_evens.required_green_premium_usd_t.toFixed(0)}/t</b></div>
        <div><span>CFADS shortfall</span><b className="mono">{compactMoney(cfadsShortfall)}/yr</b></div>
      </div>
      <div className="basis-compare">
        <div>
          <span>Enterprise transition-window charge</span>
          <b className="mono">{enterpriseOption.after_spread_bps.toFixed(1)} bps</b>
          <small>{enterpriseOption.result_contract?.basis_id ?? "enterprise transition-window basis"}</small>
        </div>
        <div>
          <span>Project-from-base-year charge</span>
          <b className="mono">{projectOption.risk.risk_charge_bps.toFixed(1)} bps</b>
          <small>{projectOption.risk.result_contract?.basis_id ?? "project from base-year basis"}</small>
        </div>
        <p><b>Comparison warning:</b> both are conditional-risk-charge normalizations, but their commissioning and exposure bases differ. Do not read their numeric difference as contract impact.</p>
      </div>
    </section>
  );
}

export default function UnderwritingDashboard({ data, deals }: { data: any; deals: any }) {
  const firms = data.firms as any[];
  const [mode, setMode] = useState<"investor" | "treasury" | "deal">("investor");
  const [firmId, setFirmId] = useState(firms.find((f) => f.firm_id === "POSCO")?.firm_id ?? firms[0].firm_id);
  const firm = firms.find((f) => f.firm_id === firmId)!;
  const [sector, setSector] = useState(firm.sector);
  const visibleFirms = firms.filter((candidate) => candidate.sector === sector);
  const firstChoice = firm.decision_summary.best_de_risker?.intervention_id ?? firm.contract_options[0].intervention_id;
  const [selectedByFirm, setSelectedByFirm] = useState<Record<string, string>>({});
  const selectedId = selectedByFirm[firmId] ?? firstChoice;
  const selected = firm.contract_options.find((o: any) => o.intervention_id === selectedId) ?? firm.contract_options[0];
  const uw = firm.underwriting;
  const sensitivity = uw.sensitivity;
  const dealFirm = deals.firms.find((d: any) => d.firm_id === firmId)!;
  const dealConfigured = dealFirm.route_cases.find((routeCase: any) => routeCase.is_configured_route)!;
  const [routeByFirm, setRouteByFirm] = useState<Record<string, string>>({});
  const [dealSelectionByRoute, setDealSelectionByRoute] = useState<Record<string, string>>({});
  const dealRouteName = routeByFirm[firmId] ?? dealFirm.configured_route;
  const dealRouteCase = dealFirm.route_cases.find((routeCase: any) => routeCase.route === dealRouteName) ?? dealConfigured;
  const dealSelectionKey = `${firmId}|${dealRouteCase.route}`;
  const storedDealSelection = dealSelectionByRoute[dealSelectionKey];
  const dealSelectedId = storedDealSelection === "base"
    || dealRouteCase.options.some((option: any) => option.applicable && option.intervention_id === storedDealSelection)
    ? storedDealSelection
    : dealRouteCase.frontier.best_value;
  const investorDealSelectedId = dealConfigured.options.some(
    (option: any) => option.applicable && option.intervention_id === selectedId,
  ) ? selectedId : dealConfigured.frontier.best_value;
  const investorDealSelected = dealConfigured.options.find(
    (option: any) => option.intervention_id === investorDealSelectedId,
  )!;
  const portfolioRow = data.portfolio.find((row: any) => row.firm_id === firmId);
  const currentRoute = mode === "deal" ? dealRouteCase.route : firm.route;
  const currentInterventionId = mode === "deal" ? dealSelectedId : selectedId;
  const currentInterventionLabel = mode === "deal"
    ? currentInterventionId === "base"
      ? "No intervention"
      : dealRouteCase.options.find((option: any) => option.intervention_id === currentInterventionId)?.label ?? currentInterventionId
    : selected.label;
  const pathwayHref = scenarioHref("/pathways", {
    firm: firmId,
    mode,
    intervention: currentInterventionId,
    route: currentRoute,
  });

  useEffect(() => {
    const query = readScenarioQuery();
    const nextFirm = firms.find((candidate) => candidate.firm_id === query.firm)
      ?? firms.find((candidate) => candidate.firm_id === "POSCO")
      ?? firms[0];
    const nextMode = query.mode === "treasury" || query.mode === "deal" ? query.mode : "investor";
    const nextDealFirm = deals.firms.find((candidate: any) => candidate.firm_id === nextFirm.firm_id);
    const configured = nextDealFirm.route_cases.find((routeCase: any) => routeCase.is_configured_route);
    const routeCase = nextDealFirm.route_cases.find((candidate: any) => candidate.route === query.route) ?? configured;
    const nextDefault = nextFirm.decision_summary.best_de_risker?.intervention_id
      ?? nextFirm.contract_options[0].intervention_id;
    const nextContract = nextFirm.contract_options.some((option: any) => option.intervention_id === query.intervention)
      ? query.intervention!
      : nextDefault;
    const dealOptionValid = query.intervention === "base"
      || routeCase.options.some((option: any) => option.applicable && option.intervention_id === query.intervention);
    const nextDealSelection = dealOptionValid ? query.intervention! : routeCase.frontier.best_value;

    setFirmId(nextFirm.firm_id);
    setSector(nextFirm.sector);
    setMode(nextMode);
    setSelectedByFirm((old) => ({ ...old, [nextFirm.firm_id]: nextContract }));
    setRouteByFirm((old) => ({ ...old, [nextFirm.firm_id]: routeCase.route }));
    setDealSelectionByRoute((old) => ({
      ...old,
      [`${nextFirm.firm_id}|${routeCase.route}`]: nextDealSelection,
    }));
    replaceScenarioQuery({
      firm: nextFirm.firm_id,
      mode: nextMode,
      intervention: nextMode === "deal" ? nextDealSelection : nextContract,
      route: nextMode === "deal" ? routeCase.route : nextFirm.route,
    });
  // URL state is intentionally hydrated once; later changes flow through the handlers below.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function selectContract(id: string) {
    setSelectedByFirm((old) => ({ ...old, [firmId]: id }));
    replaceScenarioQuery({ firm: firmId, mode, intervention: id, route: firm.route });
  }

  function selectSector(nextSector: string) {
    const nextFirm = firms.find((candidate) => candidate.sector === nextSector);
    if (!nextFirm) return;
    selectFirm(nextFirm.firm_id);
  }

  function selectFirm(id: string) {
    const nextFirm = firms.find((candidate) => candidate.firm_id === id);
    if (!nextFirm) return;
    const nextDealFirm = deals.firms.find((candidate: any) => candidate.firm_id === id);
    const nextRoute = routeByFirm[id]
      ?? nextDealFirm.route_cases.find((routeCase: any) => routeCase.is_configured_route).route;
    const nextRouteCase = nextDealFirm.route_cases.find((routeCase: any) => routeCase.route === nextRoute);
    const nextDealId = dealSelectionByRoute[`${id}|${nextRoute}`] ?? nextRouteCase.frontier.best_value;
    const nextContractId = selectedByFirm[id]
      ?? nextFirm.decision_summary.best_de_risker?.intervention_id
      ?? nextFirm.contract_options[0].intervention_id;
    setSector(nextFirm.sector);
    setFirmId(id);
    replaceScenarioQuery({
      firm: id,
      mode,
      intervention: mode === "deal" ? nextDealId : nextContractId,
      route: mode === "deal" ? nextRoute : nextFirm.route,
    });
  }

  function selectMode(nextMode: "investor" | "treasury" | "deal") {
    setMode(nextMode);
    replaceScenarioQuery({
      firm: firmId,
      mode: nextMode,
      intervention: nextMode === "deal" ? dealSelectedId : selectedId,
      route: nextMode === "deal" ? dealRouteCase.route : firm.route,
    });
  }

  function selectDealRoute(route: string) {
    const routeCase = dealFirm.route_cases.find((candidate: any) => candidate.route === route);
    if (!routeCase) return;
    const nextId = dealSelectionByRoute[`${firmId}|${route}`] ?? routeCase.frontier.best_value;
    setRouteByFirm((old) => ({ ...old, [firmId]: route }));
    replaceScenarioQuery({ firm: firmId, mode, intervention: nextId, route });
  }

  function selectDealScenario(id: string) {
    setDealSelectionByRoute((old) => ({ ...old, [dealSelectionKey]: id }));
    replaceScenarioQuery({ firm: firmId, mode, intervention: id, route: dealRouteCase.route });
  }

  return (
    <div className="uw-dash">
      <div className="uw-toolbar">
        <div className="seg" role="tablist" aria-label="Audience view">
          <button className={mode === "investor" ? "on" : ""} onClick={() => selectMode("investor")}>Investor underwriting</button>
          <button className={mode === "treasury" ? "on" : ""} onClick={() => selectMode("treasury")}>Corporate treasury</button>
          <button className={mode === "deal" ? "on" : ""} onClick={() => selectMode("deal")}>Deal &amp; investment</button>
        </div>
        <div className="seg seg--sector" role="tablist" aria-label="Sector">
          {Object.keys(SECTOR_LABEL).filter((candidate) => firms.some((f) => f.sector === candidate)).map((candidate) => (
            <button key={candidate} className={sector === candidate ? "on" : ""} onClick={() => selectSector(candidate)}>{SECTOR_LABEL[candidate]}</button>
          ))}
        </div>
        <div className="seg" role="tablist" aria-label="Firm">
          {visibleFirms.map((f) => (
            <button key={f.firm_id} className={f.firm_id === firmId ? "on" : ""} onClick={() => selectFirm(f.firm_id)}>
              {f.firm}
            </button>
          ))}
        </div>
      </div>

      <section className="scenario-strip" aria-label="Current scenario" aria-live="polite">
        <b>Current scenario</b>
        <dl>
          <div><dt>Company</dt><dd>{firm.firm}</dd></div>
          <div><dt>Route</dt><dd className="mono">{currentRoute.replaceAll("_", " ")}</dd></div>
          <div><dt>Selected term</dt><dd>{currentInterventionLabel}</dd></div>
          <div><dt>Regime</dt><dd>reform-priced</dd></div>
          <div><dt>Scope</dt><dd>{mode === "deal" ? "project from base year" : "enterprise transition window"}</dd></div>
        </dl>
        <Link href={pathwayHref}>Why this charge exists →</Link>
      </section>

      {mode === "investor" && (
        <InvestorDecisionSummary enterpriseOption={selected} projectOption={investorDealSelected} profile={deals.profile} />
      )}

      {mode !== "deal" && (
        <>
          <section className="uw-firm-header">
            <div>
              <p className="eyebrow">{SECTOR_LABEL[firm.sector]} · {firm.route.replaceAll("_", " ")}</p>
              <h2>{firm.firm}</h2>
            </div>
            <dl>
              <div><dt>Dominant exposure</dt><dd>{DRIVER_LABEL[uw.dominant_driver]}</dd></div>
              <div>
                <dt>Cumulative alignment gap</dt>
                <dd className="mono">≈{portfolioRow?.cumulative_alignment_gap_mtco2?.toFixed(1) ?? "—"} MtCO₂</dd>
                <small className="uw-evidence-note">PROVISIONAL · surrogate required path</small>
              </div>
            </dl>
          </section>

          <section className="uw-kpis">
            <ChargeRangeKpi underwriting={uw} />
            <article>
              <span>Transition cost uncertainty</span>
              <b className="mono">${uw.transition_cost_sigma_usd_bn.toFixed(1)} <small>bn</small></b>
              <em>PV standard deviation</em>
            </article>
            <article>
              <span>Annual charge equivalent</span>
              <b className="mono">${uw.annual_risk_charge_usd_m.toFixed(1)} <small>m/yr</small></b>
              <em>conditional charge × enterprise value</em>
            </article>
          </section>
        </>
      )}

      {mode === "investor" ? (
        <>
          <div className="uw-grid uw-grid--lead">
            <section className="panel">
              <div className="uw-panel-head">
                <div>
                  <p className="eyebrow">Technology risk map</p>
                  <h2>{firm.firm} · {firm.route.replaceAll("_", " ")}</h2>
                </div>
                <span className="uw-dominant">dominant · {DRIVER_LABEL[uw.dominant_driver]}</span>
              </div>
              <p className="panel__lede">The technology route determines the exposure vector. The mix below is uncertainty contribution, not emissions share.</p>
              <RiskAnatomy firm={firm} shares={uw.risk_anatomy} />
              <p className="panel__foot">The covariance envelope is a base-regime stress band. The displayed anatomy is reform-priced and can sit outside that band.</p>
            </section>

            <section className="panel">
              <p className="eyebrow">Contract-adjusted underwriting</p>
              <h2>What changes the charge?</h2>
              <label className="uw-select-label">
                Counterfactual
                <select value={selectedId} onChange={(e) => selectContract(e.target.value)}>
                  {firm.contract_options.map((o: any) => <option key={o.intervention_id} value={o.intervention_id} disabled={!o.applicable}>{o.label}{o.applicable ? "" : " · not applicable"}</option>)}
                </select>
              </label>
              <div className="uw-before-after">
                <div><span>before · enterprise window</span><b className="mono">{selected.before_spread_bps.toFixed(1)}</b><small>bps</small></div>
                <i>→</i>
                <div className={selected.risk_cut_bps > 0 ? "good" : selected.risk_cut_bps < 0 ? "bad" : "neutral"}><span>after · enterprise window</span><b className="mono">{selected.after_spread_bps.toFixed(1)}</b><small>bps</small></div>
              </div>
              <div className="uw-impact-line">
                <span>Risk-charge change</span>
                <b className="mono">{signed(-selected.risk_cut_bps)} bps</b>
              </div>
              <div className="uw-impact-line">
                <span>{selected.risk_cut_bps >= 0 ? "Annual charge reduction equivalent" : "Annual charge increase equivalent"}</span>
                <b className="mono">${Math.abs(selected.annual_risk_charge_value_usd_m).toFixed(1)}m/yr</b>
              </div>
              <div className="evidence-badges">
                <EvidenceBadge>scenario-conditional</EvidenceBadge>
                <EvidenceBadge tone="basis">enterprise transition-window basis</EvidenceBadge>
              </div>
              <p className="panel__foot">Equivalent value is a normalization, not a promised loan-price saving. Contract premium and counterparty pricing are not yet observed.</p>
            </section>
          </div>

          <InvestorPortfolioMap
            portfolio={data.portfolio.filter((row: any) => row.sector === sector)}
            selectedFirmId={firmId}
            onSelect={selectFirm}
          />

          <div className="deal-visual-grid deal-visual-grid--frontier uw-investor-frontier">
            <EfficientFrontier
              routeCase={dealConfigured}
              selectedId={investorDealSelectedId}
              onSelect={(id) => { if (id !== "base") selectContract(id); }}
            />
            <InvestmentCommitteePanel routeCase={dealConfigured} selected={investorDealSelected} profile={deals.profile} />
          </div>

          <section className="panel uw-portfolio">
            <div className="uw-panel-head">
              <div><p className="eyebrow">Relative value screen</p><h2>Portfolio underwriting comparison</h2></div>
              <span className="tag tag--sample">priced-route firms only</span>
            </div>
            <div className="uw-table-wrap">
              <table className="uw-table">
                <thead><tr><th>Firm</th><th>Route</th><th>Dominant risk</th><th>Alignment gap</th><th>Annual equivalent</th><th>Conditional risk charge</th></tr></thead>
                <tbody>
                  {data.portfolio.filter((row: any) => row.sector === sector).map((row: any) => (
                    <tr key={row.firm_id} className={row.firm_id === firmId ? "sel" : ""} onClick={() => selectFirm(row.firm_id)}>
                      <td><b>{row.firm}</b></td>
                      <td className="mono">{row.route}</td>
                      <td>{DRIVER_LABEL[row.dominant_driver]}</td>
                      <td className="mono">{row.cumulative_alignment_gap_mtco2.toFixed(1)} MtCO₂</td>
                      <td className="mono">${row.annual_risk_charge_usd_m.toFixed(1)}m</td>
                      <td className="mono uw-hot">{row.spread_bps.toFixed(1)} bps</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <div className="uw-panel-head">
              <div><p className="eyebrow">Pricing uncertainty</p><h2>λ × probability of binding transition</h2></div>
              <span className="uw-range mono">{sensitivity.range_bps.lo.toFixed(1)}–{sensitivity.range_bps.hi.toFixed(1)} bps</span>
            </div>
            <p className="panel__lede">An underwriting sensitivity surface, not a confidence interval. The outlined cell is the current assumption set; technology exposure and covariance remain fixed.</p>
            <SensitivityMatrix sensitivity={sensitivity} />
          </section>
        </>
      ) : mode === "treasury" ? (
        <>
          <section className={`uw-recommend ${firm.decision_summary.best_de_risker?.risk_cut_bps < MATERIAL_RISK_CUT_BPS ? "uw-recommend--immaterial" : ""}`}>
            <div>
              {firm.decision_summary.best_de_risker?.risk_cut_bps >= MATERIAL_RISK_CUT_BPS ? (
                <>
                  <p className="eyebrow">First material de-risking conversation</p>
                  <h2>{firm.decision_summary.best_de_risker.label}</h2>
                  <p>Dominant unhedged exposure: <b>{DRIVER_LABEL[firm.decision_summary.dominant_unhedged_driver]}</b>. The ranking is based on modeled conditional-risk-charge reduction before contract price.</p>
                </>
              ) : (
                <>
                  <p className="eyebrow">Package-level de-risking required</p>
                  <h2>No standalone instrument is commercially material.</h2>
                  <p>
                    The best standalone term, {firm.decision_summary.best_de_risker?.label ?? "none"}, changes the conditional risk charge by only {firm.decision_summary.best_de_risker?.risk_cut_bps.toFixed(1) ?? "0.0"} bps, below the {MATERIAL_RISK_CUT_BPS.toFixed(0)} bps screen. Review the integrated package and obtain executable quotes before opening a standalone negotiation.
                  </p>
                </>
              )}
            </div>
            {firm.decision_summary.best_de_risker && (
              <div className="uw-recommend__number mono">
                <b>−{firm.decision_summary.best_de_risker.risk_cut_bps.toFixed(1)}</b>
                <span>{firm.decision_summary.best_de_risker.risk_cut_bps >= MATERIAL_RISK_CUT_BPS ? "bps modeled cut" : `bps · below ${MATERIAL_RISK_CUT_BPS.toFixed(0)} bps screen`}</span>
              </div>
            )}
          </section>

          <ContractCoverageLadder options={firm.contract_options} selectedId={selectedId} onSelect={selectContract} />

          <section className="panel">
            <div className="uw-panel-head">
              <div><p className="eyebrow">Contract optimizer · benefit side</p><h2>Compare the available risk transformations</h2></div>
              <span className="tag tag--sample">cost frontier pending quotes</span>
            </div>
            <div className="uw-table-wrap">
              <table className="uw-table uw-contract-table">
                <thead><tr><th>Instrument</th><th>Terms used</th><th>Risk cut</th><th>Annual equivalent</th><th>Residual</th><th>Decision read</th></tr></thead>
                <tbody>
                  {firm.contract_options.map((o: any) => {
                    const terms = o.terms;
                    const termText = terms.operation === "combine"
                      ? `${terms.components.length} instruments`
                      : `${terms.coverage != null ? `${(terms.coverage * 100).toFixed(0)}% · ` : ""}${terms.start_year}–${terms.end_year}`;
                    return (
                      <tr key={o.intervention_id} className={`${o.intervention_id === selectedId ? "sel" : ""} ${!o.applicable ? "muted" : ""}`} onClick={() => selectContract(o.intervention_id)}>
                        <td><b>{o.label}</b><small>{terms.targets.map((d: string) => DRIVER_LABEL[d] ?? d).join(" + ")}</small></td>
                        <td className="mono">{o.applicable ? termText : "not route-applicable"}</td>
                        <td className={`mono ${o.risk_cut_bps > 0 ? "uw-good" : o.risk_cut_bps < 0 ? "uw-bad" : ""}`}>{signed(o.risk_cut_bps)} bps</td>
                        <td className="mono">${signed(o.annual_risk_charge_value_usd_m)}m/yr</td>
                        <td className="mono">{(o.residual_charge_ratio * 100).toFixed(0)}%</td>
                        <td><span className={`uw-class uw-class--${o.decision_class}`}>{CLASS_LABEL[o.decision_class]}</span></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <div className="uw-grid">
            <section className="panel">
              <p className="eyebrow">Residual risk</p>
              <h2>After {selected.label}</h2>
              <p className="panel__lede">Coverage, tenor and basis assumptions are retained. The remaining mix tells treasury what must be contracted next.</p>
              <RiskAnatomy firm={firm} shares={selected.residual_shares} residual />
              <div className="uw-residual-line">
                <span>Residual conditional charge</span>
                <b className="mono">{selected.after_spread_bps.toFixed(1)} bps · {(selected.residual_charge_ratio * 100).toFixed(0)}%</b>
              </div>
            </section>

            <section className="panel">
              <p className="eyebrow">Package attribution</p>
              <h2>Who changes the package charge?</h2>
              <p className="panel__lede">Order-averaged contribution. Positive bars reduce the charge; negative values add charge under the package.</p>
              <div className="uw-attribution">
                {Object.entries(firm.package_attribution.order_averaged_cut_bps).map(([id, value]: [string, any]) => {
                  const max = Math.max(...Object.values(firm.package_attribution.order_averaged_cut_bps).map((v: any) => Math.abs(v)), 1);
                  const option = firm.contract_options.find((o: any) => o.intervention_id === id);
                  return (
                    <div key={id}>
                      <span>{option?.label ?? id}</span>
                      <div><i className={value >= 0 ? "pos" : "neg"} style={{ width: `${Math.abs(value) / max * 100}%` }} /></div>
                      <b className="mono">{signed(value)} bps</b>
                    </div>
                  );
                })}
              </div>
              <p className="panel__foot">This is a contribution decomposition, not proof that the package is cost-effective.</p>
            </section>
          </div>
        </>
      ) : (
        <DealScreen
          firm={dealFirm}
          profile={deals.profile}
          routeName={dealRouteCase.route}
          selectedId={dealSelectedId}
          onRouteSelect={selectDealRoute}
          onScenarioSelect={selectDealScenario}
        />
      )}

      {mode !== "deal" && <section className="uw-disclaimer">
        <b>Decision boundary</b>
        <span>{data.definitions.model_implied_spread}. {data.definitions.contract_ranking}. Output is research analytics, not investment advice or a credit rating.</span>
      </section>}
    </div>
  );
}
