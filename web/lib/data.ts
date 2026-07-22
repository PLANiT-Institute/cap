// 빌드타임 데이터 로더 — 웹은 계산하지 않는다. outputs/*.json만 읽는다.
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "..");
const OUT = path.join(ROOT, "outputs");

export function artifact<T = any>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(OUT, `${name}.json`), "utf-8"));
}

export function theoryDoc(slug: string): string {
  return fs.readFileSync(
    path.join(process.cwd(), "content", "theory", `${slug}.md`),
    "utf-8"
  );
}

export function theorySlugs(): string[] {
  return fs
    .readdirSync(path.join(process.cwd(), "content", "theory"))
    .filter((f) => f.endsWith(".md") && f !== "LEDGER.md")
    .map((f) => f.replace(/\.md$/, ""));
}

export function provenanceMd(): string {
  return fs.readFileSync(path.join(ROOT, "data", "DATA_PROVENANCE.md"), "utf-8");
}

export const DRIVER_LABELS: Record<string, string> = {
  carbon: "탄소정책 repricing",
  h2: "수소",
  elec: "전력",
  capex: "자본",
};
