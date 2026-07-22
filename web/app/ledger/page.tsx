import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { theoryDoc } from "../../lib/data";
import StatusBadge from "../../components/StatusBadge";

// /ledger — proven/conditional 원장 (config status에서 자동 생성된 LEDGER.md 렌더)
export default function LedgerPage() {
  const md = theoryDoc("LEDGER");
  return (
    <>
      <p style={{ fontSize: 13 }}>
        범례: <StatusBadge status="measured" />
        <StatusBadge status="banded" />
        <StatusBadge status="assumed" />
      </p>
      <article style={{ lineHeight: 1.75, maxWidth: 820 }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
      </article>
    </>
  );
}
