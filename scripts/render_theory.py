"""make render-theory — 이론 md의 {{...}} 라이브 수치를 outputs/*.json에서 치환.

미해결 {{키}}가 남으면 exit 1 — 이론과 숫자가 어긋난 상태로는 빌드가 통과하지 않는다.
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
    lam_k = art("lambda_k_sensitivity")
    stranding = art("stranding")
    gaps = art("condition_gap")
    imp = art("intervention_impacts")
    manifest = art("manifest")

    ctx: dict[str, str] = {}
    for r in cal["sigmas"]:
        ctx[f"sigma.{r['driver']}"] = f"{r['value']:.2f}"
    d = cal["derived"]
    for c in ("KR", "JP"):
        lc = c.lower()
        ctx[f"sigma.carbon_reform_{lc}"] = f"{d['sigma_carbon_reform'][c]:.2f}"
        ctx[f"sigma.carbon_binding_{lc}"] = f"{d['sigma_carbon_binding'][c]:.2f}"
        ctx[f"derived.l_bind_{lc}"] = f"{d['l_bind'][c]:.1f}"
        ctx[f"derived.p_bind_{lc}"] = f"{d['p_bind'][c]:.2f}"
        ctx[f"derived.jump_share_{lc}"] = pct(
            d["carbon_variance_decomposition"][c]["binding_conditional_jump_share"], 0
        )
        ctx[f"derived.unconditional_jump_share_{lc}"] = pct(
            d["carbon_variance_decomposition"][c]["unconditional_jump_share"], 0
        )
    for p, obj in cal["pricing"].items():
        ctx[f"pricing.{p}"] = f"{obj['value']:g}"

    def scen_summary(driver: str) -> str:
        rows = [s for s in cal["scenarios"] if s["driver"] == driver]
        return " · ".join(f"{{{s['scenario']} ${s['level_usd']:g} · {s['prob']:.2f}}}" for s in rows)

    ctx["scenarios.kr_summary"] = scen_summary("carbon_kr")
    ctx["scenarios.jp_summary"] = scen_summary("carbon_jp")
    ctx["gcam.source"] = d["t_required_source"]

    for f in shares["firms"]:
        for dr, v in f["shares"].items():
            ctx[f"shares.{f['firm_id']}.{dr}"] = f"{v:.3f}"
            ctx[f"shares.{f['firm_id']}.{dr}_pct"] = pct(v)
        for dr, v in f["shares_reform"].items():
            ctx[f"shares_reform.{f['firm_id']}.{dr}"] = f"{v:.3f}"
            ctx[f"shares_reform.{f['firm_id']}.{dr}_pct"] = pct(v)
    for f in cvr["firms"]:
        for dr, v in f["cost_shares"].items():
            ctx[f"cost.{f['firm_id']}.{dr}_pct"] = pct(v)
        for dr, v in f["risk_shares"].items():
            ctx[f"risk.{f['firm_id']}.{dr}_pct"] = pct(v)

    ctx["invariance.max_share_deviation"] = f"{inv['max_share_deviation']:.1e}"
    ctx["invariance.share_decimals"] = str(inv["share_invariant_to_decimals"])
    ctx["invariance.level_min_bps"] = f"{inv['level_min_bps']:.2f}"
    ctx["invariance.level_max_bps"] = f"{inv['level_max_bps']:.2f}"
    ctx["lambda_k.max_shift_pct"] = pct(max(f["max_shift"] for f in lam_k["firms"]))
    ctx["stranding.asset_ids"] = ", ".join(a["asset_id"] for a in stranding["assets"])

    for f in gaps["firms"]:
        ctx[f"gap.{f['firm_id']}.cum_mtco2"] = f"{f['cumulative_alignment_gap_mtco2']:.0f}"
        ctx[f"gap.{f['firm_id']}.first_year"] = str(f["first_misalignment_year"] or "—")

    iv_table = cal["interventions"]
    h2row = next(r for r in iv_table if r["intervention_id"] == "h2_cfd")
    ctx["iv.h2_cfd_price"] = f"{h2row['value']:g}"
    for f in imp["firms"]:
        pk = f["interventions"].get("package")
        if pk:
            ctx[f"iv.{f['firm_id']}.package_dtau"] = f"{pk['delta']['tau_star_years']:+.1f}"
            ctx[f"iv.{f['firm_id']}.package_dgap"] = f"{pk['delta']['cumulative_gap_mtco2']:+.0f}"
        cfd = f["interventions"].get("h2_cfd")
        if cfd:
            ctx[f"iv.{f['firm_id']}.h2_cfd_dtau"] = f"{cfd['delta']['tau_star_years']:+.2f}"
            ctx[f"iv.{f['firm_id']}.h2_cfd_dcharge"] = f"{cfd['delta']['risk_charge_bps']:+.2f}"

    tau = art("tau_star")
    ctx["lsm.p_bind_in_exercise"] = "ON" if tau["p_bind_in_exercise"] else "OFF"

    def cluster_range(cluster: str, driver: str) -> str:
        vals = [f["shares"][driver] for f in shares["firms"] if f["cluster"] == cluster]
        return f"{pct(min(vals))}–{pct(max(vals))}" if len(vals) > 1 else pct(vals[0])

    ctx["cluster.h2_route.h2_range_pct"] = cluster_range("h2_route", "h2")
    ctx["cluster.h2_route.carbon_range_pct"] = cluster_range("h2_route", "carbon")
    ctx["cluster.grid_route.carbon_range_pct"] = cluster_range("grid_route", "carbon")
    all_carbon = [f["shares"]["carbon"] for f in shares["firms"]]
    ctx["cluster.all.carbon_range_pct"] = f"{pct(min(all_carbon))}–{pct(max(all_carbon))}"
    lw = art("level_wedge")
    for f in lw["firms"]:
        b = f["base"]
        fid = f["firm_id"]
        ctx[f"lw.{fid}.level"] = f"{b['level_gap_usd_t']:.0f}"
        ctx[f"lw.{fid}.wedge"] = f"{b['wedge_usd_t']:.0f}"
        ctx[f"lw.{fid}.m"] = f"{b['trigger_multiple_project']:.2f}"
        ctx[f"lw.{fid}.sigma_project"] = f"{b['sigma_project']:.3f}"
        ctx[f"lw.{fid}.var_h2_pct"] = pct(b["gap_variance_shares"]["h2"])
        ctx[f"lw.{fid}.var_carbon_pct"] = pct(b["gap_variance_shares"]["carbon"])
        ctx[f"lw.{fid}.wedge_overstated"] = f"{b['legacy_attribution']['wedge_usd_t_overstated']:.0f}"
        # 규칙 7: 배수를 문서에 하드코딩하지 않는다 (감사 2026-08-04에서 1.9× 하드코드 발견)
        ctx[f"lw.{fid}.legacy_overstatement_x"] = (
            f"{b['legacy_attribution']['wedge_usd_t_overstated'] / b['wedge_usd_t']:.2f}"
            if b["wedge_usd_t"] > 0
            else "n/a"
        )
    ctx["manifest.config_sha"] = manifest["config_sha256"][:12]
    ctx["manifest.dirty"] = "dirty" if manifest["git_dirty"] else "clean"
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
