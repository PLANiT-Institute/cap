// Server component — hand-built SVG from outputs/emission_pathway.json.
// CSS draws the two paths on load (globals.css .pathway), no chart lib.
export default function PathwayChart({
  pathway,
}: {
  pathway: { years: number[]; bau_index: number[]; nz_index: number[]; source: string };
}) {
  const W = 520;
  const H = 330;
  const PAD = { l: 44, r: 16, t: 24, b: 34 };
  const years = pathway.years;
  const x = (yr: number) =>
    PAD.l + ((yr - years[0]) / (years[years.length - 1] - years[0])) * (W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + ((110 - v) / 110) * (H - PAD.t - PAD.b);

  const line = (vals: number[]) =>
    vals.map((v, i) => `${i === 0 ? "M" : "L"}${x(years[i]).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  const wedgePoly =
    line(pathway.bau_index) +
    " " +
    pathway.nz_index
      .map((v, i, a) => {
        const j = a.length - 1 - i;
        return `L${x(years[j]).toFixed(1)},${y(a[j]).toFixed(1)}`;
      })
      .join(" ") +
    " Z";

  const ticks = years.filter((yr) => yr % 10 === 0 || yr === years[0]);

  return (
    <figure style={{ margin: 0 }}>
      <svg
        className="pathway"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Sector emission index: business-as-usual stays at 100 while the net-zero-consistent pathway falls toward 27 by 2061. The shaded area between them is the exposure this model prices."
        style={{ width: "100%", height: "auto" }}
      >
        {[100, 75, 50, 25].map((g) => (
          <g key={g}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(g)} y2={y(g)} stroke="rgba(255,255,255,0.08)" />
            <text x={PAD.l - 8} y={y(g) + 4} fontSize="10" fill="#64748b" textAnchor="end">
              {g}
            </text>
          </g>
        ))}
        {ticks.map((yr) => (
          <text key={yr} x={x(yr)} y={H - 12} fontSize="10" fill="#64748b" textAnchor="middle">
            {yr}
          </text>
        ))}
        <path className="wedge-fill" d={wedgePoly} fill="rgba(217,119,6,0.14)" />
        <path className="draw" d={line(pathway.bau_index)} pathLength={1} fill="none" stroke="#94a3b8" strokeWidth="2" strokeDasharray="5 4" />
        <path className="draw draw--delay" d={line(pathway.nz_index)} pathLength={1} fill="none" stroke="#f59e0b" strokeWidth="2.5" />
        <text x={W - PAD.r} y={y(100) - 8} fontSize="11" fill="#94a3b8" textAnchor="end">
          business as usual
        </text>
        <text x={W - PAD.r} y={y(pathway.nz_index[pathway.nz_index.length - 1]) - 10} fontSize="11" fill="#f59e0b" textAnchor="end">
          required pathway
        </text>
        <text x={x(2046)} y={y(65)} fontSize="11" fill="#e8edf5" textAnchor="middle" fontStyle="italic">
          the exposure
        </text>
      </svg>
      <figcaption className="mono" style={{ fontSize: 11, color: "#64748b", marginTop: 6 }}>
        Sector emission index (2026 = 100). Required pathway from GCAM deployment curve ({pathway.source}).
      </figcaption>
    </figure>
  );
}
