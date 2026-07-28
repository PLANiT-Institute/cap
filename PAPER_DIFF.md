# PAPER_DIFF — 논문 원본 수치 vs 재구축 파이프라인 (2026-07-22)

> **갱신 (2026-07-22 오후)**: KAU 일별 시계열을 ICAP Allowance Price Explorer에서 확보.
> σ_carbon-diffusion **0.397 (measured)** · μ_carbon **0.087 (measured, 장기 endpoint 추세)** ·
> carbon_base_kr **$14.93 (measured, 최근 종가)** — 기존 banded 0.40 / 0.086 / $9.5와 부합·대체.
> 논문의 "KAU ~$9.5" 서술은 구 시점 값; 라이브 치환으로 자동 갱신됨.
> POSCO carbon share 52.2%→49.3%로 논문(44.3%)에 근접.
>
> **갱신 2 (계산기 전환)**: 시계열의 μ·현물 자동 오버라이드 제거 — 가격 수준·추세는
> 시나리오(config)가 구동, 시계열은 σ 캘리브레이션 + 연단위 레퍼런스
> (`reference_prices.json`)만. carbon_base_kr=14.93은 config 값으로 이동 (measured 표기).
> `model/api.py` compute() 추가 — 오버라이드 in/결과 out 순수 계산기 (MCP 시임).

PLAN 지시: "불일치는 버그가 아니라 발견일 수 있으니 조용히 맞추지 말고 기록할 것."
아래는 재구축 파이프라인(config 주도, 하드코딩 제로)의 출력과 논문 서술 수치의 대조다.
회귀 테스트(`model/tests/test_regression.py`)는 *구조적* 성질(σ 검산, 불변성, 클러스터
분리, Δπ>0)을 고정하고, *수준·조성 수치*는 이 문서로 추적한다.

## 정확히 재현된 것

| 항목 | 논문 | 파이프라인 | 판정 |
|---|---|---|---|
| σ_carbon 개혁 미가격→가격 | 0.40 → 0.88 | 0.40 → 0.88 | **일치** (공식 그대로: jump var/ℓ̄²=0.615) |
| λ×p_bind 격자에서 share 불변 | 소수점 6자리 | 이탈 0.0e+00 (기계 정밀도) | **일치** (Prop 1 항등) |
| 두 클러스터 carbon share 불교차 | 불교차 | 불교차, gap 12.1%p (band draw 전체) | **일치** |
| Δπ > 0 전 기업 | > 0 | 11.1–19.3bps | **일치** (부호) |
| scrap/가스 route H₂ share = 0 | 0 (구성상) | 0 | **일치** (A4) |

## 다른 것 (기록 — 원인 가설 포함)

| 항목 | 논문 | 파이프라인 | 원인 가설 |
|---|---|---|---|
| POSCO carbon share (기준) | 44.3% | 52.2% | 노출 창 정의: 재구축은 전환연도 = min(τ*, T^GCAM) 용량가중 (2041) — 논문의 창은 더 이른 전환(reline 근접)이었을 가능성. 탄소 창이 길어지면 carbon share 상승 |
| POSCO carbon share (reform) | 72.5% | 83.6% | 상동 + ρ(elec,carbon)=0.3 가정의 차이 가능 |
| H₂-route H₂ share | 49–51% | POSCO 44.2% / Nippon 69.9% | Nippon: JP wacc 4%가 전환 후 H₂ 창의 PV를 크게 키움. 논문이 국가별 할인율을 노출 PV에 어떻게 적용했는지 미상 — **저자 확인 필요** |
| grid-route carbon share | 79–83% | JFE 95.7% / Kobe 89.8% | 재구축의 전력 노출(EAF 전력 원단위 × 시장가)이 논문보다 작음. 논문이 그리드 전환 노출을 더 넓게 (예: 전 에너지 전화) 정의했을 가능성 |
| λ×p_bind 수준 스윙 | 2.85–37.99bps | 1.60–45.79bps | 같은 자릿수·같은 구조 (bps = k·λ·p_bind·σ_B 연금화/EV). σ_B와 EV 근사 차이 |
| σ_B 선형성 R² | 0.99 | 0.957 | MC 노이즈(4000경로) + drift 도입. band 범위 스케일로 측정 |
| Fig 3 기업 수 | 5사 (Hyundai 포함) | 4사 | **의도된 변경**: A4/R3 해소 — Hyundai 자산(A03, A08)은 no_feasible_route로 stranding 분리 (PLAN Phase 2 "Hyundai 처리 일관화"). Hyundai의 79–83% carbon share 서술은 stranding annex로 이동 필요 |
| POSCO cost vs risk (carbon) | 36% vs 44% | cost_vs_risk.json 참조 (구조 동일: cost < risk) | 부호·순서 재현, 수치는 창 정의 따라 이동 |

