"""s02: config + processed → 검증된 CalibrationSet 하나.

이후 단계(s03–s07)는 이 객체만 받는다 — 모델 코드 어디에도 숫자 리터럴 없음.

핵심 구조 (2026-07 개편):
- 탄소는 국가별 factor: carbon_kr / carbon_jp (+cbam_common 공통요인 태그).
  ℓ_bind·점프분산·σ_reform 전부 국가별. KR 시나리오를 JP 기업에 적용하지 않는다.
- p_bind 정의 = Option A: p_bind(country) = Σ prob(binds=1). 별도 파라미터 없음.
- T_required: route별 배치 풀 분리. no_feasible_route 자산은 priced 풀을 소비하지
  않는다. H₂-DRI surrogate 곡선은 h2_dri 자산에만; scrap/NG는 자체 풀 스케일의
  동형 곡선 (PROVISIONAL). reline 순 배분은 LCOA merit order가 아니라 근사임.
- 확산과 정책점프를 동일 상관·동일 연σ로 합산하는 것은 근사 (분해는 별도 기록).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.schema.config_schemas import (  # noqa: E402
    correlations_schema,
    firms_schema,
    interventions_schema,
    lsm_schema,
    pathways_schema,
    pricing_schema,
    routes_schema,
    scenarios_schema,
    sigmas_schema,
    transaction_assumptions_schema,
)
from model.lib.artifacts import (  # noqa: E402
    EMPIRICAL,
    PROVISIONAL,
    SCENARIO_CONDITIONAL,
    claim,
    write_artifact,
)
from model.lib.jump import (  # noqa: E402
    binding_level,
    scenario_mean_level,
    sigma_carbon_binding,
    sigma_carbon_combined,
)

CFG = ROOT / "config"
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
TRADING_DAYS = 252  # 연율화 관례 상수 (파라미터 아님)
COUNTRIES = ("KR", "JP")


@dataclass
class CalibrationSet:
    sigmas: pd.DataFrame
    correlations: pd.DataFrame
    pricing: dict[str, float]
    lsm: dict[str, float]
    scenarios: pd.DataFrame
    firms: pd.DataFrame
    routes: pd.DataFrame
    interventions: pd.DataFrame
    transaction_assumptions: pd.DataFrame
    pathways: dict[str, float]  # 요구 경로 파라미터 (config/pathways.csv)
    param_status: dict[str, str]
    # 국가별 탄소 구조 (Option A: p_bind 파생)
    l_bar: dict[str, float]
    l_bind: dict[str, float]
    p_bind: dict[str, float]
    sigma_carbon_reform: dict[str, float]
    sigma_carbon_binding: dict[str, float]
    carbon_var_decomp: dict[str, dict[str, float]]
    # X9: 탄소 drift는 파라미터가 아니라 파생값 — 현물이 anchor 연한에 걸쳐
    # 시나리오 기대수준(ℓ̄)에 도달하는 궤도. 도달 후 성장 0 (수준 유지).
    # CAP은 수익률을 전망하지 않는다; sigmas.mu의 carbon 행은 미사용.
    mu_carbon: dict[str, float]
    k_offcycle_mult: float
    t_required: dict[str, dict]  # asset_id → {year, status, pool}
    # S3: 풀 수준 연속 배치 경로 — pool_id → {years, q_fraction(0..1), ...}.
    # required 배출 경로는 자산 배정 계단이 아니라 이 q(t)로 계산한다 (pro-rata).
    required_pool_paths: dict[str, dict]
    t_required_source: str
    measured_overrides: list[str] = field(default_factory=list)

    @property
    def required_path_provisional(self) -> bool:
        """True when any priced asset still depends on a surrogate benchmark."""
        return any(
            row["status"] == PROVISIONAL for row in self.t_required.values()
        )

    def sigma(self, driver: str) -> float:
        return float(self.sigmas.set_index("driver").loc[driver, "value"])

    def sigma_band(self, driver: str) -> tuple[float, float]:
        row = self.sigmas.set_index("driver").loc[driver]
        return float(row["band_lo"]), float(row["band_hi"])

    def mu_vector(self, elec_driver: str) -> np.ndarray:
        s = self.sigmas.set_index("driver")["mu"]
        return np.array(
            [s["carbon_diffusion"], s["h2"], s[elec_driver], s["feedstock"], s["capex"]],
            dtype=float,
        )

    def rho_matrix(
        self, elec_driver: str, carbon_sigma: float | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """(σ 벡터, ρ 5×5) — DRIVERS 순서 [carbon, h2, elec, feedstock, capex].
        주의: 점프 포함 σ_carbon에도 확산과 동일 ρ를 적용 — 근사 (§5 명시)."""
        from model.lib.anatomy import DRIVERS

        sig = np.array(
            [
                carbon_sigma if carbon_sigma is not None else self.sigma("carbon_diffusion"),
                self.sigma("h2"),
                self.sigma(elec_driver),
                self.sigma("feedstock"),
                self.sigma("capex"),
            ]
        )
        rho = np.eye(len(DRIVERS))
        pair = {
            (r["driver_i"], r["driver_j"]): float(r["value"])
            for _, r in self.correlations.iterrows()
        }
        for i, di in enumerate(DRIVERS):
            for j, dj in enumerate(DRIVERS):
                if i == j:
                    continue
                v = pair.get((di, dj), pair.get((dj, di)))
                if v is not None:
                    rho[i, j] = v
        return sig, rho

    def carbon_scenarios(self, country: str) -> pd.DataFrame:
        return self.scenarios[self.scenarios["driver"] == f"carbon_{country.lower()}"]


def _annualized_sigma(returns: pd.Series) -> float:
    return float(returns.std() * np.sqrt(TRADING_DAYS))


# status 집계는 최악 우선 — 한 행이라도 assumed면 테이블 전체가 assumed로 흐른다
STATUS_RANK = ("measured", "banded", "provisional", "assumed")


def _worst_status(col: pd.Series) -> str:
    present = {str(v) for v in col.dropna()}
    for s in reversed(STATUS_RANK):
        if s in present:
            return s
    return "assumed"


def _pool_share_curve(
    years: np.ndarray, curve: np.ndarray, saturation: float, rebase: bool
) -> np.ndarray:
    """배치 곡선(Mt) → 풀 전환 **비율** q(t) ∈ [0,1].

    설계 결정 (S3 정정, 2026-08-04):
    - 곡선을 **자기 포화값**으로 나눈다 — 풀 용량으로 나누면 작은 풀이 더 빠른 요구
      경로를 갖는 나눗셈 아티팩트가 생기고, 두 분기(h2/비h2)의 q가 서로 다른 객체가 된다.
      비율로 정규화하면 pro_rata 규약대로 모든 풀이 같은 배치 **일정**을 공유한다.
    - `rebase`면 기준연도 비율을 빼고 재정규화 — 기준연도에 H₂-DRI 설비는 0이므로
      q(base_year)=0이어야 한다. 이 항이 없으면 요구 경로가 2026년에 이미 몇 %가
      전환된 것으로 주장해 first_misalignment_year가 전부 기준연도로 붕괴한다.
    """
    q = curve / max(float(saturation), np.finfo(float).tiny)
    if rebase:
        q0 = float(q[0])
        q = (q - q0) / max(1.0 - q0, np.finfo(float).tiny)
    return np.clip(q, 0.0, 1.0)


def _t_required(
    firms: pd.DataFrame, lsm: dict[str, float], pathways: dict[str, float]
) -> tuple[dict[str, dict], str, dict[str, dict]]:
    """route별 배치 풀로 T_required + 풀 연속 경로(q-곡선) 산출 (S3).

    - priced_route 자산만 풀에 들어간다 (no_feasible_route는 풀 소비 금지).
    - h2_dri: GCAM H₂-DRI 곡선 (raw 있으면 raw, 없으면 logistic surrogate).
      q(t) = min(curve/pool_cap, 1).
    - 기타 철강 route: route별 경로 부재 → 동형 logistic의 **비율 곡선** q(t)=curve/L
      사용 (endpoint 재정규화 금지 — 풀 마지막 자산 T_required가 지평말에 고정되던
      아티팩트의 원인, FORMULA_LEDGER R-6). status=PROVISIONAL.
    - 자산별 T_required = q(t)가 자산 누적용량 **중점**(cum−cap/2)/pool_cap에 닿는
      첫 해 — 연속 풀 경로의 pro-rata 해석. 미도달이면 None (지평말 고정 아님).
    - required **배출 경로**는 자산 배정이 아니라 q(t)로 직접 계산한다
      (lib/pathways.required_firm_pathway). T_required는 wedge 보고용 파생값.
    - 석유화학 archetype: 자산별 next investment cycle 계단 유지 (풀 곡선 없음).
    - 풀 내 순서는 reline 연도순 — LCOA merit order가 아니라 근사 (명시).
    """
    raw_csv = RAW / "gcam" / "Q_gcam_h2dri.csv"
    base_year = int(lsm["base_year"])
    years = np.arange(base_year, base_year + int(lsm["horizon_years"]) + 1, dtype=float)
    # 파라미터는 config/pathways.csv에서만 온다 (규칙 1·3·4 — 이전에는 읽기전용 raw yaml에서
    # 직접 읽어 status·anchor·PAPER_DIFF 추적 밖에 있었다: 갱신 14 §C)
    sat = float(pathways["required_saturation_mt"])
    rebase = bool(pathways["required_rebase_to_base_year"])
    surrogate_q = sat / (
        1.0
        + np.exp(
            -float(pathways["required_steepness_per_yr"])
            * (years - float(pathways["required_inflection_year"]))
        )
    )
    if raw_csv.exists():
        q = pd.read_csv(raw_csv).sort_values("year")
        years_raw, q_raw = q["year"].to_numpy(float), q["Q_h2dri_Mt"].to_numpy(float)
        source = "mixed"  # KR H2 raw; JP and non-H2 pools remain surrogate until supplied
    else:
        years_raw, q_raw = years, surrogate_q
        source = "surrogate"

    out: dict[str, dict] = {}
    pool_paths: dict[str, dict] = {}
    priced = firms[firms["category"] == "priced_route"]
    for (sector, country, route), g in priced.groupby(["sector", "country", "route"]):
        pool_id = f"{sector}:{country}:{route}"
        if sector == "petrochemicals":
            for _, row in g.iterrows():
                year = float(np.clip(row["next_investment_year"], years[0], years[-1]))
                out[row["asset_id"]] = {
                    "year": year,
                    "status": PROVISIONAL,
                    "pool": pool_id,
                    "benchmark_source": "asset investment-cycle surrogate",
                    "intended_benchmark": "sector pathway not yet supplied",
                    "pathway_kind": "INVESTMENT_CYCLE_SURROGATE",
                    "allocation_rule": "asset next_investment_year clipped to model horizon",
                    "headline_eligible": False,
                    "note": "petrochemical investment-cycle surrogate (PROVISIONAL; not a firm mandate or validated sector pathway)",
                }
            continue
        pool_cap = float(g["capacity_mt_yr"].sum())
        if route == "h2_dri" and country == "KR" and raw_csv.exists():
            yrs = years_raw
            q_frac = _pool_share_curve(years_raw, q_raw, float(np.max(q_raw)), rebase)
            route_status = EMPIRICAL
            benchmark_source = "GCAM-KAIST Q_gcam_h2dri.csv"
            intended_benchmark = "GCAM-KAIST"
            pathway_kind = "IAM_SOURCED"
            headline_eligible = True
            pool_note = "Korean H2-DRI deployment curve (GCAM raw)"
        elif route == "h2_dri":
            yrs, q_frac = years, _pool_share_curve(years, surrogate_q, sat, rebase)
            route_status = PROVISIONAL
            benchmark_source = "legacy-config logistic H2-DRI surrogate"
            intended_benchmark = "GCAM-KAIST" if country == "KR" else "TZ-OSeMOSYS-STEEL"
            pathway_kind = "SURROGATE"
            headline_eligible = False
            pool_note = f"{country} H2-DRI logistic surrogate; intended IAM not supplied"
        else:
            # 동형 logistic의 비율 곡선 — endpoint 재정규화 금지 (S3, R-6 해소)
            yrs = years
            q_frac = _pool_share_curve(years, surrogate_q, sat, rebase)
            route_status = PROVISIONAL
            benchmark_source = "legacy-config H2 logistic fraction applied to route-country pool"
            intended_benchmark = "route-specific sector pathway not yet supplied"
            pathway_kind = "SURROGATE_RESCALED"
            headline_eligible = False
            pool_note = (
                f"route pathway unavailable — logistic fraction shape for {country}:{route} pool "
                "(PROVISIONAL; shape constructed, saturation not pinned to horizon end)"
            )
        pool_paths[pool_id] = {
            "years": [float(y) for y in yrs],
            "q_fraction": [float(v) for v in q_frac],
            "status": route_status,
            "pathway_kind": pathway_kind,
            "allocation_rule": "pro_rata",
        }
        ordered = g.sort_values("next_investment_year")
        cum = ordered["capacity_mt_yr"].cumsum()
        for (_, row), need in zip(ordered.iterrows(), cum):
            frac_need = (float(need) - float(row["capacity_mt_yr"]) / 2.0) / pool_cap
            reached = yrs[q_frac >= frac_need]
            out[row["asset_id"]] = {
                "year": float(reached[0]) if len(reached) else None,
                "status": route_status,
                "pool": pool_id,
                "benchmark_source": benchmark_source,
                "intended_benchmark": intended_benchmark,
                "pathway_kind": pathway_kind,
                "allocation_rule": (
                    "pro_rata — continuous pool q(t); asset T_required = capacity-midpoint "
                    "crossing (reporting derivative; emissions path uses q(t) directly)"
                ),
                "headline_eligible": headline_eligible,
                "note": pool_note + " · reline-order queue (approximation, not LCOA merit order)",
            }
    for _, row in firms[firms["category"] == "no_feasible_route"].iterrows():
        out[row["asset_id"]] = {
            "year": None,
            "status": "UNAVAILABLE",
            "pool": "stranding",
            "benchmark_source": "none",
            "intended_benchmark": "stranding/closure branch",
            "pathway_kind": "UNAVAILABLE",
            "allocation_rule": "excluded from priced-route deployment pools",
            "headline_eligible": False,
            "note": "no_feasible_route — priced-route 풀을 소비하지 않음; stranding/closure branch",
        }
    return out, source, pool_paths


def load_calibration() -> CalibrationSet:
    xlsx = CFG / "calibration.xlsx"
    sigmas = sigmas_schema.validate(pd.read_excel(xlsx, sheet_name="sigmas"))
    correlations = correlations_schema.validate(pd.read_excel(xlsx, sheet_name="correlations"))
    pricing_df = pricing_schema.validate(pd.read_excel(xlsx, sheet_name="pricing"))
    lsm_df = lsm_schema.validate(pd.read_excel(xlsx, sheet_name="lsm"))
    scenarios = scenarios_schema.validate(pd.read_csv(CFG / "scenarios.csv"))  # csv 우선
    firms = firms_schema.validate(pd.read_csv(CFG / "firms.csv"))
    invariant_cols = ["sector", "country", "route", "wacc", "ev_usd_bn", "elec_driver"]
    inconsistent = {
        firm_id: [c for c in invariant_cols if group[c].nunique(dropna=False) > 1]
        for firm_id, group in firms[firms["category"] == "priced_route"].groupby("firm_id")
    }
    inconsistent = {firm_id: cols for firm_id, cols in inconsistent.items() if cols}
    if inconsistent:
        raise ValueError(
            "priced-route firm rows must agree on fields consumed at firm level: "
            f"{inconsistent}"
        )
    routes = routes_schema.validate(pd.read_csv(CFG / "routes.csv"))
    interventions = interventions_schema.validate(pd.read_csv(CFG / "interventions.csv"))
    pathways_df = pathways_schema.validate(pd.read_csv(CFG / "pathways.csv"))
    transaction_assumptions = transaction_assumptions_schema.validate(
        pd.read_csv(CFG / "transaction_assumptions.csv")
    )

    # 계산기 원칙: 시계열은 σ 캘리브레이션·레퍼런스에만. 수준·추세는 config가 구동.
    measured = []
    kau = PROCESSED / "kau_daily.parquet"
    if kau.exists():
        kau_df = pd.read_parquet(kau)
        px = kau_df["close_krw"].astype(float)
        sig = _annualized_sigma(np.log(px).diff().dropna())
        i = sigmas.index[sigmas["driver"] == "carbon_diffusion"][0]
        sigmas.loc[i, ["value", "status", "source"]] = [
            sig, "measured", "KAU 일별 로그수익률 연율화 (processed/kau_daily.parquet)",
        ]
        sigmas.loc[i, "band_lo"] = min(float(sigmas.loc[i, "band_lo"]), sig)
        sigmas.loc[i, "band_hi"] = max(float(sigmas.loc[i, "band_hi"]), sig)
        measured.append("carbon_diffusion")
    smp = PROCESSED / "smp_daily.parquet"
    if smp.exists():
        px = pd.read_parquet(smp)["smp_krw_kwh"].astype(float)
        sig = _annualized_sigma(np.log(px).diff().dropna())
        i = sigmas.index[sigmas["driver"] == "elec_kr_smp"][0]
        sigmas.loc[i, ["value", "status", "source"]] = [sig, "measured", "EPSIS SMP 연율화"]
        measured.append("elec_kr_smp")
        if kau.exists():
            a = pd.read_parquet(kau).set_index("date")["close_krw"].astype(float)
            b = pd.read_parquet(smp).set_index("date")["smp_krw_kwh"].astype(float)
            joined = pd.concat({"kau": np.log(a).diff(), "smp": np.log(b).diff()}, axis=1).dropna()
            if len(joined) > 1:
                rho_meas = float(joined["kau"].corr(joined["smp"]))
                j = correlations.index[
                    (correlations["driver_i"] == "elec") & (correlations["driver_j"] == "carbon")
                ][0]
                correlations.loc[j, ["value", "status", "source"]] = [
                    rho_meas, "measured", "SMP×KAU 일별 로그수익률 상관 (실측)",
                ]
                measured.append("rho_elec_carbon")
    jepx = PROCESSED / "jepx_daily.parquet"
    if jepx.exists():
        px = pd.read_parquet(jepx)["system_price_jpy_kwh"].astype(float)
        sig = _annualized_sigma(np.log(px[px > 0]).diff().dropna())
        i = sigmas.index[sigmas["driver"] == "elec_jp"][0]
        sigmas.loc[i, ["value", "status", "source"]] = [sig, "measured", "JEPX 스팟 연율화"]
        measured.append("elec_jp")

    pricing = dict(zip(pricing_df["param"], pricing_df["value"].astype(float)))
    lsm = dict(zip(lsm_df["param"], lsm_df["value"].astype(float)))

    l_bar: dict[str, float] = {}
    l_bind: dict[str, float] = {}
    p_bind: dict[str, float] = {}
    sigma_reform: dict[str, float] = {}
    sigma_binding: dict[str, float] = {}
    var_decomp: dict[str, dict[str, float]] = {}
    sigma_diff = float(sigmas.set_index("driver").loc["carbon_diffusion", "value"])
    for c in COUNTRIES:
        scen = scenarios[scenarios["driver"] == f"carbon_{c.lower()}"]
        levels = scen["level_usd"].to_numpy(float)
        probs = scen["prob"].to_numpy(float)
        binds = scen["binds"].to_numpy(int)
        l_bar[c] = scenario_mean_level(levels, probs)
        l_bind[c] = binding_level(levels, probs, binds)
        p_bind[c] = float(probs[binds.astype(bool)].sum())  # Option A 파생
        sigma_reform[c] = sigma_carbon_combined(sigma_diff, levels, probs)
        sigma_binding[c] = sigma_carbon_binding(sigma_diff, levels, probs, binds)
        lb = l_bar[c]
        jump_var = float(np.dot(probs, (levels - lb) ** 2)) / lb**2
        mask = binds.astype(bool)
        cond_probs = probs[mask] / probs[mask].sum()
        bind_jump_var = float(
            np.dot(cond_probs, (levels[mask] - l_bind[c]) ** 2) / l_bind[c] ** 2
        )
        var_decomp[c] = {
            "diffusion_var": sigma_diff**2,
            "unconditional_jump_var": jump_var,
            "unconditional_jump_share": jump_var / (sigma_diff**2 + jump_var),
            "binding_conditional_jump_var": bind_jump_var,
            "binding_conditional_jump_share": (
                bind_jump_var / (sigma_diff**2 + bind_jump_var)
            ),
        }

    # X9: 탄소 drift 파생 — 현물 → ℓ̄ 수렴 궤도 (anchor 연한), 도달 후 0
    anchor_years = float(lsm["mu_anchor_years"])
    mu_carbon = {
        c: float(np.log(l_bar[c] / pricing[f"carbon_base_{c.lower()}"]) / anchor_years)
        for c in COUNTRIES
    }

    status: dict[str, str] = {}
    for _, r in sigmas.iterrows():
        status[f"sigma_{r['driver']}"] = r["status"]
    for _, r in correlations.iterrows():
        status[f"rho_{r['driver_i']}_{r['driver_j']}"] = r["status"]
    for _, r in pricing_df.iterrows():
        status[r["param"]] = r["status"]
    status["scenarios"] = "assumed"  # 시나리오 확률에 시장 규율 부재 (R2)
    status["p_bind"] = "assumed"  # 파생이지만 원천(시나리오 확률)이 assumed
    status["ev_usd_bn"] = "assumed"
    # 최악 status로 집계 — mode()는 소수의 assumed 행(archetype)을 삼켜 배지를 지웠다
    # (감사 2026-08-04). 규칙 4: assumed가 하나라도 있으면 결과에 conditional_on이 붙는다.
    status["firms_registry"] = _worst_status(firms["status"])
    status["routes_sensitivity"] = _worst_status(routes["status"])
    status["interventions"] = "assumed"
    status["transaction_assumptions"] = str(transaction_assumptions["status"].mode()[0])
    status["t_required"] = "provisional"
    for _, r in pathways_df.iterrows():
        status[r["param"]] = r["status"]
    # 노출 정의·전환시점 규칙 — MODEL_CONDITIONAL 근원. S4: t_sw = τ* (사적 경로 정합)
    status["exposure_model"] = "model"

    capex = pd.read_parquet(PROCESSED / "capex_refs.parquet").set_index("item_id")
    k_off = float(capex.loc["K12", "mid"]) / float(capex.loc["K11", "mid"])

    pathways = dict(zip(pathways_df["param"], pathways_df["value"].astype(float)))
    t_required, t_source, pool_paths = _t_required(firms, lsm, pathways)

    return CalibrationSet(
        sigmas=sigmas,
        correlations=correlations,
        pricing=pricing,
        lsm=lsm,
        scenarios=scenarios,
        firms=firms,
        routes=routes,
        interventions=interventions,
        transaction_assumptions=transaction_assumptions,
        pathways=pathways,
        param_status=status,
        l_bar=l_bar,
        l_bind=l_bind,
        p_bind=p_bind,
        sigma_carbon_reform=sigma_reform,
        sigma_carbon_binding=sigma_binding,
        carbon_var_decomp=var_decomp,
        mu_carbon=mu_carbon,
        k_offcycle_mult=k_off,
        t_required=t_required,
        required_pool_paths=pool_paths,
        t_required_source=t_source,
        measured_overrides=measured,
    )


def reference_prices() -> dict:
    """연단위 레퍼런스 가격 — 모델을 구동하지 않는다 (계산기 원칙). 대조·표시용."""
    out: dict = {"carbon_kr_annual": [], "elec_base": []}
    kau = PROCESSED / "kau_daily.parquet"
    if kau.exists():
        df = pd.read_parquet(kau)
        df["year"] = df["date"].str.slice(0, 4)
        agg = df.groupby("year").agg(
            mean_krw=("close_krw", "mean"),
            mean_usd=("close_usd", "mean") if "close_usd" in df.columns else ("close_krw", "size"),
            n_obs=("close_krw", "size"),
        )
        out["carbon_kr_annual"] = [
            {"year": y, "mean_krw": round(r["mean_krw"], 0), "mean_usd": round(r["mean_usd"], 2),
             "n_obs": int(r["n_obs"])}
            for y, r in agg.iterrows()
        ]
        out["carbon_source"] = "ICAP Allowance Price Explorer (KAU secondary) — data/raw/kau/"
    prices = pd.read_parquet(PROCESSED / "prices.parquet").set_index("price_id")
    for pid, label in [("P02", "elec_kr_industrial"), ("P03", "elec_jp_industrial")]:
        r = prices.loc[pid]
        out["elec_base"].append(
            {"series": label, "base_2026_usd_mwh": float(r["base_2026"]), "source": str(r["reference"]),
             "note": "연단위 시계열은 SMP/JEPX 확보 시 대체 (data/raw/{smp,jepx}/MISSING.md)"}
        )
    return out


def main() -> int:
    cal = load_calibration()
    write_artifact(
        "reference_prices",
        reference_prices(),
        cal.param_status,
        claims={
            "carbon_kr_annual": claim(EMPIRICAL, ["sigma_carbon_diffusion"],
                                      "ICAP 실측 연평균 — 모델 파라미터 아님"),
            "elec_base": claim(PROVISIONAL, ["routes_sensitivity"], "SMP/JEPX 미확보"),
        },
        note="연단위 레퍼런스 — 시나리오(config)가 모델을 구동한다",
    )
    write_artifact(
        "calibration_resolved",
        {
            "sigmas": cal.sigmas.to_dict(orient="records"),
            "correlations": cal.correlations.to_dict(orient="records"),
            "pricing": {k: {"value": v, "status": cal.param_status.get(k)} for k, v in cal.pricing.items()},
            "scenarios": cal.scenarios.to_dict(orient="records"),
            "interventions": cal.interventions.to_dict(orient="records"),
            "transaction_assumptions": cal.transaction_assumptions.to_dict(orient="records"),
            "pathways": {
                k: {"value": v, "status": cal.param_status.get(k)} for k, v in cal.pathways.items()
            },
            "derived": {
                "l_bar": cal.l_bar,
                "l_bind": cal.l_bind,
                "p_bind": cal.p_bind,
                "p_bind_definition": "Option A — p_bind(country) = Σ prob(binds=1); 별도 파라미터 없음",
                "sigma_carbon_reform": cal.sigma_carbon_reform,
                "sigma_carbon_binding": cal.sigma_carbon_binding,
                "carbon_variance_decomposition": cal.carbon_var_decomp,
                "jump_correlation_note": "점프에 확산과 동일 ρ·연σ 적용 — 근사 (Merton 비판 R2)",
                "mu_carbon": cal.mu_carbon,
                "mu_carbon_definition": (
                    "X9 — ln(ℓ̄/현물)/mu_anchor_years; anchor 이후 drift 0 (수준 유지). "
                    "수익률 전망 아님: 시나리오 수준 도달 궤도의 파생값"
                ),
                "k_offcycle_mult": cal.k_offcycle_mult,
                "t_required_source": cal.t_required_source,
                "t_required_provisional": cal.required_path_provisional,
                "t_required": cal.t_required,
                "required_pool_paths": cal.required_pool_paths,
                "required_pool_paths_definition": (
                    "S3 — 풀 연속 배치 비율 q(t) (pro-rata). required 배출 경로는 "
                    "자산 배정 계단이 아니라 q(t)로 계산; 자산 T_required는 "
                    "용량 중점 교차의 보고용 파생값 (R-6 endpoint 아티팩트 해소)"
                ),
            },
            "measured_overrides": cal.measured_overrides,
        },
        cal.param_status,
        claims={
            "derived.l_bind": claim(SCENARIO_CONDITIONAL, ["scenarios"]),
            "derived.p_bind": claim(SCENARIO_CONDITIONAL, ["scenarios"], "Option A 파생"),
            "derived.sigma_carbon_reform": claim(SCENARIO_CONDITIONAL,
                                                 ["scenarios", "sigma_carbon_diffusion"]),
            "derived.sigma_carbon_binding": claim(
                SCENARIO_CONDITIONAL,
                ["scenarios", "sigma_carbon_diffusion"],
                "E[level|bind]와 짝을 이루는 조건부 σ; charge에 p_bind를 한 번만 곱함",
            ),
            "derived.t_required": claim(PROVISIONAL, ["t_required"],
                                        "surrogate — 실증 식별된 기업 의무로 해석 금지"),
        },
        note="s02 캘리브레이션 해상본 — 이후 단계의 유일한 파라미터 소스",
    )
    print(
        f"OK — σ_unconditional KR {cal.sigma_carbon_reform['KR']:.2f} / JP {cal.sigma_carbon_reform['JP']:.2f}; "
        f"σ_binding KR {cal.sigma_carbon_binding['KR']:.2f} / JP {cal.sigma_carbon_binding['JP']:.2f}, "
        f"p_bind KR {cal.p_bind['KR']:.2f} / JP {cal.p_bind['JP']:.2f}, T_required={cal.t_required_source}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
