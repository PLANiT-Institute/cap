# CAP 문헌조사 설계 — 공리·referee note를 문헌으로 지지하기

작성 2026-07-28. 승인된 브레인스토밍 결과.

## 문제

`theory/09_contribution.md`는 다섯 기초(Dixit–Pindyck, McGlade–Ekins, GCAM, MACC,
Bolton–Kacperczyk)를 이름으로만 부른다. `theory/08_referee_notes.md`의 R1–R6은
CAP가 아는 약점이고, 그중 R1(λ 균일성)과 R2(점프리스크)는 선행연구가 이미 다룬
문제인데 우리 쪽 근거가 없다. 기존 `data/raw/reference/CAP_Literature_References.xlsx`
200행은 기업 IR·평가 프레임워크(TPI, CA100+, SBTi)이지 학술 문헌이 아니다.

목표: 공리와 referee note마다 그것을 지지(또는 반박)하는 문헌을 붙이고, 그 연결을
빌드가 검증하게 만든다. 문헌이 죽은 bib 파일이 되지 않게 하는 것이 설계의 전부다.

## 산출물

```
theory/refs.bib          # 진실원천 (BibTeX)
References/<citekey>.md  # load-bearing 문헌 심층 노트 (~15편)
References/INDEX.md      # 도메인별 색인
```

별도 메타데이터 파일을 두지 않는다. 연결은 BibTeX `keywords` 필드에 산다:

```bibtex
@article{merton1976,
  ...
  keywords = {domain:jump-risk, supports:referee-2, supports:axiom-variance-not-mean},
}
```

`supports:<anchor-id>`는 `theory/*.md`의 `{#anchor-id}`를 가리킨다. config의
`theory_anchor`와 같은 규약이므로 기존 정규식이 그대로 먹는다.

`refs.bib` 첫 줄에 유예 목록을 둔다:

```
% deferred: axiom-linear-cost, axiom-route-sensitivity, claim-separately-contractible
% deferred: referee-3, referee-4, referee-6
```

여러 줄로 나눌 수 있으나 각 줄이 `deferred:`로 시작해야 한다. 이어쓰기를 인정하지
않는 이유는 파서가 무관한 주석을 유예로 삼키면 게이트가 조용히 헐거워지기 때문이다.

이번 회차에서 조사하지 않기로 한 앵커. 유예가 침묵이 아니라 파일에 남는다.

### 심층 노트 스키마 (5필드 고정)

| 필드 | 내용 |
|---|---|
| citekey | refs.bib 키 |
| 한 줄 주장 | 이 논문이 확립한 것 |
| CAP에서 쓰이는 지점 | supports 앵커 + 어느 문장에 붙는가 |
| 우리와 다른 점 | 설정·가정·대상의 차이 (경계) |
| 인용할 문장·수치 | 페이지와 함께 |

"우리와 다른 점"이 필수인 이유: 이 필드가 없으면 나중에 CAP 기여가 선행연구와
겹쳐 보이고, R1–R6 방어에 쓸 실탄이 남지 않는다.

## 검증 배관

`scripts/check_anchors.py`를 확장한다. 새 파일도 새 make 타깃도 만들지 않는다
(`make check-anchors`에 흡수). 기존 검사 두 개에 두 개를 더한다:

3. `refs.bib`의 모든 `supports:X`가 `theory/*.md`에 실재하는가
4. 모든 공리(`#axiom-*`), 주장(`#claim-*`), referee note(`#referee-*`)가 최소 하나의
   bib 엔트리에 지지되는가 — 단 `% deferred:` 목록에 있는 앵커는 면제

깨지면 exit 1. config에 안 붙은 공리가 이미 빌드를 깨는 것처럼, 문헌이 없는 공리도
빌드를 깬다.

## 조사 프로토콜

`paper-researcher` 에이전트 5개 병렬. 도메인과 표적 앵커:

| 도메인 | 표적 앵커 |
|---|---|
| ① 실물옵션·투자 타이밍·행사정책 | `#wedge`, `#claim-wedge-conjunction`, `#referee-5` |
| ② 분산=리스크, 변동성 프리미엄 | `#axiom-variance-not-mean`, `#variance-premium` |
| ③ 탄소리스크 프리미엄 실증 + 탄소예산·좌초자산 | `#purpose`, `#axiom-budget-binds`, `#claim-policy-repricing`, `#carbon-jump` |
| ④ 점프리스크 가격화 | `#referee-2` (현재 PARTIAL, 최우선) |
| ⑤ 요인 λ 균일성·SDF 식별 | `#axiom-uniform-lambda`, `#claim-lambda-invariance`, `#proposition1`, `#referee-1` |

유예(deferred): ⑥ 철강 탈탄소 기술경제·MACC (`#axiom-linear-cost`,
`#axiom-route-sensitivity`, `#referee-3`), ⑦ 전환계약 CfD/PPA
(`#claim-separately-contractible`, `#referee-4`). 추가로 `#referee-6`(수익 측면)은
SCOPE-NOTE이므로 유예.

에이전트 공통 지시 — 문헌마다 반드시 산출한다:

- `supports:` 앵커 (없으면 그 문헌은 뺀다)
- 우리와 다른 점
- 인용 가능한 정확한 수치 또는 문장

"관련 있음"만 적힌 항목은 반려한다.

포함 기준: 피어리뷰 저널, 워킹페이퍼(NBER·SSRN), 또는 IEA·IPCC급 기관 보고서.
기업 IR과 평가 프레임워크 문서는 제외 — 이미 xlsx에 있다.

규모: 도메인당 5–10편, 총 ~40편. 심층 노트는 load-bearing ~15편만.

## 실행 순서

1. **배관 먼저.** `check_anchors.py` 확장 + 빈 `refs.bib`. 이 시점에 빌드는
   빨간불이다(공리·referee 대부분 미지지). 그 빨간불이 진척도 게이지다.
2. 도메인 5개 병렬 조사 → 통합 → `refs.bib`
3. completeness critic 1개 — 빠진 도메인과 **반박 문헌**(CAP 주장을 깨는 논문) 점검
4. load-bearing ~15편 심층 노트 + `References/INDEX.md`
5. `make check-anchors` 초록 확인 → `theory/09_contribution.md` 계보 문단 rewrite

## 범위 밖

- `PAPER_DIFF.md`에 문헌↔우리 수치 불일치 기록 (다음 회차)
- 웹 `/refs` 페이지
- 문헌 자동 갱신 cron, 인용 그래프 시각화
- 도메인 ⑥⑦ 조사

## 완료 기준

`make check-anchors`가 초록이고, 그때 `refs.bib`의 `% deferred:` 목록이 위에
유예하기로 한 여섯 앵커와 정확히 일치한다. 즉 공리 A1(`#axiom-variance-not-mean`)·
A2(`#axiom-budget-binds`)·A5(`#axiom-uniform-lambda`), 주장
`#claim-wedge-conjunction`·`#claim-policy-repricing`·`#claim-lambda-invariance`,
referee note R1·R2·R5가 각각 최소 하나의 문헌에 지지된다.
