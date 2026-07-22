# KAU 일별 시계열 — ICAP로 확보 (2026-07-22)

**상태**: 해소. KRX 직접 다운로드는 세션 차단이었으나 ICAP Allowance Price Explorer
API(`/api/systems`, Korean ETS id=8, secondary 시장)가 KAU 일별 [USD, EUR, KRW]
2015-01-12~현재를 제공 — `icap_systems_20260722.json`으로 저장.

**ingest 계약**: `s01_ingest.py`가 이 JSON에서 `processed/kau_daily.parquet`
(date, close_krw, close_usd) 생성. `s02`가 σ_carbon-diffusion(로그수익률 연율화)·
μ_carbon(로그선형 추세)·carbon_base_kr(최근 종가 USD)을 **measured**로 승격.

**갱신 방법**: `curl -sL -A "Mozilla/5.0" https://allowancepriceexplorer.icapcarbonaction.com/api/systems -o data/raw/kau/icap_systems_YYYYMMDD.json` (최신 파일이 이김) → provenance 패턴 자동 매칭 → `make all`.

**비고**: KRX 정본(`krx_kau_daily_*.csv`)이 도착하면 그것이 우선한다 (연물별 해상도).
검증: ICAP 실측 σ=0.397·μ=0.085 — 기존 banded 0.40·0.086과 부합.
