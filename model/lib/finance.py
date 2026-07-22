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
