"""s12: LEVEL/WEDGE decomposition — the closed-form approximation lane.

Formalizes the knowledge-base prototype (Day-5, 2026-07-24) under the repo's
rules. Everything the toy hardcoded is derived here from config (DECISIONS,
unification U1):

  gap coefficients   ← config/routes.csv sensitivity vector a (no base_diff,
                       no h2_slope literals — they are q·p products)
  σ, ρ, μ            ← config/sheets (via CalibrationSet)
  carbon prices      ← country regimes (dated spot for the private view — X6)
  capex annuity life ← config/transaction_assumptions.csv

Two corrections over the toy, from the 2026-07-29 verification note:

  1. The DP trigger multiple m(σ) is fed the PROJECT sigma estimated from the
     exposure-weighted cost basket — not σ_carbon. Feeding σ_carbon attributes
     the entire project volatility to one driver and overstates the carbon
     wedge (carbon is ~18% of gap variance at current prices, not dominant).
  2. The per-driver dollar-volatility decomposition is reported alongside, so
     "which σ matters" is answered by exposure×σ, not raw σ.

Approximation status (stated, not hidden): m(σ)=β/(β−1) is the perpetual-
option closed form (McDonald–Siegel / Dixit–Pindyck). The definition of
record for private timing remains the finite-horizon LSM τ* (s03). This
artifact carries its own basis_id and must not be cited against LSM wedges.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.artifacts import MODEL_CONDITIONAL, claim, write_artifact  # noqa: E402
from model.lib.result_contract import LEVEL_WEDGE_BASIS, LEVEL_WEDGE_METRIC  # noqa: E402
from model.s02_calibrate import CalibrationSet, load_calibration  # noqa: E402

DRIVERS = ["carbon", "h2", "elec", "feedstock", "capex"]


def crf(rate: float, years: float) -> float:
    """Capital recovery factor — annualizes k_capex the LCOA way."""
    if rate <= 0:
        return 1.0 / years
    return rate * (1 + rate) ** years / ((1 + rate) ** years - 1)


def dp_multiple(sigma: float, r: float, delta: float) -> float:
    """Perpetual-option trigger multiple m = β/(β−1) (Dixit–Pindyck closed form)."""
    mm = (r - delta) / sigma**2
    beta = 0.5 - mm + np.sqrt((mm - 0.5) ** 2 + 2 * r / sigma**2)
    return float(beta / (beta - 1.0))


def firm_level_wedge(cal: CalibrationSet, firm_rows, reform: bool) -> dict:
    """Capacity-weighted LEVEL and WEDGE for one firm's configured route."""
    meta = firm_rows.iloc[0]
    country = meta["country"]
    route = cal.routes.set_index("route").loc[meta["route"]]
    wacc = float(meta["wacc"])
    life = float(cal.transaction_assumptions.iloc[0]["project_life_years"])

    p_elec = float(
        route["p_elec_base_kr_usd_mwh"] if country == "KR" else route["p_elec_base_jp_usd_mwh"]
    )
    carbon_spot = float(
        cal.pricing["carbon_base_kr"] if country == "KR" else cal.pricing["carbon_base_jp"]
    )
    terms = {
        "h2_usd_t": float(route["q_h2_kg_t"]) * float(route["p_h2_base_usd_kg"]),
        "elec_usd_t": float(route["q_elec_mwh_t"]) * p_elec,
        "feedstock_usd_t": float(route["q_feedstock_t_t"]) * float(route["p_feedstock_base_usd_t"]),
        "other_opex_usd_t": float(route["route_opex_other_usd_t"]),
        "capex_annuity_usd_t": float(route["k_capex_usd_t"]) * crf(wacc, life),
        "avoided_opex_usd_t": float(route["avoided_opex_usd_t"]),
    }

    # asset-level dEmis (intensity − residual), capacity-weighted to the firm
    residual = float(route["residual_intensity_tco2_t"])
    caps = firm_rows["capacity_mt_yr"].to_numpy(float)
    demis = firm_rows["emission_intensity_tco2_t"].to_numpy(float) - residual
    demis_cw = float((demis * caps).sum() / caps.sum())

    carbon_price = float(cal.l_bind[country]) if reform else carbon_spot
    level = (
        terms["h2_usd_t"] + terms["elec_usd_t"] + terms["feedstock_usd_t"]
        + terms["other_opex_usd_t"] + terms["capex_annuity_usd_t"]
        - terms["avoided_opex_usd_t"] - demis_cw * carbon_price
    )
    level = max(0.0, level)

    # driver dollar-vol: |per-tonne exposure| × σ_k  (verification-note method)
    elec_driver = meta["elec_driver"]
    sigma_carbon = cal.sigma_carbon_binding[country] if reform else cal.sigma("carbon_diffusion")
    sig, rho = cal.rho_matrix(elec_driver, carbon_sigma=sigma_carbon)
    exposure = np.array([
        demis_cw * carbon_price,
        terms["h2_usd_t"],
        terms["elec_usd_t"],
        terms["feedstock_usd_t"],
        terms["capex_annuity_usd_t"],
    ])
    dollar_vol = exposure * sig
    gross = float(exposure.sum())
    total_var = float(dollar_vol @ rho @ dollar_vol)
    sigma_gap_usd = float(np.sqrt(max(total_var, 0.0)))
    sigma_project = sigma_gap_usd / gross if gross > 0 else 0.0

    # X9: δ는 가정 상수(dp_delta)가 아니라 파생 — 시나리오-앵커 경로에서 앵커 도달
    # 이후 기대성장 0 ⇒ δ = r − 0 = r. 이 폐형해 레인은 수렴 후 세계(정상상태)의
    # 대기 프리미엄을 근사한다. 수렴 전 구간의 타이밍은 LSM(s03)의 소관.
    delta = wacc
    m_project = dp_multiple(sigma_project, wacc, delta) if sigma_project > 0 else 1.0
    m_carbon_only = dp_multiple(sigma_carbon, wacc, delta)

    contrib = dollar_vol * (rho @ dollar_vol)  # Euler split of gap variance
    var_shares = contrib / total_var if total_var > 0 else np.zeros(len(DRIVERS))

    return {
        "country": country,
        "route": str(meta["route"]),
        "wacc": wacc,
        "carbon_price_used_usd_tco2": carbon_price,
        "demis_capacity_weighted_tco2_t": demis_cw,
        "gap_terms_usd_t": terms,
        "level_gap_usd_t": level,
        "driver_dollar_vol_usd_t": dict(zip(DRIVERS, dollar_vol.tolist())),
        "gap_variance_shares": dict(zip(DRIVERS, var_shares.tolist())),
        "sigma_project": sigma_project,
        "trigger_multiple_project": m_project,
        "wedge_usd_t": (m_project - 1.0) * level,
        "legacy_attribution": {
            "note": (
                "toy method — m(sigma_carbon) attributes ALL project volatility to "
                "carbon; kept for lineage, do not cite"
            ),
            "sigma_carbon": float(sigma_carbon),
            "trigger_multiple_carbon_only": m_carbon_only,
            "wedge_usd_t_overstated": (m_carbon_only - 1.0) * level,
        },
    }


