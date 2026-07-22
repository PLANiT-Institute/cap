# MISSING — GCAM raw pathway (D1 BLOCKER)

**목적**: T_i^GCAM (시나리오 요구 전환연도)를 surrogate가 아닌 GCAM 원출력에서 산출.
**필요**: GCAM NZ2050 (한국/일본) 철강 부문 기술별 배치 경로 —
`Q_gcam_h2dri.csv` (컬럼: year, Q_h2dri_Mt), 가능하면 지역·기술 해상도 원본 쿼리 출력.
**출처 후보**: Zenodo 14171830, KOASAS 300934, KAIST EPRG (Eom et al. 2022).
상세 요청 명세: 구 리포 `CAP_GCAM_Data_Request.md` (data/raw/legacy_config/ 참조 아님 —
CAP_local 루트에 있음).
**현행 fallback**: `s02_calibrate.py`가 logistic surrogate
Q(t)=L/(1+exp(-k(t-t0))), L=38Mt, t0=2040, k=0.28/yr (legacy_config/model_parameters.yaml
`gcam_nz2050.surrogate`)로 T^GCAM을 생성하고 manifest에 `t_gcam_source: "surrogate"` 기록.
**해소 시**: 이 폴더에 `Q_gcam_h2dri.csv` 저장 → provenance 등록 → surrogate 자동 대체,
manifest `t_gcam_source: "gcam_raw"`.
