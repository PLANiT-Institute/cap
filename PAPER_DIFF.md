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

---

## 갱신 5 (2026-07-29 — 문헌조사 2차: 유예 도메인 + 원문 검증)

### D8. 인용 오류 1건 — Décaire 외(2020)의 "52%"는 원문에 없다

1차 노트가 인용한 "firms forego 52% of option value by not delaying investment"는
**원문에 존재하지 않는 문장**이다(NBER WP 25624 전문 대조). 조기 행사된 **시추공의 비율
57%**를 가치 기준 지표와 혼동한 것으로 보인다 — 단위가 다르다.

원문 수치: 포기 가치 평균 $0.42M (평균 트리거 가치 $7.08M 대비 **약 6%**, Table 9),
순진한 정보집합 하 조기 행사 비율 57%(peer 정보 반영 시 44%). 또한 이 논문의 **핵심 기여는
peer effects·정보 외부성**이지 "포기 가치"가 아니다 — 1차 노트는 이를 누락했다.
`References/decaire2020.md` 교체 완료, R8 서술도 정정.

이 항목이 중요한 이유: 해당 노트는 `supports:wedge`로 CAP의 핵심 개념을 떠받치는 자리에
있었다. **초록 기반 조사의 실패 모드가 실재함을 보여주는 사례**이므로 남긴다.

### D9. 원문 검증 결과 (18편)

| 판정 | 수 |
|---|---|
| CONFIRMED (서지·수치 원문 대조) | 12 |
| UNVERIFIABLE (서지만 대조, 본문 유료장벽) | 5 |
| WRONG | 1 (D8) |

서지 정보(저자·연도·저널·권·호·면)는 18편 전부 정확했다. 부호 반전은 D8 외에 추가 발견 없음.
각 노트에 판정이 스탬프돼 있다. **UNVERIFIABLE 5편은 인용 전 원문 확인 필요**:
artzneretal1999, dixit1994, flora2023, meyer1987, roncalliweisang2016.

### D10. A3(선형 비용함수)도 지지 문헌 0편

철강 techno-economics 조사에서 A3를 지지하는 문헌이 나오지 않았다. 반대 증거만:
Kesicki(2012) MACC 방법론 비판, Rissman 외(2020) 감축수단 간 상호작용·순서의존성,
Vogl 외(2018)·Fischedick 외(2014)는 탄소가격×전력가격 교차항과 학습곡선 비선형성을 보인다.
A5에 이어 두 번째 `% unsupported:` 항목.

함의: B = aᵀX의 선형성은 **국소 근사**로 재서술해야 한다. 현재 문서는 이를 공리로 두고 있다.

### D11. A4(route 감응도)는 지지되지만 R3는 문헌이 비판 쪽

지지 4편(Vogl 외 2018의 고정 공학계수 벡터, Fischedick 외 2014의 이산 route 분류,
IEA 2020 분류 체계, Vogl 외 2021의 설비 단위 reline-vs-convert 결정점). 그러나 IEA(2020)와
Wachsmuth 외(2021)는 자산 단위 단일 벡터가 아니라 **시스템 수준 기술 믹스 비중**을 제시하고,
Ozorio 외(2013)는 자산이 고정 벡터가 아니라 **조건부 옵션**을 보유한다고 본다 — R3의 지적 그대로.

R3 대응 후보 2개: ① share 가중 합성 감응도 `a_mixed = Σ w_r·a_r` (산업 로드맵 관행),
② 복합·스위칭 옵션 표현(Ozorio 외 2013) — CAP이 이미 스위칭 옵션 구조를 쓰므로 후자가 native.
**철강 특화 mixture 감응도의 폐형 해는 문헌에 없음** — CAP의 기여 공간.

### D12. 계약 분리가능성 — PPA 헤지 유효성 5–10%

Peña 외(2024): 거래소 상장 선물을 통한 PPA 헤지의 분산 감소가 **태양광 10%·풍력 5%**에
그치고 때로는 음수다(basis + volumetric risk). Lee 외(2025)는 CCfD 행사가 설계의 역선택·
정보지대 문제를 지적한다.

