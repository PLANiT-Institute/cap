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

---

## 갱신 10 (2026-07-29 — anchor 대차대조표)

`References/INDEX.md` 상단에 자동 생성 대차대조표 추가 (`make ledger`). anchor마다
지지/반박 편수와 반박 citekey 목록. 반박 > 지지인 anchor에 ⚠.

### D22. A1(분산=리스크)이 1:11로 최악의 비대칭 — A5보다 나쁘다

표를 만들자 드러났다. A5는 0:10으로 이미 D1에 기록했지만, **A1은 지지 1편(French–Schwert–
Stambaugh 1987) 대 반박 11편**이다. 반박 편수로는 리포 전체에서 가장 공격받는 공리다.

단 질적으로는 결이 다르다. A5 반박은 "λ가 driver마다 다르다"는 동일 방향의 수렴이지만,
A1 반박 11편은 세 갈래다: ① 하방/왜도 등 고차 모멘트가 가격된다(Ang 계열, Harvey–Siddique),
② 점프·꼬리는 분산이 못 담는다(Merton, Bollerslev–Todorov, Ilhan 외), ③ 평균-분산의
효용 정합성 자체가 location-scale 밖에서 깨진다(Meyer, Rothschild–Stiglitz).

대응 방침(논문 서술용): A1을 "리스크는 분산이다"라는 실증 명제로 팔지 말고, **"본 모델은
2차 모멘트 귀속을 다룬다"는 범위 선언**으로 내린다. ①②는 gross-exposure 범위 선언(R6)과
점프 분해 artifact(R2 대응)로 흡수하고, ③은 Meyer 노트의 방향대로 share를 효용 기반 조성이
아니라 분산 귀속으로 서술한다. 이렇게 내리면 반박 11편 중 어느 것도 모델 결과 자체를
부정하지 않는다 — 부정되는 것은 과잉 해석뿐이다.

### 대차대조표 요약 (⚠ = 반박 우세)

| anchor | 지지:반박 |
|---|---|
| #axiom-variance-not-mean ⚠ | 1:11 |
| #axiom-uniform-lambda ⚠ | 0:10 |
| #axiom-linear-cost ⚠ | 1:6 |
| #contribution ⚠ | 0:6 |
| #claim-policy-repricing ⚠ | 3:6 |
| #claim-lambda-invariance ⚠ | 2:4 |
| #claim-separately-contractible ⚠ | 1:2 |
| #purpose | 6:6 |
| #carbon-jump | 9:0 |
| #referee-2 | 11:0 |

읽는 법: 반박 우세가 수치(공리) 쪽에 몰려 있고, **carbon-jump와 referee 대응 문헌은 탄탄**하다.
논문의 무게중심을 "공리가 참이다"에서 "공리 하에서 무엇이 따라나오는지 + 공리가 깨지는
방향의 감응도"로 옮기라는 뜻이다. 이는 이미 LEDGER의 conditional 구조와 같은 방향이다.

---

## 갱신 10 (2026-07-29 — DECISIONS X4: 일본 WACC 4.0% → 5.75%)

`DECISIONS.md` X4 확정 반영. 근거: 신일철 유이자부채 5.3조엔(2배 증가), blended 조달비용
조사 밴드 5.0–6.5%의 중앙값 (외부 조사 2026-07-22). 기존 4.0%는 저금리기 관행값.
`config/firms.csv`의 JP 철강 5개 자산(A04/A09/A05/A10/A11)에 적용. JP_NCC(0.050)는 별도
archetype 가정이므로 유지. KR(7.5% vs 조사 7.75%)은 차이 경미로 보류 — X4 범위 밖.

### 수치 이동 (base 시나리오, before → after)

| 항목 | before | after | 해석 |
|---|---|---|---|
| **NIPPON τ* (Oita A04)** | 2053.6 | **None (지평 밖)** | 가장 큰 이동 — 아래 |
| NIPPON τ* (Kashima A09) | 2053.5 | 2053.8 | |
| NIPPON 누적 alignment gap | 236.2 | **311.0 MtCO₂ (+32%)** | A04 사적 전환 소멸분 |
| NIPPON risk charge | 9.71 bps | 8.75 bps | 할인율↑ → 노출 PV↓ |
| NIPPON share (h2/carbon) | 78.2% / 10.1% | 73.5% / 15.2% | PAPER_DIFF D2 항목("JP WACC 4%가 H₂ share 왜곡") 방향대로 완화 |
| JFE / KOBE | τ* None 유지, gap 불변 | 동일 | 이미 사적 전환 없음 |
| POSCO (통제) | 15.6630 bps | 15.6630 bps | KR 불변 확인 |

### 발견

**일본의 "저 WACC 해자"가 실질 계산을 하고 있었다.** 4.0%에서는 오이타 고로가 2053년에
사적 전환했지만, 현실적 조달비용(5.75%)에서는 **일본 최대 H₂-DRI 전환 자산조차 지평 내
사적 전환이 사라진다.** 결과적으로 "요구 경로만이 전환을 만든다"(갱신 3의 JFE/Kobe 발견)가
일본 철강 전체로 확장된다. 동시에 risk charge는 오히려 줄어드는데(9.7→8.8), 이는 수준(bps)과
정렬(gap)이 반대로 움직일 수 있음을 다시 보여준다 — 타이밍 지표와 리스크 지표는 같지 않다.

검증: 회귀 36개 통과, KR 기업 전 지표 불변(통제), λ 불변성·share 합=1 유지.

