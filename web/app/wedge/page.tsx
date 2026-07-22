import { artifact } from "../../lib/data";
import WedgeView from "../../components/WedgeView";
import ConditionalNote from "../../components/ConditionalNote";

// /wedge — 고로별 덤벨 (Fig 2) + WACC-equalized 토글
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
    <>
      <h1>Wedge — τ* vs T_GCAM</h1>
      <p style={{ maxWidth: 720, lineHeight: 1.7 }}>
        Exposure_i = τ*_i − T_i^GCAM. 사적 최적 전환연도(LSM)가 시나리오 요구연도보다 늦은
        만큼이 노출이다 — "오늘 합리적, 내일 노출됨". T_GCAM 출처: {wedge.t_gcam_source}.
      </p>
      <WedgeView rows={rows} />
      <ConditionalNote conditional={wedge.conditional_on} />
    </>
  );
}
