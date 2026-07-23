# 01. 노출의 존재 — 두 이론의 교집합 {#wedge}

## 주장 W1 {#claim-wedge-conjunction}

노출은 어느 한 이론이 아니라 두 이론의 결합이 정의한다.

* **실물옵션 이론** (Dixit–Pindyck): 전환이 비가역적·고비용·불확실하면 기다림이 사적 최적이다. 기업의 미전환은 비합리가 아니다.
* **탄소예산 이론** (McGlade–Ekins, stranded assets): 유한한 넷제로 예산은 그 최적이 영원할 수 없음을 뜻한다. 옵션은 언젠가 강제 행사된다.

둘을 합치면:

$$\text{timing gap}_i = \tau^*_i - T_i^{required}$$

시간 gap만으로 끝나지 않는다 — 핵심 상태는 자산 용량·배출강도를 반영한 **누적 초과배출 gap** = Σ_t max(E_private − E_required, 0)이다 (`outputs/condition_gap.json`).

사적 최적 전환연도가 시나리오 요구연도보다 늦은 만큼이 노출이다. "오늘 합리적, 내일 노출됨(rational today, exposed tomorrow)"의 형식적 내용.

`status: CLAIM`

**코드 대응**: `model/s03_lsm.py`가 τ*(전 경로 기대 전환연도)를, route별 배치 풀(surrogate)이 T_required를 산출. no_feasible_route 자산은 풀을 소비하지 않는다. **Required pathway is a provisional surrogate and must not be interpreted as an empirically identified firm mandate.**

**현행 수치**: `outputs/wedge.json`·`condition_gap.json` (POSCO 누적 gap 361 MtCO₂, 최초 이탈 2032). τ*는 예산 없는 measure — A2와 R5 참조. 사적 전환 확률이 문턱 미만인 자산(τ*=None)은 '지평 내 사적 전환 없음'으로 처리된다.
