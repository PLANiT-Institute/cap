import Link from "next/link";
import { artifact } from "../lib/data";
import { SharesStackedBar } from "../components/charts";
import ConditionalNote from "../components/ConditionalNote";

// / — 핵심 결과: 두 클러스터 100% 누적막대 (Fig 3) + 한 문단 요약
export default function Home() {
  const shares = artifact("shares_by_firm");
  const stranding = artifact("stranding");
  const sep = artifact("cluster_separation");
  const manifest = artifact("manifest");

  const rows = shares.firms.map((f: any) => ({
    name: f.firm,
    cluster: f.cluster,
    ...f.shares,
  }));

  return (
    <>
      <h1>프리미엄의 조성 (anatomy)</h1>
      <p style={{ maxWidth: 720, lineHeight: 1.7 }}>
        전환리스크 프리미엄의 <strong>수준(bps)</strong>은 λ·p_bind에 조건부지만,{" "}
        <strong>조성</strong>은 기업의 물리적 포지션(a)과 공분산(σ, ρ)만의 함수다 (Prop
        1). 아래 driver share는 두 클러스터로 갈린다 — 수소경제에 short인 H₂-route와
        그리드 전환에 short인 scrap/가스-route. 두 클러스터의 탄소 share 구간은{" "}
        {sep.separated ? "불교차" : "교차"} (gap {(sep.gap * 100).toFixed(1)}%p) —
        절반은 발견, 절반은 A4 배정의 귀결.
      </p>
      <SharesStackedBar rows={rows} />
      <ConditionalNote conditional={shares.conditional_on} />
      <p style={{ fontSize: 13, color: "#64748b" }}>
        stranding 분리 (no_feasible_route):{" "}
        {stranding.assets.map((a: any) => `${a.firm} ${a.facility} ${a.bf_number}`).join(", ")} —{" "}
        <Link href="/ledger">원장</Link> 참조. 기업별 상세:{" "}
        {shares.firms.map((f: any, i: number) => (
          <span key={f.firm_id}>
            {i > 0 && " · "}
            <Link href={`/anatomy/${f.firm_id}`}>{f.firm}</Link>
          </span>
        ))}
      </p>
      <p style={{ fontSize: 12, color: "#94a3b8" }}>
        config {manifest.config_sha256.slice(0, 12)} · seed {manifest.seed} · T_GCAM ={" "}
        {manifest.t_gcam_source}
      </p>
    </>
  );
}
