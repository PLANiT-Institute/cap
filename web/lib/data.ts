// Build-time data loader — the site computes nothing; it renders outputs/*.json.
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "..");
const OUT = path.join(ROOT, "outputs");

export function artifact<T = any>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(OUT, `${name}.json`), "utf-8"));
}
