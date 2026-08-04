# CAP 최종 업데이트 계획 — Capital Allocation Pathway (2026-08-03, v2)

> **이 문서가 이 프로젝트의 마지막 구조 변경 계획이다.** 이후에는 데이터 수정과
> 2차 프로젝트(심화)만 있다. 진단은 `REVIEW_2026-08.md`, 이름 계보는 README 각주,
> 정리된 과거는 `archive/2026-08_final_update/TOMBSTONE.md`.
> 코어(theory 00–10, 캘리브레이션 → LSM → anatomy → 개입 엔진)는 유지한다.

## 1. 프로젝트의 최종 형태 — 세 개의 화면

제품은 세 개의 화면이고, 각 화면이 하나의 질문에 답한다.

### View 1 — LEVEL과 WEDGE: 자본은 왜, 얼마나 늦게 움직이는가

- 기업·자산별로 격차를 둘로 갈라 보여준다:
  **LEVEL** = 불확실성이 없어도 남는 순손실 (본전 격차 — 보조금의 영역),
  **WEDGE** = 불확실성이 m(σ) 문턱을 통해 만드는 추가 기다림 (계약의 영역).
- **배출효과도 같은 축으로 분해한다 (신규 확정)**: 개입을 세 부류로 태그하고
  — LEVEL 레버(CAPEX 지원·concessional), WEDGE 레버(CfD·PPA·collar의 σ-절단),
  이중 레버(carbon reform·collar: 수준과 σ를 동시에 만짐) —
  부류별 Δτ*·Δgap(MtCO₂)을 **order-averaged(Shapley)** 로 귀속시킨다.
  "LEVEL 완화가 닫는 배출량 → WEDGE 완화가 닫는 배출량" 순서의 폭포 그림이
  View 1의 헤드라인 figure다. (엔진은 이미 지원 — s06의 부류 태그와 집계만 추가)
- **GCAM 섹터 경로의 시설 배분 (단순화 확정)**: **용량 비례(pro-rata) 하나로 간다.**
  섹터 배치 풀을 자산 용량 비율로 나누되, 전환은 reline 투자창에서만 실행된다는
  제약만 유지한다. 규칙은 config 한 줄(`allocation_rule = pro_rata`)로 명시하고
  status는 `assumed`로 표기 — "배분 규칙은 단순 가정"임을 숨기지 않는 것이 방어다.
  merit-order(감축단가 순 배분) 등 정교화는 **2차 프로젝트**로 미룬다.

### View 2 — 리스크의 해부: 그 불확실성은 무엇으로 만들어져 있는가

- 드라이버별(탄소·수소·전력·원료·CAPEX) Euler 분해를 **밴드로** 보여준다.
  밴드 = 캘리브레이션 band × 노출 정의(M1) × 드라이버 분할(M2) × λ_k.
- 서술 규율: H₂ 기업은 **조성**(수소 58–83% 등), 비전환 기업은 **집중**
  (탄소정책 단일 노출 — 민간 계약 부재 영역)으로 다르게 읽는다.
- 각 성분 옆에 계약 이름과 결정 주체(joint/public/lender)를 붙인다 — 분해가
  곧 "누가 무엇을 없앨 수 있는가"의 지도가 되도록.

### View 3 — 투자자 번역: 그 리스크는 몇 bps인가 (가정은 당신 것)

- 엔진이 확정하는 것: σ_B(달러), 조성, Δσ·Δbps·순위, NPV·DSCR·break-even.
- **λ·k·p_bind·EV는 화면에서 투자자가 직접 입력한다** (기본값 = 현행 config,
  status 배지 유지). `model/api.py`의 compute(오버라이드 in → 결과 out)가
  이미 이 용도로 설계돼 있다 — 웹 슬라이더만 연결하면 된다.
- 효과: 프리미엄 수준의 식별 문제를 "우리의 가정"에서 **"당신의 가정"**으로 옮긴다.
  Δ와 순위는 λ에 강건하므로 고정 서술로 유지.

## 2. 작업 패키지 (총 ~3주)

