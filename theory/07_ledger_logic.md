# 07. 원장 — proven vs conditional {#ledger-logic}

원장은 문서가 아니라 **데이터 구조**다. 파라미터 status(measured/banded/assumed)와 별개로 **claim 수준 상태**가 있다:

| 상태 | 의미 |
|---|---|
| IDENTITY | 수학적 항등 (share 합=1, scalar λ·p_bind 소거) |
| MODEL_CONDITIONAL | 노출 정의·전환시점 규칙·B=aᵀX 구조에 조건부 (share가 여기) |
| SCENARIO_CONDITIONAL | 시나리오 수준·확률에 조건부 (risk charge가 여기) |
| EMPIRICAL | 관측자료 검증 (σ_carbon-diffusion 등) |
| PROVISIONAL | surrogate·미확정 데이터 (T_required) |
| OPEN | 미구현·미검증 (SDF 식별, 점프리스크 분리) |

각 artifact의 `claims` 블록이 result별 status와 depends_on을 기록한다 — artifact 전체 단위의 'proven' 딱지는 없다.

흐름: config의 `status` 컬럼 → 출력 JSON의 `conditional_on` → 웹 UI 배지까지 한 줄로 흐른다.

* `measured` — 시계열에서 실측 (예: KAU 확보 시 σ_carbon-diffusion)
* `banded` — 문헌 밴드 (s05 envelope의 입력)
* `assumed` — 가정 (λ, k, EV, 시나리오 확률; p_bind는 시나리오에서 파생) — depends_on에 있으면 `conditional_on`으로 집계된다

**심사자 대응 프레임**: "share는 scalar pricing scale에 항등 불변(P1)이되 model-conditional; 절대 수준은 conditional risk charge로 상태와 함께 명시; 모든 숫자는 lineage(manifest 해시·claims)로 추적 가능."

기계 생성 원장: [LEDGER.md](LEDGER.md) (`make ledger` — 손으로 고치지 말 것; 해설 섹션만 수동).
