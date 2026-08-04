# GCAM-KAIST 1.0 (Zenodo 14171830) 추출 결과

수집일: 2026-08-03 / 출처: https://zenodo.org/records/14171830 (CC-BY-4.0)

| 파일 | SHA256 |
|---|---|
| Configration_GCAM-KAIST_1.0.zip | 4bc75904a220bc9b6d8ab5a2f5051e11fb0464686726957ec191406e9e5be423 |
| Input_Korea_GCAM-KAIST_1.0.zip | 8265b7e692398e250a099a69921100dc5bef258a4eb0f9813d3acca4b78dae97 |
| Input_default_GCAM-KAIST_1.0.zip | 4a450acf15ecca888a9e704164ae6cc22aedcf3fb6e626658e45b020fda39344 |

## 핵심 발견 (두 개의 블로커)

### 1. 결과값이 없다 — 입력 XML만 있음
Zenodo 설명의 "input files and database"에서 database는 **입력 XML 묶음**이지
solved BaseX 출력 DB가 아니다. 281개 파일 전부 `<scenario>` 입력.
따라서 **전력가격(`Price|Secondary Energy|Electricity`), 발전믹스, 배출경로 등
내생 결과는 이 패키지에서 얻을 수 없다.** GCAM을 직접 빌드·실행해야 한다.

### 2. 철강 부문이 없다 — CAP의 D1 블로커는 이 데이터로 해소 불가
`industry.xml`의 subsector는 `coal / gas / electricity / hydrogen / biomass /
refined liquids / district heat / industry` — **연료별 집계**다.
`steel`, `iron` 문자열이 전체 입력에 0회 등장.
GCAM v5.x 계열이라 detailed iron & steel 부문이 도입되기 전 버전.
→ `data/raw/gcam/MISSING.md`의 `Q_gcam_h2dri.csv`는 **원리적으로** 이 버전에서 나올 수 없다.
→ 상세 철강 부문이 있는 **GCAM v7 기반 릴리스**(github.com/GCAM-KAIST/gcam-kaist7-release)를
   요청해야 한다.

## 추출한 파일 (전부 가정값 = 입력)

| 파일 | 내용 | 행 |
|---|---|---|
| `gcam_kaist_scenario_map.csv` | 5개 시나리오 ↔ config ↔ 스위치 매핑 | 5 |
| `korea_carbon_policy_trajectories.csv` | 한국 탄소정책 궤적 (constraint MtCO2e / fixedTax) | 194 |
| `korea_elec_tech_cost_assumptions.csv` | 한국 전원별 capital-overnight, FCR, O&M | 822 |

### 시나리오 축 (config diff로 확인)
5개 시나리오는 정확히 세 개의 스위치만 다르다:

- **탄소정책**: `curpol`은 정책파일 없음 / NZ2050 4종은 `1p5_incr_UC_kor_LUC.xml` (배출제약)
- **CCS**: `Cstorage.xml` ↔ `Cstorage_NoCCS.xml`
- **원전**: `electricity_water_HW.xml` ↔ `..._Nur.xml`

### 탄소가격 단위 주의
`fixedTax`는 GCAM 관례상 **1990$/tC**. LEDS_Med는 2025년 170 → 2050년 325.
CSV의 `value_2020USD_per_tCO2` 열은 44/12로 나누고 GDP 디플레이터 1.73을 곱한 값
(2025년 ≈ $80, 2050년 ≈ $153). **디플레이터는 내가 가정한 값이므로 `assumed` 처리 필요.**

`1p5_incr_UC_kor.xml`은 가격이 아니라 **배출제약**: 2025년 675.5 → 2050년 37 MtCO2e.
이 경우 탄소가격은 shadow price로 내생 결정되며, 그 값도 결과 DB에만 존재한다.

### 전원 기술비용 (1975$/kW, FCR 0.13 전 기술 동일)
| 기술 | 2020 | 2030 | 2040 | 2050 |
|---|---|---|---|---|
| coal (conv pul) | 900 | 700 | 500 | 419 |
| coal (conv pul CCS) | 1556 | 1067 | 750 | 629 |
| gas (CC) | 222 | 222 | 222 | 222 |
| Gen_III (원전) | 1681 | 1591 | 1504 | 1408 |
| PV | 345 | 277 | 246 | 220 |
| wind | 414 | 339 | 307 | 274 |
| wind_offshore | 794 | 573 | 413 | 299 |

## CAP 반영 시 처리

`data/raw/`는 읽기 전용 + provenance 필수라 여기(`tmp/`)에 뒀다.
정식 등록하려면 `DATA_PROVENANCE.md`에 위 SHA256 3줄을 추가하고
`data/raw/gcam/zenodo_14171830/`로 옮길 것.
단, **현행 logistic surrogate는 유지**해야 한다 — 이 데이터가 대체하지 못한다.
`MISSING.md`는 "Zenodo 14171830" 후보를 **기각**으로 갱신 권장.