---

## 갱신 5 (2026-07-31 — LSM 행사가치 drift 일치 수정)

### 원인

`lib/lsm_engine.exercise_value`가 행사시점 **현물가격을 잔여기간 전체에 동결**
(`annual × annuity`)한 반면, 시뮬레이션 경로는 config μ로 drift했다
(carbon +0.086/yr, h2 −0.05/yr, elec −0.015/yr, capex −0.03/yr). 계속가치(회귀 대상
실현 cashflow)는 drift를 보고 행사 payoff는 못 보는 비대칭 — 조기 행사일수록 잔여창이
길어 과소평가가 커지므로 **τ*가 체계적으로 늦어지고 wedge가 과대**되는 편향이었다.

### 수정

행사가치의 가격 드라이버 항을 드라이버별 `growth_annuity(rate, μ_k, 잔여연수)`
(= Σ e^{μs}/(1+r)^s, GBM의 E[P_{t+s}]=P_t·e^{μs}와 일치)로 교체. 상수 opex 항은
무성장 annuity 유지. 회귀 테스트 `test_exercise_value_is_drift_consistent` 추가.
동시에 `lib/anatomy.premium_bps`(호출자 0, 연율화 누락으로 정본 공식과 ~12배 불일치
위험)를 삭제하고 s04/s05가 공유하는 `risk_charge_annual_usd`로 단일화 — **premium 수치
자체는 불변** (공식 동일, 위치만 이동).

### 수치 이동 (τ* 앞당김 — 방향은 전부 예측대로)

| 항목 | 이전 (동결 payoff) | 이후 (drift 일치) |
|---|---|---|
| POSCO 광양 (A01) | 2050.7 | **2044.7** (−6.0y) |
| Nippon 오이타 (A04) | None (p_ex 0.49) | **2050.3** (문턱 통과) |
| 현대제철 당진 (A03/A08) | None (p_ex 0.42–0.44) | **2046–2047** (문턱 통과) |
| JFE·Kobe (A05/A10/A11) | None (p_ex 0.12–0.14) | None 유지 (p_ex 0.19–0.20) |

> 정정 (2026-08-04, 갱신 14 B12): 위 표의 설비·기업 귀속이 틀려 있었다 —
> A04는 기미츠가 아니라 **오이타**, A03/A08은 JFE 후쿠야마가 아니라 **현대제철 당진**,
> A05/A10은 Kobe가 아니라 **JFE**(A11만 Kobe). 기미츠·후쿠야마는 레지스트리에 없다.
> 수치는 원래 값을 유지하고 이름만 정정한다.
| 옵션가치 | 42–3095 USD/t | 87–3236 USD/t (~1.1–3.1×) |
| timing gap (양수 유지) | 7.3–18.8y | **2.7–15.2y** |
| σ-linearity R² | 0.957 | 재계산 (구조 유지) |

**해석 주의**: "요구 경로만이 전환을 만든다"는 갱신 3·4의 발견이 **약화**된다 —
drift 일치 payoff에서는 JFE 고로·Nippon 기미츠도 지평 내 사적 전환이 살아난다
(Kobe scrap/NG route만 여전히 None). wedge는 전 자산 양수 유지되나 크기가 절반 안팎으로
줄어듦. 논문 서술이 동결-payoff 수치에 기대고 있다면 **저자 확인 필요** — 동결이 의도된
보수적 가정이었는지(그렇다면 config μ=0으로 명시하는 게 정합), 아니면 버그였는지.

검증: 회귀 38개 통과 (신규 1 포함), anchors 그린, KR/JP regime 분리·λ 불변성·share 합=1 유지.

---

## 갱신 11 (2026-08-01 — 논리 감사: gap-loss bridge, benchmark pool, 탄소 regime)

### 1. condition gap을 손실분포로 직접 사상

새 `s13_gap_pricing`은 연도별 초과배출 `G_t`를
`PV_loss_j = Σ DF_t·G_t·max(P_j−P_reference, 0)`로 국가 탄소 시나리오에 사상한다.
전체 시나리오 확률을 한 번 사용하므로 p_bind를 다시 곱하지 않는다. 산출물
`alignment_gap_loss.json`은 transition-cost anatomy와 **별도 basis**이며, joint covariance가
없으므로 두 charge를 합산하지 않는다.

현행 surrogate run의 예시: POSCO gap 251.6 MtCO2 → 기대 PV loss $1,889m,
loss sigma $2,342m, gap-linked charge 7.63 bps. 이는 검증된 규제부채나 관측 spread가 아니다.

### 2. required deployment pool을 country x route로 분리

기존 `sector x route` pool은 한국·일본 H2 자산이 같은 배치곡선을 소비했다. 이를
`sector x country x route`로 분리하고, asset마다 benchmark source, intended benchmark,
pathway kind, allocation rule, headline eligibility를 기록한다. surrogate row는 모두
`headline_eligible=false`다.

이 구조 수정만으로 POSCO cumulative gap이 193.2 → 251.6 MtCO2, NIPPON이
193.0 → 241.2 MtCO2로 이동했다. POSCO base anatomy도 carbon/H2 31.6%/63.8% →
21.8%/73.2%로 이동했다. 따라서 구 deck의 gap·cluster 수치는 benchmark pool 구성에
민감한 것으로 판정하고 외부 헤드라인에서 철회한다.

### 3. 탄소 조건부/무조건부 통계량 정합

