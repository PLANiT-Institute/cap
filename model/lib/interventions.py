"""Intervention engine — 계약·정책을 σ=0 스위치가 아니라 파라미터 변환으로.

config/interventions.csv의 행을 (route, country)별 유효 파라미터로 변환한다.
근사 두 가지를 명시한다:
- coverage 결합: σ_eff = (1−cov)·σ + cov·basis  (동일 driver 내 가법 근사)
- basis는 점추정이 아니라 밴드다: basis_case="lo"|"hi"가 basis_sigma / basis_sigma_hi를 고른다.
  전력계약 헤지 유효성 실측이 낮다는 문헌(Peña 외 2024) 때문 — PAPER_DIFF D12.
- tenor: [start,end] 창을 지평 대비 비율로 가중 (시간가변 LSM 대신 1차 근사)
숫자는 전부 config에서 온다.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from .jump import (
    binding_level,
    scenario_mean_level,
    sigma_carbon_binding,
    sigma_carbon_combined,
)


@dataclass
class CarbonRegime:
    l_bar: float
    l_bind: float
    p_bind: float
    sigma_unconditional: float
    sigma_binding: float
    scenarios: pd.DataFrame


@dataclass
class ParamSet:
    """한 (route, country)의 유효 파라미터 — base 또는 intervention 적용 후."""
    p_h2: float
    sigma_h2: float
    p_elec: float
    sigma_elec: float
    p_feedstock: float
    sigma_feedstock: float
    k_capex_mult: float
    wacc_delta: float
    carbon: CarbonRegime
    applied: tuple[str, ...] = ()
    double_count_warning: bool = False


def _window_frac(row: pd.Series, base_year: float, horizon: float) -> float:
    span = max(0.0, min(float(row["end_year"]), base_year + horizon) - max(float(row["start_year"]), base_year))
    return min(1.0, span / horizon)


def carbon_regime(scen: pd.DataFrame, sigma_diff: float) -> CarbonRegime:
    levels = scen["level_usd"].to_numpy(float)
    probs = scen["prob"].to_numpy(float)
    binds = scen["binds"].to_numpy(int)
    return CarbonRegime(
        l_bar=scenario_mean_level(levels, probs),
        l_bind=binding_level(levels, probs, binds),
        p_bind=float(probs[binds.astype(bool)].sum()),
        sigma_unconditional=sigma_carbon_combined(sigma_diff, levels, probs),
        sigma_binding=sigma_carbon_binding(sigma_diff, levels, probs, binds),
        scenarios=scen.copy(),
    )


def reform_shift(scen: pd.DataFrame, shift: float) -> pd.DataFrame:
    """carbon_reform: 비구속(SQ) 확률의 shift 비율을 구속 시나리오로 비례 재배분."""
    out = scen.copy()
    nonbind = out["binds"] == 0
    moved = float(out.loc[nonbind, "prob"].sum()) * shift * 0.5  # 절반 이전 (notes 정의)
    out.loc[nonbind, "prob"] = out.loc[nonbind, "prob"] * (1 - shift * 0.5)
    bind_probs = out.loc[~nonbind, "prob"]
    out.loc[~nonbind, "prob"] = bind_probs + moved * bind_probs / bind_probs.sum()
    return out


def base_params(cal, route_row: pd.Series, country: str, elec_driver: str) -> ParamSet:
    p_elec = float(
        route_row["p_elec_base_kr_usd_mwh"] if country == "KR" else route_row["p_elec_base_jp_usd_mwh"]
    )
    return ParamSet(
        p_h2=float(route_row["p_h2_base_usd_kg"]),
        sigma_h2=cal.sigma("h2"),
        p_elec=p_elec,
        sigma_elec=cal.sigma(elec_driver),
        p_feedstock=float(route_row["p_feedstock_base_usd_t"]),
        sigma_feedstock=cal.sigma("feedstock"),
        k_capex_mult=1.0,
        wacc_delta=0.0,
        carbon=CarbonRegime(
            l_bar=cal.l_bar[country],
            l_bind=cal.l_bind[country],
            p_bind=cal.p_bind[country],
            sigma_unconditional=cal.sigma_carbon_reform[country],
            sigma_binding=cal.sigma_carbon_binding[country],
            scenarios=cal.carbon_scenarios(country).copy(),
        ),
    )


def apply_interventions(
    cal,
    route: str,
    country: str,
    elec_driver: str,
    ids: list[str],
    *,
    base_year_override: float | None = None,
    horizon_override: float | None = None,
    basis_case: str = "lo",
) -> ParamSet:
    route_row = cal.routes.set_index("route").loc[route]
    ps = base_params(cal, route_row, country, elec_driver)
    base_year = (
        float(cal.lsm["base_year"])
        if base_year_override is None
        else float(base_year_override)
    )
    horizon = (
        float(cal.lsm["horizon_years"])
        if horizon_override is None
        else float(horizon_override)
    )
    table = cal.interventions.set_index("intervention_id")
    basis_col = {"lo": "basis_sigma", "hi": "basis_sigma_hi"}[basis_case]

    def expand(ids_: list[str]) -> list[str]:
        out: list[str] = []
        for i in ids_:
            row = table.loc[i]
            if row["operation"] == "combine":
                out.extend(str(row["components"]).split(";"))
            else:
                out.append(i)
        return out

    applied = []
    flat = expand(ids)
    for iid in flat:
        row = table.loc[iid]
        route_sector = str(route_row["sector"])
        if row["applicable_sector"] != "all" and row["applicable_sector"] != route_sector:
            continue
        if row["applicable_route"] != "all" and row["applicable_route"] != route:
            continue
        wf = _window_frac(row, base_year, horizon)
        cov_t = float(row["coverage"]) * wf  # coverage × tenor 비율 (1차 근사)
        op, param = row["operation"], row["parameter"]
        if op == "contract_for_difference" and param == "p_h2_and_sigma":
            ps = replace(
                ps,
                p_h2=cov_t * float(row["value"]) + (1 - cov_t) * ps.p_h2,
                sigma_h2=(1 - cov_t) * ps.sigma_h2 + cov_t * float(row[basis_col]),
            )
        elif op == "contract_for_difference" and param == "p_elec_and_sigma":
            ps = replace(
                ps,
                p_elec=cov_t * float(row["value"]) + (1 - cov_t) * ps.p_elec,
                sigma_elec=(1 - cov_t) * ps.sigma_elec + cov_t * float(row[basis_col]),
            )
        elif op == "contract_for_difference" and param == "p_feedstock_and_sigma":
            ps = replace(
                ps,
                p_feedstock=cov_t * float(row["value"]) + (1 - cov_t) * ps.p_feedstock,
                sigma_feedstock=(1 - cov_t) * ps.sigma_feedstock
                + cov_t * float(row[basis_col]),
            )
        elif op == "multiply" and param == "k_capex":
            ps = replace(ps, k_capex_mult=ps.k_capex_mult * float(row["value"]))
        elif op == "add" and param == "wacc":
            warn = ps.double_count_warning or ("capex_subsidy" in applied)
            ps = replace(ps, wacc_delta=ps.wacc_delta + float(row["value"]), double_count_warning=warn)
        elif op == "shift_to_binding" and param == "carbon_scenarios":
            scen = reform_shift(cal.carbon_scenarios(country), float(row["value"]))
            ps = replace(ps, carbon=carbon_regime(scen, cal.sigma("carbon_diffusion")))
        applied.append(iid)
    return replace(ps, applied=tuple(applied))
