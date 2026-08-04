# 00. 목적 — 우리가 답하려는 질문 {#purpose}

기존의 모든 전환리스크 도구는 자본 배분 결정 직전에서 멈춘다. 시나리오 정합성 프레임워크(TPI, PACTA, SBTi)는 야심을 채점하고, MACC 연구는 기대비용을 주고, 등급·footprint는 과거를 보고, IAM은 세계를 그리되 기업을 그리지 않는다. 전부 유용하지만, 어느 것도 다음 문장을 산출하지 못한다:

> "이 기업의 전환리스크 프리미엄은 탄소정책 repricing C%, 수소 H%, 전력 E%, 원료 F%, 자본 K%로 구성되며 — 그 이유는 이 기업이 보유한(혹은 보유를 거부한) 기술 포지션이고 — 각 성분은 실재하는 계약으로 개별 변환 가능하다."

CAP(Capital Allocation Pathway)의 핵심 질문은 이것이다:

> **"전환 자본은 왜 탄소중립으로 흐르지 않는가, 언제·얼마나 필요한가, 무엇이 그것을 움직이는가."**

그 계산적 형태:

> **"CAP maps the gap between privately optimal and required decarbonization pathways into a conditional distribution of transition cash-flow losses, decomposes its sources, and evaluates which interventions change both transition timing and residual risk."**

격차의 언어: **LEVEL**(불확실성이 없어도 남는 본전 격차 — 보조금의 영역)과
**WEDGE**(불확실성이 m(σ) 문턱을 통해 만드는 추가 기다림 — 계약의 영역)([[10_level_wedge]]).
기다림은 사적으로 합리적이지만 리스크를 없애지 않는다 — gap으로 쌓는다.
리스크 프리미엄(bps)은 이 구조의 투자자 번역층이며 헤드라인이 아니다.

인과 순서: 현재 자산 구성 → 사적 최적 감축경로(τ*) → 요구 감축경로(T_required) → **condition gap** (누적 초과배출) → gap의 경제적 원인 → 개입 후 바뀐 전환시점·경로 → 잔여 위험 anatomy → **conditional risk charge**. 감축경로가 원인이고, condition gap이 핵심 상태이며, anatomy는 설명이고, premium은 조건부 결과다.

조성(share)은 scalar λ·p_bind에는 항등적으로 불변이지만([[03_proposition1]]), 노출 모델·시나리오·전환시점·캘리브레이션에는 조건부다 — "calibration-independent"가 아니다. 현재 구현은 정확한 시장위험프리미엄을 증명하지 않는다.

**왜 조성인가.** 배분자(allocator)에게 수준은 "얼마나 위험한가"를 말하지만, 조성은 두 가지 실행 가능한 답을 준다: (1) 어떤 노출이 섹터 공통요인이라 종목선택으로 벗을 수 없고 직접 헤지(탄소상품)가 필요한가, (2) 어떤 노출이 종목선택으로 다이얼을 돌릴 수 있는가. 그리고 계약 지도([[05_contracts_identification]])를 통해 각 성분을 소거하는 단일 상품의 이름을 댄다.

**Phase 1의 대상**: 한·일 철강 5사(POSCO, Nippon, Hyundai, JFE, Kobe) 11개 고로 —
5사 조강 생산의 **약 1/3(기업별 21–48%)에 해당하는 부분 함대**이며 전 설비가 아니다.
따라서 기업 전체 EV로 나눈 bps는 기업 간 비교에 쓸 수 없다 (DECISIONS X12); $/t와 Δ·순위는 무영향. 철강을 먼저 하는 이유 — 전환 route가 이산적이고 공개돼 있으며(수소환원 vs scrap-EAF), 자산이 크고 수명이 길어 타이밍 문제가 실재하고, 한국 관점에서 K-ETS·CBAM 정책 채널이 직접 물린다.

**Sector extension**: 동일한 CAP 구조를 석유화학 NCC에 적용하되, 노출벡터에 원료를 추가하고 e-cracker·cracker+CCUS·circular-olefins를 별도 route로 둔다. 현행 두 NCC는 제품 검증용 archetype이며 용량·EV·WACC·기술경제성·T_required가 `assumed/provisional`이다. 따라서 석유화학 숫자는 기업 실증 결과가 아니라 모델이 어떤 데이터를 요구하고 어떤 계약을 비교하는지 보여주는 계산 사례다.

## 공리 색인

| 공리 | 내용 | 위치 |
|---|---|---|
| A1 | 리스크는 평균이 아니라 분산 | [02_variance_premium.md](02_variance_premium.md) `#axiom-variance-not-mean` |
| A2 | 부호 규약 — 예산 구속 (단일 실패 지점) | [02_variance_premium.md](02_variance_premium.md) `#axiom-budget-binds` |
| A3 | 선형 비용함수 B = aᵀX | [02_variance_premium.md](02_variance_premium.md) `#axiom-linear-cost` |
| A4 | route 감응도 배정 | [02_variance_premium.md](02_variance_premium.md) `#axiom-route-sensitivity` |
| A5 | λ 균일성 | [03_proposition1.md](03_proposition1.md) `#axiom-uniform-lambda` |

이 문서의 모든 공리·주장 블록은 anchor ID를 갖는다. config의 파라미터는 반드시 이 anchor 중 하나를 `theory_anchor`로 참조해야 하며, 참조되지 않는 공리(고아)와 근거 없는 파라미터는 `make check-anchors`에서 빌드를 깨뜨린다. **이 문서는 설명서가 아니라 시스템의 일부다.**