기존은 `E[level|bind]`에 전체 시나리오 sigma를 붙이고 p_bind를 다시 곱했다. 이제
transition-cost charge는 `E[level|bind]`와 `sigma_binding`을 짝지은 뒤 p_bind를 한 번
곱한다. 전체 시나리오 sigma는 진단용으로만 유지한다. KR sigma는 unconditional 0.88,
binding-conditional 0.60; JP는 1.13 / 0.67이다.

### 4. 데이터·재현성 fail-closed

`params_consolidated`와 향후 intensity export는 candidate parquet로 ingest되지만
`candidate_input_contract.json`에 `model_effect=none_until_DECISIONS...`로 기록된다.
모델 값은 config 승격 전에는 바뀌지 않는다. manifest는 실행 전/후 dirty를 분리하고,
`make test`는 calibration에 의존하도록 수정했다.

검증: 회귀 38개 통과. full `make all` 결과는 아래 최종 실행 기록에서 갱신한다.

최종 실행: `make all` 42개 회귀 + Next.js static build 통과. Next 15.5.22로
patch update하고 postcss 8.5.25 / sharp 0.35.3을 override해 `npm audit` high 3건을
0건으로 닫았다. manifest에 web package-lock hash를 추가했다.

---

## 갱신 12 (2026-08-03 — 측도 감사: 시나리오→drift 오역과 X9)

### 발견 (구조 감사, `FORMULA_LEDGER_2026-08-03.md` §D)

1. **μ_carbon > WACC (초임계 대기)**: μ 0.086 vs WACC — NIPPON/JFE/KOBE 5.75%,
   POSCO 7.5%, KR_NCC 7.0%, JP_NCC 5.0% → priced 전 기업 δ = r − μ < 0
   (HYUNDAI 10.5%만 양수). 갱신 5의 drift-consistency 수정이 μ를 행사가치까지
   전파하면서, 07-22의 "시나리오 앵커"가 사실상 영구 복리 상승 전망이 됨.
   시뮬레이션 KR 탄소가 2061년 기대 ~$300 — 시나리오 표 최대 $85와 모순.
2. **σ 부호 역전 (재현 실험)**: σ 스케일 0.5→2.0에서 τ*가 2046.2→2041.3으로
   단조 하락 — E[min(τ,H)]·p50·행사경로 조건부 평균 세 정의 모두 동일 방향
   (seed 8~12개). H₂ CfD의 σ-절단 채널만 분리 시 τ* +1.4y 지연, 완전 헤지 시
   p_exercised 0.74→0.58 붕괴. 유리한 실현(싼 수소)이 행사 트리거인데 헤지가
   이를 제거하는 구조. 출하 artifact와 정합 (intervention_impacts: POSCO h2_cfd
   Δτ* +0.50y, Δgap +21.7Mt).
3. **두 레인의 δ 충돌**: LSM은 δ<0 세계, s12는 `dp_delta=+0.05` 세계 —
   같은 계약에 반대 처방 (theory/10의 σ-절단 서사 vs LSM 출력).
4. **탄소가격 네 표현 병존**: s03 현물+drift / s04 ℓ_bind / s09 ℓ̄ / s12 현물.

### 판정

버그도 발견도 아닌 **번역 오류**: 시나리오는 "수준 도달 후 유지"를 말하는데
drift는 "영원 복리"로 옮겼다. CAP은 수익률을 전망하지 않는다 (계산기 원칙 —
시나리오가 수준을 구동). 갱신 3·4의 "요구 경로만이 전환을 만든다" 및 s06 개입
부호 서술은 이 오역에 조건부였으므로 X9 구현 후 재판정 대상.

### 결정 → DECISIONS X9 (RESOLVED 2026-08-03)

LSM 탄소경로를 시나리오-앵커 수렴 경로로 교체: μ_t = ln(target/spot)/T_anchor
(t ≤ anchor), 이후 0. μ는 파라미터→파생값 강등, dp_delta 삭제, s12 δ 동일
경로에서 유도. 수치 이동은 구현 후 이 문서에 기록 (규칙 8).

### X9 구현 수치 이동 (2026-08-03, 동일 config·seed, before → after)

| 항목 | before (영구 drift 8.6%) | after (앵커 수렴: KR 5.6%/JP 14.3% → 0) |
|---|---|---|
| 파생 μ_carbon | 0.086 전역 | **KR 0.0561 / JP 0.1433, anchor(15y) 후 0** |
| E[P_carbon] 2061 KR | ~$300 (시나리오 최대 $85의 3.5배) | **~$34.7 = ℓ̄ (R-5 해소, 회귀 테스트 고정)** |
| POSCO τ* (용량가중) | 2044.6 (p_ex 0.74–0.75) | **2050.0 (p_ex 0.55 — 경계적)** |
| POSCO 누적 gap | 251.6 Mt | **404.4 Mt (+61%)** |
| HYUNDAI τ* | 2046.2–2046.9 (p_ex 0.60–0.63) | **None (p_ex 0.24–0.26) — 사적 전환 소멸** |
| NIPPON τ* / gap | 2050.3 / 241.2 Mt | 2050.3 / 241.2 Mt (JP는 앵커 전 급등 구간이 지배 — 거의 불변) |
| JFE / KOBE τ* | None 유지 | None 유지 (p_ex 0.16–0.21 → 0.16) |
| KR_NCC gap | 14.0 Mt | 18.7 Mt |
| s12 m(σ) JFE | 1.82 (dp_delta=0.05) | **1.66 (δ=r 파생, dp_delta 삭제)** |
| 개입: capex_subsidy POSCO | Δτ* −1.05y, Δgap −28.0Mt | **Δτ* −1.26y, Δgap −40.9Mt — 최대 gap 레버로 부상** |
| 개입: carbon_reform POSCO | Δgap −55.9Mt | −25.8Mt (drift 재앵커 효과 축소 — 파생 μ가 상한) |
| 개입: h2_cfd POSCO | Δτ* +0.50y, Δgap +21.7Mt | **Δτ* +1.11y, Δgap +36.4Mt — σ-절단 지연 잔존** |

