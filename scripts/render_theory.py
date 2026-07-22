"""make render-theory — 이론 md의 {{...}} 라이브 수치를 outputs/*.json에서 치환 (PLAN §4.2).

theory/*.md → web/content/theory/*.md. 미해결 {{키}}가 남으면 exit 1 —
"이론과 숫자가 어긋난 상태로는 빌드가 통과하지 않는다" (PLAN §4.3).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
THEORY = ROOT / "theory"
DEST = ROOT / "web" / "content" / "theory"

TEMPLATE = re.compile(r"\{\{([a-zA-Z0-9_.]+)\}\}")


def art(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


def pct(x: float, nd: int = 1) -> str:
    return f"{x * 100:.{nd}f}%"


def build_context() -> dict[str, str]:
    cal = art("calibration_resolved")
    shares = art("shares_by_firm")
    cvr = art("cost_vs_risk")
    inv = art("lambda_invariance")
    sep = art("cluster_separation")
    lam_k = art("lambda_k_sensitivity")
    stranding = art("stranding")
    wedge = art("wedge")
    dpi = art("delta_pi_ranking")
    manifest = json.loads((OUT / "manifest.json").read_text())

    ctx: dict[str, str] = {}
    sig = {r["driver"]: r for r in cal["sigmas"]}
    for d, r in sig.items():
        ctx[f"sigma.{d}"] = f"{r['value']:.2f}"
    ctx["sigma.carbon_reform"] = f"{cal['derived']['sigma_carbon_reform']:.2f}"
    ctx["derived.l_bar"] = f"{cal['derived']['l_bar']:.2f}"
    ctx["derived.l_bind"] = f"{cal['derived']['l_bind']:.2f}"
    for p, obj in cal["pricing"].items():
        ctx[f"pricing.{p}"] = f"{obj['value']:g}"
    ctx["scenarios.summary"] = " · ".join(
        f"{{{s['scenario']} ${s['level_usd']:g} · {s['prob']:.2f}}}" for s in cal["scenarios"]
    )
    ctx["gcam.source"] = cal["derived"]["t_gcam_source"]

    for f in shares["firms"]:
        for d, v in f["shares"].items():
            ctx[f"shares.{f['firm_id']}.{d}"] = f"{v:.3f}"
            ctx[f"shares.{f['firm_id']}.{d}_pct"] = pct(v)
        for d, v in f["shares_reform"].items():
            ctx[f"shares_reform.{f['firm_id']}.{d}"] = f"{v:.3f}"
            ctx[f"shares_reform.{f['firm_id']}.{d}_pct"] = pct(v)
    for f in cvr["firms"]:
        for d, v in f["cost_shares"].items():
            ctx[f"cost.{f['firm_id']}.{d}_pct"] = pct(v)
        for d, v in f["risk_shares"].items():
            ctx[f"risk.{f['firm_id']}.{d}_pct"] = pct(v)

    ctx["invariance.max_share_deviation"] = f"{inv['max_share_deviation']:.1e}"
    ctx["invariance.share_decimals"] = str(inv["share_invariant_to_decimals"])
    ctx["invariance.level_min_bps"] = f"{inv['level_min_bps']:.2f}"
    ctx["invariance.level_max_bps"] = f"{inv['level_max_bps']:.2f}"

    ctx["lambda_k.max_shift_pct"] = pct(max(f["max_shift"] for f in lam_k["firms"]))
    ctx["stranding.asset_ids"] = ", ".join(a["asset_id"] for a in stranding["assets"])

    wedges = [a["wedge_years"] for a in wedge["assets"] if a["wedge_years"] is not None]
    ctx["wedge.mean_years"] = f"{sum(wedges) / len(wedges):.1f}"
    ctx["lsm.p_bind_in_exercise"] = "ON" if json.loads((OUT / "tau_star.json").read_text())["p_bind_in_exercise"] else "OFF"

    def cluster_range(cluster: str, driver: str) -> str:
        vals = [f["shares"][driver] for f in shares["firms"] if f["cluster"] == cluster]
        return f"{pct(min(vals))}–{pct(max(vals))}" if len(vals) > 1 else pct(vals[0])

    ctx["cluster.h2_route.h2_range_pct"] = cluster_range("h2_route", "h2")
    ctx["cluster.h2_route.carbon_range_pct"] = cluster_range("h2_route", "carbon")
    ctx["cluster.grid_route.carbon_range_pct"] = cluster_range("grid_route", "carbon")
    all_carbon = [f["shares"]["carbon"] for f in shares["firms"]]
    ctx["cluster.all.carbon_range_pct"] = f"{pct(min(all_carbon))}–{pct(max(all_carbon))}"

    rows = ["| 기업 | π 미확약 (bps) | π 확약 (bps) | Δπ (bps) |", "|---|---|---|---|"]
    for r in dpi["ranking"]:
        rows.append(
            f"| {r['firm']} | {r['pi_uncommitted_bps']:.1f} | {r['pi_committed_bps']:.1f} | **{r['delta_pi_bps']:.1f}** |"
        )
    ctx["delta_pi.table"] = "\n".join(rows)
    ctx["manifest.config_sha"] = manifest["config_sha256"][:12]
    return ctx


def main() -> int:
    ctx = build_context()
    DEST.mkdir(parents=True, exist_ok=True)
    unresolved: list[str] = []
    for md in sorted(THEORY.glob("*.md")):
        text = md.read_text()

        def sub(m: re.Match) -> str:
            key = m.group(1)
            if key in ctx:
                return ctx[key]
            unresolved.append(f"{md.name}: {{{{{key}}}}}")
            return m.group(0)

        (DEST / md.name).write_text(TEMPLATE.sub(sub, text))
    if unresolved:
        print("FAIL — 미해결 라이브 수치 키:", file=sys.stderr)
        for u in unresolved:
            print(f"  {u}", file=sys.stderr)
        return 1
    print(f"OK — {len(list(THEORY.glob('*.md')))}개 문서 치환 → web/content/theory/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
