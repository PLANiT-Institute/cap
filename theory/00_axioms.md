# 00. 목적 — 우리가 답하려는 질문 {#purpose}

기존의 모든 전환리스크 도구는 자본 배분 결정 직전에서 멈춘다. 시나리오 정합성 프레임워크(TPI, PACTA, SBTi)는 야심을 채점하고, MACC 연구는 기대비용을 주고, 등급·footprint는 과거를 보고, IAM은 세계를 그리되 기업을 그리지 않는다. 전부 유용하지만, 어느 것도 다음 문장을 산출하지 못한다:

> "이 기업의 전환리스크 프리미엄은 탄소정책 repricing 리스크 C%, 수소비용 리스크 H%, 그리드전환 리스크 E%, 자본 리스크 K%로 구성되며 — 그 이유는 이 기업이 보유한(혹은 보유를 거부한) 포지션이고 — 각 성분은 실재하는 상품으로 개별 소거 가능하다."

CAP의 산출물은 프리미엄의 수준(bps)이 아니라 이 **조성(anatomy)** 이다. 수준은 시장위험가격 λ와 탄소예산 구속확률에 조건부인 삽화로만 살아남는다. 조성은 그 둘에 독립임을 증명한다([[03_proposition1]]).

**왜 조성인가.** 배분자(allocator)에게 수준은 "얼마나 위험한가"를 말하지만, 조성은 두 가지 실행 가능한 답을 준다: (1) 어떤 노출이 섹터 공통요인이라 종목선택으로 벗을 수 없고 직접 헤지(탄소상품)가 필요한가, (2) 어떤 노출이 종목선택으로 다이얼을 돌릴 수 있는가. 그리고 계약 지도([[05_contracts_identification]])를 통해 각 성분을 소거하는 단일 상품의 이름을 댄다.

**Phase 1의 대상**: 한·일 철강 5사(POSCO, Nippon, Hyundai, JFE, Kobe) 11개 고로. 철강을 먼저 하는 이유 — 전환 route가 이산적이고 공개돼 있으며(수소환원 vs scrap-EAF), 자산이 크고 수명이 길어 타이밍 문제가 실재하고, 한국 관점에서 K-ETS·CBAM 정책 채널이 직접 물린다.

## 공리 색인

| 공리 | 내용 | 위치 |
|---|---|---|
| A1 | 리스크는 평균이 아니라 분산 | [02_variance_premium.md](02_variance_premium.md) `#axiom-variance-not-mean` |
| A2 | 부호 규약 — 예산 구속 (단일 실패 지점) | [02_variance_premium.md](02_variance_premium.md) `#axiom-budget-binds` |
| A3 | 선형 비용함수 B = aᵀX | [02_variance_premium.md](02_variance_premium.md) `#axiom-linear-cost` |
| A4 | route 감응도 배정 | [02_variance_premium.md](02_variance_premium.md) `#axiom-route-sensitivity` |
| A5 | λ 균일성 | [03_proposition1.md](03_proposition1.md) `#axiom-uniform-lambda` |

이 문서의 모든 공리·주장 블록은 anchor ID를 갖는다. config의 파라미터는 반드시 이 anchor 중 하나를 `theory_anchor`로 참조해야 하며, 참조되지 않는 공리(고아)와 근거 없는 파라미터는 `make check-anchors`에서 빌드를 깨뜨린다. **이 문서는 설명서가 아니라 시스템의 일부다.**
