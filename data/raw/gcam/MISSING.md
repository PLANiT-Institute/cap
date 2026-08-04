# GCAM raw pathway — 확보 현황 (2026-08-04 조사 결과로 전면 갱신)

## 확보 (이 폴더에 있음, provenance 등록됨)

`gcam_kaist_1p0_NZ2050_korea_ghg_constraint.xml` (+ `_noLUC` 대조판, `.csv` 파생)
= **GCAM-KAIST 1.0의 한국 NZ2050 정책 입력** — 경제 전체 GHG 배출 제약:

| 연도 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 | 2055~ |
|---|---|---|---|---|---|---|---|
| MtCO2e | 691 | 558 | 435 | 312 | 189 | 66 | ~5 |

출처: Zenodo 10.5281/zenodo.14171830 (Kim Hanwoong, Princeton, 2024-11-15, **CC BY 4.0**).
`configuration_NZ2050_Final / _NoCCS / _Nuc / _Nuc_NoCCS` 네 개 전부 `1p5_incr_UC_kor_LUC.xml`을
로드한다 (DECISIONS X7이 지목한 **NZ2050_limCCS = configuration_NZ2050_NoCCS**).

## 미확보 — 그리고 **이 모델에서는 원리적으로 나오지 않는 것**

### 1. 철강 H₂-DRI 배치 경로 (`Q_gcam_h2dri.csv`) — GCAM-KAIST 1.0에는 없다

직접 확인(2026-08-04): GCAM-KAIST 1.0은 **GCAM v5.2** 확장이고, 모든 NZ2050 config가 로드하는
산업 입력 `industry_New_HW.xml`의 supplysector는 **세 개뿐**이다 —
`industry`, `industrial energy use`, `industrial feedstocks`.
철강·iron·DRI·EAF·blast furnace 기술 **0건** (grep 확인). 논문(Eom et al. 2022) 본문도
"산업부문은 정제·시멘트·비료를 제외한 모든 산업활동"의 **집계 부문**이라고 명시한다.

→ **GCAM-KAIST NZ2050(_limCCS)은 철강 기술별 배치 경로를 산출할 수 없다.**
   `legacy_config/model_parameters.yaml`의 `deployment_2050_Mt: 38` /
   `deployment_2050_Mt_source: "GCAM NZ2050 Korea scenario"` 표기는 **사실과 다르다**
   (PAPER_DIFF 갱신 14에 기록. raw는 읽기전용이므로 파일 자체는 수정하지 않는다).

### 2. 탄소가격 경로 — GCAM-KAIST에서는 **내생 shadow price**

정책이 배출 **제약**으로 들어가므로 탄소가격은 모델 **출력**(shadow price)이다.
Zenodo 자료는 input only — 출력 DB는 미공개. 따라서 X10("GCAM 탄소가격 넣기")은
저자 요청 또는 다른 출처가 필요하다.

### 3. 철강 분해 GCAM이 있는 올바른 출처 (저자 요청 대상)

**Lee, McJeon, Yu, Liu, Kim, Eom (2024), "Decarbonization pathways for Korea's industrial
sector towards its 2050 carbon neutrality goal", J. Cleaner Production 476:143749** —
DRI-EAF-H₂를 명시적으로 다루는 산업부문 GCAM 논문 (엄지용 교수 공저). 유료·데이터 미공개.
요청 항목: (a) iron & steel 기술별 배치 경로(연도×기술, Mt 또는 share),
(b) 시나리오별 탄소 shadow price 경로, (c) 시나리오 정의.

### 4. 공개 대안 (탄소가격만, 2035 지평)

GCAM-ROK — Choi, Park, McJeon (2025 preprint, SNU+KAIST): KR ETS 가격
**8,870 KRW/tCO2** (현행정책, 2023 수준 고정) → **30,411 KRW/tCO2** (강화 시나리오, 2035, CCfD).
주의: 같은 논문의 `$42→$84/tCO2`는 **CCS 보조금**(IRA 45Q 유사)이며 탄소가격이 아니다.
Data-availability가 지목한 GitHub(`choiHenry/gcam-core@cht/proj/korea-2035`)를 확인한 결과
committed output은 **표준 GCAM Core 진단자료(Core_Ref, 2017-03-11)**뿐이고, 한국 시나리오
출력은 비공개 로컬 XML DB(`/data/project/tae/gcam-core`) 쿼리로만 생성된다 — 실제 출력 미공개.

## 현행 fallback (변경 없음)

`s02_calibrate.py`가 logistic surrogate Q(t)=L/(1+exp(−k(t−t0))), L=38Mt, t0=2040, k=0.28/yr로
풀 경로를 만들고 `t_required_source: "surrogate"`, 자산 `headline_eligible: False`로 기록한다.
S3(2026-08-04) 이후 비H₂ 풀은 endpoint 재정규화 없이 **비율 곡선**을 쓴다.

## 해소 시

`Q_gcam_h2dri.csv` (컬럼: year, Q_h2dri_Mt) 를 이 폴더에 저장 → provenance 등록 →
s02가 자동으로 surrogate를 대체, manifest `t_required_source`가 `mixed`/`gcam_raw`로 바뀐다.

---

## 저자 요청 명세 (2026-08-04 작성 — 발송은 저자 판단)

**대상**: Hanju Lee · Haewon McJeon · Sha Yu · Yang Liu · Hanwoong Kim · **Jiyong Eom**,
"Decarbonization pathways for Korea's industrial sector towards its 2050 carbon neutrality
goal", *Journal of Cleaner Production* **476** (2024) 143749.
(공개 연락처: hmcjeon@kaist.ac.kr — GCAM-ROK 논문 교신저자로 공개돼 있음. Eom 교수는
KAIST Green Growth & Sustainability.)

**요청 항목** (CAP이 실제로 소비하는 형태로):

1. `Q_gcam_h2dri.csv` — 컬럼 `year, Q_h2dri_Mt`. 한국 iron & steel 부문의
   **DRI-EAF-H₂ 배치 경로** (조강 Mt/yr 또는 부문 점유율). 시나리오별로 분리.
   → CAP의 요구 경로 surrogate(logistic L=38, t0=2040, k=0.28)를 대체한다.
2. 같은 시나리오의 **탄소 shadow price 경로** (연도 × USD/tCO2, 실질 기준연도 명기).
   → X10. CAP의 시나리오 표(SQ/MSR/CBAM)를 근거 있는 경로로 교체.
3. 시나리오 정의 (CCS 가용성·수소 가용성 제약의 구체적 수치)와 GCAM 버전.
4. 가능하면 iron & steel 기술별(BF, BF-CCS, DRI-EAF, DRI-EAF-H₂, EAF-scrap) 산출 분해.

**요청 시 밝힐 것**: CAP은 이 경로를 **요구 경로 벤치마크**로만 쓰고 기업별 사적 최적
전환시점(τ*)과의 격차를 계산한다. 재배포는 하지 않으며 출처·라이선스를 명기한다.
현행 대용물이 GCAM 출력이 아니라 분석자 가정이라는 점을 이미 문서화했다
(PAPER_DIFF 갱신 14 §A).

**대안 (요청 불가 시)**: NGFS Phase V Scenario Explorer (IIASA) — GCAM/REMIND/MESSAGE,
한국·일본, shadow carbon price 다운로드 가능. 철강 기술 해상도는 없다.
