# 01. 노출의 존재 — 두 이론의 교집합 {#wedge}

## 주장 W1 {#claim-wedge-conjunction}

노출은 어느 한 이론이 아니라 두 이론의 결합이 정의한다.

* **실물옵션 이론** (Dixit–Pindyck): 전환이 비가역적·고비용·불확실하면 기다림이 사적 최적이다. 기업의 미전환은 비합리가 아니다.
* **탄소예산 이론** (McGlade–Ekins, stranded assets): 유한한 넷제로 예산은 그 최적이 영원할 수 없음을 뜻한다. 옵션은 언젠가 강제 행사된다.

둘을 합치면:

$$\text{Exposure}_i = \tau^*_i - T_i^{GCAM}$$

사적 최적 전환연도가 시나리오 요구연도보다 늦은 만큼이 노출이다. "오늘 합리적, 내일 노출됨(rational today, exposed tomorrow)"의 형식적 내용.

`status: CLAIM`

**코드 대응**: `model/s03_lsm.py`가 τ*를, GCAM 배치곡선(현재 surrogate)이 T^GCAM을 산출. wedge는 존재 증명이고, 크기(σ_B)를 [[02_variance_premium]]에 넘긴다.

**현행 수치**: 11개 고로의 wedge는 `outputs/wedge.json` (평균 4.3년). τ*는 예산 없는 measure에서 풀린다 — [[02_variance_premium]]의 A2와 [08_referee_notes.md](08_referee_notes.md) R5 참조.
