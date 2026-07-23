"use client";
// ① 첫 화면 — 감축경로: BAU / private / required / intervention + gap 음영.
// SVG 직접 렌더 (계산 없음 — outputs 값 그대로).
import { useState } from "react";

const COLORS: Record<string, string> = {
  bau: "#64748b",
  private: "#7fa3d0",
  required: "#f59e0b",
  intervention: "#4ade80",
};

export default function PathwayPanel({
  firm,
  years,
  selectedIv,
  provisional,
  singleAsset,
}: {
  firm: any;
  years: number[];
  selectedIv: string | null;
  provisional: boolean;
  singleAsset?: any;
}) {
  const [indexMode, setIndexMode] = useState(false);
  const [tip, setTip] = useState<number | null>(null);
  const P = firm.pathways;
  const key = indexMode ? "emissions_index_base100" : "emissions_mtco2";
  const seriesOf = (p: any) => p[key] as number[];
  const tracks: [string, number[]][] = [
    ["bau", seriesOf(P.bau)],
    ["private", seriesOf(P.private)],
    ["required", seriesOf(P.required)],
  ];
  if (selectedIv && P.interventions[selectedIv]) {
    tracks.push(["intervention", seriesOf(P.interventions[selectedIv])]);
  }
  const W = 860;
  const H = 340;
  const PAD = { l: 48, r: 16, t: 16, b: 30 };
  const yMax = Math.max(...tracks.flatMap(([, s]) => s)) * 1.05;
  const X = (i: number) => PAD.l + (i / (years.length - 1)) * (W - PAD.l - PAD.r);
  const Y = (v: number) => H - PAD.b - (v / yMax) * (H - PAD.t - PAD.b);
  const line = (s: number[]) =>
    s.map((v, i) => `${i === 0 ? "M" : "L"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");

  const priv = seriesOf(P.private);
  const req = seriesOf(P.required);
  const gapPoly =
    line(priv) +
    " " +
    [...req].reverse().map((v, i) => `L${X(req.length - 1 - i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ") +
    " Z";

  const ti = tip !== null ? tip : null;

  if (singleAsset) {
    const minYear = years[0];
    const maxYear = years[years.length - 1];
    const position = (year: number | null | undefined) =>
      year == null ? 100 : ((Math.min(Math.max(year, minYear), maxYear) - minYear) / (maxYear - minYear)) * 100;
    const interventionYear = selectedIv ? singleAsset.tau_interventions?.[selectedIv] : null;
    const lanes = [
      { label: "Required pathway", year: singleAsset.t_required, className: "required" },
      { label: "Private optimum", year: singleAsset.tau_star_year, className: "private" },
      ...(selectedIv ? [{ label: `With ${selectedIv}`, year: interventionYear, className: "intervention" }] : []),
    ];
    return (
      <div className="pw-single">
        <div className="pw-ctls">
          <span>Single-asset pathway · timeline view</span>
          {provisional && <span className="tag tag--sample">REQUIRED: PROVISIONAL</span>}
        </div>
        <div className="pw-single__axis mono">
          {[2030, 2040, 2050, 2060].filter((year) => year >= minYear && year <= maxYear).map((year) => (
            <span key={year} style={{ left: `${position(year)}%` }}>{year}</span>
          ))}
        </div>
        <div className="pw-single__lanes">
          {lanes.map((lane) => (
            <div key={lane.label} className={`pw-single__lane is-${lane.className}`}>
              <span>{lane.label}</span>
              <div>
                <i style={{ width: `${position(lane.year)}%` }} />
                {lane.year != null ? (
                  <b className="mono" style={{ left: `${position(lane.year)}%` }}>{lane.year.toFixed(0)}</b>
                ) : (
                  <em>no transition in horizon</em>
                )}
              </div>
            </div>
          ))}
        </div>
        <p className="pw-single__note">
          {singleAsset.facility} is one modeled archetype ({singleAsset.capacity_mt.toFixed(1)} Mt,
          {" "}{singleAsset.intensity_tco2_t.toFixed(2)} tCO₂/t). A timeline is shown instead of a
          stepped emissions curve because there is no portfolio aggregation to interpret.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="pw-ctls">
        <label>
          <input type="checkbox" checked={indexMode} onChange={(e) => setIndexMode(e.target.checked)} />{" "}
          index (2026 = 100)
        </label>
        {provisional && (
          <span className="tag tag--sample" title="Required pathway is a provisional surrogate and must not be interpreted as an empirically identified firm mandate.">
            REQUIRED: PROVISIONAL
          </span>
        )}
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: "100%", height: "auto" }}
        onMouseLeave={() => setTip(null)}
        onMouseMove={(e) => {
          const rect = (e.target as SVGElement).closest("svg")!.getBoundingClientRect();
          const frac = (e.clientX - rect.left) / rect.width;
          const i = Math.round(((frac * W - PAD.l) / (W - PAD.l - PAD.r)) * (years.length - 1));
          setTip(Math.min(Math.max(i, 0), years.length - 1));
        }}
        role="img"
        aria-label={`Emission pathways for ${firm.firm}: business-as-usual, privately optimal, required, and intervention.`}
      >
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line x1={PAD.l} x2={W - PAD.r} y1={Y(yMax * f)} y2={Y(yMax * f)} stroke="rgba(255,255,255,0.07)" />
            <text x={PAD.l - 6} y={Y(yMax * f) + 4} fontSize="10" fill="#64748b" textAnchor="end" className="mono">
              {(yMax * f).toFixed(indexMode ? 0 : 1)}
            </text>
          </g>
        ))}
        {years.filter((y) => y % 10 === 0).map((y) => (
          <text key={y} x={X(years.indexOf(y))} y={H - 10} fontSize="10" fill="#64748b" textAnchor="middle" className="mono">
            {y}
          </text>
        ))}
        <path d={gapPoly} fill="rgba(217,119,6,0.16)" />
        {tracks.map(([k, s]) => (
          <path
            key={k}
            d={line(s)}
            fill="none"
            stroke={COLORS[k]}
            strokeWidth={k === "bau" ? 1.5 : 2.2}
            strokeDasharray={k === "bau" ? "5 4" : undefined}
          />
        ))}
        {ti !== null && (
          <g>
            <line x1={X(ti)} x2={X(ti)} y1={PAD.t} y2={H - PAD.b} stroke="rgba(255,255,255,0.25)" />
            {tracks.map(([k, s]) => (
              <circle key={k} cx={X(ti)} cy={Y(s[ti])} r={3.5} fill={COLORS[k]} />
            ))}
          </g>
        )}
      </svg>
      {ti !== null && (
        <div className="pw-tip">
          <b>{years[ti]}</b>
          {tracks.map(([k, s]) => (
            <span key={k} style={{ color: COLORS[k] }}>
              {k} {s[ti].toFixed(indexMode ? 0 : 2)}
            </span>
          ))}
          <span>
            annual gap {Math.max(priv[ti] - req[ti], 0).toFixed(2)}
            {indexMode ? "" : " Mt"}
          </span>
          <span>
            transitioned {P.private.transitioned_capacity_mt[ti].toFixed(1)} Mt · cum gap{" "}
            {firm.cum_gap_by_year?.[ti]?.toFixed(0) ?? "—"} Mt
          </span>
        </div>
      )}
      <div className="pw-legend">
        <span style={{ color: COLORS.bau }}>— — BAU</span>
        <span style={{ color: COLORS.private }}>— private optimal (τ*)</span>
        <span style={{ color: COLORS.required }}>— required (T_required)</span>
        {selectedIv && <span style={{ color: COLORS.intervention }}>— with {selectedIv}</span>}
        <span style={{ color: "#b45309" }}>▨ alignment gap</span>
      </div>
    </div>
  );
}