**판독 (구현 직후, 서술 확정 아님):**

1. 시나리오-정합 가격에서 **사적 전환은 더 어려워진다** — POSCO마저 p_ex 0.55의
   경계에 서고, HYUNDAI의 사적 전환은 사라진다. "요구 경로와 정책 없이는 전환이
   없다"는 발견이 X9 이후 **강화**되었다 (약화가 아님).
2. LEVEL 레버(capex_subsidy)가 gap을 가장 크게 닫는 수단으로 부상 — 격차의 1차
   문제는 수준임이 더 뚜렷해짐.
3. **H₂ CfD 단독의 τ* 지연은 X9 이후에도 잔존** — 한계적 프로젝트에서 σ-절단이
   "유리한 실현(싼 수소)" 트리거를 제거하는 메커니즘은 측도 수정과 무관하게 남는다.
   단 이는 **금융비용 채널(σ_B→스프레드→WACC) 미배선 상태의 결과**다: 계약이
   자본비용을 낮추는 경로가 없는 엔진에서 계약의 타이밍 효과는 실물옵션 채널만
   남기 때문. S2(금융 루프) 배선 후 재판정. 서술 잠정 금지, 두 채널 합산 후 확정.
4. 검증: 43/44 통과 (실패 1건은 샌드박스 환경의 uv 호출 문제 — macOS에서 재확인
   필요). 신규 회귀 test_carbon_drift_is_scenario_anchored: 파생 μ 항등,
   anchored_growth_annuity 항등 3종, E[P] anchor 도달·후 발산 없음.

## 갱신 13 (2026-08-04 — S2·S3·S4 구현: 금융 채널, 풀 연속 required, t_sw=τ*)

RESTRUCTURE §6의 구조 수정 잔여분 구현 (S5는 X11로 축소·해소 — DECISIONS 참조).
동일 config·seed. 커밋: S3 `8296986`, S4 `e7a7be4`, S2 `af85d76`.

### S3 — required 경로: 자산 배정 계단 → 풀 연속 q(t) (R-6 해소)

| 항목 | before | after |
|---|---|---|
| JFE A05 T_required | **2061 (endpoint 아티팩트)** | **2044** |
| KOBE A11 T_required | **2061 (동일)** | **2040** |
| JFE 누적 gap | 137.4 Mt | **281.4 Mt (+105%)** |
| KOBE 누적 gap | 3.0 Mt | **64.1 Mt (+21배)** |
| NIPPON / POSCO gap | 241.2 / 404.4 Mt | 272.7 / 448.1 Mt |

비H₂ 풀은 endpoint 재정규화 대신 logistic 비율 곡선; 자산 T_required는 용량 중점
교차의 보고용 파생값 (미도달 시 None — 지평말 고정 없음). required **배출 경로**는
q(t)로 직접 계산 (pro-rata), 사적 경로는 자산 계단 유지.

### S4 — 노출 전환연도 t_sw = τ* (R-7 해소)

| 기업 | carbon share (before → after) | h2 share | t_sw |
|---|---|---|---|
| POSCO | 0.218 → **0.920** | 0.732 → 0.070 | 2036.0 → 2050.0 |
| NIPPON | 0.067 → **0.797** | 0.883 → 0.164 | 2034.2 → 2050.3 |
| JFE / KOBE | 0.977/1.000 → **1.000/1.000** | 0 | → 2061 (τ*=None) |
| KR_NCC / JP_NCC | 0.026/0.018 → 0.099/0.076 | — | feedstock 지배 유지 |

**판독 (중대)**: required 시점 전환 가정이 사라지자 **H₂ 기업조차 탄소 지배**로 —
사적 경로(τ*≈2050)에서는 전환 전 탄소 노출(강도×ℓ_bind×24년)이 압도한다.
"조성(H₂ 58–83%) vs 집중"의 두 클러스터 서사는 **노출창을 required로 두었을 때의
산물**이었다. View 2 서술 재작성 필요: 조성 서사는 "전환한 세계의 잔여 리스크"
(개입 후 or required-조건부)로 옮겨야 하고, 사적 경로의 anatomy는 "전환 전
탄소정책 집중 + 늦은 전환"이 헤드라인이다. σ-linearity R² 0.814 → **0.998**
(노출창 정합의 부수 효과). τ*=None 기업(JFE·KOBE)의 100%는 아티팩트가 아니라
**집중이라는 발견** (X11).

### S2 — 금융 채널 (σ_B → 스프레드 → WACC → τ*, 1회 전파)

