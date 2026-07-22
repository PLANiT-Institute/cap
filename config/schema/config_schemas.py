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

scenarios_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "driver": Column(str, Check.isin(["carbon", "elec_kr", "elec_jp"])),
        "scenario": Column(str),
        "level_usd": Column(float, Check.gt(0)),
        "prob": Column(float, Check.in_range(0, 1)),
        "binds": Column(int, Check.isin([0, 1])),
        "anchor_note": Column(str),
    },
    checks=[
        Check(
            lambda df: (df.groupby("driver")["prob"].sum() - 1.0).abs().max() < 1e-9,
            error="driver별 prob 합 ≠ 1",
        )
    ],
)

firms_schema = pa.DataFrameSchema(
    coerce=True,
    columns={
        "asset_id": Column(str, unique=True),
        "firm_id": Column(str),
        "firm": Column(str),
        "country": Column(str, Check.isin(["KR", "JP"])),
        "crude_steel_mt_yr": Column(float, Check.gt(0)),
        "next_reline_year": Column(int),
        "emission_intensity_tco2_t": Column(float, Check.gt(0)),
        "route": Column(str),
        "category": Column(str, Check.isin(["priced_route", "no_feasible_route"])),
        "wacc": Column(float, Check.in_range(0, 1)),
        "hurdle": Column(float, Check.in_range(0, 1)),
        "ev_usd_bn": Column(float, Check.gt(0)),
        "elec_driver": Column(str),
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
        "q_h2_kg_t": Column(float, Check.ge(0)),
        "q_elec_mwh_t": Column(float, Check.gt(0)),
        "residual_intensity_tco2_t": Column(float, Check.ge(0)),
        "k_capex_usd_t": Column(float, Check.gt(0)),
        "avoided_opex_usd_t": Column(float, Check.ge(0)),
        "route_opex_other_usd_t": Column(float, Check.ge(0)),
        "p_h2_base_usd_kg": Column(float, Check.gt(0)),
        "p_elec_base_kr_usd_mwh": Column(float, Check.gt(0)),
        "p_elec_base_jp_usd_mwh": Column(float, Check.gt(0)),
        "status": Column(str, STATUS),
        "source": Column(str),
        "theory_anchor": Column(str, ANCHOR),
    }
)