함의: `claim-separately-contractible`을 "완전 분리 가능"에서 **"부분 분리 + 잔여 basis risk"**로
낮춰야 한다. s06의 coverage·tenor·basis 파라미터 변환은 방향이 맞지만, 저 크기라면
waterfall의 Δπ 해석에 잔여 basis를 명시해야 한다. **s06 재검토 대상.**

### D13. R4(WACC 순환성) — 해결 논문 없음, 식별 전략 2개

깔끔히 푸는 논문은 없다. 문헌이 실제로 쓰는 전략: ① 외생 충격 이벤트스터디·DiD
(파리협정, Seltzer 외 2022) — WACC를 동시 회귀변수가 아니라 반응으로 둔다,
② IV 기반 채널 분해 — Campello 외(2011)는 헤지의 실질 효과가 **자기자본 할인율이 아니라
부채 스프레드·약정조건**으로 간다고 본다(순진한 WACC 채널 서사에 대한 반증).

### 남은 데이터·문헌 공백

- **한·일 철강 route 비용 문헌 없음** — 전부 EU/스웨덴/글로벌/브라질. KEEI·RITE 국문·일문 보고서 추가 조사 필요
- **K-ETS/CBAM 한국 철강 이벤트스터디 없음** (D6에서 이월)
- **수소 offtake 헤지 유효성·basis risk의 피어리뷰 정량 연구 부재** — 실무 보고서만 존재

---

## 갱신 6 (2026-07-29 — s06 재검토: basis를 점추정에서 밴드로)

D12(PPA 헤지 유효성 5–10%)의 모델 반영. `config/interventions.csv`에 `basis_sigma_hi`
컬럼을 추가하고, `apply_interventions(..., basis_case="lo"|"hi")`로 계약 잔여 basis를
밴드로 푼다. hi 값은 문헌 최악(헤지 유효성 ≈10% 분산감소, Peña 외 2024)을 해당 driver
원 σ의 0.95배로 근사한 것이다 — **측정치가 아니라 명시적 stress 경계**다.

`outputs/intervention_impacts.json`의 각 개입에 `residual.risk_charge_bps_high_basis`와
`delta.risk_charge_bps_high_basis`가 붙는다.

### D14. 계약의 위험 감축 효과 절반 이상이 basis 가정에 걸려 있다

| 기업 | 계약 | Δ risk charge (lo basis) | Δ (hi basis) | 남는 비율 |
|---|---|---|---|---|
| POSCO | H2 CfD | −2.06 bps | −0.95 bps | 46% |
| NIPPON | H2 CfD | −1.88 bps | −0.85 bps | 45% |
| POSCO | PPA | −0.13 bps | −0.01 bps | 8% |
| NIPPON | PPA | −0.29 bps | −0.19 bps | 66% |

H2 CfD의 위험 감축은 문헌 최악 basis에서 **절반 이하**로 줄고, PPA는 사실상 사라진다.
계약 waterfall의 Δπ를 점추정으로 제시하면 안 된다는 뜻이다.

부수 확인: 애초에 PPA의 위험 감축은 lo basis에서도 −0.05~−0.29bps로 작다. 계약이 주로
**타이밍(τ*)** 을 움직이고 위험 수준은 거의 못 움직인다는 갱신 3의 발견과 일치한다.
"계약으로 각 성분을 소거한다"는 서사는 위험 수준 기준으로는 이미 약했고, basis를 넣으면 더 약해진다.

회귀 테스트 `test_high_basis_never_improves_the_hedge` — hi가 lo보다 좋아지면 실패하고,
basis가 결과에 아예 안 들어가도 실패한다.

**미해결**: 수소 offtake basis의 실측 근거가 문헌에 없다(D12). `basis_sigma_hi=0.285`는
전력 문헌의 유효성 비율을 수소에 이식한 것이므로 status는 `assumed`다.

---

## 갱신 7 (2026-07-29 — 한·일 route 비용 문헌)

