import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { provenanceMd } from "../../lib/data";

// /data — provenance 테이블 (DATA_PROVENANCE.md 렌더)
export default function DataPage() {
  return (
    <article style={{ lineHeight: 1.7, fontSize: 13, overflowX: "auto" }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{provenanceMd()}</ReactMarkdown>
    </article>
  );
}
