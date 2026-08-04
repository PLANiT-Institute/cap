"use client";

import tokens from "../tokens.json";

const DRIVER_LABEL: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  feedstock: "Feedstock",
  capex: "Capital cost",
  financing: "Financing",
};

function scale(value: number, d0: number, d1: number, r0: number, r1: number) {
  if (d0 === d1) return (r0 + r1) / 2;
  return r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);
}

function ticks(min: number, max: number, count = 5) {
  return Array.from({ length: count }, (_, index) => min + ((max - min) * index) / (count - 1));
}

export function InvestorPortfolioMap({
  portfolio,
  selectedFirmId,
  onSelect,
}: {
  portfolio: any[];
  selectedFirmId: string;
  onSelect: (firmId: string) => void;
}) {
  const width = 760;
  const height = 338;
  const margin = { left: 64, right: 34, top: 30, bottom: 54 };
  const xs = portfolio.map((row) => row.cumulative_alignment_gap_mtco2);
  const ys = portfolio.map((row) => row.spread_bps);
  const charges = portfolio.map((row) => row.annual_risk_charge_usd_m);
  const xRawMin = Math.min(...xs);
  const xRawMax = Math.max(...xs);
  const yRawMin = Math.min(...ys);
  const yRawMax = Math.max(...ys);
  const xPad = Math.max((xRawMax - xRawMin) * 0.16, 2);
  const yPad = Math.max((yRawMax - yRawMin) * 0.16, 1);
  const xMin = Math.max(0, xRawMin - xPad);
  const xMax = xRawMax + xPad;
  const yMin = Math.max(0, yRawMin - yPad);
  const yMax = yRawMax + yPad;
  const chargeMin = Math.min(...charges);
  const chargeMax = Math.max(...charges);
  const px = (value: number) => scale(value, xMin, xMax, margin.left, width - margin.right);
  const py = (value: number) => scale(value, yMin, yMax, height - margin.bottom, margin.top);

  return (
    <section className="panel sector-portfolio-map">
      <div className="uw-panel-head">
        <div><p className="eyebrow">Sector allocation map</p><h2>Financial risk vs climate alignment gap</h2></div>
        <span className="deal-chart-direction">lower-left is lighter risk</span>
      </div>
      <svg className="deal-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="sector-map-title sector-map-desc">
        <title id="sector-map-title">Sector transition-risk allocation map</title>
        <desc id="sector-map-desc">Cumulative alignment gap on the horizontal axis, conditional risk charge on the vertical axis, and annual charge equivalent shown by bubble size.</desc>
        {ticks(yMin, yMax).map((tick) => (
          <g key={`y-${tick}`}>
            <line className="deal-chart__grid" x1={margin.left} x2={width - margin.right} y1={py(tick)} y2={py(tick)} />
            <text className="deal-chart__tick" x={margin.left - 9} y={py(tick) + 4} textAnchor="end">{tick.toFixed(1)}</text>
          </g>
        ))}
        {ticks(xMin, xMax).map((tick) => (
          <g key={`x-${tick}`}>
            <line className="deal-chart__grid" x1={px(tick)} x2={px(tick)} y1={margin.top} y2={height - margin.bottom} />
            <text className="deal-chart__tick" x={px(tick)} y={height - margin.bottom + 19} textAnchor="middle">{tick.toFixed(0)}</text>
          </g>
        ))}
        {portfolio.map((row, index) => {
          const x = px(row.cumulative_alignment_gap_mtco2);
          const y = py(row.spread_bps);
          const radius = scale(row.annual_risk_charge_usd_m, chargeMin, chargeMax, 7, 15);
          const selected = row.firm_id === selectedFirmId;
          const rightSide = x > width - 150;
          return (
            <g key={row.firm_id} className={`sector-portfolio-point is-${row.sector} ${selected ? "is-selected" : ""}`}>
              <circle
                cx={x}
                cy={y}
                r={selected ? radius + 2 : radius}
                role="button"
                tabIndex={0}
                aria-label={`${row.firm}, ${row.sector}, cumulative alignment gap ${row.cumulative_alignment_gap_mtco2.toFixed(1)} million tonnes CO2, conditional risk charge ${row.spread_bps.toFixed(1)} basis points`}
                onClick={() => onSelect(row.firm_id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") onSelect(row.firm_id);
                }}
              />
              <text x={x + (rightSide ? -radius - 5 : radius + 5)} y={y + (index % 2 ? 12 : -7)} textAnchor={rightSide ? "end" : "start"}>{row.firm}</text>
            </g>
          );
        })}
        <text className="deal-chart__axis-label" x={(margin.left + width - margin.right) / 2} y={height - 7} textAnchor="middle">Cumulative alignment gap (MtCO₂) →</text>
        <text className="deal-chart__axis-label" transform={`translate(15 ${(margin.top + height - margin.bottom) / 2}) rotate(-90)`} textAnchor="middle">Conditional charge (bps) →</text>
      </svg>
      <div className="sector-map-legend" aria-hidden="true">
        {/* W1: archetype 여부는 섹터명 하드코딩이 아니라 artifact의 headline_eligible로 판정 */}
        <span><i className={portfolio[0]?.headline_eligible === false ? "petro" : "steel"} />{portfolio[0]?.headline_eligible === false ? `${portfolio[0]?.sector} · archetypes (not headline)` : portfolio[0]?.sector ?? "steel"}</span>
        <span>bubble area ≈ annual charge equivalent</span>
      </div>
    </section>
  );
}

