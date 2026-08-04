"""할인·연금 순수 함수. 숫자 리터럴 없음 — 전부 인자."""
from __future__ import annotations

import numpy as np


def df(rate: float, t: float) -> float:
    return float((1.0 + rate) ** -t)


def annuity(rate: float, n_years: float) -> float:
    """연말 지급 n년 연금의 현재가치 계수."""
    if n_years <= 0:
        return 0.0
    return float((1.0 - (1.0 + rate) ** -n_years) / rate)


def growth_annuity(rate: float, mu: float, n_years: float) -> float:
    """연말 지급, 기대수준이 e^{μs}로 자라는 연금의 PV 계수.

    GBM 아래 E[P_{t+s}] = P_t·e^{μs} — 시뮬레이션 measure와 일치하는 행사가치용.
    μ=0이면 annuity()와 동일.
    """
    if n_years <= 0:
        return 0.0
    q = float(np.exp(mu)) / (1.0 + rate)
    if abs(q - 1.0) < np.finfo(float).eps:
        return float(n_years)
    return float(q * (1.0 - q**n_years) / (1.0 - q))


def anchored_growth_annuity(
    rate: float, mu: float, n_years: float, growth_years: float
) -> float:
    """성장이 growth_years년 후 멈추는(수준 유지) 연금의 PV 계수 — X9 시나리오-앵커 경로.

    E[P_{t+s}] = P_t·e^{μ·min(s, g)} : 앵커까지는 e^{μs}로 자라고, 도달 후 수준 유지.
    g=0 → annuity()와 동일, g≥n → growth_annuity()와 동일, μ=0 → annuity()와 동일.
    CAP은 수익률을 전망하지 않는다 — μ는 시나리오 수준 도달 궤도의 파생값 (DECISIONS X9).
    """
    if n_years <= 0:
        return 0.0
    g = min(max(growth_years, 0.0), n_years)
    head = growth_annuity(rate, mu, g)
    if n_years <= g:
        return head
    level = float(np.exp(mu * g))
    return head + level * (annuity(rate, n_years) - annuity(rate, g))


def pv_window(rate: float, t_start: float, t_end: float) -> float:
    """t_start~t_end 사이 연 1달러 흐름의 PV (t=0 기준)."""
    if t_end <= t_start:
        return 0.0
    return annuity(rate, t_end) - annuity(rate, t_start)


def nearest_psd(m: np.ndarray) -> np.ndarray:
    """대칭행렬을 최근접 PSD로 사영 (고유값 클리핑) — band draw 시 ρ 유효성 보장."""
    sym = (m + m.T) / 2.0
    w, v = np.linalg.eigh(sym)
    w_clipped = np.clip(w, 0.0, None)
    out = v @ np.diag(w_clipped) @ v.T
    d = np.sqrt(np.clip(np.diag(out), a_min=np.finfo(float).tiny, a_max=None))
    out = out / np.outer(d, d)
    np.fill_diagonal(out, 1.0)
    return out
