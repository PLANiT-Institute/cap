"""s06: intervention impacts — 개입이 τ*·경로·anatomy·수준을 일관되게 바꾼다.

각 intervention에 대해 (reform-priced 관점, 국가별 regime):
- τ* before/after (자산별 + 용량가중)
- timing gap·cumulative emissions gap before/after (lib/pathways)
- residual risk anatomy before/after — coverage·tenor·basis 반영, 근거 없는 0 금지
- conditional risk charge before/after + residual unhedged
- standalone / sequential(package 순서) / order-averaged(Shapley) 기여
- S2 금융 채널: Δcharge → debt_share 가중 ΔWACC → τ* 1회 재解 —
  실물옵션 채널과 **별도 필드** (합산 전 부호 각각 판독; λ 밴드 병기)
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.anatomy import DRIVERS  # noqa: E402
from model.lib.artifacts import (  # noqa: E402
    MODEL_CONDITIONAL,
    PROVISIONAL,
    SCENARIO_CONDITIONAL,
    claim,
    write_artifact,
)
from model.lib.gap_pricing import price_alignment_gap  # noqa: E402
from model.lib.interventions import apply_interventions  # noqa: E402
from model.lib.pathways import condition_gap, firm_pathway, required_firm_pathway  # noqa: E402
from model.lib.result_contract import (  # noqa: E402
    ALIGNMENT_GAP_BASIS,
    ALIGNMENT_GAP_LOSS_BASIS,
    ALIGNMENT_GAP_LOSS_METRIC,
    ALIGNMENT_GAP_RISK_CHARGE_METRIC,
    ALIGNMENT_GAP_METRIC,
    ENTERPRISE_RISK_BASIS,
    RISK_CHARGE_METRIC,
    result_descriptor,
)
from model.lib.lsm_engine import lsm_tau_star  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402
from model.s03_lsm import build_spec, tau_year_of  # noqa: E402
from model.s04_anatomy import ANATOMY_DEPS, anatomy_for, firm_exposures, firm_frame  # noqa: E402

OUT = ROOT / "outputs"


def _firm_tau_capw_at_wacc_shift(
    cal: CalibrationSet, assets: "pd.DataFrame", ids: list[str], dwacc: float,
    positions: dict[str, int],
) -> tuple[float, frozenset]:
    """개입 ids 하에서 WACC를 dwacc만큼 이동시킨 뒤 (기업 τ* 용량가중, 행사 자산 집합).

    seed offset은 s03과 동일(cal.firms 행 순서) — dwacc=0이면 tau_star artifact와
    동일한 난수 경로이므로, 차이는 전적으로 dwacc에 귀속된다.
    두 번째 반환값은 τ*가 유한한(=p_ex ≥ threshold) 자산 집합 — 이 집합이 바뀌면
    Δτ*는 연속 반응이 아니라 **문턱 플립**이므로 금융 채널로 읽으면 안 된다.
    """
    thr = float(cal.lsm["tau_exercise_threshold"])
    horizon_end = float(cal.lsm["base_year"] + cal.lsm["horizon_years"])
    taus, caps, exercised = [], [], []
    for _, a in assets.iterrows():
        asset = a.to_dict()
        ps = apply_interventions(
            cal, asset["route"], asset["country"], asset["elec_driver"], ids
        ) if ids else None
        res = lsm_tau_star(
            build_spec(cal, asset, float(asset["wacc"]) + dwacc, positions[asset["asset_id"]], ps),
            tau_threshold=thr,
        )
        ty = tau_year_of(cal, res)
        if ty is not None:
            exercised.append(asset["asset_id"])
        taus.append(ty if ty is not None else horizon_end)
        caps.append(float(asset["capacity_mt_yr"]))
    return float(np.average(taus, weights=caps)), frozenset(exercised)


def financing_channel(
    cal: CalibrationSet,
    assets: "pd.DataFrame",
    iid: str,
    delta_charge_bps: float,
    iv_tau_capw: float,
    positions: dict[str, int],
) -> dict:
    """S2: σ_B → 스프레드 → WACC → τ* **1회 전파** (고정점 반복 금지 — 2차 범위).

    ΔWACC = debt_share × Δcharge(bps)/1e4. Δcharge는 k·λ·p_bind·σ_B 스케일 —
    전부 assumed이므로 점추정 금지: λ 프리셋(lambda_grid_lo/base/hi) 밴드로 출력.
    직접 WACC 개입(concessional 등 wacc_delta≠0)은 이중계상 방지를 위해 제외
    (같은 메커니즘이 두 번 계산되면 안 된다 — 검토 2026-08-04 상호배제 규약).
    """
    route = str(assets["route"].iloc[0])
    country = str(assets["country"].iloc[0])
    elec = str(assets["elec_driver"].iloc[0])
    ps_iv = apply_interventions(cal, route, country, elec, [iid])
    excluded = ps_iv.wacc_delta != 0.0
    debt_share = float(cal.transaction_assumptions.iloc[0]["debt_share"])
    lam = float(cal.pricing["lambda"])
    lam_grid = {"lo": float(cal.lsm["lambda_grid_lo"]), "base": lam,
                "hi": float(cal.lsm["lambda_grid_hi"])}
    resolution = float(cal.pathways["financing_channel_resolution_years"])
    out = {
        "channel": "sigma_B -> spread -> WACC -> tau* (one-pass; fixed point out of scope)",
        "excluded_direct_wacc_intervention": excluded,
        "debt_share": debt_share,
        "lambda_presets": lam_grid,
        "mc_resolution_years": resolution,
        "delta_wacc_bps": 0.0,
        "delta_tau_financing_channel_years": 0.0,
        "delta_tau_raw_years": 0.0,
        "below_mc_resolution": False,
        "threshold_flip": False,
        "lambda_band_sign_consistent": True,
        "band_years": {"lambda_lo": 0.0, "lambda_hi": 0.0},
        "note": ("λ·k·p_bind·debt_share(전부 assumed)에 정비례 — 점추정이 아니라 "
                 "밴드로 읽을 것; 실물옵션 채널(delta.tau_star_years)과 분리 판독"),
    }
    if excluded or not ps_iv.applied or delta_charge_bps == 0.0:
        if excluded:
            out["note"] = ("직접 WACC 개입 — 금융 채널 미적용 (이중계상 상호배제); "
                           "WACC 효과는 실물옵션 채널 τ*에 이미 반영")
        return out
    # dwacc=0 기준선을 같은 추정기로 잡아 행사 자산 집합을 비교한다
    _, ref_set = _firm_tau_capw_at_wacc_shift(cal, assets, [iid], 0.0, positions)
    deltas, flips = {}, False
    for tag, lam_x in lam_grid.items():
        dwacc = debt_share * (delta_charge_bps * lam_x / lam) / 1e4
        tau_fin, ex_set = _firm_tau_capw_at_wacc_shift(cal, assets, [iid], dwacc, positions)
        deltas[tag] = tau_fin - iv_tau_capw
        flips = flips or (ex_set != ref_set)
    signs = {np.sign(v) for v in deltas.values() if v != 0.0}
    out["delta_wacc_bps"] = debt_share * delta_charge_bps
    out["delta_tau_raw_years"] = deltas["base"]
    out["band_years"] = {"lambda_lo": deltas["lo"], "lambda_hi": deltas["hi"]}
    out["threshold_flip"] = bool(flips)
    out["lambda_band_sign_consistent"] = len(signs) <= 1
    # 세 가지 이유로 금융 채널을 0으로 보고한다 (감사 2026-08-04):
    # ① 문턱 플립 — p_ex가 임계를 넘으면 τ*가 유한↔지평말로 점프한다. 0.1bp 이동에
    #    수 년이 움직이는 것은 금융 효과가 아니라 위상 전환이다 (p_ex 절벽).
    # ② MC 해상도 — τ*는 이산 행사규칙의 몬테카를로 평균이므로 미분이 아니다.
    # ③ λ 밴드 부호 불일치 — dwacc ∝ λ이므로 진짜 반응은 λ에 단조여야 한다.
    if flips:
        out["note"] = (
            "문턱 플립 감지 (p_ex가 tau_exercise_threshold를 교차) — Δτ*가 위상 전환이므로 "
            f"금융 채널로 읽지 않는다. 원값 {deltas['base']:+.4f}y는 delta_tau_raw_years에 보존"
        )
    elif abs(deltas["base"]) <= resolution:
        out["below_mc_resolution"] = True
        out["note"] = (
            f"금융 채널 |Δτ*| = {abs(deltas['base']):.4f}y ≤ MC 해상도 {resolution}y — "
            "0으로 보고. 이 배선·이 λ에서 금융 채널은 이 추정기로 0과 구별되지 않는다 "
            "(실물옵션 채널과의 비교는 여전히 유효: 그쪽은 해상도의 수십 배)"
        )
    elif not out["lambda_band_sign_consistent"]:
        out["note"] = (
            "λ 밴드에서 부호가 뒤집힘 — dwacc ∝ λ이므로 진짜 반응은 λ에 단조여야 한다. "
            f"추정 잡음으로 판정하고 0으로 보고 (원값 {deltas['base']:+.4f}y 보존)"
        )
    else:
        out["delta_tau_financing_channel_years"] = deltas["base"]
    return out


def firm_state(
    cal: CalibrationSet, firm_id: str, tau_map: dict | None, ids: list[str], basis_case: str = "lo"
) -> dict:
    """한 기업의 (anatomy, charge, gap) 상태 — 개입 ids 적용.

    basis_case="hi"는 계약 잔여 basis를 문헌 최악(Peña 외 2024)으로 두고 다시 푼다.
    """
    tau_art = json.loads((OUT / "tau_star.json").read_text())
    private_tau = (
        {a["asset_id"]: a["tau_star_year"] for a in tau_art["assets"]}
        if tau_map is None
        else tau_map
    )
    frame = firm_frame(cal, tau_map=tau_map)
    g_all = frame[frame["firm_id"] == firm_id]
    g = g_all[g_all["category"] == "priced_route"]
    if g.empty:
        return {}
    # 계약 coverage는 **가격이 매겨지는 노출창** [t_sw, H] 기준으로 가중한다.
    # S4 이후 t_sw=τ*이므로 지평 기준 가중은 만료된 계약이 만료 후 구매를 헤지한 것으로
    # 계산했다 (감사 2026-08-04 B11). LSM 레인은 전 지평을 보므로 그대로 둔다.
    horizon_end = float(cal.lsm["base_year"] + cal.lsm["horizon_years"])
    t_sw_capw = float(np.average(g["t_switch_year"], weights=g["capacity_mt_yr"]))
    ps = apply_interventions(
        cal, g["route"].iloc[0], g["country"].iloc[0], g["elec_driver"].iloc[0], ids,
        base_year_override=t_sw_capw,
        horizon_override=max(0.0, horizon_end - t_sw_capw),
        basis_case=basis_case,
    )
    meta = firm_exposures(cal, g, ps=ps)
    an = anatomy_for(cal, meta, reform=True)  # 정책 점프 가격화 관점 (문서화)
    base_year = int(cal.lsm["base_year"])
    years = np.arange(base_year, base_year + int(cal.lsm["horizon_years"]) + 1)
    residual = dict(zip(cal.routes["route"], cal.routes["residual_intensity_tco2_t"]))
    priced_ids = set(g["asset_id"])
    # ``firm_frame`` uses the horizon end as a finite exposure proxy when τ* is
    # None.  Emissions pathways must retain the raw None, which means no switch
    # within the model horizon.  Mixing the two conventions understated the
    # base gap and made s06 disagree with s07/s13.
    pmap = {asset_id: private_tau.get(asset_id) for asset_id in g_all["asset_id"]}
    rmap = {a: cal.t_required[a]["year"] for a in g_all["asset_id"]}
    p_track = firm_pathway(g_all, {a: pmap.get(a) for a in priced_ids}, years, residual)
    # S3: required는 풀 연속 q(t) — s07과 동일 빌더 (basis 정합)
    r_track = required_firm_pathway(g_all, years, residual, cal.t_required, cal.required_pool_paths)
    gap = condition_gap(p_track["emissions_mtco2"], r_track["emissions_mtco2"], years)
    country = str(g["country"].iloc[0])
    gap_loss = price_alignment_gap(
        gap["annual_alignment_gap_mtco2"],
        years,
        base_year=base_year,
        rate=float(meta["wacc"]),
        horizon_years=float(cal.lsm["horizon_years"]),
        reference_price_usd_tco2=float(cal.pricing[f"carbon_base_{country.lower()}"]),
        scenarios=ps.carbon.scenarios,
        risk_price_lambda=float(cal.pricing["lambda"]),
        risk_scale_k=float(cal.pricing["k"]),
        enterprise_value_usd_bn=float(meta["ev_usd_bn"]),
    )
    tau_capw = float(np.average(g["tau_star_year"], weights=g["capacity_mt_yr"]))
    tg = [
        (t - rmap[a]) for a, t in zip(g["asset_id"], g["tau_star_year"]) if rmap.get(a) is not None
    ]
    return {
        "risk_result_contract": result_descriptor(
            RISK_CHARGE_METRIC,
            ENTERPRISE_RISK_BASIS,
            "SCENARIO_CONDITIONAL",
            uncertainty="lambda, k, scenarios, covariance and exposure calibration",
            interpretation="enterprise transition-window risk; not project-at-commissioning risk",
        ),
        "alignment_result_contract": result_descriptor(
            ALIGNMENT_GAP_METRIC,
            ALIGNMENT_GAP_BASIS,
            "PROVISIONAL" if cal.required_path_provisional else "MODEL_CONDITIONAL",
            uncertainty="required pathway source and private transition model",
            interpretation="surrogate-conditioned central case" if cal.required_path_provisional else "raw-pathway comparison",
        ),
        "alignment_gap_loss_result_contract": result_descriptor(
            ALIGNMENT_GAP_LOSS_METRIC,
            ALIGNMENT_GAP_LOSS_BASIS,
            "PROVISIONAL",
            uncertainty="surrogate required path and assumed carbon scenario distribution",
            interpretation="scenario-valued PV loss implied by the annual physical gap",
        ),
        "alignment_gap_risk_result_contract": result_descriptor(
            ALIGNMENT_GAP_RISK_CHARGE_METRIC,
            ALIGNMENT_GAP_LOSS_BASIS,
            "PROVISIONAL",
            uncertainty="gap-loss distribution plus assumed lambda and k",
            interpretation="separate gap-linked charge; not additive to transition-cost charge",
        ),
        "tau_star_cap_weighted": tau_capw,
        "timing_gap_mean_years": float(np.mean(tg)) if tg else None,
        "cumulative_gap_mtco2": gap["cumulative_alignment_gap_mtco2"],
        "expected_pv_gap_loss_usd_m": gap_loss["expected_pv_gap_loss_usd_m"],
        "sigma_pv_gap_loss_usd_m": gap_loss["sigma_pv_gap_loss_usd_m"],
        "gap_risk_charge_bps": gap_loss["gap_risk_charge_bps"],
        "shares": an["shares"],
        "sigma_b_usd_bn": an["sigma_b_usd_bn"],
        "risk_charge_bps": an["premium_bps"],
        "double_count_warning": ps.double_count_warning,
    }


def main() -> int:
    cal = load_calibration()
    tau_art = json.loads((OUT / "tau_star.json").read_text())
    iv_tau = tau_art["interventions"]
    iv_ids = list(iv_tau.keys())
    package_row = cal.interventions.set_index("intervention_id").loc["package"]
    components = [c for c in str(package_row["components"]).split(";") if c]

    firms = sorted(set(cal.firms[cal.firms["category"] == "priced_route"]["firm_id"]))
    positions = {row["asset_id"]: i for i, (_, row) in enumerate(cal.firms.iterrows())}
    out_firms = []
    for fid in firms:
        before = firm_state(cal, fid, tau_map=None, ids=[])
        g_assets = cal.firms[
            (cal.firms["firm_id"] == fid) & (cal.firms["category"] == "priced_route")
        ]
        ivs = {}
        for iid in iv_ids:
            after = firm_state(cal, fid, tau_map=iv_tau[iid], ids=[iid])
            high = firm_state(cal, fid, tau_map=iv_tau[iid], ids=[iid], basis_case="hi")
            fc = financing_channel(
                cal, g_assets, iid,
                after["risk_charge_bps"] - before["risk_charge_bps"],
                after["tau_star_cap_weighted"], positions,
            )
            ivs[iid] = {
                "label": cal.interventions.set_index("intervention_id").loc[iid, "label"],
                "before": {k: before[k] for k in ("tau_star_cap_weighted", "timing_gap_mean_years",
                                                  "cumulative_gap_mtco2", "expected_pv_gap_loss_usd_m",
                                                  "gap_risk_charge_bps", "risk_charge_bps", "sigma_b_usd_bn")},
                "after": {k: after[k] for k in ("tau_star_cap_weighted", "timing_gap_mean_years",
                                                "cumulative_gap_mtco2", "expected_pv_gap_loss_usd_m",
                                                "gap_risk_charge_bps", "risk_charge_bps", "sigma_b_usd_bn")},
                "delta": {
                    # 실물옵션 채널 (금융 채널과 분리 판독 — S2)
                    "tau_star_years": after["tau_star_cap_weighted"] - before["tau_star_cap_weighted"],
                    "delta_tau_financing_channel_years": fc["delta_tau_financing_channel_years"],
                    "delta_tau_total_years": (
                        after["tau_star_cap_weighted"] - before["tau_star_cap_weighted"]
                        + fc["delta_tau_financing_channel_years"]
                    ),
                    "cumulative_gap_mtco2": after["cumulative_gap_mtco2"] - before["cumulative_gap_mtco2"],
                    "expected_pv_gap_loss_usd_m": (
                        after["expected_pv_gap_loss_usd_m"]
                        - before["expected_pv_gap_loss_usd_m"]
                    ),
                    "gap_risk_charge_bps": (
                        after["gap_risk_charge_bps"] - before["gap_risk_charge_bps"]
                    ),
                    "risk_charge_bps": after["risk_charge_bps"] - before["risk_charge_bps"],
                    "risk_charge_bps_high_basis": high["risk_charge_bps"] - before["risk_charge_bps"],
                },
                "residual": {
                    "shares": after["shares"],
                    "sigma_b_usd_bn": after["sigma_b_usd_bn"],
                    "risk_charge_bps": after["risk_charge_bps"],
                    "risk_charge_bps_high_basis": high["risk_charge_bps"],
                    "gap_risk_charge_bps": after["gap_risk_charge_bps"],
                    "gap_charge_aggregation_warning": (
                        "separate basis; do not add to transition-cost risk_charge_bps"
                    ),
                    "note": "coverage·tenor·basis 반영 잔여 — 0으로 만들지 않음. "
                            "high_basis는 헤지 유효성 실측이 낮다는 문헌(Peña 외 2024)의 최악 경계",
                },
                "financing_channel": fc,
                "double_count_warning": after["double_count_warning"],
                "assumptions": cal.interventions.set_index("intervention_id").loc[iid, "notes"],
            }

        # sequential (package 구성 순서대로 누적) — 순서 의존성 명시
        # 첫 단계가 base→package 타이밍 점프를 전부 흡수하지 않도록 기준선도
        # package τ*(빈 집합)에서 잡는다 — Shapley와 같은 특성함수 (감사 2026-08-04)
        seq = []
        prev_charge = firm_state(cal, fid, tau_map=iv_tau["package"], ids=[])["risk_charge_bps"]
        seq_baseline_bps = prev_charge
        for j in range(1, len(components) + 1):
            ids_j = components[:j]
            st = firm_state(cal, fid, tau_map=iv_tau["package"], ids=ids_j)
            seq.append({"after_ids": ids_j, "risk_charge_bps": st["risk_charge_bps"],
                        "cut_bps": prev_charge - st["risk_charge_bps"]})
            prev_charge = st["risk_charge_bps"]

        # order-averaged (Shapley) — risk charge 감축 기여, 2^n 부분집합
        shapley = {c: 0.0 for c in components}
        n = len(components)
        charge_cache: dict[frozenset, float] = {}

        def charge_of(subset: frozenset) -> float:
            # 노출창(t_sw)을 package τ*로 **고정**한 채 charge를 비교한다.
            # 공집합만 base τ*로 두면 base→package 타이밍 점프가 전부 S=∅ 항에 실리고,
            # 그 항의 Shapley 가중이 모든 참가자에게 1/n로 같아서 **적용조차 안 되는
            # 계약에도 1/n씩 배분된다** (null player 공리 위반, 감사 2026-08-04).
            if subset not in charge_cache:
                st = firm_state(cal, fid, tau_map=iv_tau["package"], ids=sorted(subset))
                charge_cache[subset] = st["risk_charge_bps"]
            return charge_cache[subset]

        for c in components:
            others = [x for x in components if x != c]
            for r in range(len(others) + 1):
                for combo in itertools.combinations(others, r):
                    s = frozenset(combo)
                    weight = (
                        float(math.factorial(r) * math.factorial(n - r - 1))
                        / float(math.factorial(n))
                    )
                    shapley[c] += weight * (charge_of(s) - charge_of(s | {c}))

        out_firms.append(
            {
                "firm_id": fid,
                "sector": str(g_assets["sector"].iloc[0]),
                "before": before,
                "interventions": ivs,
                "sequential_package": {
                    "order": components,
                    "steps": seq,
                    "baseline_bps": seq_baseline_bps,
                    "note": "순차 소거는 적용 순서에 따라 배분이 달라진다 — order-averaged 참조. "
                            "기준선은 package τ*의 무계약 charge (타이밍 점프 분리)",
                },
                "order_averaged_contribution_bps": shapley,
                "attribution_basis": (
                    "charge at fixed exposure window (package τ*); base→package timing effect is "
                    "NOT distributed here — read delta.tau_star_years for it. Non-applicable "
                    "instruments receive exactly 0 (null-player axiom)"
                ),
            }
        )

    write_artifact(
        "intervention_impacts",
        {"interventions": iv_ids, "firms": out_firms,
         "perspective": "reform-priced (국가별 σ_reform 관점)"},
        cal.param_status,
        claims={
            "firms.interventions.delta": claim(
                MODEL_CONDITIONAL, ANATOMY_DEPS + ["interventions"],
                "coverage·tenor 1차 근사; τ*·경로·anatomy·수준 동시 재계산 — "
                "tau_star_years는 실물옵션 채널만 (금융 채널 분리)",
            ),
            "firms.interventions.delta.delta_tau_financing_channel_years": claim(
                SCENARIO_CONDITIONAL,
                ANATOMY_DEPS + ["interventions", "lambda", "k", "ev_usd_bn",
                                "transaction_assumptions"],
                "S2 금융 채널 1회 전파 — Δcharge(λ·k·p_bind 스케일)×debt_share 경유 "
                "ΔWACC로 τ* 재解. λ-free가 아님: 점추정 금지, financing_channel.band_years "
                "밴드로 읽을 것. 직접 WACC 개입은 상호배제로 제외",
            ),
            "firms.interventions.residual.risk_charge_bps_high_basis": claim(
                SCENARIO_CONDITIONAL, ANATOMY_DEPS + ["interventions", "lambda", "k", "ev_usd_bn"],
                "basis_sigma_hi(문헌 최악) 하 잔여 — Δπ를 밴드로 읽을 것",
            ),
            "firms.interventions.residual.risk_charge_bps": claim(
                SCENARIO_CONDITIONAL, ANATOMY_DEPS + ["interventions", "lambda", "k", "ev_usd_bn"],
                "잔여 conditional risk charge — fully-hedged 0 주장 금지",
            ),
            "firms.interventions.delta.gap_risk_charge_bps": claim(
                PROVISIONAL,
                ["t_required", "scenarios", "carbon_base_kr", "carbon_base_jp",
                 "lambda", "k", "ev_usd_bn", "interventions"],
                "연도별 condition gap을 시나리오 손실분포로 직접 사상; p_bind 재곱 없음",
            ),
        },
        note="개입 = 파라미터 변환: τ* before/after, gap before/after, residual anatomy, charge",
        sector_enabled=cal.sector_enabled,
    )
    for f in out_firms:
        pk = f["interventions"].get("package", {})
        if pk:
            print(
                f"{f['firm_id']:8s} package: Δτ*={pk['delta']['tau_star_years']:+.1f}y "
                f"(fin {pk['delta']['delta_tau_financing_channel_years']:+.2f}y) "
                f"Δgap={pk['delta']['cumulative_gap_mtco2']:+.1f}Mt "
                f"charge {pk['before']['risk_charge_bps']:.1f}→{pk['after']['risk_charge_bps']:.1f}bps"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
