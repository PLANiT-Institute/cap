# 09. 지적 계보 — 발명이 아니라 조합 {#contribution}

다섯 개의 확립된 기초를 하나의 대상으로 조합한다:

| 기초 | 원류 | CAP이 쓰는 부분 |
|---|---|---|
| 실물옵션 | Dixit–Pindyck (1994), McDonald–Siegel (1986) | 비가역성 + 불확실성 → 대기 프리미엄, τ* |
| 물리자산 옵션평가 | Brennan–Schwartz (1985), Margrabe (1978) | 고로를 교환옵션으로 캐스팅 |
| 탄소예산·좌초자산 | McGlade–Ekins (2015) | T_required, condition gap |
| 탄소리스크 프리미엄 | Bolton–Kacperczyk (2021, 2023) | 전환노출이 가격된다는 전제 |
| 리스크 기여도 분해 | Litterman (1996), Tasche (2008) | Euler 분해로 driver별 share |

> **불확실성으로 가격되고, 드라이버로 분해되며, 계약으로 식별 가능한 기업의 전환노출의 해부도.**

## 기여의 위치 {#contribution-claim}

**방법론적 기여를 P1로 두지 않는다.** Euler 분산분해를 기후 리스크에 적용하는 이동은
이미 인접 문헌에 있다 — Roncalli–Weisang (2016)이 자산이 아니라 **리스크 팩터**에 대한
Euler 분산분해를 정식화했고, Le Guenedal 외 (2021)는 포트폴리오 분산을 탄소 리스크 팩터
기여로 분해한다. Barnett–Brock–Hansen (2020), Battiston 외 (2017), Desnos 외 (2023)도
"기후 불확실성을 named source별로 귀속시킨다"는 같은 이동을 한다. P1은 그 항등식의
CAP 판본이지 새로운 정리가 아니다.

살아남는 기여는 **방법이 아니라 대상**이다:

> Euler 분산분해를 수익률 포트폴리오가 아니라 **자산의 route-conditional 엔지니어링
> 비용함수 B = aᵀX**에 적용하고, 감응도 벡터 a를 기업이 실제로 보유한(혹은 보유를 거부한)
> 기술 포지션에서 bottom-up으로 구성한 것.

인접 문헌은 전부 상장 수익률에서 출발해 탄소 노출을 **추정**한다. CAP은 고로 단위 route
경제성에서 출발해 노출을 **구성**한다. 그래서 각 성분에 계약 이름을 붙일 수 있다
([[05_contracts_identification]]) — 추정된 팩터 로딩에는 붙일 수 없는 것이다.

경험적 기여는 한·일 철강의 2-클러스터 구조, 그리고 탄소 share = 자국 정책 repricing이라는
독해다. 후자는 현재 **식별이 미완**이다: 글로벌 기후뉴스 채널(Engle 외 2020)과 자국 정책
채널을 분리하는 전략이 없다. 인용으로 메울 공백이 아니라 설계로 메울 공백이며
`PAPER_DIFF.md` D6에 기록돼 있다.

## 문헌

`theory/refs.bib` — 82편, 5개 도메인(real-options / variance-premium / carbon-premium /
jump-risk / sdf-lambda). 각 엔트리는 `supports:` 또는 `counters:`로 이 문서들의 anchor를
참조하며, `make check-anchors`가 공리·주장·referee note의 지지 여부를 검증한다.

미조사 도메인(철강 techno-economics·MACC, 전환계약 CfD/PPA)은 `refs.bib`의 `deferred:`에,
조사했으나 지지 문헌이 없는 anchor는 `unsupported:`에 명시돼 있다. 현재 후자는
`#axiom-uniform-lambda` 한 건이다 — 상세는 `PAPER_DIFF.md` D1.

기업 공시·평가 프레임워크(TPI, CA100+, SBTi 등)는 별도:
`data/raw/reference/CAP_Literature_References.xlsx`.
