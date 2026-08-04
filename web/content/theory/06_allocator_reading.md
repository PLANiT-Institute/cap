# 06. 해석 층 — 배분자의 독법 {#allocator-reading}

**먼저 노출창 정정 (S4, 2026-08-04)**: 이전 판은 클러스터를 "조성 vs 집중"으로 갈랐다.
그 대비는 노출을 **요구 시점 전환**으로 계산했을 때의 산물이었다. 노출창을 사적 최적
τ*로 정합시키면(View 1과 View 2가 같은 미래를 봄) **전환 route와 무관하게 탄소가 지배한다**
— τ*≈2050까지의 전환 전 탄소 노출이 전환 후 투입물 노출을 압도하기 때문이다.
따라서 아래 두 베팅은 **전환이 실제로 일어난 세계**(요구 경로 또는 개입 패키지)의 독법이고,
사적 경로의 독법은 "전 기업이 탄소정책 집중 + 늦은 전환"이다 (PAPER_DIFF 갱신 13).

전환 후 세계에서 두 클러스터는 "수소 기업 vs 전력 기업"이 아니라 **에너지 전환의 어느 부분이 도래하는가에 대한 두 개의 베팅**이다:

* **H₂-route** (POSCO, Nippon): 수소경제의 도래에 short. 전환 후 잔여 리스크가 그린수소의 비용·가용성에 물린다 (사적 경로 현행값: H₂ 7.0%–16.4%, carbon 79.7%–92.0% — 위 정정대로 탄소 지배).
* **Scrap/가스-route** (JFE, Kobe — Hyundai는 A4에 따라 stranding 분리, [08_referee_notes.md](08_referee_notes.md) R3): 그리드의 전환에 short. H₂ = 0, 탄소 지배 (100.0%–100.0%). 이들은 τ*=None(사적 전환 없음)이므로 집중이 **발견**이다 — 정부만 만질 수 있는 단일 노출. 한국 전력노출은 규제요금 pass-through(σ≈0.12 — 전력 가면을 쓴 정책리스크)와 SMP(σ≈0.14)로 분해되고, 일본의 높은 σ_elec=0.22는 전자의 부재(JEPX 자유화).
* **Petrochemical routes (provisional archetypes)**: e-cracker는 전력과 나프타 원료, cracker+CCUS는 포집 후 잔여탄소와 원료, circular-olefins는 circular feedstock의 가격·품질·mass-balance에 short다. 이 분리는 현행 route 원단위와 가정된 σ·ρ의 귀결이며 기업 실증 발견이 아니다.

**배분 함의**: 탄소정책 repricing은 **공통요인** — anatomy에 든 전 기업이 지므로(carbon share 7.6%–100.0%) 섹터 내 종목선택으로 벗을 수 없고 탄소상품 직접 헤지만이 소거한다. 수소·전력·원료 리스크는 route 선택으로 바뀌는 **선택 가능 노출**이다. 따라서 섹터 선택과 종목/기술 선택을 같은 차트에서 보되, archetype을 실측 기업처럼 비교하지 않는 것이 중요하다.

`status: INTERPRETATION · mix는 model-conditional (scalar λ·p_bind에만 항등 불변) — 수치는 outputs/*.json 라이브 주입`