| WP | 내용 | 산출 | 기간 |
|---|---|---|---|
| W1 | 스코프 정리: 석유화학 NCC를 `sector_enabled` config 플래그로 헤드라인 출력에서 제외(archetype 예시로 강등), Hyundai는 stranding annex 유지 | config 플래그 + 테스트 갱신 | 1일 |
| W2 | 노출 정의 축 (`exposure_model.csv`: window × elec_scope) + 드라이버 분할 축 (`partitions.csv`) → s05 envelope 확장 | `share_envelopes.json` 확장, `partition_sensitivity.json` | 4일 |
| W3 | GCAM 시설 배분: pro-rata + reline 제약을 config에 명시(`allocation_rule`, status=assumed) → s07 정합 확인 | config 명시 + 문서화 | 1일 |
| W4 | 개입 부류 태그(LEVEL/WEDGE/dual) + 부류별 Shapley Δτ*·Δgap 집계 → View 1 폭포 figure | `intervention_impacts.json` 확장 | 2일 |
| W5 | 자본흐름 집계: 자산별 K×capacity를 요구/사적 두 시간축에 얹은 연도별 프로파일, 공적자금 $당 ΔMt·Δτ* | `capital_pathway.json` (신규) | 2일 |
| W6 | View 3 계산기(웹 슬라이더 ↔ api.compute) + 웹 헤드라인 순서 교체 + 태그 `v3-final` (문서 통합·STATUS.md·테스트 갱신은 2026-08-03 선행 완료) | 웹 갱신 | 3일 |
| 이후 | **데이터 수정** (알려진 오류, PROVISIONAL 레지스트리, GCAM raw, Nippon WACC) — 공개된 envelope 안에서 점이 움직이는 작업으로 수행 | PAPER_DIFF 기록 | — |

순서 고정: W2·W3(불확실성의 그릇을 먼저) → W4·W5(내용물) → W6(화면) → 데이터.

## 3. 이미 실행된 정리 (2026-08-03)

`archive/2026-08_final_update/`로 이동 완료 (묘비: TOMBSTONE.md, 테스트 43개 통과 확인):
`subprojects/transition_decision_bridge`(s06/s13이 대체), `tmp/`(provenance 미등록 작업물),
`MILESTONE_20/30`·`PUBLIC_RELEASE_CHECKLIST`(→ `STATUS.md` 통합, 테스트 갱신 완료),
`FINANCIAL_TOOL.md`(asset-pricing 프레임 문서 — View 3가 승계). README·MODEL_CARD·PLAN·
theory/00의 정정 반영 완료, 테스트 43개 통과.

## 4. 동결 원칙

- 이 계획(§2 W1–W6, §5 T1–T6) 밖의 새 모듈·새 문서·새 governance 계층은 만들지 않는다.
- 애매한 가정(λ·k, 시나리오 확률, screening 계약 조건, GCAM surrogate)은 수정하지
  않고 status 표기로 관리한다 — λ 역산, WACC 고정점, 과점 행사, merit-order 배분은
  **2차 연구**의 범위다.
- 논문·보고의 헤드라인 체인 최종형:
  **자본이 안 움직인다(τ* vs required) → 얼마나·왜(LEVEL/WEDGE, 배출 분해) →
  무엇으로 만들어졌나(anatomy 밴드) → 누가 없애나(계약/정부) → 번역(당신의 λ로 bps).**

## 5. 툴화 로드맵 — MCP·CLI 진입점 (W6 이후 착수, ~2주)

### 5.0 구조 감사 결과 (2026-08-03, 착수 전제)

| 레이어 | 판정 | 근거 |
|---|---|---|
| config → s02 CalibrationSet | **통과** | 모든 단계(s03–s13, api)가 s02 단일 관문으로만 config 접근, pandera 검증 |
| lib (순수 함수) | **통과** | 파일 IO는 `lib/artifacts.py`(전담 writer)뿐 — 수학 모듈 전부 순수 |
| 웹 | **통과** | `outputs/*.json` 외 접근 0건 — 계산 없음 |
| 단계 간 결합 | **결함 ①** | s05·s06·s08·s09가 s04의 함수(firm_frame·firm_exposures·anatomy_for)를, s13이 s07을, api가 s03/s04/s09를 직접 import — 계산 함수가 lib이 아니라 단계 스크립트에 산다 |
| artifact 계약 | **결함 ②** | config 스키마는 있으나 **출력 JSON 스키마가 없다** — 단계 간 계약이 테스트로만 암묵 보장 |

결함 2건이 T1·T2의 근거다. 나머지 레이어는 툴화 준비 완료 상태.

### 5.1 툴 정의 — 여섯 개의 아웃풋, 하나의 엔진