| 기업·개입 | 실물옵션 Δτ* | 금융 Δτ* (λ 밴드) | ΔWACC |
|---|---|---|---|
| POSCO h2_cfd | **+1.11y (지연 잔존)** | +0.00y (0/0) | +0.04bp |
| POSCO carbon_reform | −1.02y | +0.03y (+0.006/+0.041) | +4.5bp |
| POSCO capex_subsidy | −1.26y | −0.00y | −0.13bp |
| NIPPON package | −0.92y | −0.02y | +2.3bp |

**판독**: 금융 채널은 현행 배선(Δcharge×debt_share, λ=0.40)에서 **2차적**(<0.05y).
갱신 12 판독 3의 유보 조건("S2 배선 후 재판정")이 닫혔다 — **H₂ CfD 단독의 τ*
지연(+1.1y)은 두 채널 합산 후에도 잔존**한다. σ-절단이 자본비용 경로로 회수하는
이득이 위험 charge 몇 bps 수준이라 실물옵션 손실을 상쇄하지 못한다. 단 이 결론은
charge→스프레드 번역(λ·k·p_bind·debt_share 전부 assumed)에 조건부 —
`delta_tau_financing_channel_years`에 conditional_on 자동 전파, λ 밴드 병기.
concessional은 직접 WACC 개입이므로 상호배제(금융 채널 미적용).

### 부수: p_ex 절벽 표기

POSCO·NIPPON의 H₂ 자산 6개 전부 `tau_threshold_fragile=true` (p_ex 0.55 vs 임계
0.5±0.1) — X1(수소 원단위 ±49%)·X3(잔여강도) 결정에 따라 τ* 위상이 유한↔None으로
불연속 점프할 수 있음을 artifact가 명시. 서술 시 반드시 병기.

### 논문 대비 함의

- 논문의 H₂ share 58–83% 문장은 **required-시점 노출창 정의에 조건부**였다 —
  갱신 7의 "share 수준은 노출 창 정의에 민감"이 정점에 도달. 저자 항목 1(창 정의)은
  이제 "사적 τ* 창"으로 **결정됨** (S4, R-7 해소가 근거).
- gap 수준(JFE +105%, KOBE +21배)은 surrogate 비율 곡선에 조건부 (PROVISIONAL 유지,
  X10의 GCAM-KAIST 가격·경로 도착 시 재계산).

## 갱신 14 (2026-08-04 — 데이터 진실성 감사 + GCAM 출처 검증)

세 가지 질문에 대한 감사: ① GCAM 데이터 확보 ② 엔진·서사 정합 ③ 기업 데이터의 거짓.
아래는 **직접 파일 검증을 통과한 것만** 기록한다 (에이전트 주장은 재확인 후 채택).

### A. GCAM 출처 — 표기가 사실과 다르다 (BLOCKER)

직접 확인: `Input_Korea_GCAM-KAIST_1.0.zip`·`Input_default_...zip` (Zenodo 14171830,
CC BY 4.0) 다운로드 후 실제 입력 파일 검사.

1. GCAM-KAIST 1.0 = **GCAM v5.2** 확장. 모든 NZ2050 config가 로드하는 산업 입력
   `industry_New_HW.xml`의 supplysector는 `industry`·`industrial energy use`·
   `industrial feedstocks` **3개뿐** — 철강·iron·DRI·EAF·blast furnace 기술 **0건**.
   논문 본문도 산업부문을 집계 부문으로 명시.
   → **GCAM-KAIST NZ2050(_limCCS)은 철강 H₂-DRI 배치 경로를 산출할 수 없다.**
2. 따라서 `legacy_config/model_parameters.yaml`의
   `deployment_2050_Mt: 38` + `deployment_2050_Mt_source: "GCAM NZ2050 Korea scenario"`,
   `deployment_onset_yr_source: "Eom et al. 2022; KAIST EPRG"`는 **거짓 출처**다.
   38 Mt는 "한국 조강의 약 절반"이라는 **분석자 가정**이며 GCAM 출력이 아니다.
   영향: KR h2_dri 자산 4개(POSCO)의 T_required → condition gap → wedge 전부.
   raw는 읽기전용이므로 파일은 수정하지 않고 이 항목과 MISSING.md로 정정 기록.
   **DECISIONS X7 재개** — "Korea = GCAM-KAIST NZ2050_limCCS" 문장은 현재 근거 없음.
3. 실제로 확보한 것(등록 완료): 같은 시나리오의 **경제 전체 GHG 배출 제약**
   2025 **691** → 2030 558 → 2035 435 → 2040 312 → 2045 189 → 2050 **66** MtCO2e.
   철강 경로가 아니라 국가 배출 봉투다.
4. GCAM-KAIST의 탄소가격은 제약의 **내생 shadow price** = 모델 출력. Zenodo는
   input only, 출력 DB 미공개 → X10은 저자 요청 또는 타 출처 필요.
5. 철강 분해가 있는 올바른 출처: **Lee, McJeon, Yu, Liu, Kim, Eom (2024),
   J. Cleaner Production 476:143749** (DRI-EAF-H₂ 명시, 엄지용 공저). 유료·데이터 미공개.
6. 공개 대안(탄소가격, 2035 지평): GCAM-ROK — Choi·Park·McJeon 2025 preprint.
   KR ETS **8,870 KRW/tCO2**(현행정책 2023 수준 고정) → **30,411 KRW/tCO2**(강화, 2035).
   fx 1300 환산 $6.8 → $23.4. **CAP config의 SQ $12 / MSR $35보다 낮다.**
   주의: 같은 논문의 $42→$84/tCO2는 **CCS 보조금**(IRA 45Q 유사)이며 탄소가격 아님.
   같은 논문의 data-availability GitHub은 표준 GCAM Core 진단자료(2017)만 담고 있고
   한국 시나리오 출력은 비공개 로컬 DB — 즉 공개 출력 없음.

