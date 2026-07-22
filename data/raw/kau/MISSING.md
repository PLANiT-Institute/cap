# MISSING — KAU 일별 시계열

**목적**: σ_carbon-diffusion을 `banded`(0.40)에서 `measured`로 승격.
**필요**: KAU(할당배출권) 일별 종가·거래량, 2021-01 ~ 현재. KAU24/KAU25 등 연물별.
**출처**: KRX 배출권시장 정보플랫폼 (data.krx.co.kr → 배출권시장 → 일별매매정보,
화면 MDCSTAT15801). 웹 다운로드는 세션 기반이라 자동화 차단됨(2026-07-22 시도, OTP 거부).
**수집 방법**: 브라우저에서 CSV 다운로드 → 이 폴더에 `krx_kau_daily_YYYYMMDD.csv`로 저장
→ `DATA_PROVENANCE.md` 등록 → `make ingest`.
**ingest 계약**: 파일이 존재하면 `s01_ingest.py`가 `processed/kau_daily.parquet` 생성,
`s02`가 로그수익률 연율화 σ를 계산해 sigmas 시트의 carbon_diffusion을 measured로 오버라이드.
