"use client";

import tokens from "../tokens.json";

const DRIVERS = ["carbon", "h2", "elec", "feedstock", "capex"] as const;
const DRIVER_LABEL: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  feedstock: "Feedstock",
  capex: "Capital cost",
};

const SHORT_LABEL: Record<string, string> = {
  base: "Baseline",
  h2_cfd: "H₂ CfD",
  ppa: "PPA",
  feedstock_hedge: "Feed collar",
  circular_feedstock: "Feedstock",
  capex_subsidy: "Grant",
  carbon_reform: "Policy",
  concessional: "Finance",
  package: "Package",
};

function compactMoney(value: number) {
  const sign = value < 0 ? "−" : "";
  const abs = Math.abs(value);
  return abs >= 1000 ? `${sign}$${(abs / 1000).toFixed(1)}bn` : `${sign}$${abs.toFixed(0)}m`;
}

function axisMoney(value: number) {
  const sign = value < 0 ? "−" : "";
  const abs = Math.abs(value);
  return abs >= 1000 ? `${sign}$${(abs / 1000).toFixed(abs >= 10000 ? 0 : 1)}bn` : `${sign}$${abs.toFixed(0)}m`;
}

function scale(value: number, d0: number, d1: number, r0: number, r1: number) {
  if (d0 === d1) return (r0 + r1) / 2;
  return r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);
}