D10의 후속. 한국어·일본어 검색으로 국가 특정 문헌 4편 확보(gei2024, kang2022, shibata2023,
jiangetal2025). 언론보도 3건은 KEPCO·KOSA 통계를 인용한 2차 자료라 `refs.bib`에서 제외하고
아래 데이터 단서로만 남긴다.

### D15. A3는 '국소 근사'다 — unsupported에서 해제

`gei2024`가 A3의 첫 지지 문헌이다. 한국 H₂-DRI-EAF 비용이 탄소가 $15/$30/$50에서
$596/$571/$537per t로 움직여 기울기가 −1.67 / −1.70 USD/t per $1/tCO₂ — 우리가 쓰는
탄소가 구간에서 사실상 선형이다.

반대 방향은 여전히 우세하다: 수입 수소 캐리어 비용이 해외 생산원가의 **1.5–2.5배**
(shibata2023), 감축수단 상호작용·순서의존성(Rissman 외 2020), MACC 가법성 비판(Kesicki 2012).

결론: A3를 **"관측 가격 구간 안에서, 고정 시점 route 기술 사양 하에서 선형"**으로 재서술했다
(`theory/02_variance_premium.md`). 공리 철회가 아니라 적용 범위 명시다.

### D16. K-ETS 실가격이 전환 임계 탄소가의 1/7 — 가장 큰 발견

`gei2024` 기준 한국의 route 전환 손익분기 탄소가는 약 **$50/tCO₂**인데, 실제 K-ETS 가격은
**$6–7/tCO₂** 수준이다(InfluenceMap 2025). 유럽은 EU ETS 가격이 자체 손익분기 밴드
(34–68 EUR/tCO₂) 안에 들어 있다.

함의는 크다. 한국에서 전환 프리미엄은 **가격 신호 이야기가 아니라 정책 신뢰성 이야기**다.
τ*를 현재 탄소가로 풀면 사적 전환은 지평 내에 오지 않고(JFE/Kobe에서 이미 관측된 결과와 일치),
CAP이 측정하는 것은 "현재 가격 대비 노출"이 아니라 "**미래 정책이 구속할 확률에 대한 노출**"이다.
이는 `#claim-policy-repricing`의 서술을 강화하는 방향이면서, 동시에 D6(글로벌 기후뉴스 채널과
자국 정책 채널의 분리 식별 부재)를 더 시급하게 만든다.

**config 대조 필요**: 현행 `carbon_base_kr = 14.93` (measured, ICAP 최근 종가)와 위 $6–7은
시점·출처가 다르다. 어느 쪽도 조용히 바꾸지 않는다 — 원 출처 대조 후 결정.

### D17. 한국 route 비용은 유럽 기준보다 불리하다

| 항목 | 유럽 기준(현행) | 한국(gei2024) | 방향 |
|---|---|---|---|
| H₂-DRI-EAF 비용 | 361–640 EUR/t | **$621/t** (green H₂ $1/kg) | 비교 7개국 중 최악 |
| BF-BOF 기준선 | — | $605/t | 전환 시 +$16/t |
| 손익분기 탄소가 | 34–68 EUR/tCO₂ | 약 $50/tCO₂ | 유사 |

일본(shibata2023, IEEJ): 환원로 단계 전력 **135 kWh/t-DRI**, 철광석 1,417 kg/t-DRI,
수소 800 Nm³/t-DRI. 유럽의 3.48 MWh/t는 전 공정 기준이므로 **직접 비교 불가** — 단계 정의를
맞춘 뒤에야 config에 넣을 수 있다.

### 데이터 단서 (refs.bib 제외, 1차 자료 확보 필요)

- POSCO HyREX 손익분기: 수소 ¥1,000–2,000/kg, 탄소가 $15–20/tCO₂, 전력 사용 고로 대비 +60%↑
  (언론 인용 POSRI 추정 — POSRI 원 보고서 미확보)
- 한국 산업용 전기요금 4년간 70%↑ (105.5 → 181 KRW/kWh, KEPCO 통계 인용 보도)
- 한국 철스크랩 자급률 85.9%(2021), 일본 수출 축소 예상 2030 — scrap-EAF route 실현성 제약

