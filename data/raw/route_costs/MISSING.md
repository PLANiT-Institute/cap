# MISSING — 한·일 route별 투입원단위·비용 (2026-07-29 문헌조사에서 확인)

**목적**: `config/routes.csv`의 감응도 벡터 a는 **벤더·글로벌 기관 원단위**다 —
Midrex Tech Sheet 2023(I01 수소 60 kg/t), LBL Green Steel(I02 전력 0.8 MWh/t, 외부 수소 기준),
IRENA/Lhyfe(I03 전해조 포함 3.6 MWh/t), IEA ETP 2024(I10 잔여 0.1 tCO₂/t).
한국·일본 어느 쪽도 아니고 특정 지역 값도 아니다. 대상은 한·일 고로이므로
국가 특정 원단위로 교체하거나, 못 하면 **"국가 무관 벤더 기준"임을 결과 서술에 명시**해야 한다.
CAP의 A3(선형 비용함수)·A4(route 감응도)가 이 표에 직접 걸려 있다.

주의: `q_elec_mwh_t = 0.8`은 **외부 조달 수소 기준**(I02)이다. 전해조를 자가 보유하면 3.6
(I03)이고, 유럽 연구의 3.48 MWh/t(Vogl 외 2018)와 일본 IEEJ의 135 kWh/t-DRI(환원로 단계만)는
**셋 다 공정 경계가 다르다**. 비교 전에 경계를 맞출 것 — `PAPER_DIFF.md` D17.

## 1. KEEI 보고서의 route별 투입원단위 표 (최우선)

**필요**: `kang2022` (에너지경제연구원)의 route별 투입원단위 표 —
route(BF-BOF / H2-DRI / scrap-EAF / gas-DRI / CCUS retrofit)별
수소 kg/t, 전력 MWh/t, 철광석·스크랩 kg/t, 탄소 tCO₂/t.
**현황 (2026-07-29 갱신)**: **부분 확보.** 기본연구보고서 22-03(강병욱, KEEI, 2022-12) 본문에서:

| route | 항목 | KEEI 값 | config 현행 | 차이 |
|---|---|---|---|---|
| BF-BOF | 코크스 | 313.2 kg/tHM | 0.7 t/t (I06, IEA Coal 2024) | 단위·경계 상이 |
| BF-BOF | 철광석 | 1,652 kg/tHM | 1.65 t/t (I07, World Bank) | **일치** |
| H2-DRI | 수소 | **89.6 kg/t 조강** | 60 kg/t (I01, Midrex) | **+49%** |
| H2-DRI | 전력 | **550 kWh/t** | 800 kWh/t (I02, LBL) | **−31%** |

**미확보**: route별 CO₂ t/t, gas-DRI, CCUS retrofit — 이 보고서에 없음. 다른 출처 필요.

**반영 보류 이유**: 수소 +49%는 결과를 크게 움직이는 크기다. KEEI는 "t 조강" 기준이고
Midrex는 "t steel" 기준이라 경계가 같은지 확인 전에는 바꾸지 않는다(규칙 8·6).
전력 550 kWh/t도 전해조 포함 여부가 명시되지 않았다 — 아래 3번과 같은 문제.
**확인되면 `status: measured`(한국 특정)로 승격 후 `make model` 재실행. 결과가 바뀔 것을 전제.**
**출처**: keei.re.kr 기본연구보고서 22-03.
**ingest 계약**: 확보 시 `data/raw/route_costs/keei_route_intensity.csv`로 저장 →
provenance 등록 → `config/routes.csv`의 해당 계수를 `status: measured`로 승격.
승격 전까지 routes.csv의 원단위는 **유럽 이식값**임을 결과 서술에서 명시할 것.

## 2. POSRI HyREX 톤당 비용 보고서

**필요**: HyREX(POSCO 유동층 수소환원)의 톤당 비용 구조와 손익분기 수소가·탄소가.
**현황**: posri.re.kr 목록만 확인, 본문 미확보. 언론 인용 추정치(수소 ¥1,000–2,000/kg,
탄소가 $15–20/tCO₂, 전력 +60%)는 2차 자료라 `refs.bib`에 넣지 않았다 — `PAPER_DIFF.md` D17.
**ingest 계약**: 확보 시 POSCO 자산의 route 파라미터를 기업 특정값으로 분리.

## 3. 일본 원단위의 공정 단계 정의

**필요**: `shibata2023`(IEEJ)의 135 kWh/t-DRI는 **환원로 단계만**이고, 유럽의 3.48 MWh/t는
전 공정 기준이다. 두 수치는 직접 비교 불가.
**필요 작업**: 단계 경계(환원 / 용해·정련 / 압연)를 맞춘 원단위 재구성.
**ingest 계약**: 단계 정의가 맞춰지기 전에는 일본 수치를 config에 넣지 않는다.

## 4. K-ETS 가격 시점 대조

`config`의 `carbon_base_kr = 14.93`(measured, ICAP 최근 종가)과 문헌의 $6–7/tCO₂
(InfluenceMap 2025)이 다르다. 시점·정의 차이로 보이나 확인 전 어느 쪽도 바꾸지 않는다.
**ingest 계약**: 두 출처의 기준일·정의를 대조해 하나를 선택하고 나머지를 provenance 각주로.
