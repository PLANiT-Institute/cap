"""Euler 분산 분해 (§02 A1: anatomy는 평균이 아니라 분산 분해).

w_k = E_k·σ_k (드라이버별 달러 변동성), σ_B² = wᵀρw,
RC_k = w_k(ρw)_k/σ_B, s_k = RC_k/σ_B = w_k(ρw)_k/σ_B². Σs_k = 1 항등.
s_k는 (a, σ, ρ)만의 함수 — λ·p_bind 불진입 (Prop 1, #claim-lambda-invariance).
"""
from __future__ import annotations

import numpy as np

DRIVERS = ["carbon", "h2", "elec", "capex"]


def euler_shares(w: np.ndarray, rho: np.ndarray) -> tuple[float, np.ndarray]:
    """(σ_B, shares). w=0 벡터면 shares는 0."""
    rw = rho @ w
    var = float(w @ rw)
    if var <= 0:
        return 0.0, np.zeros_like(w)
    return float(np.sqrt(var)), (w * rw) / var


def lambda_k_shares(w: np.ndarray, rho: np.ndarray, lambdas: np.ndarray) -> np.ndarray:
    """driver별 λ_k 허용 시 s_k = λ_k·RC_k / Σλ_j·RC_j (A5 깨질 때의 감응도, R1 대응)."""
    sigma_b, shares = euler_shares(w, rho)
    rc = shares * sigma_b
    weighted = lambdas * rc
    total = weighted.sum()
    return weighted / total if total > 0 else np.zeros_like(w)


def premium_bps(
    k: float, lam: float, p_bind: float, sigma_b_usd: float, ev_usd: float, bps_scale: float
) -> float:
    """π = k·λ·p_bind·σ_B, EV 대비 bps. 곱 구조가 Prop 1의 전제."""
    return k * lam * p_bind * sigma_b_usd / ev_usd * bps_scale