| 툴 | 질문 | 입력(오버라이드 가능) | 출력 artifact | 기존 코드 |
|---|---|---|---|---|
| `cap.level` | 전환 손익은 얼마인가 | 섹터 팩, 가격 기준 | level_wedge 계열 | s12 |
| `cap.timing` | 자본은 언제 움직이나 (τ*, m(σ)) | σ·시나리오 | tau_star, wedge | s03 |
| `cap.gap` | 초과배출은 얼마나 쌓이나 | allocation_rule, T_required | condition_gap, pathways | s07 |
| `cap.anatomy` | 불확실성은 무엇으로 구성되나 | 노출 정의, 분할 | shares, envelopes | s04·s05 |
| `cap.intervene` | 어떤 계약·정책이 무엇을 바꾸나 | interventions 조건 | intervention_impacts | s06 |
| `cap.translate` | 투자자 언어로 몇 bps인가 | **λ·k·p_bind·EV (사용자 입력)** | premium, underwriting, deal | s08·s09, api |

원칙: 툴은 **읽기 전용·파일 불변**(file-invariant) 모드만 노출한다. artifact 재생성은
`make model`의 전유물 — 툴 호출이 리포 상태를 바꾸지 않는다.

### 5.2 작업 패키지

| TP | 내용 | 기간 |
|---|---|---|
| T1 | **lib 승격**: 단계 스크립트의 공유 함수(s03 solve_tau_map, s04 firm_frame·firm_exposures·anatomy_for, s07 build, s09 risk_for_project)를 `model/lib/`로 이동, 단계는 얇은 실행 래퍼로. 결함 ① 해소 | 2일 |
| T2 | **출력 스키마**: `config/schema/artifacts/`에 JSON-schema, `write_artifact`에서 검증 + result_contract 필수 필드 강제. 결함 ② 해소 | 2일 |
| T3 | **파사드 완성**: `model/api.py`를 §5.1의 6개 함수로 확장 (현행 compute·screen_transaction은 translate·intervene의 부분집합). 반환값에 result_contract·conditional_on 동봉 | 2일 |
| T4 | **CLI**: pyproject `[project.scripts]` → `cap level` … `cap translate`, JSON 출력. 문서는 README 한 절 | 1일 |
| T5 | **MCP 서버**: 6개 tool + 2개 resource(manifest, calibration_resolved). 오버라이드는 응답에 echo(가정 은폐 방지). λ 프리셋 3종(보수/중립/공격) 내장 | 3일 |
| T6 | **섹터 팩 스펙**: 팩 = `config/packs/<sector>/`(firms·routes·scenarios·anchor·provenance), s02에 `--pack` 로더. 철강 = 기준 팩, **LNG(흑자 속의 좌초) = 첫 확장 팩** 파일럿 | 2일+데이터 |

### 5.3 안전 원칙

1. 리포 분할 금지 — 진입점(CLI·MCP·웹)만 늘린다. 엔진·SSOT는 하나.
2. 어떤 진입점으로 나가든 result_contract(basis·evidence_grade·conditional_on)가
   출력에 동봉된다 — 단독 사용 시에도 경고가 벗겨지지 않는다.
3. basis가 다른 수치의 비교 금지는 툴 계층에서도 테스트로 강제한다.
4. 툴별 문서를 만들지 않는다 — 스키마 + README 한 절이 문서다.

---

## 6. 개정 (2026-08-03 저녁) — X9 구현 완료, Claude Code 인계

§2의 W-패키지에 선행하는 구조 수정 5건(S1–S5)이 확정되었다. 근거는
`FORMULA_LEDGER_2026-08-03.md`(산식·가정 전수 감사)와 `PAPER_DIFF.md` 갱신 12.
**S1은 구현 완료** — 이 세션에서 코드·config·테스트·artifact 재생성까지 마쳤다.

### 완료 (S1 — X9: 시나리오-앵커 탄소 경로)

- `lib/finance.py`: `anchored_growth_annuity` 추가 (성장 g년 후 수준 유지)
- `lib/lsm_engine.py`: `LsmSpec.mu_anchor_t` 추가, simulate_paths 시간가변 drift,
  exercise_value를 anchored annuity로 교체
- `s02_calibrate.py`: `cal.mu_carbon` 파생 (ln(ℓ̄/현물)/anchor, 국가별) + artifact 기록
- `s03_lsm.py`: build_spec이 유효 시나리오에서 μ 직접 파생; reference_l_bar 제거
- `model/api.py`: solve_tau_map 호출 단순화
- `s12_level_wedge.py`: δ = r (앵커 후 정상상태 파생값); `dp_delta` 삭제 (sheets/lsm.csv)
- 테스트: `test_carbon_drift_is_scenario_anchored` 신규, drift-consistency 갱신 — 43/44
  (1건은 Linux 샌드박스의 uv 환경 문제 — macOS 검증 필요)