### B. 기업 데이터 — 검증된 결함

| # | 항목 | 현행 | 검증 결과 |
|---|---|---|---|
| B1 | `ev_usd_bn` 5개 | 40/18/40/15/8 | **UNTRACED** — `data/raw/` 전체에 EV 필드 없음(grep 0건). 전 bps의 분모. status=assumed로 배지는 흐름 |
| B2 | NIPPON 배출강도 | 1.90 | **raw와 모순** — `reference/CAP_Company_Data.xlsx`는 ~2.14(5사 중 최고). config는 최저로 배치 → −11%·순위 역전 |
| B3 | JFE/KOBE 강도 | 2.00/1.95 | 같은 raw는 2.08/2.0 |
| B4 | A05 JFE Keihin BF1 | 2036 reline, priced | **실재 의심** — Keihin 상공정 폐쇄(2023 취풍정지)가 사실이면 존재하지 않는 설비를 모델링. 같은 raw 워크북의 JFE 서사는 전부 서일본(Kurashiki) |
| B5 | A10 Kurashiki 투자연도 | 2034 | raw 워크북은 **2028**(2Mtpa EAF, FID 2025-04)·BF 폐쇄창 2027–2030 |
| B6 | 함대 커버리지 | 11기 | 조강 대비 **33%**, 기업별 21%(NIPPON)~48%(KOBE) = **2.3배 편차**. `premium_bps`는 자산합 π ÷ 기업 전체 EV → **기업간 bps 비교가 통제되지 않은 채 왜곡**. $/t는 무영향 |
| B7 | A08 당진 BF2 | start 2012, reline 2013 | **물리적 불가** 1년 캠페인. 2028 투자연도가 여기서 파생 |
| B8 | A06 포항 BF4 | start 2010, reline 2016 | 6년 캠페인 — 2031 파생값 오염 |
| B9 | HYUNDAI WACC/hurdle | 10.5%/12% | **UNTRACED** — raw에 없음. legacy_config은 국가 단위 KR 7.5%/10%만 보유 |
| B10 | POSCO WACC 출처 | "DART WACC" | **오귀속** — legacy_config 실제 출처는 GuruFocus·RMI, `[VERIFY]` 플래그가 config 진입 시 탈락 |
| B11 | config `capacity_mt_yr` | 4.2 등 | 내용은 raw의 `crude_steel_mt_yr`(실생산). nameplate(4.5)가 아님 — **이름이 내용과 다름**. 회귀 테스트로 규약 고정 |
| B12 | PAPER_DIFF 갱신 11 표 | 536–539행 | **귀속 오류**: A04는 Oita(기미츠 아님), A03/A08은 **현대 당진**(JFE 후쿠야마 아님), A05/A10은 **JFE**(Kobe 아님). 원고 진입 시 조작된 귀속이 된다 |
| B13 | `dart_portfolio.csv` | POSCO 2023 매출 1.45조 | 같은 raw의 `company_financials.csv`는 77.13조 — 항목 추출 오류. `verified=True` 표기. **모델 미사용**이나 거짓 재무가 등록 상태 |

미등록·미조사(저자 확인 필요): POSCO 광양 2고로(같은 워크북이 "CAP Gap 5 anchor"로 지목,
누적 137 MtCO2 고정)가 레지스트리에 **없음**; Nippon Oita BF1 5.2Mt/2004는 **2고로** 제원으로 보임.

### C. 코드 결함 — 수정 완료 (수치 불변)

1. `s01_ingest.py`: `intensities/prices/capex_refs/instruments` 기록이
   `ingest_candidate_tables()`의 `return` **뒤 도달불가 코드**로 07-26 스냅샷에 동결.
   `capex_refs`(→k_offcycle_mult)와 `prices`(→reference_prices)는 s02가 **소비**하므로
   raw를 고쳐도 모델이 따라오지 않는 잠재 drift였다. 도달 위치로 이동 + 신선도 테스트.
   (동결 parquet이 raw와 일치했으므로 현재 수치 이동 없음 — 잠재 결함이 실현 전에 잡힘.)
2. `s02_calibrate.py`: `firms_registry`·`routes_sensitivity` status가 `mode()`였다 —
   11 banded 뒤에 2 assumed(archetype)가 삼켜져 배지가 사라졌다. **최악 우선 집계**로
   교체 → `premium_levels.conditional_on`에 `firms_registry` 등장 (규칙 4 복구).
3. drift 가드 테스트 3종 신설: config↔raw 자산 일치, 소수 status 전파, 소비 parquet 신선도.

### 판정

**현 시점 `premium_bps`는 방어 불가**: 출처 없는 분모(B1) × 통제되지 않은 함대 커버리지(B6).
$/t와 Δ·순위는 살아남는다 (외부 리뷰 Step 8과 동일 결론이 데이터 쪽에서 재확인됨).
B2·B4·B5·B12는 **원고 진입 차단** 항목. B12는 이 문서 자체의 오류이므로 즉시 정정 대상.

### D. 엔진 감사 — BLOCKER 3건 수정 후 수치 재이동 (갱신 14 이어서)

갱신 13의 S3 수치는 **정정된다** (내가 S3에서 넣은 정규화 버그 때문).

