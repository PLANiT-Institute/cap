"""Phase 1 ingest: data/raw → data/processed 표준화.

규칙 (PLAN Phase 1):
- raw는 절대 수정하지 않는다. processed는 이 스크립트로만 생성.
- 날짜 ISO, 통화 USD 컬럼 + 원통화 병기 (fx는 config pricing 시트에서 — 코드 리터럴 금지).
- 결측은 NaN 유지, 임의 보간 금지.
- provenance 미등록 raw 파일이 있으면 실패 (scripts/provenance.py 선행 실행).
- KAU/SMP/JEPX 파일이 존재하면 시계열 parquet 생성 (MISSING.md의 ingest 계약).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
sys.path.insert(0, str(ROOT))

from config.schema.config_schemas import pricing_schema  # noqa: E402

assets_out_schema = pa.DataFrameSchema(
    {
        "asset_id": Column(str, unique=True),
        "company": Column(str),
        "country": Column(str, Check.isin(["KR", "JP"])),
        "crude_steel_mt_yr": Column(float, Check.gt(0)),
        "next_reline_year_est": Column("Int64"),
        "emission_intensity_tco2_t": Column(float, Check.gt(0)),
    },
    strict=False,
)

financials_out_schema = pa.DataFrameSchema(
    {
        "company": Column(str),
        "currency_local": Column(str),
        "revenue_local_tn": Column(float, nullable=True),
        "revenue_usd_bn": Column(float, nullable=True),
    },
    strict=False,
)


def load_fx() -> dict[str, float]:
    pricing = pd.read_csv(ROOT / "config" / "sheets" / "pricing.csv")
    pricing_schema.validate(pricing)
    vals = dict(zip(pricing["param"], pricing["value"]))
    return {"KR": vals["fx_usdkrw"], "JP": vals["fx_usdjpy"]}


def ingest_assets() -> None:
    df = pd.read_csv(RAW / "assets" / "assets_blast_furnace.csv")
    df["next_reline_year_est"] = df["next_reline_year_est"].astype("Int64")
    for col in ("capacity_mt_yr", "crude_steel_mt_yr", "emission_intensity_tCO2_t"):
        df[col] = df[col].astype(float)
    df = df.rename(columns={"emission_intensity_tCO2_t": "emission_intensity_tco2_t"})
    assets_out_schema.validate(df)
    df.to_parquet(PROCESSED / "assets.parquet", index=False)


def ingest_financials(fx: dict[str, float]) -> None:
    df = pd.read_csv(RAW / "financials" / "company_financials.csv")
    df["currency_local"] = df["country"].map({"KR": "KRW", "JP": "JPY"})
    rate = df["country"].map(fx)
    for col in ("revenue", "op_profit", "ibd_debt", "equity", "interest"):
        df[f"{col}_local_tn"] = df[col + "_tn"].astype(float)
        # tn local / (local per USD) = tn USD → ×1000 = bn USD
        df[f"{col}_usd_bn"] = df[f"{col}_local_tn"] / rate * 1e3
        df = df.drop(columns=[col + "_tn"])
    financials_out_schema.validate(df)
    df.to_parquet(PROCESSED / "financials.parquet", index=False)


def ingest_simple_tables() -> None:
    pd.read_csv(RAW / "production" / "company_production.csv").to_parquet(
        PROCESSED / "production.parquet", index=False
    )
    pd.read_csv(RAW / "opex_energy" / "intensity_coefficients.csv").to_parquet(
        PROCESSED / "intensities.parquet", index=False
    )
    pd.read_csv(RAW / "opex_energy" / "price_parameters.csv").to_parquet(
        PROCESSED / "prices.parquet", index=False
    )
    pd.read_csv(RAW / "capex_refs" / "capex_h2dri_references.csv").to_parquet(
        PROCESSED / "capex_refs.parquet", index=False
    )
    pd.read_csv(RAW / "research" / "CAP_instruments_2026-07-03.csv").to_parquet(
        PROCESSED / "instruments.parquet", index=False
    )


def ingest_optional_timeseries() -> list[str]:
    """KAU/SMP/JEPX — 존재할 때만. 반환: 생성된 시계열 이름."""
    made = []
    kau_files = sorted(RAW.glob("kau/krx_kau_daily_*.csv"))
    icap_files = sorted(RAW.glob("kau/icap_systems_*.json"))
    if kau_files:  # KRX 정본이 ICAP보다 우선 (MISSING.md 계약)
        frames = [pd.read_csv(f, encoding="utf-8-sig") for f in kau_files]
        df = pd.concat(frames, ignore_index=True)
        date_col, close_col = df.columns[0], df.columns[1]
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d"),
                "close_krw": pd.to_numeric(df[close_col], errors="coerce"),
            }
        ).dropna(subset=["date"]).sort_values("date")
        out.to_parquet(PROCESSED / "kau_daily.parquet", index=False)
        made.append("kau_daily")
    elif icap_files:
        import json

        systems = json.loads(icap_files[-1].read_text())  # 최신 파일
        korea = next(s for s in systems if s["name"].startswith("Korean Emissions"))
        rows = [
            {"date": dt, "close_usd": v[0], "close_krw": v[2]}
            for dt, v in sorted(korea["values"]["secondary"].items())
            if v and v[0] is not None and v[2] is not None
        ]
        pd.DataFrame(rows).to_parquet(PROCESSED / "kau_daily.parquet", index=False)
        made.append("kau_daily(icap)")
    smp_files = sorted(RAW.glob("smp/smp_daily_*.csv"))
    if smp_files:
        df = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in smp_files], ignore_index=True)
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(df[df.columns[0]]).dt.strftime("%Y-%m-%d"),
                "smp_krw_kwh": pd.to_numeric(df[df.columns[1]], errors="coerce"),
            }
        ).dropna(subset=["date"]).sort_values("date")
        out.to_parquet(PROCESSED / "smp_daily.parquet", index=False)
        made.append("smp_daily")
    jepx_files = sorted(RAW.glob("jepx/spot_summary_*.csv"))
    if jepx_files:
        df = pd.concat(
            [pd.read_csv(f, encoding="shift-jis") for f in jepx_files], ignore_index=True
        )
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(df[df.columns[0]], errors="coerce").dt.strftime("%Y-%m-%d"),
                "system_price_jpy_kwh": pd.to_numeric(df[df.columns[1]], errors="coerce"),
            }
        ).dropna(subset=["date"]).sort_values("date")
        out.to_parquet(PROCESSED / "jepx_daily.parquet", index=False)
        made.append("jepx_daily")
    return made


def main() -> int:
    check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "provenance.py")], cwd=ROOT
    )
    if check.returncode != 0:
        return check.returncode
    PROCESSED.mkdir(parents=True, exist_ok=True)
    fx = load_fx()
    ingest_assets()
    ingest_financials(fx)
    ingest_simple_tables()
    made = ingest_optional_timeseries()
    n = len(list(PROCESSED.glob("*.parquet")))
    print(f"OK — processed {n} tables; optional timeseries: {made or 'none (MISSING.md 참조)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
