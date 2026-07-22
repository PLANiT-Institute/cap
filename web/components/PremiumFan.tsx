// Server component — the investor hero. Built from outputs/lambda_invariance.json:
// the premium level fans out with the price of risk (λ·p_bind), while the driver
// mix inside the fan keeps constant proportions (Prop 1). Size = bet, mix = fact.
import tokens from "../tokens.json";

const DRIVERS = ["carbon", "h2", "elec", "capex"] as const;
const LABELS: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  capex: "Capital",
};

export default function PremiumFan({
  grid,
  shares,
  firm,
  baseCase,
}: {
  grid: { lambda: number; p_bind: number; premium_bps: number }[];
  shares: Record<string, number>;
  firm: string;
  baseCase: { lambda: number; p_bind: number; premium_bps: number };
}) {
  const W = 560;
  const H = 360;
  const PAD = { l: 46, r: 118, t: 30, b: 46 };
  const pts = [...grid]
    .map((g) => ({ x: g.lambda * g.p_bind, y: g.premium_bps }))
    .sort((a, b) => a.x - b.x);
  const xMin = pts[0].x;
  const xMax = pts[pts.length - 1].x;
  const yMax = pts[pts.length - 1].y * 1.06;
  const X = (v: number) => PAD.l + ((v - xMin) / (xMax - xMin)) * (W - PAD.l - PAD.r);
  const Y = (v: number) => H - PAD.b - (v / yMax) * (H - PAD.t - PAD.b);

  // stacked layers: cumulative share × total premium at each x (proportions constant)
  const order = DRIVERS.filter((d) => shares[d] > 1e-9);
  const cum: Record<string, [number, number]> = {};
  let acc = 0;
  for (const d of order) {
    cum[d] = [acc, acc + shares[d]];
    acc += shares[d];
  }
  const layerPath = (d: string) => {
    const [lo, hi] = cum[d];
    const top = pts.map((p) => `${X(p.x).toFixed(1)},${Y(p.y * hi).toFixed(1)}`);
    const bot = [...pts].reverse().map((p) => `${X(p.x).toFixed(1)},${Y(p.y * lo).toFixed(1)}`);
    return `M${top.join(" L")} L${bot.join(" L")} Z`;
  };

  const colors = tokens.drivers as Record<string, string>;
  // fills stay token colors; labels need dark-bg legible variants
  const labelColors: Record<string, string> = {
    carbon: "#7fa3d0",
    h2: "#5cb8c9",
    elec: "#f0a24a",
    capex: "#a8b6c8",
  };
  const baseX = X(baseCase.lambda * baseCase.p_bind);
  const swing = (pts[pts.length - 1].y / pts[0].y).toFixed(0);

  return (
    <figure style={{ margin: 0 }}>
      <svg
        className="fan"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${firm}'s transition-risk premium fans from ${pts[0].y.toFixed(1)} to ${pts[pts.length - 1].y.toFixed(1)} basis points depending on the assumed price of risk — a ${swing}-fold swing — while the mix of drivers inside stays fixed.`}
        style={{ width: "100%", height: "auto" }}
      >
        {/* y grid */}
        {[10, 20, 30, 40].map((g) =>
          g < yMax ? (
            <g key={g}>
              <line x1={PAD.l} x2={W - PAD.r} y1={Y(g)} y2={Y(g)} stroke="rgba(255,255,255,0.08)" />
              <text x={PAD.l - 8} y={Y(g) + 4} fontSize="10" fill="#64748b" textAnchor="end">
                {g}
              </text>
            </g>
          ) : null
        )}
        {/* stacked fan, revealed left→right */}
        <g className="fan-reveal">
          {order.map((d) => (
            <path key={d} d={layerPath(d)} fill={colors[d]} opacity={0.92} />
          ))}
        </g>
        {/* base case marker */}
        <g className="fan-late">
          <line x1={baseX} x2={baseX} y1={Y(baseCase.premium_bps)} y2={H - PAD.b} stroke="#f59e0b" strokeDasharray="4 4" strokeWidth="1.4" />
          <circle cx={baseX} cy={Y(baseCase.premium_bps)} r="4" fill="#f59e0b" />
          <text x={baseX} y={Y(baseCase.premium_bps) - 10} fontSize="11" fill="#f59e0b" textAnchor="middle">
            base case {baseCase.premium_bps.toFixed(1)} bps
          </text>
        </g>
        {/* right-edge mix labels — only slices big enough to name; collision-spaced */}
        <g className="fan-late">
          {(() => {
            const labeled = order.filter((d) => shares[d] >= 0.02);
            const yTop = pts[pts.length - 1].y;
            let prevY = Infinity;
            return labeled
              .slice()
              .reverse() // top of stack first
              .map((d) => {
                const [lo, hi] = cum[d];
                let yMid = Y((yTop * (lo + hi)) / 2) + 4;
                if (prevY !== Infinity && yMid - prevY < 14) yMid = prevY + 14; // push down
                prevY = yMid;
                return (
                  <text key={d} x={W - PAD.r + 10} y={yMid} fontSize="11" fill={labelColors[d]}>
                    {LABELS[d]} {(shares[d] * 100).toFixed(0)}%
                  </text>
                );
              });
          })()}
          <text x={W - PAD.r + 10} y={Y(pts[pts.length - 1].y) - 16} fontSize="10" fill="#94a3b8">
            mix: proven, fixed
          </text>
        </g>
        {/* axes */}
        <text x={PAD.l} y={H - 26} fontSize="10.5" fill="#64748b">
          conservative
        </text>
        <text x={W - PAD.r} y={H - 26} fontSize="10.5" fill="#64748b" textAnchor="end">
          stressed
        </text>
        <text x={(PAD.l + W - PAD.r) / 2} y={H - 10} fontSize="10.5" fill="#94a3b8" textAnchor="middle">
          λ × p_bind — how dearly the market prices this risk
        </text>
        <text x={PAD.l - 34} y={PAD.t - 10} fontSize="10.5" fill="#94a3b8">
          bps
        </text>
      </svg>
      <figcaption className="mono" style={{ fontSize: 11, color: "#64748b", marginTop: 6 }}>
        {firm}. Level swings ×{swing} with the assumed price of risk — the mix of drivers does not
        move (Prop 1). Every firm carries the same proof.
      </figcaption>
    </figure>
  );
}
