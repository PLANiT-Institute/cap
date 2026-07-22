# MISSING — JEPX 현물 시계열 (선택)

**목적**: σ_elec(JP)=0.22 (banded) 검증.
**필요**: JEPX 스팟 시스템프라이스 일별 평균, 2021 ~ 현재.
**출처**: jepx.jp → 取引情報 → スポット市場 → spot_summary CSV (봇 차단으로 자동화 실패, 2026-07-22).
**수집 방법**: 브라우저 다운로드 → `spot_summary_YYYY.csv` 저장 → provenance 등록.
**ingest 계약**: 존재 시 `processed/jepx_daily.parquet` 생성, σ_elec_JP 검증치 리포트.
