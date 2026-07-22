"""s02: config + processed → 검증된 CalibrationSet 하나.

이후 단계(s03–s06)는 이 객체만 받는다 — 모델 코드 어디에도 숫자 리터럴 없음.
- calibration.xlsx 5시트 로드 + pandera 검증 (carbon_jump는 scenarios.csv가 우선)
- KAU/SMP/JEPX processed가 있으면 σ·ρ를 measured로 승격 (MISSING.md 계약)
- 탄소 점프혼합: σ_reform = sqrt(σ_diff² + Σp(ℓ−ℓ̄)²/ℓ̄²), 수준은 E[ℓ|bind] (A2)
- GCAM T^GCAM: raw 있으면 그것, 없으면 logistic surrogate (manifest에 출처 기록)
- 산출: outputs/calibration_resolved.json
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.schema.config_schemas import (  # noqa: E402
    correlations_schema,
    firms_schema,
    lsm_schema,
    pricing_schema,
    routes_schema,
    scenarios_schema,
    sigmas_schema,
)
from model.lib.anatomy import DRIVERS  # noqa: E402
from model.lib.artifacts import write_artifact  # noqa: E402
from model.lib.jump import binding_level, scenario_mean_level, sigma_carbon_combined  # noqa: E402

CFG = ROOT / "config"
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
TRADING_DAYS = 252  # 연율화 관례 상수 (파라미터 아님)


@dataclass
class CalibrationSet:
    sigmas: pd.DataFrame
    correlations: pd.DataFrame
    pricing: dict[str, float]
    lsm: dict[str, float]
    scenarios: pd.DataFrame
    firms: pd.DataFrame
    routes: pd.DataFrame
    param_status: dict[str, str]
    l_bar: float
    l_bind: float
    sigma_carbon_reform: float
    k_offcycle_mult: float
    t_gcam: dict[str, float]
    t_gcam_source: str
    measured_overrides: list[str] = field(default_factory=list)

    def sigma(self, driver: str) -> float:
        return float(self.sigmas.set_index("driver").loc[driver, "value"])

    def sigma_band(self, driver: str) -> tuple[float, float]:
        row = self.sigmas.set_index("driver").loc[driver]
        return float(row["band_lo"]), float(row["band_hi"])

    def mu_vector(self, elec_driver: str) -> np.ndarray:
        """드라이버 drift — DRIVERS 순서 [carbon, h2, elec, capex]."""
        s = self.sigmas.set_index("driver")["mu"]
        return np.array(
            [s["carbon_diffusion"], s["h2"], s[elec_driver], s["capex"]], dtype=float
        )

    def rho_matrix(self, elec_driver: str, carbon_sigma: float | None = None) -> tuple[np.ndarray, np.ndarray]:
        """(σ 벡터, ρ 4×4) — DRIVERS 순서 [carbon, h2, elec, capex]."""
        sig = np.array(
            [
                carbon_sigma if carbon_sigma is not None else self.sigma("carbon_diffusion"),
                self.sigma("h2"),
                self.sigma(elec_driver),
                self.sigma("capex"),
            ]
        )
        rho = np.eye(len(DRIVERS))
        pair = {(r["driver_i"], r["driver_j"]): float(r["value"]) for _, r in self.correlations.iterrows()}
        for i, di in enumerate(DRIVERS):
            for j, dj in enumerate(DRIVERS):
                if i == j:
                    continue
                v = pair.get((di, dj), pair.get((dj, di)))
                if v is not None:
                    rho[i, j] = v
        return sig, rho


def _annualized_sigma(returns: pd.Series) -> float:
    return float(returns.std() * np.sqrt(TRADING_DAYS))


def _gcam_t(firms: pd.DataFrame, lsm: dict[str, float]) -> tuple[dict[str, float], str]:
    """자산별 T^GCAM. raw CSV 우선, 없으면 legacy logistic surrogate."""
    raw_csv = RAW / "gcam" / "Q_gcam_h2dri.csv"
    legacy = yaml.safe_load((RAW / "legacy_config" / "model_parameters.yaml").read_text())
    g = legacy["gcam_nz2050"]
    if raw_csv.exists():
        q = pd.read_csv(raw_csv).sort_values("year")
        years, q_mt = q["year"].to_numpy(float), q["Q_h2dri_Mt"].to_numpy(float)
        source = "gcam_raw"
    else:
        s = g["surrogate"]
        years = np.arange(lsm["base_year"], lsm["base_year"] + lsm["horizon_years"] + 1, dtype=float)
        q_mt = s["L_Mt"] / (1.0 + np.exp(-s["k_steepness"] * (years - s["t0_inflection_yr"])))
        source = "surrogate"
    # merit order: reline이 이른 자산부터 배치 요구 (T_i_GCAM_rule의 근사 — LCOA 대신 reline 순)
    ordered = firms.sort_values("next_reline_year")
    cum_cap = ordered["crude_steel_mt_yr"].cumsum()
    out = {}
    for (idx, row), need in zip(ordered.iterrows(), cum_cap):
        reached = years[q_mt >= need]
        out[row["asset_id"]] = float(reached[0]) if len(reached) else float(years[-1])
    return out, source


def load_calibration() -> CalibrationSet:
    xlsx = CFG / "calibration.xlsx"
    sigmas = sigmas_schema.validate(pd.read_excel(xlsx, sheet_name="sigmas"))
    correlations = correlations_schema.validate(pd.read_excel(xlsx, sheet_name="correlations"))
    pricing_df = pricing_schema.validate(pd.read_excel(xlsx, sheet_name="pricing"))
    lsm_df = lsm_schema.validate(pd.read_excel(xlsx, sheet_name="lsm"))
    scenarios = scenarios_schema.validate(pd.read_csv(CFG / "scenarios.csv"))  # csv 우선 (PLAN §2.1)
    firms = firms_schema.validate(pd.read_csv(CFG / "firms.csv"))
    routes = routes_schema.validate(pd.read_csv(CFG / "routes.csv"))

    # 계산기 원칙: 가격 '수준·추세'는 시나리오(config)가 구동한다. 시계열은
    # σ·ρ 캘리브레이션과 연단위 레퍼런스에만 쓴다 (μ·base 자동 오버라이드 없음).
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
        # measured 값이 기존 band 밖이면 band를 값까지 확장 (스키마 정합)
        sigmas.loc[i, "band_lo"] = min(float(sigmas.loc[i, "band_lo"]), sig)
        sigmas.loc[i, "band_hi"] = max(float(sigmas.loc[i, "band_hi"]), sig)
        measured.append("carbon_diffusion")
    smp = PROCESSED / "smp_daily.parquet"
    if smp.exists():
        px = pd.read_parquet(smp)["smp_krw_kwh"].astype(float)
        sig = _annualized_sigma(np.log(px).diff().dropna())
        i = sigmas.index[sigmas["driver"] == "elec_kr_smp"][0]
        sigmas.loc[i, ["value", "status", "source"]] = [sig, "measured", "EPSIS SMP 연율화 (processed/smp_daily.parquet)"]
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
                correlations.loc[j, ["value", "status", "source"]] = [rho_meas, "measured", "SMP×KAU 일별 로그수익률 상관 (실측)"]
                measured.append("rho_elec_carbon")
    jepx = PROCESSED / "jepx_daily.parquet"
    if jepx.exists():
        px = pd.read_parquet(jepx)["system_price_jpy_kwh"].astype(float)
        sig = _annualized_sigma(np.log(px[px > 0]).diff().dropna())
        i = sigmas.index[sigmas["driver"] == "elec_jp"][0]
        sigmas.loc[i, ["value", "status", "source"]] = [sig, "measured", "JEPX 스팟 연율화 (processed/jepx_daily.parquet)"]
        measured.append("elec_jp")

    pricing = dict(zip(pricing_df["param"], pricing_df["value"].astype(float)))
    lsm = dict(zip(lsm_df["param"], lsm_df["value"].astype(float)))

    carbon_scen = scenarios[scenarios["driver"] == "carbon"]
    levels = carbon_scen["level_usd"].to_numpy(float)
    probs = carbon_scen["prob"].to_numpy(float)
    binds = carbon_scen["binds"].to_numpy(int)

    status: dict[str, str] = {}
    for _, r in sigmas.iterrows():
        status[f"sigma_{r['driver']}"] = r["status"]
    for _, r in correlations.iterrows():
        status[f"rho_{r['driver_i']}_{r['driver_j']}"] = r["status"]
    for _, r in pricing_df.iterrows():
        status[r["param"]] = r["status"]
    status["scenarios"] = "assumed"  # 시나리오 확률에 시장 규율 부재 (R2)
    status["ev_usd_bn"] = "assumed"
    status["firms_registry"] = str(firms["status"].mode()[0])
    status["routes_sensitivity"] = str(routes["status"].mode()[0])

    capex = pd.read_parquet(PROCESSED / "capex_refs.parquet").set_index("item_id")
    k_off = float(capex.loc["K12", "mid"]) / float(capex.loc["K11", "mid"])

    t_gcam, t_gcam_source = _gcam_t(firms, lsm)

    return CalibrationSet(
        sigmas=sigmas,
        correlations=correlations,
        pricing=pricing,
        lsm=lsm,
        scenarios=scenarios,
        firms=firms,
        routes=routes,
        param_status=status,
        l_bar=scenario_mean_level(levels, probs),
        l_bind=binding_level(levels, probs, binds),
        sigma_carbon_reform=sigma_carbon_combined(
            float(sigmas.set_index("driver").loc["carbon_diffusion", "value"]), levels, probs
        ),
        k_offcycle_mult=k_off,
        t_gcam=t_gcam,
        t_gcam_source=t_gcam_source,
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
            {"year": y, "mean_krw": round(r["mean_krw"], 0), "mean_usd": round(r["mean_usd"], 2), "n_obs": int(r["n_obs"])}
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
        uses=[],
        note="연단위 레퍼런스 — 모델 파라미터가 아님. 시나리오(config)가 모델을 구동한다",
    )
    write_artifact(
        "calibration_resolved",
        {
            "sigmas": cal.sigmas.to_dict(orient="records"),
            "correlations": cal.correlations.to_dict(orient="records"),
            "pricing": {k: {"value": v, "status": cal.param_status.get(k)} for k, v in cal.pricing.items()},
            "scenarios": cal.scenarios.to_dict(orient="records"),
            "derived": {
                "l_bar": cal.l_bar,
                "l_bind": cal.l_bind,
                "sigma_carbon_reform": cal.sigma_carbon_reform,
                "k_offcycle_mult": cal.k_offcycle_mult,
                "t_gcam_source": cal.t_gcam_source,
                "t_gcam": cal.t_gcam,
            },
            "measured_overrides": cal.measured_overrides,
        },
        cal.param_status,
        uses=list(cal.pricing.keys()) + ["scenarios"],
        note="s02 캘리브레이션 해상본 — 이후 단계의 유일한 파라미터 소스",
    )
    print(
        f"OK — σ_carbon {cal.sigma('carbon_diffusion'):.2f}→{cal.sigma_carbon_reform:.2f}, "
        f"ℓ̄={cal.l_bar:.2f}, ℓ_bind={cal.l_bind:.2f}, T_GCAM={cal.t_gcam_source}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
