# 07. 원장 — proven vs conditional {#ledger-logic}

원장은 문서가 아니라 **데이터 구조**다 (PLAN §2.1). 논리는 하나: P1이 증명하는 것(조성·클러스터·서열)과 λ·p_bind에 조건부인 것(절대 bps)을 절대 섞어 말하지 않는다.

흐름: config의 `status` 컬럼 → 출력 JSON의 `conditional_on` → 웹 UI 배지까지 한 줄로 흐른다.

* `measured` — 시계열에서 실측 (예: KAU 확보 시 σ_carbon-diffusion)
* `banded` — 문헌 밴드 (s05 envelope의 입력)
* `assumed` — 가정 (λ, p_bind, k, EV, 시나리오 확률) — 이 파라미터가 수준에 들어가면 해당 artifact에 `conditional_on`이 자동으로 붙는다

**심사자 대응 프레임**: "anatomy는 구조적으로 증명되고 캘리브레이션 독립(Prop 1); 절대 수준은 조건부이며 상태와 함께 명시; 모든 숫자는 model repository의 계산 출력으로 추적 가능."

기계 생성 원장: [LEDGER.md](LEDGER.md) (`make ledger` — 손으로 고치지 말 것; 해설 섹션만 수동).
