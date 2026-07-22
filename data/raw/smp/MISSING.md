# MISSING — SMP 시계열

**목적**: ρ(elec, carbon)을 실측 상관으로 승격 + σ_elec(KR, SMP) 검증 (논문 σ≈0.135).
**필요**: 육지 SMP 일별(또는 월별) 가중평균, 2021-01 ~ 현재.
**출처**: 전력거래소 EPSIS (epsis.kpx.or.kr) 또는 공공데이터포털 data.go.kr
"한국전력거래소_계통한계가격" openAPI (API 키 필요 — 자동화 차단됨, 2026-07-22 시도).
**수집 방법**: EPSIS → 전력시장 → 계통한계가격 → 엑셀 다운로드, `smp_daily_YYYYMMDD.csv`
(또는 .xlsx)로 저장 → provenance 등록 → `make ingest`.
**ingest 계약**: 존재 시 `processed/smp_daily.parquet` 생성, KAU와 겹치는 기간에서
ρ(SMP, KAU) 계산해 correlations 시트의 elec_KR×carbon을 measured로 오버라이드.
