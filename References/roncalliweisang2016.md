# roncalliweisang2016

> 태그: `domain:variance-premium, counters:claim-lambda-invariance, counters:contribution`
> 검증: critic 조사 기반, 원문 대조 미완 (2026-07-28) — `PAPER_DIFF.md` D2·D5 참조.

- **citekey**: roncalliweisang2016 (Roncalli & Weisang, "Risk Parity Portfolios with Risk Factors", QF 16(3), 377–388)
- **한 줄 주장**: 리스크 기여도(Euler 분산분해)를 자산이 아니라 **리스크 팩터**에 대해 정식화하고, 팩터가 상관돼 있을 때 그 분해가 **좌표계 선택(회전)에 불변이 아님**을 보인다.
- **CAP에서 쓰이는 지점**: 두 곳을 동시에 친다. ① `contribution` — "전환리스크 driver 가격 선형결합의 분산을 Euler 분해"라는 CAP의 방법론적 novelty 주장을 falsify한다. 그 수학은 이 논문에 이미 있고, CAP이 한 일은 팩터에 탄소·수소·전력·원료라는 이름을 붙인 것이다. ② `claim-lambda-invariance` — P1이 자랑하는 "scalar λ에 불변"보다 **driver 정의 자유도가 훨씬 큰 취약점**임을 보인다. CAP의 5개 driver는 강하게 상관돼 있다(탄소↔전력↔수소).
- **우리와 다른 점**: 대상이 **수익률 포트폴리오**이고 CAP은 **엔지니어링 비용함수 B=aᵀX**다. 그리고 CAP의 a는 추정된 팩터 로딩이 아니라 route별 기술 포지션에서 bottom-up으로 구성된다 — 살아남는 기여는 여기뿐이다(`09_contribution.md` 개정 반영).
- **인용할 문장·수치**: 상관 팩터에 대한 리스크 기여도의 회전 비불변성 (QF 2016, 16(3), pp. 377–388). 이 비판은 현재 R1–R6 어디에도 없다 → **referee note 신설 후보**.