### 확보 실패 (MISSING.md 대상)

- **KEEI kang2022의 route별 투입원단위 표** — 목차만 접근 가능, 수치 표 미확보. **최우선 추적 대상**
- POSRI HyREX 톤당 비용 보고서 — 목록만 확인

---

## 갱신 8 (2026-07-29 — D16 가격 불일치 해소, 자체 데이터)

D16이 "K-ETS 실가격 $6–7 vs 손익분기 $50 = 1/7"이라 적었다. `data/processed/kau_daily.parquet`
(2015-01 ~ 2026-06, 2,814 영업일)로 직접 대조한 결과 **둘 다 맞고 시점이 다르다**:

| 기간 | KAU 평균 USD/tCO₂ | 최저–최고 |
|---|---|---|
| 2019 | 25.56 | 21.55–34.78 |
| 2020 | 25.46 | 15.00–33.54 |
| 2023 | 8.75 | 5.46–13.47 |
| 2024 | 6.92 | 5.86–9.22 |
| 2025 | 6.60 | 5.91–7.87 |
| 2026 (~6/30) | 11.00 | 7.04–18.85 |

문헌(InfluenceMap 2025)의 $6–7은 **2024–25 평균**이고, config의 `carbon_base_kr = 14.93`은
**2026-06-30 종가**다. **config 오류가 아니다** — 갱신 4의 "measured, 최근 종가" 표기가 정확하다.

### D16 정정

전환 손익분기(~$50/tCO₂) 대비 격차는 **1/7이 아니라 약 1/3.3**(14.93 기준)이다. 결론의 방향은
유지된다 — 현재 가격은 여전히 route 전환을 사적으로 정당화하지 못하고, 따라서 CAP이 재는 것은
"미래 정책이 구속할 확률에 대한 노출"이다. 그러나 **배수는 위 표의 어느 시점을 쓰느냐에 달렸고**,
논문은 기준일을 명시해야 한다.

부수 관찰 — KAU는 2019–20 $25대에서 2025 $6.6까지 내려갔다가 2026 상반기에 다시 배로 올랐다.
**7년 사이 4배 범위를 오간 가격**이라는 사실 자체가 σ_carbon-diffusion=0.397(measured)의 근거이자,
"탄소 노출 = 정책 신뢰성 노출"이라는 D16 독해를 뒷받침한다.

### D17 정정 (2026-07-29) — 현행 원단위는 '유럽'이 아니라 '벤더·글로벌'

갱신 7의 D17 표가 현행 config를 "유럽 기준"이라 적었다. `data/processed/intensities.parquet`
대조 결과 부정확하다. 실제 출처는 Midrex Tech Sheet 2023(수소 60 kg/t), LBL Green Steel
(전력 0.8 MWh/t), IRENA/Lhyfe(전해조 포함 3.6), IEA ETP 2024(잔여 0.1 tCO₂/t) —
**벤더·글로벌 기관 값이며 특정 지역 값이 아니다.**

그리고 세 전력 수치는 서로 비교 대상이 아니다:

| 값 | 출처 | 공정 경계 |
|---|---|---|
| 0.8 MWh/t | LBL (config 현행) | **외부 조달 수소** 기준, 전해조 제외 |
| 3.6 MWh/t | IRENA/Lhyfe | 전해조 포함 |
| 3.48 MWh/t | Vogl 외 2018 (유럽) | 전 공정 |
| 135 kWh/t-DRI | IEEJ shibata2023 (일본) | **환원로 단계만** |

config의 0.8과 문헌의 3.48을 나란히 놓고 "한국이 불리하다/유리하다"를 말할 수 없다.
경계를 맞추는 것이 국가 특정 값을 구하는 것보다 먼저다.

---

## 갱신 9 (2026-07-29 — 무료 전문 확보 시도 결과)

유료 우회 없이 합법적 무료 경로(저자 공개본·arXiv·기관 아카이브)만 사용. 6건 중 4건 진전.

### D18. R7의 인용이 틀렸다 — 원문은 회전 비불변성을 증명하지 않는다