- artifact 재생성 완료. 수치 이동: PAPER_DIFF 갱신 12 표.

### Claude Code 착수 지시 (순서 고정)

**T0. macOS 검증 (즉시)**: `uv sync && make all` — 44개 테스트 전부(render 포함),
anchors, ledger, 웹 빌드. theory/의 {{치환}} 수치 갱신 확인. 통과 시 커밋
(`feat(X9): scenario-anchored carbon path — no return forecasts`).

**S2. 금융비용 루프 (~3일)**: σ_B → 스프레드 → WACC → τ* 1회 반영.
`compute` 파이프라인에 `wacc_delta_from_charge` 단계 추가: 개입 후 Δcharge(bps)를
debt_share 가중으로 WACC에 반영해 τ* 재解. 고정점 반복은 금지(2차 범위) — 1회
전파만. 산출: intervention_impacts에 `delta_tau_financing_channel` 필드 분리 기록.
**수용 기준**: 실물옵션 채널과 금융 채널의 Δτ*가 별도 필드로 나올 것 (합산 전
부호를 각각 판독 가능해야 함 — PAPER_DIFF 갱신 12 판독 3 참조).

**S3. T_required 정리 (~2일)**: 비H₂ route 재정규화의 종점 아티팩트 제거 —
required 경로를 자산 배정 대신 **풀 수준 연속 경로** E_req(t) = (pool_cap−Q(t))·강도
+ Q(t)·잔여강도로 전환 (lib/pathways). 사적 경로는 자산 단위 계단 유지.
**수용 기준**: 풀 마지막 자산의 T_required가 지평말에 고정되는 성질이 사라질 것
(회귀 테스트로 고정), KOBE·JFE gap 재계산.

**S4. t_sw 정의 (~1일)**: s04의 min(τ*, T_required) → τ* 기반(사적 경로 정합)으로
교체하고 `exposure_model` 의존성 기록 갱신. View 1(못 움직인다)과 View 2(노출)가
같은 미래를 보게 됨. **수용 기준**: shares_by_firm의 t_switch_year가 tau_star와 일치.

**S5. 철강 원료 드라이버 + 연율화 (~1일)**: routes.csv 철강 행에
q_feedstock·p_feedstock(고철 1.1t/t·$400, NG 등) 활성화, route_opex_other에서 해당
상수 제거(이중계상 방지, provenance 기록). s04 charge 연율화를 annuity(wacc, 노출창)
로 정합. **수용 기준**: JFE anatomy에 feedstock 성분 등장; 탄소 100% 퇴행 해소
(S3·S4와 결합 시).

이후 §2의 W1·W2·W4·W6 재개 (W3는 S3가 대체, W5는 grant-equivalent 회계 규약 결정
전 보류). 서술 재작성 대상: theory/01·06·10의 WEDGE·σ-절단 문장 (X9·S2 결과 반영,
PAPER_DIFF 갱신 12 판독 3의 "두 채널 합산 후 확정" 원칙).

---

## 7. 검토 반영 (2026-08-04) — T0 통과, S-패키지 수정 3건 + 저자 결정 2건

**T0 완료**: macOS `uv sync && make all` — 44/44 테스트, anchors, ledger, 웹 빌드 전부 통과.
X9 커밋 완료 (`feat(X9): scenario-anchored carbon path`). S2–S5는 **아직 미구현** (계획 상태).

외부 검토(REVIEW·FORMULA_LEDGER 대조)에서 §6의 S-패키지에 수정 3건:

1. **S5 수용 기준 분리 + 순서 재고**: S4(t_sw=τ*) 이후 τ*=None 기업(JFE·KOBE·HYUNDAI)은
   전환후 창=0 → "JFE anatomy에 feedstock 등장"은 기계적으로 불가. 수용 기준을
   (a) 배관 기준(드라이버가 상태·노출에 들어감, τ* 유한한 케이스에서 성분 등장)과
   (b) 서술 기준(τ*=None의 탄소 100%는 퇴행이 아니라 **집중이라는 발견**)으로 분리.
   순서는 S3→S5→S4→S2 권고 (σ_B 측정을 고친 뒤 배선). **단 S5 자체가 X11로 OPEN** —
   저자 의도는 원료 제외(전환 프레임). X11 결정 전 S5 착수 금지.