## 재구축이 새로 만든 산출 (논문에 없음)

- `lambda_k_sensitivity.json` — R1 대응 λ_k 감응도 (A5 스트레스)
- `wedge.json`의 WACC-equalized 변형 — R4 부분 대응
- `stranding.json` — no_feasible_route 자산 분리
- measured 승격 파이프라인 (KAU/SMP/JEPX 파일 도착 시 자동)

## 후속 판단 필요 (저자)

1. 노출 창 정의 확정: min(τ*, T^GCAM) vs reline 연도 vs T^GCAM — anatomy 수치가 이 선택에 민감.
2. Nippon의 wacc 4% 적용 범위 (JP 노출 PV가 KR보다 구조적으로 커짐 — H₂ share 왜곡).
3. grid-route 전력 노출의 범위 (EAF 전력만 vs 전 에너지 전화).
4. GCAM surrogate 포화(38Mt) < 포트폴리오 용량(41.3Mt) → 후순위 자산 T^GCAM이 horizon 말단으로 밀림 (A01, A03). raw 확보로 해소.

---

## 갱신 3 (2026-07-22 — pathway-first 개편)

인과구조 개편으로 다수 수치가 바뀌었다. 원인별 기록 (억지로 이전 수치에 맞추지 않음):

| 변경 | 이전 | 이후 | 원인 |
|---|---|---|---|
| τ* 정의 | 행사경로 조건부 평균 | **E[min(τ,H)]** (미행사=지평말; p_ex<문턱이면 None) | 조건부 평균의 선택편의 — 개입 효과가 묻히거나 역방향으로 보임 |
| JFE/Kobe τ* | ~2050 | **None (지평 내 사적 전환 없음, p_ex 13–14%)** | scrap/NG route가 사적 NPV 음수 — required만이 전환을 만든다는 발견 |
| p_bind | 0.65 (독립 파라미터) | **파생: KR 0.55 / JP 0.50** (Option A) | 시나리오 확률과의 불일치 구조 제거 |
| 탄소 regime | KR 단일 | **국가별** (JP: SQ$5/GX$30/CBAM$85; σ_reform KR 0.88 / JP 1.13; ℓ_bind KR 53.2 / JP 46.5) | KR 시나리오를 JP에 적용하던 오류 수정 |
| T_required | 전 자산 단일 H₂ 곡선, no_feasible 포함 | **route별 풀, no_feasible 제외, 비H₂ route는 rescale(PROVISIONAL)** | 배치용량 소비 오류·경로 오적용 수정 |
| POSCO risk charge (reform) | 28.4bps | 23.3bps (개입 전) | 국가별 regime + T_required 변경 + t_switch 이동 |
| 핵심 지표 | bps | **cumulative alignment gap** (POSCO 368 / NIPPON 277 / JFE 137 / KOBE 3 MtCO₂) | 개편 §2 — 시간 gap이 아니라 용량·강도 반영 누적 초과배출 |
| 계약 효과 | σ=0 → 0bps | **파라미터 변환 → 잔여 유지** (예: POSCO package 후 25.9bps) | coverage·tenor·basis 반영 |

