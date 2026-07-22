import { artifact } from "../../lib/data";
import WedgeView from "../../components/WedgeView";
import ConditionalNote from "../../components/ConditionalNote";

export default function WedgePage() {
  const wedge = artifact("wedge");
  const rows = wedge.assets.map((a: any) => ({
    asset: `${a.asset_id} ${a.firm}`,
    t_gcam: a.t_gcam,
    tau_star: a.tau_star_year,
    tau_star_eq: a.tau_star_year_wacc_eq,
    category: a.category,
  }));
  return (
    <main className="page">
      <h1>The wedge — τ* vs T_GCAM</h1>
      <p style={{ maxWidth: 680, color: "#475569" }}>
        Exposure_i = τ*_i − T_i^GCAM. Each furnace's privately optimal switch year (least-squares
        Monte Carlo) against the year the net-zero scenario requires it. Waiting past the required
        date is rational for the firm — and is exactly what the premium prices. "Rational today,
        exposed tomorrow." T_GCAM source: {wedge.t_gcam_source}.
      </p>
      <WedgeView rows={rows} />
      <ConditionalNote conditional={wedge.conditional_on} />
    </main>
  );
}