REFORM_KEYS = (
    "carbon_price_used_usd_tco2", "level_gap_usd_t", "gap_variance_shares",
    "sigma_project", "trigger_multiple_project", "wedge_usd_t",
)


def build(cal: CalibrationSet) -> dict:
    firms = []
    steel = cal.firms[(cal.firms["sector"] == "steel") & (cal.firms["category"] == "priced_route")]
    for fid, rows in steel.groupby("firm_id", sort=True):
        base = firm_level_wedge(cal, rows, reform=False)
        reform = firm_level_wedge(cal, rows, reform=True)
        firms.append({
            "firm_id": fid,
            "firm": rows.iloc[0]["firm"],
            "base": base,
            "reform": {k: reform[k] for k in REFORM_KEYS},
        })
    return {
        "result_contract": {
            "metric_id": LEVEL_WEDGE_METRIC,
            "basis_id": LEVEL_WEDGE_BASIS,
            "evidence_grade": "MODEL_CONDITIONAL",
            "uncertainty": "perpetual-option closed form; capex annuity life; delta = r (X9 post-anchor steady state, no assumed dp_delta)",
            "interpretation": "intuition and cross-check for the LSM lane, not a pricing output",
        },
        "firms": firms,
    }


def main() -> int:
    cal = load_calibration()
    data = build(cal)
    write_artifact(
        "level_wedge",
        data,
        cal.param_status,
        claims={
            "firms.level_gap_usd_t": claim(
                MODEL_CONDITIONAL,
                ["routes_sensitivity", "firms_registry", "carbon_base_kr", "carbon_base_jp",
                 "transaction_assumptions"],
                "Marshallian gap at base prices — closed by level instruments (subsidy/CCfD strike)",
            ),
            "firms.wedge_usd_t": claim(
                MODEL_CONDITIONAL,
                ["sigma_carbon_diffusion", "sigma_h2", "rho_h2_elec", "routes_sensitivity",
                 "transaction_assumptions"],
                "waiting premium from the exposure-weighted project σ — cut by σ-truncating "
                "contracts; NOT the LSM wedge (separate basis_id)",
            ),
        },
        note=(
            "LEVEL/WEDGE closed-form approximation lane — coefficients derived from routes.csv "
            "(no literals); m(σ) fed the exposure-weighted project σ, not σ_carbon "
            "(verification note 2026-07-29). Definition of record for private timing is the "
            "LSM τ* (s03); do not compare across bases."
        ),
    )
    print(
        f"OK — level/wedge closed-form lane for {len(data['firms'])} steel firms "
        "(project-σ fed; carbon-only multiple kept as lineage)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
