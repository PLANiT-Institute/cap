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