| 기업 | 갱신 13 (버그) | **정정 후** | 비고 |
|---|---|---|---|
| POSCO 누적 gap | 448.1 Mt | **274.1 Mt** | first_misalign 2026 → **2027** |
| NIPPON | 272.7 Mt | **148.9 Mt** | timing gap None → **10.1y** (T_required 유한화) |
| JFE | 281.4 Mt | **277.6 Mt** | |
| KOBE | 64.1 Mt | **63.3 Mt** | |
| KR_NCC / JP_NCC | 18.7 / 11.8 | 18.7 / 11.8 | 계단 폴백 — 불변 |

**B3 (BLOCKER)**: S3에서 풀 q(t) = 전국 곡선 ÷ **풀 용량**으로 만들었다. 결과 ①
q(2026)=0.05~0.09 — 요구 경로가 2026년에 이미 함대의 5~9%가 전환됐다고 주장 →
전 기업 first_misalignment_year가 기준연도로 붕괴. ② 작은 풀이 더 빠른 요구 경로
(JP h2 풀은 2036년 100%, KR는 2039) — 순수 나눗셈 아티팩트. ③ h2 분기는 ÷pool_cap,
비h2 분기는 ÷L_Mt — **비교 불가능한 두 객체**. 수정: 포화값 대비 **비율 곡선** +
기준연도 재기준(q(base)=0) + 전 풀 동일 일정(pro_rata 규약). 회귀 테스트 2종 신설.

**B8 (BLOCKER)**: 갱신 13의 S2 표에 실린 금융 채널 점추정은 **잡음이었다**.
τ*는 이산 행사규칙의 MC 평균이라 수 bp 이동의 미분이 아니다 — ±5bp 프로브로 측정한
봉투가 ±0.017y이고 보고값 전부가 그 안이었다. 더 심각하게 POSCO h2_cfd의 +2.22y는
**p_ex 문턱 플립**(0.1bp 이동에 τ*→None)이었다. 게이트 3종 도입(문턱 플립 감지·해상도
바닥·λ 밴드 부호 일관성) 후 48개 중 **2개만 생존**: carbon_reform POSCO +0.030y /
NIPPON +0.021y. 둘 다 charge를 올리는 개입이므로 **지연**이 정상 부호.
→ **갱신 13 판독 정정**: "금융 채널은 2차적"이 아니라 **"이 배선·이 λ에서 0과 구별되지
않는다"**. H₂ CfD 지연(+1.11y)이 잔존한다는 결론은 오히려 강해진다 (해상도의 65배).

**B11 (BLOCKER)**: 계약 coverage가 **지평** 기준으로 가중되는데 s04는 [t_sw, H]를
가격했다. S4 이후 t_sw≈2050이므로 h2_cfd(tenor 2030–2045)·ppa(2028–2043)가
**만료 후 구매를 헤지한 것으로 계산**됐다. 노출창 기준 가중으로 교체 →
POSCO h2_cfd의 anatomy 효과가 0이 되고, 남은 Δcharge +0.19bps는 순수 **타이밍** 효과다.
**이것은 발견이다**: 현재 제시된 계약 조건은 문제가 되는 연도(2050년대)에 도달하지 못한다.
LSM 레인은 전 지평을 보므로 지평 기준을 유지 — 두 레인의 창이 다른 이유를 명시.

**B10 (SERIOUS)**: Shapley·sequential이 null-player 공리를 위반했다. 공집합만 base τ*,
나머지는 package τ*로 평가돼 base→package 타이밍 점프 전체가 S=∅ 항에 실렸고 그 항의
가중이 모든 참가자에게 1/n이라 **적용조차 안 되는 계약에 1/n씩 배분**됐다 (POSCO
feedstock_hedge 0.0303bps 등). 특성함수를 package τ*로 고정 → 비적용 계약 정확히 0.
W4 폭포 figure의 입력이므로 출판 전 필수 수정이었다.

**A1·A2 (SERIOUS, 규칙 1)**: carbon_reform의 "절반 이전"이 `reform_shift`에 0.5로
하드코드돼 있었다 (config value=1.0은 곱수일 뿐) → config value=0.5가 유일 출처로.
요구 경로 surrogate(L·t0·k)는 읽기전용 raw yaml에서 직접 읽혀 status·anchor·PAPER_DIFF
추적 밖이었다 → **`config/pathways.csv` 신설**(status=assumed, theory_anchor, pandera 검증).
anchor 검증의 config 참조가 10 → 11개로 늘었다.

**C1·C2 (SERIOUS, 서술)**: 산출물과 모순되던 서술 정정 — README(조성 vs 집중),
theory/05(H₂ CfD "거의 앞당기지 못한다" → **늦춘다** + tenor 미달), theory/06(두 클러스터
서사를 "전환한 세계"로 이동), theory/10(H₂ CfD 최대 risk cut 주장 철회, δ=r은 **앵커
이후만** 해소임을 명시, 하드코딩 1.9배 → 렌더값), GLOSSARY(수소 63.8% → 탄소 92.0%).
`cluster_separation`에 `separation_is_material` 병기 — S4 이후 두 클러스터 모두 탄소
지배라 "분리됐다"만으로는 공허하다.

### 미해결로 남긴 것 (저자 판단 필요)

