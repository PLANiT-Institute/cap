# LOGIC_MAP — CAP과 GCAM의 보완 구조, 데이터 흐름, 시각 산출물

> 2026-08-01, 업데이트 계획 v4 기준. 상세 파이프라인은 [ARCHITECTURE.md](../ARCHITECTURE.md),
> 승격 규약은 [CONTRIBUTING.md](../CONTRIBUTING.md) / [DATA_INTERFACE.md](../DATA_INTERFACE.md)가 정본.

**한 줄 정의 (v4).** CAP은 GCAM 섹터 경로를 자산·기업에 배분하고, 사적(private) 경로와
비교해 필요 조건을 역산하며, 다시 섹터로 재합산해 검산하는 **번역·정렬 엔진**이다.
GCAM은 섹터까지만 안다 — 기업과 설비가 없다. 그 missing middle이 CAP의 자리다.

## 1. GCAM 브리지

경로 3종 분리(P7): `gcam_sector_pathway`(IAM_SOURCED) / `required_*_pathway`(CAP_DOWNSCALED)
/ `private_*_pathway`(CAP_MODELED). required 배분에 private economics 금지(P8),
재합산 등식 없이는 "GCAM과 연결됐다" 주장 금지(P6).

```mermaid
flowchart TB
  subgraph GCAM["GCAM-KAIST (IAM_SOURCED)"]
    G1["섹터 배출·기술 경로<br/>limCCS + CurPol/NZ2050/lowH2 밴드"]
    G2["3표 스키마: sector_pathways ·<br/>technology_pathways · prices"]
  end
  subgraph BRIDGE["CAP Bridge — gcam_bridge.py (Phase 3)"]
    B1["배분 규칙 (P8: private economics 배제)<br/>하드제약: 가능 route만 · reline 이전 전환불가 ·<br/>용량초과 금지 · 기술별 합계 = GCAM"]
  end
  subgraph FIRM["기업·자산 층"]
    R1["required 경로 (CAP_DOWNSCALED)<br/>T_required = Downscale(GCAM, 자산대장, 배분규칙)"]
    P1["private 경로 (CAP_MODELED)<br/>LSM 교환옵션 → 자산별 τ*"]
  end
  W["wedge = τ* − T_required<br/>→ anatomy (탄소/수소/전력/자본 %분해)<br/>→ premium · 개입 효과"]
  RC["재합산 검산 (P6)<br/>sector_reconciliation + residual_sector<br/>기술별·총생산 0.1% · 배출 1%"]
  G1 --> B1
  G2 --> B1
  B1 --> R1
  R1 --> W
  P1 --> W
  R1 --> RC
  RC -. "등식 불성립 = 연결 주장 금지" .-> GCAM
```

현재 GCAM 원시 데이터 미도착(`data/raw/gcam/MISSING.md`), `scenario=surrogate`로 구동.
도착 시 곡선만 교체하고 **순위 안정성 테스트가 헤드라인 robustness**가 된다(Phase 4-1).

## 2. 데이터 흐름 — Drive 지식기지 → 리포 → 산출물

```mermaid
flowchart LR
  subgraph DRIVE["Drive 지식기지 (탐구 자유)"]
    D1["01_Knowledge — 문헌 PDF · 노트"]
    D2["02_Data — CAP_DS_&lt;이름&gt;.xlsx<br/>raw / clean / export 3시트"]
    D3["05_Paper — 원고 (수치 손기입 금지)"]
  end
  subgraph REPO["이 리포 = SSOT (승격은 관문)"]
    R0["data/raw/&lt;dataset&gt;/*.csv<br/>+ provenance.yaml 등록 필수"]
    R1["make ingest → parquet<br/>(보간 없음 · NaN 유지)"]
    R2["config/sheets · firms · routes · scenarios<br/>(모든 수치의 SSOT)"]
    R3["s02 CalibrationSet"]
    R4["s03 LSM τ* → s04 anatomy → s05 robustness →<br/>s06 개입 → s07 경로 → s08–s09 금융 심사"]
    R5["outputs/*.json = 공개 API<br/>manifest.json (git SHA · 해시 · seed)"]
  end
  W["web/content → 사이트 (계산 없음)"]
  D2 -- "export → 날짜 CSV" --> R0
  R0 --> R1 --> R3
  R2 --> R3 --> R4 --> R5 --> W
  D3 -. "수치는 artifact 인용" .- R5
  D1 -. "검증 스탬프 노트만 → References/" .-> REPO
```

| 승격 레인 | 관문 |
|---|---|
| 데이터 | export 시트 → 날짜 CSV → `data/raw/` + provenance 등록 → `make ingest` (미등록 파일 실패) |
| 파라미터 | `DECISIONS.md` 등록 → 결정 → config 반영 → `PAPER_DIFF.md` 기록 |
| 이론·주장 | anchor ID + config 역참조 + 테스트 — 양방향 검사 깨지면 빌드 실패 |
| 문헌 | PDF는 Drive 보관, 리포에는 검증 스탬프 노트만 (`References/`) |

## 3. 시각 산출물 (Phase 5)

시각 규약: required **진녹 실선+밴드** / private **주황** / intervention **파랑 점선** /
BAU **회색** / gap 반투명 면적 / residual 회색 사선 / surrogate=회색·점선, GCAM=실선·유색 /
동일 축(2025–2050) / 경로 차트 뒤 reconciliation 필수.

1. **그림 1 "척추"** — 상단 GCAM 배치곡선 vs 사적 집계(음영=섹터 gap), 하단 기업별 stacked 분해.
2. **그림 2 자산 타임라인(Gantt)** — 고로별 reline 창 + τ* + T_required 한 축, censored는 "≥" 화살표.
3. **그림 3 탄소가격 사다리** — 현물 → 시나리오 → CBAM → shadow price, 국가별 세로축.

덱 8단: GCAM 도착점 → missing middle → bridge 구조도 → 기업 small multiples →
자산 타임라인 → gap waterfall → reconciliation 패널 → 정책 수렴.

### artifact ↔ 그림 매핑

| 스테이지 | artifact | 시각물 |
|---|---|---|
| s03 | `tau_star` · `wedge` | 그림 2 마커 (CAP_MODELED) |
| s02+bridge | `calibration_resolved` · (신설) `sector_reconciliation` | 그림 1 상단 · reconciliation 패널 |
| s04 | `shares_by_firm` · `premium_levels` · `stranding` | anatomy stacked bar · 프리미엄 표 |
| s05 | `share_envelopes` · `lambda_invariance` · `cluster_separation` | envelope 밴드 · P1 불변성 그리드 |
| s06–s07 | `intervention_impacts` · `emissions_pathways_by_firm` · `condition_gap` | 그림 1 하단 · gap waterfall |
| s08–s09 | `transition_underwriting` · `deal_screening` | 스프레드 표면 · 딜 스크린 표 |
