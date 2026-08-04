# 10 · LEVEL/WEDGE 분해 — 폐형해 근사 레인

**이 장이 주장하는 것**: 전환을 막는 격차는 수준(LEVEL)과 기다림(WEDGE)으로 가법 분해되며, 두 성분은 서로 다른 정책 수단에 반응한다.
**전제**: 영구옵션 폐형해(m(σ)=β/(β−1)), routes.csv 감응도, config 파라미터.
**아직 열린 것**: 유한지평·reline 격자와의 정합(LSM이 정의), WEDGE의 경로 기반 정의 구현.

---

## 분해 {#claim-level-wedge-split}

같은 "왜 기다리는가"를 §01의 wedge(τ* − T_required, 시간 축)와 다른 축으로 자른다 — **달러 축**:

> conditions gap ($/t) = **LEVEL** + **WEDGE**
>
> LEVEL = max(0, E[전환 손익]) — 불확실성이 전혀 없어도 남는 순손실 (Marshallian, 옵션 OFF)
> WEDGE = (m(σ_project) − 1) · LEVEL — 불확실성이 만드는 기다림의 값

`status: CLAIM · 폐형해 근사 — LSM(§03의 τ*)이 정의이고 이 레인은 직관·검산용. 별도 basis_id
(project_levelized.closed_form_approximation.derived_coefficients)로 격리되며 LSM wedge와 비교 인용 금지.`

계수는 전부 유도값이다. base_diff·h2_slope 같은 축약형 상수는 존재하지 않는다 — 각 항은
routes.csv의 물량 원단위 × config 기준가의 곱이고, capex는 transaction_assumptions의
수명으로 연금화한다(CRF). 지식 기지 prototype(2026-07-24)이 하드코딩했던 모든 숫자가
여기서는 config 한 곳에서 온다.

현재 산출 (base, 각국 현물 탄소가 — 기준일 {{pricing.carbon_base_kr}}$/t는 2026-06-30 종가):

| 기업 | LEVEL $/t | σ_project | m | WEDGE $/t |
|---|---|---|---|---|
| POSCO | {{lw.POSCO.level}} | {{lw.POSCO.sigma_project}} | {{lw.POSCO.m}}x | {{lw.POSCO.wedge}} |
| NIPPON | {{lw.NIPPON.level}} | {{lw.NIPPON.sigma_project}} | {{lw.NIPPON.m}}x | {{lw.NIPPON.wedge}} |
| JFE | {{lw.JFE.level}} | {{lw.JFE.sigma_project}} | {{lw.JFE.m}}x | {{lw.JFE.wedge}} |
| KOBE | {{lw.KOBE.level}} | {{lw.KOBE.sigma_project}} | {{lw.KOBE.m}}x | {{lw.KOBE.wedge}} |

## 어떤 σ를 m에 넣는가 — 검증 노트의 교정 {#claim-project-sigma}

prototype은 m(σ)에 σ_carbon(0.50)을 넣었다. 이는 프로젝트 변동성 전부를 탄소 하나에
귀속시키는 셈이다. 2026-07-29 검증(지식 기지 `03_Notes/_verification_...md`)이 보인 것:
노출은 물량×가격×σ의 곱이므로, **노출가중 분산에서 탄소 비중은 base에서 소수**다
(POSCO {{lw.POSCO.var_carbon_pct}}, 수소 {{lw.POSCO.var_h2_pct}}).

따라서 s12는 m에 **노출가중 비용 바스켓의 변동계수 σ_project**를 넣고, σ_carbon 단독
귀속치는 `legacy_attribution`으로 병기만 한다(계보 — 인용 금지). POSCO 기준 탄소 단독
귀속은 WEDGE를 {{lw.POSCO.legacy_overstatement_x}}배 과대평가한다.

`status: CLAIM · 검증 노트 재현 가능 · challenged-by 없음`

주의 — 이 레인의 base 탄소가는 **각국 현물**(사적 시점 뷰)이다. §04의 anatomy가 쓰는
ℓ_bind(구속 조건부 가격)와 다르므로, JFE·KOBE의 탄소 비중이 여기서는 작고 anatomy에서는
지배적인 것은 모순이 아니라 **basis 차이**다. reform 열은 ℓ_bind로 재계산한다.

## σ-절단 수단의 자리 {#claim-sigma-truncation}

분해가 곧 정책 지도다:

- **LEVEL을 줄이는 수단** — 보조금, CCfD strike, CAPEX 지원, 조건부 무상할당: 경계(수준)를 내린다.
- **WEDGE를 줄이는 수단** — σ를 자르는 계약(CfD·PPA·collar): m(σ)를 낮춘다.
- 탄소 **collar**는 기대수준을 올리며(LEVEL↓) σ_carbon을 동시에 자르므로(WEDGE↓) 변동성
  spot 탄소가격을 **탄소 성분에 한해** 약우월한다. GX-ETS의 floor/ceiling이 실증 사례다.

단, 우선순위는 var share가 정한다: 이 레인의 base에서 지배 성분은 탄소가 아니라
**수소**(h2-route) 또는 **전력**(grid-route)이다. 그러나 **s06의 개입 결과는 σ-절단
계약을 1순위로 지지하지 않는다** (2026-08-04 정정):

- H₂ CfD 단독은 τ*를 **늦추고**(POSCO {{iv.POSCO.h2_cfd_dtau}}y) charge를 줄이지 못한다 —
  유리한 실현(싼 수소)이 행사 트리거인데 σ-절단이 그것을 함께 제거한다.
- 게다가 사적 경로에서 노출창은 [τ*, H]≈[2050, 2061]인데 h2_cfd tenor는 2030–2045로
  **겹치지 않는다**. 즉 현재 제시된 계약 조건은 문제가 되는 연도에 도달하지 못한다
  (감사 2026-08-04 B11 — coverage는 이제 노출창 기준으로 가중된다).
- 실제 최대 risk cut은 LEVEL 레버(capex_subsidy·concessional)다.

이 불일치는 두 레인의 **노출창 차이**에서 온다: s12는 전환 후 levelized 바스켓만 보고,
s04는 전환 전 탄소 레그(24년)를 포함한다. "collar가 wedge 전체를 붕괴시킨다"는
prototype 서술은 폐기되고, 이 문서의 서술도 s06 산출에 종속된다.

`status: CLAIM · s06 intervention_impacts와 **부분 불일치** (위 정정 참조) · 정량은 s12 artifact`

## 한계 (명시)

1. 영구옵션·GBM·단일 복합자산 가정 — 유한지평·다요인·reline 격자는 LSM 레인(§03)만 다룬다.
2. δ(convenience yield 유사항)는 X9(2026-08-03) 이후 파라미터가 아니라 **파생값 δ = r**이다
   (`dp_delta` 삭제; 앵커 이후 정상상태). 단 **앵커 전 구간(15년)에는 여전히 δ = r − μ_carbon**
   이고 일본은 μ_JP > WACC이므로 δ < 0이다 — LSM 레인은 그 구간에서 초임계 대기 세계에 있고
   s12는 δ = r을 전 구간에 쓴다. 즉 R-2는 **앵커 이후만** 해소됐다 (감사 2026-08-04).
   m은 δ에 민감하므로 이 레인의 수치는 수준이 아니라 **비교·방향** 용도다.
3. WEDGE의 경로 기반 정의(행사확률 50% 기준)는 미구현 — prototype docstring과 구현의
   불일치를 승계하지 않기 위해 여기 명시해둔다.
