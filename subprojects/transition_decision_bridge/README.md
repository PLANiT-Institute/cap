# Transition Decision Bridge

> CAP의 전환 격차와 개입효과를, 이중계산 없이 의사결정 가능한 최종 리스크 프리미엄으로 번역한다.

이 폴더는 CAP 본체와 분리된 실험용 서브프로젝트다. 본체 모델이나
`outputs/`를 수정하지 않고 다음 산출물을 읽기만 한다.

- `outputs/transition_underwriting.json`
- `outputs/alignment_gap_loss.json`

## 이 서브프로젝트가 만드는 것

`outputs/risk_premium_decision.json`과 같은 내용의 Markdown decision pack을
만든다. 기업별로 다음을 분리해 표시한다.

1. **Headline premium** — 기존 transition-cost conditional risk charge.
2. **Gap overlay** — provisional required path에 조건부인 gap-linked charge.
3. **Decision options** — 위험을 줄이되 alignment gap과 별도 overlay를 악화시키지 않는 개입.

Headline은 관측 채권 스프레드가 아니라 CAP의 model-implied conditional
risk premium이다. Gap overlay와의 합계는 공동 상태·공분산이 식별되기 전까지
`null`로 유지한다. 숫자가 없다는 것은 계산 실패가 아니라 이중계산을 막는
publication control이다.

## 실행

저장소 루트에서:

```bash
python3 subprojects/transition_decision_bridge/run.py
uv run python subprojects/transition_decision_bridge/run_joint.py
python3 -m unittest discover -s subprojects/transition_decision_bridge/tests -v
```

또는 core calibration을 생성한 뒤 이 폴더에서 `make all`을 실행한다.

```bash
make calibration
make -C subprojects/transition_decision_bridge all
```

## 범위

포함:

- 기업별 중앙 risk premium과 λ×p_bind 민감도 범위
- alignment gap의 별도 재무 overlay
- best de-risker, alignment-safe de-risker, dual-benefit option의 구분
- 0.1bp 또는 1MtCO2 이하의 미세한 결과를 과대해석하지 않는 materiality gate
- EV 가중 portfolio headline
- 입력 artifact 해시와 publication gate

제외:

- 관측 대출·채권 스프레드 추정
- BUY/SELL 또는 목표주가
- 완전한 3개 재무제표·부도모형
- CAP 본체 결과의 재계산

## 하나의 최종 total premium으로 승격하는 조건

다음이 모두 충족되어야 `combined_total_bps`를 숫자로 발행할 수 있다.

1. transition-cost와 gap loss를 같은 연도·시나리오 draw에서 생성한다.
2. 두 손실의 공분산 또는 공동 현금흐름 상태가 식별된다.
3. 할인·기간·EV 정규화 기준이 일치한다.
4. surrogate `T_required`가 검증된 benchmark 또는 확률분포로 교체된다.
5. holdout 또는 외부 거래자료로 calibration을 검증한다.