export function ContractCoverageLadder({
  options,
  selectedId,
  onSelect,
}: {
  options: any[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const lanes = options.filter((option) => option.applicable && option.terms.operation !== "combine");
  const width = 760;
  const margin = { left: 186, right: 30, top: 42, bottom: 34 };
  const rowHeight = 42;
  const height = margin.top + margin.bottom + lanes.length * rowHeight;
  const minYear = Math.min(...lanes.map((option) => option.terms.start_year));
  const maxYear = Math.max(...lanes.map((option) => option.terms.end_year));
  const px = (year: number) => scale(year, minYear, maxYear, margin.left, width - margin.right);
  const colors = tokens.drivers as Record<string, string>;

  return (
    <section className="panel contract-ladder">
      <div className="uw-panel-head">
        <div><p className="eyebrow">Coverage and maturity ladder</p><h2>Where certainty expires before the asset does</h2></div>
        <span className="tag tag--sample">modeled terms</span>
      </div>
      <svg className="deal-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="ladder-title ladder-desc">
        <title id="ladder-title">Contract coverage and maturity ladder</title>
        <desc id="ladder-desc">Each lane shows the modeled start, end and coverage share for a route-applicable contract, grant, policy or financing instrument.</desc>
        {ticks(minYear, maxYear, 6).map((tick) => (
          <g key={tick}>
            <line className="contract-ladder__grid" x1={px(tick)} x2={px(tick)} y1={margin.top - 12} y2={height - margin.bottom + 4} />
            <text className="deal-chart__tick" x={px(tick)} y={margin.top - 20} textAnchor="middle">{Math.round(tick)}</text>
          </g>
        ))}
        {lanes.map((option, index) => {
          const y = margin.top + index * rowHeight + rowHeight / 2;
          const target = option.terms.targets[0] ?? "financing";
          const color = colors[target] ?? tokens.palette.slate;
          const selected = option.intervention_id === selectedId;
          return (
            <g key={option.intervention_id} className={`contract-ladder__lane ${selected ? "is-selected" : ""}`}>
              <text className="contract-ladder__label" x={margin.left - 12} y={y - 3} textAnchor="end">{option.label}</text>
              <text className="contract-ladder__target" x={margin.left - 12} y={y + 12} textAnchor="end">{option.terms.targets.map((driver: string) => DRIVER_LABEL[driver] ?? driver).join(" + ")}</text>
              <line className="contract-ladder__track" x1={margin.left} x2={width - margin.right} y1={y} y2={y} />
              <rect
                x={px(option.terms.start_year)}
                y={y - 7}
                width={Math.max(3, px(option.terms.end_year) - px(option.terms.start_year))}
                height={14}
                rx={3}
                style={{ fill: color }}
                role="button"
                tabIndex={0}
                aria-label={`${option.label}, ${option.terms.start_year} to ${option.terms.end_year}, ${(option.terms.coverage * 100).toFixed(0)} percent modeled coverage`}
                onClick={() => onSelect(option.intervention_id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") onSelect(option.intervention_id);
                }}
              />
              <text className="contract-ladder__coverage" x={Math.min(width - margin.right - 3, px(option.terms.end_year) + 7)} y={y + 4}>{(option.terms.coverage * 100).toFixed(0)}%</text>
            </g>
          );
        })}
      </svg>
      <p className="panel__foot">Coverage is the model transformation share, not a quoted hedge ratio. Bars end where basis and spot exposure return.</p>
    </section>
  );
}
