# KAU 일별 시계열 — ICAP로 확보 (2026-07-22)

**상태**: 해소. KRX 직접 다운로드는 세션 차단이었으나 ICAP Allowance Price Explorer
API(`/api/systems`, Korean ETS id=8, secondary 시장)가 KAU 일별 [USD, EUR, KRW]
2015-01-12~현재를 제공 — `icap_systems_20260722.json`으로 저장.

**역할 (계산기 원칙)**: 시계열은 모델을 구동하지 않는다.
- σ_carbon-diffusion만 **measured** 승격 (로그수익률 연율화 — s02)
- 가격 수준·추세는 시나리오(config)가 구동. 시계열은 `outputs/reference_prices.json`
  연단위 레퍼런스로만 나감 (웹 /data)

**ingest 계약**: `s01_ingest.py`가 이 JSON에서 `processed/kau_daily.parquet`
(date, close_krw, close_usd) 생성.

**갱신 방법**: `curl -sL -A "Mozilla/5.0" https://allowancepriceexplorer.icapcarbonaction.com/api/systems -o data/raw/kau/icap_systems_YYYYMMDD.json` (최신 파일이 이김) → `make all`.

**비고**: KRX 정본(`krx_kau_daily_*.csv`)이 도착하면 그것이 우선 (연물별 해상도).
레퍼런스 대조: 실측 σ=0.397 (banded 0.40 부합), 장기 endpoint 추세 0.087 (μ 앵커 0.086 부합).