**모델 발견 2건**:
1. H₂ CfD 단독(계약가 $3/kg, coverage 70%·tenor 15y)은 τ*를 못 앞당김 — blended 수소가로는 route가 여전히 사적 적자. **조합(package)만 τ*·gap 동시 개선** (POSCO Δτ* −0.4y, Δgap −28Mt; NIPPON −2.2y, −26Mt).
2. carbon reform은 gap을 닫으면서 **risk charge를 올림** (가격되는 탄소 부담 증가) — timing 수단 ≠ risk 절감 수단.

---

## 갱신 4 (2026-07-28 — 문헌조사 1차)

`theory/refs.bib` 구축(82편, 5개 도메인) 과정에서 나온 **문헌 대조 발견**. 규칙 8대로
조용히 맞추지 않고 기록한다. 상세: `docs/superpowers/specs/2026-07-28-literature-review-design.md`.

### D1. A5(λ 균일성)를 지지하는 문헌이 0편 — 반대 증거만 7편

5개 도메인 조사 어디에서도 driver 간 **단일 λ**를 지지하는 문헌이 나오지 않았다. 반대로
Chen–Roll–Ross(1986), Bolton–Kacperczyk(2021, 2023), Adrian–Crump–Moench(2015),
Görgen 외(2021), Kan–Zhang(1999), Ready(2018)가 팩터별 위험가격의 차이를 보고한다.
Ready(2018)는 성분별 λ의 **부호가 반대**인 경우를 보고하는데, 이 경우 share 불변성의
실질적 의미가 사라진다.

`refs.bib`에 `% unsupported: axiom-uniform-lambda`로 선언했다 — 미조사(deferred)가 아니라
**조사 결과**다. `make check-anchors`가 매 실행마다 이 사실을 출력한다.

함의: R1은 "OPEN"이 아니라 **문헌이 비판 쪽에 서 있는** 상태다. A5의 status를 config에서
`assumed`로 유지하는 것은 정당하나, LEDGER의 서술은 "미검증"이 아니라 "반증 우세"로
바뀌어야 한다. λ_k 감응도 모듈(`outputs/lambda_k_sensitivity.json`)의 최대 share 이동이
이제 부수 robustness가 아니라 **주 결과**로 승격될 후보.

### D2. 방법론적 novelty 주장 falsified — P1은 기여가 아니다

`09_contribution.md`의 "방법론적 기여는 P1"은 방어 불가능하다. 기후 맥락에서 Euler
분산분해를 이미 쓴 선행연구: Roncalli–Weisang(2016, QF)이 **리스크 팩터**에 대한 Euler
분산분해를 정식화했고, Le Guenedal 외(2021, JPM)는 포트폴리오 분산을 탄소 리스크 팩터
기여로 분해한다. Le Guenedal–Roncalli(2022), Desnos 외(2023), Barnett–Brock–Hansen(2020),
Battiston 외(2017)도 인접하다.

살아남는 기여는 **방법이 아니라 대상**: Euler 분산분해를 수익률 포트폴리오가 아니라
자산의 route-conditional 엔지니어링 비용함수 B=aᵀX에 적용하고, 감응도 벡터 a를 기업이
보유한 기술 포지션에서 bottom-up으로 구성한 것. `09_contribution.md`가 이미 쓴
"발명이 아니라 조합"이 옳은 자기서술이고, P1을 방법론적 기여로 부르는 문장이 그것과
모순됐다. §09 수정 반영됨.

### D3. R1 방어 초안이 성립하지 않음 — 가설 불일치

Kalkbrener(2005)·Denault(2001)의 Euler 배분 **유일성 정리는 coherent 위험측도**(단조성
포함)를 전제한다. **분산은 단조 위험측도가 아니다.** 따라서 "두 독립 공리계가 같은 배분
규칙으로 수렴하므로 항등식이 trivial하지 않다"는 방어는 CAP의 측도에 그대로 적용되지
않는다 (Artzner 외 1999).

