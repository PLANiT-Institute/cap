# MISSING — 한·일 route별 투입원단위·비용 (2026-07-29 문헌조사에서 확인)

**목적**: `config/routes.csv`의 감응도 벡터 a가 현재 유럽 연구(Vogl 외 2018 등)에서 온
유럽 원단위다. 대상은 한·일 고로이므로 국가 특정 원단위로 교체해야 한다.
CAP의 A3(선형 비용함수)·A4(route 감응도)가 이 표에 직접 걸려 있다.

## 1. KEEI 보고서의 route별 투입원단위 표 (최우선)

**필요**: `kang2022` (에너지경제연구원)의 route별 투입원단위 표 —
route(BF-BOF / H2-DRI / scrap-EAF / gas-DRI / CCUS retrofit)별
수소 kg/t, 전력 MWh/t, 철광석·스크랩 kg/t, 탄소 tCO₂/t.
**현황**: 목차만 접근 가능, 수치 표 미확보 (2026-07-29 조사).
**출처**: keei.re.kr 발간물 — PDF 직접 다운로드 또는 도서관 열람.
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
