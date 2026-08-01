# 06. 해석 층 — 배분자의 독법 {#allocator-reading}

두 클러스터는 "수소 기업 vs 전력 기업"이 아니라 **에너지 전환의 어느 부분이 도래하는가에 대한 두 개의 베팅**이다:

* **H₂-route** (POSCO, Nippon): 수소경제의 도래에 short. 프리미엄이 그린수소의 비용·가용성에 지배됨 (현행 파이프라인: H₂ 73.2%–81.4%, carbon 6.7%–21.8%).
* **Scrap/가스-route** (JFE, Kobe — Hyundai는 A4에 따라 stranding 분리, [08_referee_notes.md](08_referee_notes.md) R3): 그리드의 전환에 short. H₂ = 0, 탄소 지배 (97.7%–100.0%). 한국 전력노출은 규제요금 pass-through(σ≈0.12 — 전력 가면을 쓴 정책리스크)와 SMP(σ≈0.14)로 분해되고, 일본의 높은 σ_elec=0.22는 전자의 부재(JEPX 자유화).
* **Petrochemical routes (provisional archetypes)**: e-cracker는 전력과 나프타 원료, cracker+CCUS는 포집 후 잔여탄소와 원료, circular-olefins는 circular feedstock의 가격·품질·mass-balance에 short다. 이 분리는 현행 route 원단위와 가정된 σ·ρ의 귀결이며 기업 실증 발견이 아니다.

**배분 함의**: 탄소정책 repricing은 **공통요인** — anatomy에 든 전 기업이 지므로(carbon share 1.8%–100.0%) 섹터 내 종목선택으로 벗을 수 없고 탄소상품 직접 헤지만이 소거한다. 수소·전력·원료 리스크는 route 선택으로 바뀌는 **선택 가능 노출**이다. 따라서 섹터 선택과 종목/기술 선택을 같은 차트에서 보되, archetype을 실측 기업처럼 비교하지 않는 것이 중요하다.

`status: INTERPRETATION · mix는 model-conditional (scalar λ·p_bind에만 항등 불변) — 수치는 outputs/*.json 라이브 주입`