function ticks(min: number, max: number, count: number) {
  return Array.from({ length: count }, (_, index) => min + ((max - min) * index) / (count - 1));
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

export function EfficientFrontier({
  routeCase,
  selectedId,
  onSelect,
}: {
  routeCase: any;
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const base = routeCase.base;
  const points = [
    {
      id: "base",
      label: "No intervention",
      x: 0,
      y: 0,
      residualCharge: base.risk.risk_charge_bps,
      projectNpv: base.economics.investment.project_npv_usd_m,
      riskCut: 0,
    },
    ...routeCase.options.filter((o: any) => o.applicable).map((o: any) => ({
      id: o.intervention_id,
      label: o.label,
      x: o.risk_cut_bps,
      y: o.net_incremental_value_usd_m,
      residualCharge: o.risk.risk_charge_bps,
      projectNpv: o.economics.investment.project_npv_usd_m,
      riskCut: o.risk_cut_bps,
    })),
  ];
  const frontierIds = new Set(routeCase.frontier.pareto_interventions);
  const frontier = points.filter((point) => frontierIds.has(point.id)).sort((a, b) => a.x - b.x);
  const showFrontier = points.length >= 5;
  const selected = points.find((point) => point.id === selectedId) ?? points[0];

  const width = 680;
  const height = 330;
  const margin = { left: 68, right: 24, top: 30, bottom: 52 };
  const xValues = points.map((point) => point.x);
  const yValues = points.map((point) => point.y).concat(0);
  const xRawMin = Math.min(...xValues);
  const xRawMax = Math.max(...xValues);
  const yRawMin = Math.min(...yValues);
  const yRawMax = Math.max(...yValues);
  const xPad = Math.max((xRawMax - xRawMin) * 0.12, 1);
  const yPad = Math.max((yRawMax - yRawMin) * 0.12, 250);
  const xMin = xRawMin - xPad;
  const xMax = xRawMax + xPad;
  const yMin = yRawMin - yPad;
  const yMax = yRawMax + yPad;
  const px = (value: number) => scale(value, xMin, xMax, margin.left, width - margin.right);
  const py = (value: number) => scale(value, yMin, yMax, height - margin.bottom, margin.top);
  const line = frontier.map((point) => `${px(point.x)},${py(point.y)}`).join(" ");

  return (
    <section className="panel deal-frontier">
      <div className="uw-panel-head">
        <div>
          <p className="eyebrow">{showFrontier ? "Contract efficient frontier" : "Contract candidate comparison"}</p>
          <h2>Value creation vs conditional-risk-charge reduction</h2>
        </div>
        <div className="evidence-badges">
          <span className="evidence-tag evidence-tag--basis">project-at-base-year basis</span>
          <span className="deal-chart-direction">better ↗</span>
        </div>
      </div>
      <svg className="deal-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="frontier-title frontier-desc">
        <title id="frontier-title">{showFrontier ? "Contract efficient frontier" : "Contract candidate comparison"}</title>
        <desc id="frontier-desc">Net incremental project value on the vertical axis and conditional risk charge reduction on the horizontal axis. Upper-right points are preferred.</desc>
        {ticks(yMin, yMax, 5).map((tick) => (
          <g key={`y-${tick}`}>
            <line className="deal-chart__grid" x1={margin.left} x2={width - margin.right} y1={py(tick)} y2={py(tick)} />
            <text className="deal-chart__tick" x={margin.left - 9} y={py(tick) + 4} textAnchor="end">{axisMoney(tick)}</text>
          </g>
        ))}
        {ticks(xMin, xMax, 5).map((tick) => (
          <g key={`x-${tick}`}>
            <line className="deal-chart__grid" x1={px(tick)} x2={px(tick)} y1={margin.top} y2={height - margin.bottom} />
            <text className="deal-chart__tick" x={px(tick)} y={height - margin.bottom + 19} textAnchor="middle">{tick.toFixed(1)}</text>
          </g>
        ))}
        {yMin < 0 && yMax > 0 && <line className="deal-chart__zero" x1={margin.left} x2={width - margin.right} y1={py(0)} y2={py(0)} />}
        {showFrontier && frontier.length > 1 && <polyline className="deal-frontier__line" points={line} />}
        {points.map((point, index) => {
          const isFrontier = frontierIds.has(point.id);
          const isSelected = point.id === selectedId;
          const x = px(point.x);
          const y = py(point.y);
          const anchor = x > width - 115 ? "end" : "start";
          const labelX = x + (anchor === "end" ? -9 : 9);
          const labelY = y + (index % 2 === 0 ? -9 : 14);
          return (
            <g
              key={point.id}
              className={`deal-point ${showFrontier && isFrontier ? "is-frontier" : ""} ${isSelected ? "is-selected" : ""}`}
            >
              <circle
                cx={x}
                cy={y}
                r={isSelected ? 7 : isFrontier ? 5.5 : 4.5}
                role="button"
                tabIndex={0}
                aria-label={`${point.label}: net incremental value ${compactMoney(point.y)}, conditional risk charge reduction ${point.x.toFixed(1)} basis points, residual charge ${point.residualCharge.toFixed(1)} basis points`}
                onClick={() => onSelect(point.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") onSelect(point.id);
                }}
              />
              {(!showFrontier || isFrontier || isSelected) && <text x={labelX} y={labelY} textAnchor={anchor}>{SHORT_LABEL[point.id] ?? point.label}</text>}
            </g>
          );
        })}
        <text className="deal-chart__axis-label" x={(margin.left + width - margin.right) / 2} y={height - 7} textAnchor="middle">Conditional risk charge reduction (bps) →</text>
        <text className="deal-chart__axis-label" transform={`translate(15 ${(margin.top + height - margin.bottom) / 2}) rotate(-90)`} textAnchor="middle">Counterparty-adjusted ΔNPV</text>
      </svg>
      <div className="deal-chart-legend" aria-hidden="true">
        {showFrontier && <span><i className="frontier" />efficient set</span>}<span><i className="selected" />selected</span><span><i />other candidate</span>
      </div>
      <p className="deal-chart-detail"><b>{selected.label}</b><span>ΔNPV {compactMoney(selected.y)}</span><span>charge reduction {selected.riskCut.toFixed(1)} bps</span><span>residual {selected.residualCharge.toFixed(1)} bps</span><span>project NPV {compactMoney(selected.projectNpv)}</span></p>
      <p className="panel__foot">Charge values use project commissioning from the model base year. They are not directly comparable with enterprise transition-window bps unless the result-contract basis IDs match.</p>
    </section>
  );
}

export function InvestmentCommitteePanel({ routeCase, selected, profile }: { routeCase: any; selected: any; profile: any }) {
  const econ = selected.economics;
  const npvPremium = econ.break_evens.required_green_premium_npv_usd_t;
  const dscrPremium = econ.break_evens.required_green_premium_dscr_usd_t;
  const required = Math.max(npvPremium, dscrPremium, 1);
  const annualCfads = econ.debt.dscr * econ.debt.annual_debt_service_usd_m;
  const debtShortfall = Math.max(0, econ.debt.target_dscr * econ.debt.annual_debt_service_usd_m - annualCfads);
  const feasibilityPass = routeCase.feasibility_status === "CONFIGURED_ROUTE";
  const gates = [
    ["Value", econ.investment.npv_positive ? "pass" : "fail", compactMoney(econ.investment.project_npv_usd_m)],
    ["Return", econ.investment.irr_pass ? "pass" : "fail", econ.investment.project_irr == null ? "IRR not earned" : `${(econ.investment.project_irr * 100).toFixed(1)}%`],
    ["Debt", econ.debt.dscr_pass ? "pass" : "fail", econ.debt.dscr <= 0 ? "CFADS < 0" : `${econ.debt.dscr.toFixed(2)}×`],
    ["Climate depth", routeCase.meets_configured_decarbonization_depth ? "pass" : "fail", `${econ.residual_intensity_tco2_t.toFixed(2)} tCO₂/t`],
    ["Technical case", feasibilityPass ? "pass" : "open", feasibilityPass ? "configured" : "diligence open"],
  ];

  return (
    <section className="panel deal-ic-panel">
      <div className="uw-panel-head">
        <div><p className="eyebrow">Investment committee gates</p><h2>What still blocks FID?</h2></div>
        <span className={`deal-ic-status ${econ.investment.decision === "INVESTABLE_SCREEN" ? "pass" : "fail"}`}>{econ.investment.decision === "INVESTABLE_SCREEN" ? "advance" : "hold"}</span>
      </div>
      <div className="deal-premium-gap">
        <div className="deal-premium-gap__head"><span>Required contracted premium</span><b>${required.toFixed(0)}/t</b></div>
        <div><span>NPV gate</span><i><em style={{ width: `${(npvPremium / required) * 100}%` }} /></i><b>${npvPremium.toFixed(0)}/t</b></div>
        <div><span>DSCR gate</span><i><em style={{ width: `${(dscrPremium / required) * 100}%` }} /></i><b>${dscrPremium.toFixed(0)}/t</b></div>
        <p>{npvPremium >= dscrPremium ? "Enterprise-value gate binds." : "Debt-service gate binds."} Current modeled premium: ${profile.green_premium_usd_t.toFixed(0)}/t.</p>
      </div>
      <div className="deal-gates">
        {gates.map(([label, state, value]) => (
          <div key={label}><span><i className={state} />{label}</span><b>{value}</b><em>{state}</em></div>
        ))}
      </div>
      <p className="panel__foot">Annual CFADS shortfall to the target DSCR is {compactMoney(debtShortfall)}. Gates are reported separately; CAP does not collapse them into one score.</p>
    </section>
  );
}

export function TechnologyAllocationMap({ firm, routeName, onRouteSelect }: { firm: any; routeName: string; onRouteSelect: (route: string) => void }) {
  const cases = firm.route_cases.map((routeCase: any) => ({ routeCase, best: bestCase(routeCase) }));
  const width = 680;
  const height = 315;
  const margin = { left: 68, right: 25, top: 30, bottom: 54 };
  const xMax = Math.max(...cases.map(({ best }: any) => best.economics.residual_intensity_tco2_t)) * 1.16;
  const yValues = cases.map(({ best }: any) => best.economics.investment.project_npv_usd_m).concat(0);
  const yMinRaw = Math.min(...yValues);
  const yMaxRaw = Math.max(...yValues);
  const yPad = Math.max((yMaxRaw - yMinRaw) * 0.08, 250);
  const yMin = yMinRaw - yPad;
  const yMax = yMaxRaw + yPad;
  const px = (value: number) => scale(value, 0, xMax, width - margin.right, margin.left);
  const py = (value: number) => scale(value, yMin, yMax, height - margin.bottom, margin.top);
  const configured = cases.find(({ routeCase }: any) => routeCase.is_configured_route)!;
  const depthThreshold = configured.best.economics.residual_intensity_tco2_t;
  const selected = cases.find(({ routeCase }: any) => routeCase.route === routeName) ?? configured;
  const capexValues = cases.map(({ best }: any) => best.economics.investment.capex_usd_m);
  const capexMin = Math.min(...capexValues);
  const capexMax = Math.max(...capexValues);

  return (
    <section className="panel deal-tech-map">
      <div className="uw-panel-head">
        <div><p className="eyebrow">Technology capital-allocation map</p><h2>Return, decarbonization depth and capital intensity</h2></div>
        <span className="deal-chart-direction">better ↗</span>
      </div>
      <svg className="deal-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="tech-map-title tech-map-desc">
        <title id="tech-map-title">Technology capital allocation map</title>
        <desc id="tech-map-desc">Best modeled project NPV against residual emissions intensity, with lower intensity plotted to the right. Bubble size represents capital expenditure. Upper-right routes are preferred.</desc>
        {ticks(yMin, yMax, 5).map((tick) => (
          <g key={`y-${tick}`}>
            <line className="deal-chart__grid" x1={margin.left} x2={width - margin.right} y1={py(tick)} y2={py(tick)} />
            <text className="deal-chart__tick" x={margin.left - 9} y={py(tick) + 4} textAnchor="end">{axisMoney(tick)}</text>
          </g>
        ))}
        {ticks(0, xMax, 5).map((tick) => (
          <g key={`x-${tick}`}>
            <line className="deal-chart__grid" x1={px(tick)} x2={px(tick)} y1={margin.top} y2={height - margin.bottom} />
            <text className="deal-chart__tick" x={px(tick)} y={height - margin.bottom + 19} textAnchor="middle">{tick.toFixed(2)}</text>
          </g>
        ))}
        {yMin < 0 && yMax > 0 && <line className="deal-chart__zero" x1={margin.left} x2={width - margin.right} y1={py(0)} y2={py(0)} />}
        <line className="deal-tech-map__depth" x1={px(depthThreshold)} x2={px(depthThreshold)} y1={margin.top} y2={height - margin.bottom} />
        <text className="deal-tech-map__depth-label" x={px(depthThreshold) - 6} y={margin.top + 8} textAnchor="end">configured depth</text>
        {cases.map(({ routeCase, best }: any, index: number) => {
          const x = px(best.economics.residual_intensity_tco2_t);
          const y = py(best.economics.investment.project_npv_usd_m);
          const radius = scale(best.economics.investment.capex_usd_m, capexMin, capexMax, 7, 14);
          const isSelected = routeCase.route === routeName;
          return (
            <g
              key={routeCase.route}
              className={`deal-tech-point ${routeCase.is_configured_route ? "is-configured" : ""} ${isSelected ? "is-selected" : ""}`}
            >
              <circle
                cx={x}
                cy={y}
                r={isSelected ? radius + 2 : radius}
                role="button"
                tabIndex={0}
                aria-label={`${routeCase.route}, NPV ${compactMoney(best.economics.investment.project_npv_usd_m)}, residual intensity ${best.economics.residual_intensity_tco2_t.toFixed(2)} tonnes CO2 per tonne`}
                onClick={() => onRouteSelect(routeCase.route)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") onRouteSelect(routeCase.route);
                }}
              />
              <text x={x + (index === 2 ? -10 : 10)} y={y - radius - 5} textAnchor={index === 2 ? "end" : "start"}>{routeCase.route.replaceAll("_", " ").toUpperCase()}</text>
            </g>
          );
        })}
        <text className="deal-chart__axis-label" x={(margin.left + width - margin.right) / 2} y={height - 7} textAnchor="middle">Decarbonization depth (lower residual intensity →)</text>
        <text className="deal-chart__axis-label" transform={`translate(15 ${(margin.top + height - margin.bottom) / 2}) rotate(-90)`} textAnchor="middle">Best modeled project NPV</text>
      </svg>
      <p className="deal-chart-detail"><b>{selected.routeCase.route.replaceAll("_", " ").toUpperCase()}</b><span>{selected.best.label}</span><span>NPV {compactMoney(selected.best.economics.investment.project_npv_usd_m)}</span><span>CAPEX {compactMoney(selected.best.economics.investment.capex_usd_m)}</span><span>premium ${selected.best.economics.break_evens.required_green_premium_usd_t.toFixed(0)}/t</span></p>
    </section>
  );
}

export function RiskTransferChart({ routeCase, selected }: { routeCase: any; selected: any }) {
  const colors = tokens.drivers as Record<string, string>;
  const before = routeCase.base.risk;
  const after = selected.risk;
  const riskCut = before.risk_charge_bps - after.risk_charge_bps;

  return (
    <section className="panel deal-risk-transfer">
      <div className="uw-panel-head">
        <div><p className="eyebrow">Risk-transfer anatomy</p><h2>What the selected term actually hedges</h2></div>
        <span className={riskCut >= 0 ? "uw-good" : "uw-bad"}>risk {riskCut >= 0 ? "−" : "+"}{Math.abs(riskCut).toFixed(1)} bps</span>
      </div>
      <div className="deal-risk-bars">
        {[{ label: "Unhedged", risk: before }, { label: "Selected", risk: after }].map(({ label, risk }) => (
          <div key={label}>
            <span>{label}</span>
            <i aria-label={`${label} risk anatomy`}>
              {DRIVERS.map((driver) => <em key={driver} style={{ width: `${(risk.shares[driver] ?? 0) * 100}%`, background: colors[driver] }} />)}
            </i>
            <b>{risk.risk_charge_bps.toFixed(1)} bps</b>
          </div>
        ))}
      </div>
      <div className="deal-risk-legend">
        {DRIVERS.map((driver) => (
          <div key={driver}><span><i style={{ background: colors[driver] }} />{DRIVER_LABEL[driver]}</span><b>{((before.shares[driver] ?? 0) * 100).toFixed(0)}% → {((after.shares[driver] ?? 0) * 100).toFixed(0)}%</b></div>
        ))}
      </div>
      <p className="panel__foot">Shares are marginal variance contributions, not emissions shares. A hedge can reduce total charge while concentrating the remaining exposure in another driver.</p>
    </section>
  );
}
