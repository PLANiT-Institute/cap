import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { theoryDoc } from "../../lib/data";
import StatusBadge from "../../components/StatusBadge";

// /ledger — proven vs conditional, generated from config status columns
export default function LedgerPage() {
  const md = theoryDoc("LEDGER");
  return (
    <main className="page">
      <h1>Proven vs conditional</h1>
      <p style={{ maxWidth: 680, color: "#475569", fontSize: 14 }}>
        One rule, enforced as a data structure: the composition of the premium is proven (invariant
        to the market price of risk λ and the budget-binding probability); absolute basis points are
        conditional and always labeled. Status flows from the calibration workbook to every chart on
        this site. The ledger below is machine-generated from config — the annex is in Korean, as is
        the research documentation.
      </p>
      <p style={{ fontSize: 13 }}>
        Legend: <StatusBadge status="measured" /> <StatusBadge status="banded" />{" "}
        <StatusBadge status="assumed" />
      </p>
      <article style={{ lineHeight: 1.75 }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
      </article>
    </main>
  );
}
