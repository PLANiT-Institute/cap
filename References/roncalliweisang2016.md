# roncalliweisang2016

> 태그: `domain:variance-premium, counters:claim-lambda-invariance, counters:contribution, supports:referee-7`
> 검증: **부분 확인 (2026-07-29)** — 저자 공개본 전문 대조. ⓐ는 확인, ⓑ는 **원문이 말하는 바가 다르다**.
> 이전 노트의 "회전 비불변성" 서술은 과장이었고 아래에서 교체했다.

- **citekey**: roncalliweisang2016 (Roncalli & Weisang, "Risk Parity Portfolios with Risk Factors", QF 16(3), 377–388)
- **한 줄 주장**: 리스크 기여도(Euler 분산분해)를 자산이 아니라 **리스크 팩터**에 대해 정식화한다. 팩터 수가 자산 수보다 많은 **중복(redundant) 시스템에서는 팩터 기여도가 유일하게 결정되지 않는다**(식별 실패).
- **CAP에서 쓰이는 지점**: ① `contribution` — "전환리스크 driver 가격 선형결합의 분산을 Euler 분해"라는 CAP의 방법론적 novelty 주장을 falsify한다. 그 수학은 이 논문에 이미 있고, CAP이 한 일은 팩터에 탄소·수소·전력·원료라는 이름을 붙인 것이다. ② `referee-7`·`claim-lambda-invariance` — 팩터 기여도가 팩터 **시스템 구성 방식**에 의존한다는 것, 즉 P1의 "scalar λ에 불변"이 자유도의 일부만 덮는다는 것.
- **우리와 다른 점**: 대상이 **수익률 포트폴리오**이고 CAP은 **엔지니어링 비용함수 B=aᵀX**다. 그리고 CAP의 a는 추정된 팩터 로딩이 아니라 route별 기술 포지션에서 bottom-up으로 구성된다 — 살아남는 기여는 여기뿐이다(`09_contribution.md` 개정 반영). **식별 실패 조건도 다르다**: 이 논문의 비유일성은 팩터가 자산보다 많을 때 발생하는데, CAP은 driver 5개에 자산이 더 많으므로 그 조건에 직접 걸리지 않는다.
- **인용할 문장·수치** (원문 대조): 중복 팩터 시스템에서 팩터별 리스크 기여도가 유일하지 않다는 결과 (QF 2016, 16(3), pp. 377–388).

## 정정 이력

이전 판본은 "상관된 팩터에 대해 Euler 분해가 **회전(rotation)에 불변이 아님을 보인다**"고 적었고
R7을 그 근거로 신설했다. 원문은 그 명제를 증명하지 않는다 — 보이는 것은 **중복 시스템의 식별
실패**다. R7의 서술을 교체했고, 회전 비불변성 자체를 주장하려면 다른 출처가 필요하다
(Meucci 2009가 후보이나 미확인). `PAPER_DIFF.md` 갱신 9.
