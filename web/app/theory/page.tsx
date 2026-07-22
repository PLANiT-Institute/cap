import Link from "next/link";
import { theorySlugs } from "../../lib/data";

const TITLES: Record<string, string> = {
  "00_axioms": "00 — Purpose & axiom index",
  "01_wedge": "01 — Why exposure exists (the wedge)",
  "02_variance_premium": "02 — Risk is variance, not mean",
  "03_proposition1": "03 — Proposition 1: level vs composition",
  "04_carbon_jump": "04 — Carbon driver: diffusion + policy jump",
  "05_contracts_identification": "05 — Contracts as identification",
  "06_allocator_reading": "06 — The allocator's reading",
  "07_ledger_logic": "07 — Ledger logic",
  "08_referee_notes": "08 — Known challenges (referee notes)",
  "09_contribution": "09 — Intellectual lineage",
};

export default function TheoryIndex() {
  return (
    <main className="page">
      <h1>Method</h1>
      <p style={{ maxWidth: 680, color: "#475569", fontSize: 14 }}>
        The research documentation is written in Korean and is part of the build system: every axiom
        carries an anchor ID that the calibration config must reference, and every computed figure
        in the text is injected live from model output — the documents cannot drift from the
        numbers. English translation is planned with the paper.
      </p>
      <ul style={{ lineHeight: 2 }}>
        {theorySlugs().map((s) => (
          <li key={s}>
            <Link href={`/theory/${s}`}>{TITLES[s] ?? s}</Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
