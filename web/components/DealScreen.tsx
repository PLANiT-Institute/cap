"use client";

import { useMemo } from "react";
import {
  EfficientFrontier,
  InvestmentCommitteePanel,
  RiskTransferChart,
  TechnologyAllocationMap,
} from "./DealVisuals";

const DECISION_LABEL: Record<string, string> = {
  DUE_DILIGENCE_CANDIDATE: "bankable candidate",
  IMPROVES_BUT_NOT_BANKABLE: "improves · still not bankable",
  VALUE_WITH_RISK_TRADEOFF: "value ↑ · risk trade-off",
  VALUE_TRADEOFF_NOT_BANKABLE: "value ↑ · not bankable · risk trade-off",
  DE_RISKING_BUT_VALUE_NEGATIVE: "risk ↓ · value negative",
  RENEGOTIATE_OR_REJECT: "renegotiate / reject",
};

function money(value: number) {
  const sign = value < 0 ? "−" : "";
  const abs = Math.abs(value);
  return abs >= 1000 ? `${sign}$${(abs / 1000).toFixed(1)}bn` : `${sign}$${abs.toFixed(0)}m`;
}

function signed(value: number, digits = 1) {
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function dscr(value: number, passes: boolean) {
  if (value <= 0) return "CFADS < 0";
  return `${value.toFixed(2)}×${passes ? "" : " short"}`;
}

function bestCase(routeCase: any) {
  const cases = [
    { id: "base", label: "No intervention", economics: routeCase.base.economics, risk: routeCase.base.risk },
    ...routeCase.options.filter((o: any) => o.applicable).map((o: any) => ({ id: o.intervention_id, ...o })),
  ];
  return cases.reduce((best: any, current: any) =>
    current.economics.investment.project_npv_usd_m > best.economics.investment.project_npv_usd_m ? current : best,
  );
}

export default function DealScreen({
  firm,
  profile,
  routeName,
  selectedId,
  onRouteSelect,
  onScenarioSelect,
}: {
  firm: any;
  profile: any;
  routeName: string;
  selectedId: string;
  onRouteSelect: (route: string) => void;
  onScenarioSelect: (id: string) => void;
}) {
  const routeCase = firm.route_cases.find((r: any) => r.route === routeName)!;
  const baseSelection = { id: "base", label: "No intervention", economics: routeCase.base.economics, risk: routeCase.base.risk };
  const selectedOption = routeCase.options.find((o: any) => o.intervention_id === selectedId);
  const selected = selectedId === "base" || !selectedOption ? baseSelection : { id: selectedId, ...selectedOption };
  const econ = selected.economics;
  const risk = selected.risk;
  const configuredCase = firm.route_cases.find((r: any) => r.is_configured_route)!;
  const configuredAdvance = firm.recommendation.action === "PROCEED_TO_DUE_DILIGENCE";
  const bilateralId = configuredCase.frontier.best_bilateral_contract_screen;
  const bilateral = configuredCase.options.find((o: any) => o.intervention_id === bilateralId);

  const scenarios = useMemo(
    () => [baseSelection, ...routeCase.options.filter((o: any) => o.applicable).map((o: any) => ({ id: o.intervention_id, ...o }))],
    [routeCase],
  );

  return (
    <div className="deal-screen">
      <section className={`deal-verdict ${configuredAdvance ? "deal-verdict--pass" : ""}`}>
        <div>
          <p className="eyebrow">Investment committee screen · configured route</p>
          <h2>
            {configuredAdvance
              ? "ADVANCE — diligence the support package."
              : `FID HOLD — $${firm.recommendation.configured_route_required_green_premium_usd_t.toFixed(0)}/t to bankable.`}
          </h2>
          {configuredAdvance ? (
            <p>
              The best modeled {firm.configured_route.replaceAll("_", " ")} case clears the screening gates with NPV {money(firm.recommendation.configured_route_best_npv_usd_m)} and no additional modeled product premium. Validate every support and operating assumption before treating it as bankable.
            </p>
          ) : (
            <p>
              The best modeled {firm.configured_route.replaceAll("_", " ")} case requires at least <b>${firm.recommendation.configured_route_required_green_premium_usd_t.toFixed(0)}/t</b> of additional contracted low-carbon product premium to clear both NPV and DSCR screens. Its current NPV is {money(firm.recommendation.configured_route_best_npv_usd_m)}; keep that diagnostic below the actionable price gap.
            </p>
          )}
          <div className="evidence-badges">
            <span className="evidence-tag">scenario-conditional</span>
            <span className="evidence-tag evidence-tag--illustrative">illustrative terms</span>
            <span className="evidence-tag evidence-tag--basis">project-at-base-year basis</span>
          </div>
        </div>
        <div className="deal-verdict__action">
          <span>Priority risk-transfer term</span>
          <b>{bilateral?.label ?? "No contract passes both gates"}</b>
          <small>{bilateral?.term_sheet?.modelled_core ?? "Reprice the transaction before term-sheet work."}</small>
        </div>
      </section>

      <div className="deal-route-tabs" role="tablist" aria-label="Technology investment">
        {firm.route_cases.map((r: any) => (
          <button key={r.route} className={r.route === routeName ? "on" : ""} onClick={() => onRouteSelect(r.route)}>
            <b>{r.route.replaceAll("_", " ")}</b>
            <span>{r.is_configured_route ? "configured" : "feasibility open"} · {r.meets_configured_decarbonization_depth ? "depth-equivalent" : "shallower cut"}</span>
          </button>
        ))}
      </div>

      <section className="deal-kpis">
        <article><span>Project NPV</span><b className={econ.investment.project_npv_usd_m >= 0 ? "good" : "bad"}>{money(econ.investment.project_npv_usd_m)}</b><em>{selected.label}</em></article>
        <article><span>Unlevered project IRR</span><b>{econ.investment.project_irr == null ? "not earned" : `${(econ.investment.project_irr * 100).toFixed(1)}%`}</b><em>hurdle {(econ.investment.discount_rate * 100).toFixed(1)}%</em></article>
        <article><span>Debt service cover</span><b className={econ.debt.dscr_pass ? "good" : "bad"}>{dscr(econ.debt.dscr, econ.debt.dscr_pass)}</b><em>target {econ.debt.target_dscr.toFixed(2)}×</em></article>
        <article><span>Required contracted premium</span><b className={econ.break_evens.required_green_premium_usd_t <= profile.green_premium_usd_t ? "good" : "bad"}>${econ.break_evens.required_green_premium_usd_t.toFixed(0)}/t</b><em>binding NPV / DSCR gate</em></article>
        <article><span>Residual conditional charge</span><b>{risk.risk_charge_bps.toFixed(1)} bps</b><em>project-at-base-year · {selected.risk_cut_bps == null ? "route baseline" : selected.risk_cut_bps >= 0 ? `${selected.risk_cut_bps.toFixed(1)} bps risk reduction` : `${Math.abs(selected.risk_cut_bps).toFixed(1)} bps risk increase`}</em></article>
      </section>

      <div className="deal-visual-grid deal-visual-grid--frontier">
        <EfficientFrontier routeCase={routeCase} selectedId={selectedId} onSelect={onScenarioSelect} />
        <InvestmentCommitteePanel routeCase={routeCase} selected={selected} profile={profile} />
      </div>

      <div className="deal-visual-grid deal-visual-grid--allocation">
        <TechnologyAllocationMap firm={firm} routeName={routeName} onRouteSelect={onRouteSelect} />
        <RiskTransferChart routeCase={routeCase} selected={selected} />
      </div>

      <section className="panel deal-route-compare">
        <div className="uw-panel-head">
          <div><p className="eyebrow">Technology investment comparator</p><h2>Cheaper is not necessarily climate-equivalent</h2></div>
          <span className="tag tag--sample">non-configured feasibility OPEN</span>
        </div>
        <div className="uw-table-wrap">
          <table className="uw-table">
            <thead><tr><th>Route</th><th>Residual intensity</th><th>Depth gate</th><th>Best modeled case</th><th>Best NPV</th><th>Required premium</th></tr></thead>
            <tbody>
              {firm.route_cases.map((r: any) => {
                const best = bestCase(r);
                return (
                  <tr key={r.route} className={r.route === routeName ? "sel" : ""} onClick={() => onRouteSelect(r.route)}>
                    <td><b>{r.route.replaceAll("_", " ")}</b><small>{r.is_configured_route ? "configured route" : "technical feasibility not validated"}</small></td>
                    <td className="mono">{r.base.economics.residual_intensity_tco2_t.toFixed(2)} tCO₂/t</td>
                    <td>{r.meets_configured_decarbonization_depth ? <span className="uw-good">passes</span> : <span className="uw-bad">shallower</span>}</td>
                    <td>{best.label}</td>
                    <td className={`mono ${best.economics.investment.project_npv_usd_m >= 0 ? "uw-good" : "uw-bad"}`}>{money(best.economics.investment.project_npv_usd_m)}</td>
                    <td className="mono">${best.economics.break_evens.required_green_premium_usd_t.toFixed(0)}/t</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {!firm.recommendation.economic_leader_meets_configured_depth && (
          <p className="panel__foot">The unconstrained economic leader is {firm.recommendation.economic_leader_route.replaceAll("_", " ")}, but it does not match the configured route’s decarbonization depth. CAP therefore does not promote it as the climate-equivalent investment recommendation.</p>
        )}
      </section>

      <section className="panel deal-contracts">
        <div className="uw-panel-head">
          <div><p className="eyebrow">Contract and support decision</p><h2>Which term changes value, risk and bankability?</h2></div>
          <span className="tag tag--sample">illustrative quote profile</span>
        </div>
        <div className="uw-table-wrap">
          <table className="uw-table">
            <thead><tr><th>Instrument</th><th>Required party</th><th>Project NPV</th><th>CP-adjusted ΔNPV</th><th>Risk reduction</th><th>DSCR</th><th>Required premium</th><th>IC status</th></tr></thead>
            <tbody>
              {scenarios.map((o: any) => (
                <tr key={o.id} className={o.id === selectedId ? "sel" : ""} onClick={() => onScenarioSelect(o.id)}>
                  <td><b>{o.label}</b><small>{o.instrument_type ?? "baseline"}</small></td>
                  <td>{(o.decision_owner ?? "company").replaceAll("_", " ")}</td>
                  <td className={`mono ${o.economics.investment.project_npv_usd_m >= 0 ? "uw-good" : "uw-bad"}`}>{money(o.economics.investment.project_npv_usd_m)}</td>
                  <td className="mono">{o.net_incremental_value_usd_m == null ? "—" : money(o.net_incremental_value_usd_m)}</td>
                  <td className={`mono ${o.risk_cut_bps > 0 ? "uw-good" : o.risk_cut_bps < 0 ? "uw-bad" : ""}`}>{o.risk_cut_bps == null ? "—" : `${signed(o.risk_cut_bps)} bps`}</td>
                  <td className={`mono ${o.economics.debt.dscr_pass ? "uw-good" : "uw-bad"}`}>{dscr(o.economics.debt.dscr, o.economics.debt.dscr_pass)}</td>
                  <td className="mono">${o.economics.break_evens.required_green_premium_usd_t.toFixed(0)}/t</td>
                  <td><span className={`deal-decision deal-decision--${o.contract_decision ?? "base"}`}>{o.contract_decision ? DECISION_LABEL[o.contract_decision] : "baseline"}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel deal-term-sheet">
        <div className="uw-panel-head">
          <div><p className="eyebrow">Selected transaction term sheet</p><h2>{selected.label}</h2></div>
          <span className="tag tag--sample">screening terms · not an offer</span>
        </div>
        {selected.term_sheet ? (
          <div className="deal-term-sheet__grid">
            <div>
              <h3>Modeled commercial core</h3>
              <p>{selected.term_sheet.modelled_core}</p>
            </div>
            <div>
              <h3>Clauses required before signature</h3>
              <ul>
                {selected.term_sheet.must_have_clauses.map((term: string) => <li key={term}>{term}</li>)}
              </ul>
            </div>
          </div>
        ) : (
          <p className="panel__foot">Select a contract or support instrument in the table to inspect the modeled commercial terms and diligence clauses.</p>
        )}
      </section>

      <div className="uw-grid deal-detail">
        <section className="panel">
          <p className="eyebrow">Unit economics</p>
          <h2>Why the project does or does not pay</h2>
          <div className="deal-waterfall">
            {Object.entries(econ.unit_economics_usd_t).map(([key, value]: [string, any]) => (
              <div key={key}><span>{key.replaceAll("_", " ")}</span><i className={value >= 0 ? "pos" : "neg"} /><b className="mono">{signed(value)} $/t</b></div>
            ))}
          </div>
          <p className="panel__foot">Expected carbon uses the scenario-weighted level. No low-carbon product premium is assumed in the screening profile.</p>
        </section>

        <section className="panel">
          <p className="eyebrow">Debt and break-even</p>
          <h2>Terms the negotiation must close</h2>
          <div className="deal-metrics">
            <div><span>CAPEX</span><b className="mono">{money(econ.investment.capex_usd_m)}</b></div>
            <div><span>Debt amount</span><b className="mono">{money(econ.debt.debt_amount_usd_m)}</b></div>
            <div><span>Annual debt service</span><b className="mono">{money(econ.debt.annual_debt_service_usd_m)}/yr</b></div>
            <div><span>Break-even carbon</span><b className="mono">${econ.break_evens.break_even_carbon_usd_t.toFixed(0)}/t</b></div>
            <div><span>Break-even hydrogen</span><b className="mono">{econ.break_evens.break_even_hydrogen_usd_kg == null ? "n/a" : `${econ.break_evens.break_even_hydrogen_usd_kg < 0 ? "−" : ""}$${Math.abs(econ.break_evens.break_even_hydrogen_usd_kg).toFixed(2)}/kg`}</b></div>
            {econ.break_evens.break_even_feedstock_usd_t != null && <div><span>Break-even feedstock</span><b className="mono">${econ.break_evens.break_even_feedstock_usd_t.toFixed(0)}/t</b></div>}
            <div><span>Simple counterparty EL</span><b className="mono">{selected.counterparty_adjustment ? money(selected.counterparty_adjustment.expected_loss_usd_m) : "n/a"}</b></div>
          </div>
          <p className="panel__foot">Debt rate = firm WACC plus intervention delta. Counterparty EL is a coarse PD × LGD screen, not a CVA quote. Replace both with lender and counterparty terms before any decision.</p>
        </section>
      </div>

      <section className="uw-disclaimer">
        <b>Transaction boundary</b>
        <span>{profile.quote_status}: project life {profile.project_life_years}y · debt share {(profile.debt_share * 100).toFixed(0)}% · tenor {profile.debt_tenor_years}y · DSCR target {profile.target_dscr.toFixed(2)}× · annual counterparty PD {(profile.counterparty_pd_annual * 100).toFixed(1)}%. This is a pre-deal screen, not investment advice or an executable quote.</span>
      </section>
    </div>
  );
}
