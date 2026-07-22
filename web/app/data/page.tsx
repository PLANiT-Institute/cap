import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { artifact, provenanceMd } from "../../lib/data";
import StatusBadge from "../../components/StatusBadge";

// /data — 연단위 레퍼런스 가격 + provenance 테이블
export default function DataPage() {
  const ref = artifact("reference_prices");
  return (
    <>
      <h1>레퍼런스 가격 (연단위)</h1>
      <p style={{ maxWidth: 720, fontSize: 14 }}>
        모델 파라미터가 아니다 — CAP은 계산기이고, 가격 수준·경로는 시나리오(config)가
        구동한다. 아래는 대조용 실측 레퍼런스.
      </p>
      <h2 style={{ fontSize: 16 }}>
        KAU (탄소, KR) <StatusBadge status="measured" />
      </h2>
      <table style={{ borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            {["연도", "평균 KRW/t", "평균 USD/t", "관측"].map((h) => (
              <th key={h} style={{ textAlign: "right", padding: "3px 12px", borderBottom: "1px solid #cbd5e1" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ref.carbon_kr_annual.map((r: any) => (
            <tr key={r.year}>
              <td style={{ textAlign: "right", padding: "2px 12px" }}>{r.year}</td>
              <td style={{ textAlign: "right", padding: "2px 12px" }}>{r.mean_krw.toLocaleString()}</td>
              <td style={{ textAlign: "right", padding: "2px 12px" }}>{r.mean_usd}</td>
              <td style={{ textAlign: "right", padding: "2px 12px" }}>{r.n_obs}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ fontSize: 12, color: "#64748b" }}>{ref.carbon_source}</p>
      <h2 style={{ fontSize: 16 }}>
        전력 (기준 수준) <StatusBadge status="banded" />
      </h2>
      <ul style={{ fontSize: 13 }}>
        {ref.elec_base.map((e: any) => (
          <li key={e.series}>
            {e.series}: {e.base_2026_usd_mwh} USD/MWh — {e.source} <em>({e.note})</em>
          </li>
        ))}
      </ul>
      <hr style={{ margin: "24px 0", border: "none", borderTop: "1px solid #cbd5e1" }} />
      <article style={{ lineHeight: 1.7, fontSize: 13, overflowX: "auto" }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{provenanceMd()}</ReactMarkdown>
      </article>
    </>
  );
}