2. **S2 식별 경계 명문화**: 금융 채널 Δτ*는 λ·k·p_bind·debt_share(전부 assumed)에
   정비례 — τ*의 λ-free 지위가 이 채널에서 끝난다. 요구사항: ① `delta_tau_financing_channel`에
   conditional_on 자동 전파, ② 점추정 금지 — λ 프리셋 3종 밴드로 출력, ③ concessional(직접
   WACC 변환)과 charge-유도 WACC 변환의 이중계상 상호배제 규약을 코드 전에 확정.
3. **p_ex 임계 절벽 테스트**: POSCO p_ex 0.55 vs threshold 0.5 — X1(±49%)·X3 어느 쪽이
   움직여도 τ* 위상이 불연속 점프 가능. threshold 밴드(0.4/0.5/0.6)에서 위상이 바뀌는
   기업을 표기하는 회귀 테스트 1건 추가 (S2 착수 전).

저자 결정 2건 등록 (DECISIONS):

- **X10 (OPEN)**: X9 앵커를 assumed 시나리오 수준 대신 **GCAM-KAIST(엄지용 그룹) 탄소가격
  경로**(1순위) 또는 NGFS로 교체. raw 데이터 provenance 등록이 선행 조건.
- **X11 (RESOLVED 2026-08-04)**: 원료는 결정론 유지 (전환 프레임). JFE·KOBE anatomy는
  집중으로 보고. S5 소멸 (R-8은 S4가 해소 — DECISIONS X11 참조).

### 구현 완료 (2026-08-04) — S2·S3·S4, 수치는 PAPER_DIFF 갱신 13

- **S3** `8296986`: required = 풀 연속 q(t) pro-rata; endpoint 아티팩트 제거
  (JFE gap +105%, KOBE +21배).
- **S4** `e7a7be4`: t_sw = τ*; H₂ 기업조차 탄소 지배로 (POSCO carbon 0.92) —
  조성 서사는 노출창 정의의 산물이었음이 확정. p_ex fragile 표기 추가.
- **S2** `af85d76`: 금융 채널 1회 전파, 별도 필드 + λ 밴드 + concessional 상호배제.
  발견: 금융 채널은 2차적 — **H₂ CfD 지연은 두 채널 합산 후에도 잔존**.

S-시리즈 종료. 다음: X10 데이터 → W1·W2·W4·W6 + theory/01·06·10 서술 재작성
(조성 서사를 "전환한 세계의 잔여 리스크"로 이동 — 갱신 13 판독).

### W1 완료 (2026-08-04) — 섹터 스코프

- **`config/sectors.csv` 신설** (SSOT): `sector, headline_enabled, status, source, theory_anchor`.
  steel=1(banded) / petrochemicals=0(assumed). pandera 스키마 + anchor 검증 대상.
  firms.csv에 sectors.csv에 없는 섹터가 있으면 s02가 실패한다 (스코프 결정 없는 섹터 금지).
- **전 artifact 레코드에 `headline_eligible` 자동 표기**: `lib/artifacts.write_artifact`가
  페이로드를 순회하며 `sector` 키를 가진 모든 레코드에 찍고, 상단에 `headline_scope` 블록을
  붙인다 (12개 artifact·66개 레코드). 이전에는 `sector` 문자열만이 archetype 구분자여서
  JSON을 직접 읽는 소비자가 계산 예시를 실증 결과로 오독할 수 있었다.
- **계산에서 빼지 않는다** — archetype은 "모델이 어떤 데이터를 요구하고 어떤 계약을
  비교하는지" 보여주는 예시로 남기고 표기로 강등한다 (계획의 "archetype 예시로 강등").
- 웹: archetype 배지를 섹터명 하드코딩 대신 `headline_eligible`로 구동.
- 고아 파일 `web/content/sample_petchem.json` 삭제 — 참조 0건인데 실제 기업명
  (LG Chem 여수·LOTTE 대산·YNCC·Mitsubishi 가시마·Sumitomo 지바)을 담고 있었다.
- **Hyundai는 stranding annex 유지** (계획대로): anatomy·premium_levels에서 제외되고
  `stranding.json`으로 분리. 철강이므로 `headline_eligible=true` — annex지만 실증 대상이다.
- 테스트 2종 신설: 전 레코드 플래그 일치, 헤드라인 집계가 archetype을 포함하지 않음. 55개 통과.

부수 효과: 감사에서 확인된 NCC archetype의 퍼버스 dτ*/dWACC 부호(PAPER_DIFF 갱신 14 §E1)가
헤드라인 밖으로 격리된다.
