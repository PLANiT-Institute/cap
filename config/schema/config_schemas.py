"""config 파일 pandera 스키마 — s02_calibrate가 로드 직후 검증."""
from __future__ import annotations

import pandera.pandas as pa
from pandera.pandas import Column, Check

STATUS = Check.isin(["measured", "banded", "assumed"])
ANCHOR = Check.str_startswith("#")

sigmas_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "driver": Column(str, unique=True),
        "value": Column(float, Check.gt(0)),
        "band_lo": Column(float, Check.gt(0)),
        "band_hi": Column(float, Check.gt(0)),
        "mu": Column(float),
        "status": Column(str, STATUS),
        "source": Column(str),
        "confidence": Column(str),
        "theory_anchor": Column(str, ANCHOR),
    },
    checks=[
        Check(lambda df: (df["band_lo"] <= df["value"]).all(), error="band_lo > value"),
        Check(lambda df: (df["value"] <= df["band_hi"]).all(), error="value > band_hi"),
    ],
)

correlations_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "driver_i": Column(str),
        "driver_j": Column(str),
        "value": Column(float, Check.in_range(-1, 1)),
        "band_lo": Column(float, Check.in_range(-1, 1)),
        "band_hi": Column(float, Check.in_range(-1, 1)),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
    }
)

pricing_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "param": Column(str, unique=True),
        "value": Column(float, Check.gt(0)),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
    }
)

lsm_schema = pa.DataFrameSchema(
    coerce=True,
    columns={"param": Column(str, unique=True), "value": Column(float)},
    strict=False,
)

# 요구 경로(required pathway) 파라미터 — 2026-08-04까지 data/raw/legacy_config yaml에서
# 직접 읽혀 규칙 1·3·4 밖에 있었다 (PAPER_DIFF 갱신 14 §C). config로 승격.
pathways_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "param": Column(str, unique=True),
        "value": Column(float),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
    },
    strict=False,
)

# p_bind 정의 = Option A (PLAN 개편 §5): p_bind(country) = Σ prob where binds=1.
# 별도 p_bind 파라미터는 존재하지 않는다 — 혼합 금지를 스키마 주석으로 명시.
scenarios_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "driver": Column(str, Check.isin(["carbon_kr", "carbon_jp", "elec_kr", "elec_jp"])),
        "scenario": Column(str),
        "level_usd": Column(float, Check.gt(0)),
        "prob": Column(float, Check.in_range(0, 1)),
        "binds": Column(int, Check.isin([0, 1])),
        "factor": Column(str, Check.isin(["domestic", "cbam_common"])),
        "anchor_note": Column(str),
    },
    checks=[
        Check(
            lambda df: (df.groupby("driver")["prob"].sum() - 1.0).abs().max() < 1e-9,
            error="driver별 prob 합 ≠ 1",
        ),
        Check(
            lambda df: (df.groupby("driver")["binds"].sum() > 0).all(),
            error="driver별 구속 시나리오 최소 1개 (p_bind 파생 조건)",
        ),
    ],
)

interventions_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "intervention_id": Column(str, unique=True),
        "label": Column(str),
        "jurisdiction": Column(str),
        "applicable_sector": Column(str, Check.isin(["all", "steel", "petrochemicals"])),
        "applicable_route": Column(str),
        "parameter": Column(str),
        "operation": Column(str, Check.isin(
            ["contract_for_difference", "multiply", "add", "shift_to_binding", "combine"])),
        "value": Column(float),
        "coverage": Column(float, Check.in_range(0, 1)),
        "basis_sigma": Column(float, Check.ge(0)),
        # 문헌 최악 basis (헤지 유효성 ≈10% 분산감소, Peña 외 2024) — PAPER_DIFF D12
        "basis_sigma_hi": Column(float, Check.ge(0)),
        "start_year": Column(int),
        "end_year": Column(int),
        "instrument_type": Column(str, Check.isin(
            ["offtake_contract", "energy_contract", "grant", "policy", "financing", "package"])),
        "decision_owner": Column(str, Check.isin(["company", "joint", "public", "lender"])),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
        "modelled_terms": Column(str),
        "diligence_terms": Column(str),
        "notes": Column(str),
        "components": Column(str, nullable=True),
    },
    checks=[
        Check(
            lambda df: (df["basis_sigma"] <= df["basis_sigma_hi"]).all(),
            error="basis_sigma > basis_sigma_hi",
        ),
    ],
)

transaction_assumptions_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "profile_id": Column(str, unique=True),
        "project_life_years": Column(int, Check.gt(0)),
        "debt_share": Column(float, Check.in_range(0, 1)),
        "debt_tenor_years": Column(int, Check.gt(0)),
        "target_dscr": Column(float, Check.gt(0)),
        "green_premium_usd_t": Column(float, Check.ge(0)),
        "annual_fee_usd_m": Column(float, Check.ge(0)),
        "upfront_fee_usd_m": Column(float, Check.ge(0)),
        "counterparty_pd_annual": Column(float, Check.in_range(0, 1)),
        "recovery_rate": Column(float, Check.in_range(0, 1)),
        "collateral_pct": Column(float, Check.in_range(0, 1)),
        "irr_ceiling": Column(float, Check.gt(0)),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
        "notes": Column(str),
    },
)

firms_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "asset_id": Column(str, unique=True),
        "firm_id": Column(str),
        "firm": Column(str),
        "sector": Column(str, Check.isin(["steel", "petrochemicals"])),
        "country": Column(str, Check.isin(["KR", "JP"])),
        "unit_number": Column(str),
        "capacity_mt_yr": Column(float, Check.gt(0)),
        "next_investment_year": Column(int),
        "emission_intensity_tco2_t": Column(float, Check.gt(0)),
        "route": Column(str),
        "category": Column(str, Check.isin(["priced_route", "no_feasible_route"])),
        "wacc": Column(float, Check.in_range(0, 1)),
        "hurdle": Column(float, Check.in_range(0, 1)),
        "ev_usd_bn": Column(float, Check.gt(0)),
        "elec_driver": Column(str),
        "output_unit": Column(str),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
    },
    strict=False,
)

routes_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "route": Column(str, unique=True),
        "sector": Column(str, Check.isin(["steel", "petrochemicals"])),
        "q_h2_kg_t": Column(float, Check.ge(0)),
        "q_elec_mwh_t": Column(float, Check.gt(0)),
        "q_feedstock_t_t": Column(float, Check.ge(0)),
        "residual_intensity_tco2_t": Column(float, Check.ge(0)),
        "k_capex_usd_t": Column(float, Check.gt(0)),
        "avoided_opex_usd_t": Column(float, Check.ge(0)),
        "route_opex_other_usd_t": Column(float, Check.ge(0)),
        "p_h2_base_usd_kg": Column(float, Check.gt(0)),
        "p_elec_base_kr_usd_mwh": Column(float, Check.gt(0)),
        "p_elec_base_jp_usd_mwh": Column(float, Check.gt(0)),
        "p_feedstock_base_usd_t": Column(float, Check.gt(0)),
        "output_unit": Column(str),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
    }
)
