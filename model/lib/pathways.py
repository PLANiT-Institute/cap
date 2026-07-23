"""자산별 연간 배출 경로 + condition gap (개편 §2).

모든 계산은 자산별로 수행한 뒤 기업 수준으로 합산한다 — 기업 평균 전환연도를
먼저 만드는 방식 금지. 경로:
  BAU        전 지평 현행 강도 유지 (폐쇄·전환 없음 — 명시적 기준선)
  private    자산별 τ*에 route 전환; τ* 없으면 미전환
  required   자산별 T_required에 전환; T_required 없음(no_feasible)이면 미전환 유지
  intervention  τ*(C)로 private 재계산
gap:
  timing_gap_i = τ*_i − T_required_i
  annual_alignment_gap_t = max(E_private(t) − E_required(t), 0)
  cumulative_alignment_gap = Σ_t annual_gap_t
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def asset_annual_emissions(
    capacity_mt: float,
    intensity_now: float,
    intensity_after: float,
    switch_year: float | None,
    years: np.ndarray,
) -> np.ndarray:
    """MtCO₂/yr. switch_year=None → 전 지평 미전환."""
    e = np.full(len(years), capacity_mt * intensity_now, dtype=float)
    if switch_year is not None:
        e[years >= switch_year] = capacity_mt * intensity_after
    return e


def firm_pathway(
    assets: pd.DataFrame,
    switch_years: dict[str, float | None],
    years: np.ndarray,
    residual_by_route: dict[str, float],
) -> dict:
    """자산별 배출 합산 → 기업 경로. assets: priced+stranding 전부 (BAU 합산용은 호출자 책임)."""
    total = np.zeros(len(years))
    transitioned_cap = np.zeros(len(years))
    per_asset = {}
    for _, a in assets.iterrows():
        sw = switch_years.get(a["asset_id"])
        e = asset_annual_emissions(
            float(a["capacity_mt_yr"]),
            float(a["emission_intensity_tco2_t"]),
            residual_by_route.get(a["route"], float(a["emission_intensity_tco2_t"])),
            sw,
            years,
        )
        total += e
        if sw is not None:
            transitioned_cap += np.where(years >= sw, float(a["capacity_mt_yr"]), 0.0)
        per_asset[a["asset_id"]] = e
    return {
        "emissions_mtco2": total,
        "cumulative_mtco2": np.cumsum(total),
        "transitioned_capacity_mt": transitioned_cap,
        "per_asset": per_asset,
    }


def condition_gap(private: np.ndarray, required: np.ndarray, years: np.ndarray) -> dict:
    annual = np.maximum(private - required, 0.0)
    misaligned = annual > 0
    first = int(years[misaligned][0]) if misaligned.any() else None
    restored = None
    if misaligned.any():
        after = np.where(misaligned)[0][-1]
        restored = int(years[after + 1]) if after + 1 < len(years) else None
    return {
        "annual_alignment_gap_mtco2": annual,
        "cumulative_alignment_gap_mtco2": float(annual.sum()),
        "peak_annual_gap_mtco2": float(annual.max()),
        "first_misalignment_year": first,
        "alignment_restored_year": restored,
    }