- **X12**: EV 5개 미출처 + 함대 커버리지 33%(기업별 21~48%) → `premium_bps` 기업간 비교 불가.
- **B2·B4·B5**: NIPPON 강도 1.90 vs raw 2.14, JFE Keihin 실재 의심, Kurashiki 2034 vs 2028.
- **C3**: JFE·KOBE가 전 개입에 무반응(τ*=None) — 정정 후에도 누적 gap의 **31%**(340.9/958.6 Mt)를
  차지하는데 개입 엔진이 할 말이 없다. concessional이 NCC archetype의 τ*를 **늦추는**
  퍼버스 부호(JP μ_carbon > WACC의 앵커 전 잔재). `decision_class`가 1e-4 bps 차이에
  라벨을 붙인다(`lib/underwriting.py` tol=sqrt(eps) — 재료성 문턱 아님).
- **A2 잔여**: `q_feedstock` 활성화는 X11로 종결됐으나 `total_bf_capacity_Mt: 78`은 여전히
  미사용 — 정규화 기준을 국가 용량으로 바꿀지는 X10 데이터 도착 후 결정.

### E. 엔진 최종 판정 (2026-08-04) — 남은 것은 버그가 아니다

감사 후 재검증 결과, **철강 기업 엔진에서 계산 오류는 더 발견되지 않았다.** 남은 3건은
성질이 다르므로 분류해 기록한다.

**E1. 퍼버스 부호는 δ<0의 귀결이 아니다 — 감사 보고의 인과 설명을 기각한다.**
dτ*/dWACC를 ±150bp(잡음 위)에서 직접 스캔:

| 기업 | −150bp | +150bp | 부호 | 앵커 전 δ |
|---|---|---|---|---|
| POSCO | −0.515y | +0.457y | 정상 | +0.019 |
| NIPPON | −0.515y | +0.509y | 정상 | **−0.086** |
| JFE·KOBE | 0 | 0 | 무반응 (τ*=None) | −0.086 |
| KR_NCC | **+0.370y** | −0.286y | **퍼버스** | **+0.014** |
| JP_NCC | **+0.421y** | −0.364y | **퍼버스** | −0.093 |

δ<0인 NIPPON은 정상 부호이고 δ>0인 KR_NCC가 퍼버스다 — **δ 부호와 무관**하다.
실제 원인은 route의 **탄소 전 순영업편익**:

| route | avoided−other−elec−feed−h2 | K |
|---|---|---|
| h2_dri | **−333.5 $/t** | 470 |
| scrap_eaf | −108.5 | 200 |
| e_cracker | **−7.5 (≈0)** | 650 |
| ccus_cracker | **+6.2 (≈0)** | 550 |

h2_dri는 결정론 마진이 크게 음수라 행사가 **탄소편익의 PV가 문턱을 넘는지**로 결정된다 →
r↓이면 그 PV가 커져 앞당겨진다(정상). NCC는 마진이 ≈0이라 행사가 **유리한 실현**
(싼 원료·전력, 높은 탄소)에 걸린다 → r↓이면 기다림의 옵션가치가 더 커져 늦어진다.
이는 Dixit–Pindyck의 표준 결과(dτ*/dr의 부호는 정해져 있지 않다)이며 **버그가 아니다**.
단 NCC archetype에 대한 어떤 서술도 이 메커니즘을 병기해야 한다.

**E2. 앵커 전 δ<0 (일본 4사, 지평의 43%)도 버그가 아니다.** JP 현물 $3.0 → 시나리오
기대 $25.75가 15년 수렴을 함의하므로 μ_JP=0.1433 > WACC 0.0575다. "탄소가가 급등하는
구간에는 기다림에 값이 붙는다"는 것은 경제적으로 옳다 — X9가 고친 것은 그것이
**영원히** 계속되던 오역이었다. 남은 과제는 데이터: JP 현물 $3.0(banded)의 검증.
s12는 전 구간 δ=r을 쓰므로 두 레인은 앵커 전에 다른 세계에 있다 — theory/10에 명시했다.

**E3. 구조적 사각지대 (버그 아님, 그러나 정책 분석의 한계)**: JFE·KOBE는 p_ex 0.155–0.164로
문턱 0.5에 못 미쳐 **8개 개입 전부에 무반응**이다. 두 기업이 누적 gap의 **31%**를
차지하는데 개입 엔진이 할 말이 없다. "사적 전환이 없다"는 발견 자체는 맞지만,
"무엇이 이 31%를 움직이나"에는 현행 엔진이 답하지 못한다 — 2차 과제.

**E4. 잠재 결함 수정 (X10 도착 시 조용히 깨질 것들)**: GCAM raw 곡선의 비단조·지평 미달을
fail-closed로 차단(전자는 required 경로가 설비를 역전환시키고, 후자는 np.interp 외삽으로
T_required를 왜곡) · `required_path_provisional`이 석유화학 archetype 때문에 영구 True여서
GCAM 도착 후에도 안 내려가던 문제 수정 · `cal.mu_carbon`이 api 오버라이드 후 stale로
남던 문제 동기화.

**E5. 재료성 없는 라벨링 수정**: `classify_intervention`이 sqrt(eps)≈1.5e-8을 문턱으로 써서
1e-4 bps 이동에 `de_risking_only` 라벨이 붙고 그것이 기업의 "최고 de-risker"로 보고됐다
(JFE capex_subsidy 0.00014 bps). config 재료성 문턱(0.01 bps / 0.05 Mt)으로 교체 →
JFE·KOBE는 `best_de_risker: None`이 정답이 됐다.