추가로 Tasche(2008): Euler 배분의 정당화는 **RORAC 정합성**이라는 특정 목적함수 하에서만
성립한다. CAP의 목적은 RORAC이 아니다.

### D4. RC_k < 0 가능성 — "조성" 서술 자체의 전제

driver 간 공분산이 음이면 RC_k < 0이 되어 s_k가 [0,1] 밖으로 나간다. scrap-EAF route에서
전력↔탄소 공분산이 음일 개연성이 실재한다. "탄소 C%, 수소 H%…"라는 조성 서술 전체가
여기 걸려 있다. **검증 테스트 미작성 — 다음 회차 최우선.**

### D5. 미답변 반론 2건 (referee note 신설 후보)

- **팩터 회전 비불변성** (Meucci 2009; Roncalli–Weisang 2016): Euler 리스크기여는 팩터
  좌표계 선택에 불변이 아니다. CAP의 5개 driver는 강하게 상관돼 있다. 즉 P1이 자랑하는
  "λ에 불변"보다 **driver 정의 자유도가 훨씬 큰 취약점**인데 R1–R6 어디에도 없다.
- **과점 하 옵션행사 게임** (Grenadier 2002): CAP은 τ*를 단독 최적화로 푼다. 한·일 철강은
  5사 과점이고 route 선택이 공개된다. 경쟁은 대기 프리미엄을 잠식한다.

### D6. 식별 공백 — 자국 정책 채널 vs 글로벌 기후뉴스

`claim-policy-repricing`의 지지 문헌이 사실상 얇다. Engle 외(2020)는 기후위험 뉴스가
**글로벌 뉴스 팩터**로 추출·헤지된다고 본다. 탄소 share를 "**자국** 정책 repricing"으로
읽으려면 두 채널의 분리 식별이 필요한데 현재 전략이 없다 — 인용 부족이 아니라 식별 부족.
Pástor–Stambaugh–Taylor(2022)는 실현 brown 초과수익이 기대수익(리스크 프리미엄)이 아니라
기후우려의 예상 밖 상승에서 온다고 본다.

또한 **K-ETS/CBAM 한국 철강 대상 이벤트스터디가 문헌에 없다.** K-ETS는 유동성이 낮고
무상할당 비중이 높아 EU ETS 탄력성(Hengge 외 2023)을 그대로 이식할 수 없다.

### D7. 점프 — variance share ≠ premium share

Bollerslev–Todorov(2011), Pan(2002), Broadie 외(2009): 점프·꼬리 프리미엄은 총 위험프리미엄의
크고 독립적인 부분이다. CAP의 분산 기반 share는 점프 성분의 경제적 비중을 **과소평가**할
수 있다. λ_jump / λ_diffusion 분리 전까지 "variance share"를 "premium share"로 읽으면 안 된다.
Meyer(1987)는 더 근본적이다 — 평균-분산이 기대효용과 정합적인 것은 location-scale family
내부뿐인데, R2 대응으로 점프를 도입한 순간 CAP은 그 조건을 스스로 깼다.

Ilhan–Sautner–Vilkov(2021)가 탄소 꼬리위험 가격의 유일한 직접 추정치이며, λ_jump 밴드의
실증 앵커 후보다. Kelly–Jiang(2014)은 옵션시장 없이 횡단면만으로 꼬리위험을 추정하는
방법으로, "개별 철강사 옵션시장 부재"라는 제약의 우회로다.

### 검증 상태 (중요)

82편의 인용 수치는 **초록·2차 요약 기반**이다. 조사 에이전트 5개 전부 원문 PDF 접근
실패를 자진 신고했다. 심층 노트 작성 시 원문 대조 필요. 현재 `refs.bib`는 문헌 지도이지
검증된 인용 목록이 아니다.