R7을 신설하며 [[roncalliweisang2016]]이 "상관 팩터에서 Euler 분해가 **회전에 불변이 아님**"을
보인다고 적었다. 저자 공개본 전문 대조 결과 **그 명제는 논문에 없다.** 논문이 보이는 것은
**중복(redundant) 팩터 시스템 — 팩터 수 > 자산 수 — 에서의 기여도 비유일성**, 즉 식별 실패다.

CAP은 driver 5개에 자산이 더 많으므로 **그 조건에 직접 걸리지 않는다.** R7을 폐기하지는 않는다 —
"driver 정의의 자유도가 P1이 덮는 자유도보다 크다"는 논점 자체는 살아 있고 여전히 미대응이다.
그러나 회전 비불변성을 주장하려면 다른 출처가 필요하다(Meucci 2009가 후보이나 미확인).
R7 서술과 노트 교체 완료.

**패턴**: D8(Décaire 52%)에 이어 두 번째로, 원문 대조가 우리 쪽 서술을 깎았다. 두 건 모두
"그럴듯하고 유용한 방향"의 오류였다는 점이 중요하다.

### D19. A1·R1 방어 논리는 원저자 쪽에서 확인됨

[[artzneretal1999]] 전문 확인 — 단조성(Axiom M)이 coherence 4공리 중 하나이고, 논문 자체가
분산형 측도를 단조성 결여로 배제하는 예제를 든다. 교차확인으로 **Kalkbrener(2005) 본인이
표준편차 측도가 단조가 아니며 이것이 Euler 배분 유일성 기계를 깨뜨린다고 명시**한다.

즉 D3(“CAP이 인용하려는 유일성 정리는 CAP의 측도에 적용되지 않는다”)는 우리 해석이 아니라
**원저자가 직접 적어둔 한계**다. R1 대응 문구를 쓸 때 이 점을 인용할 수 있다.

### D20. 원문 확보 현황

| 문헌 | 결과 |
|---|---|
| artzneretal1999 | CONFIRMED (Delbaen 공개 preprint 전문) |
| roncalliweisang2016 | 부분 확인 — ⓐ 확인, ⓑ 반증 (D18) |
| meyer1987 | CONFIRMED (2차: 공개 서베이 Statistical Science 28(2)). 1차 아님 |
| dixit1994 | PAYWALLED — 단행본. 인용 대상은 **Chapter 5 "The Simplest Case"**로 특정 |
| flora2023 | UNVERIFIABLE — SSRN 봇 차단, arXiv·HAL 없음, ScienceDirect 유료. 기관 접근 필요 |
| kang2022 (KEEI) | **부분 확보** — D21 |

### D21. KEEI 원단위 확보 — 수소 +49%, 전력 −31%

기본연구보고서 22-03(강병욱, 2022-12) 본문에서:

| 항목 | KEEI (한국) | config 현행 | 차이 |
|---|---|---|---|
| BF-BOF 철광석 | 1,652 kg/tHM | 1.65 t/t (World Bank) | **일치** |
| BF-BOF 코크스 | 313.2 kg/tHM | 0.7 t/t (IEA Coal 2024) | 경계 상이 |
| H2-DRI 수소 | **89.6 kg/t 조강** | 60 kg/t (Midrex) | **+49%** |
| H2-DRI 전력 | **550 kWh/t** | 800 kWh/t (LBL) | **−31%** |

철광석이 일치한다는 점이 나머지 차이가 단위 착오가 아님을 시사한다.

**반영 보류.** 수소 +49%는 POSCO·Nippon의 H₂ share와 σ_B를 크게 움직인다. KEEI는 "t 조강",
Midrex는 "t steel" 기준이고 전력 550 kWh/t는 전해조 포함 여부가 불명이다 — 경계 확인 전에는
바꾸지 않는다(규칙 6·8). 확인되면 `status: measured`(한국 특정)로 승격하고 `make model`
재실행하며, **결과가 바뀔 것을 전제**한다. route별 CO₂ t/t·gas-DRI·CCUS는 이 보고서에 없다.
