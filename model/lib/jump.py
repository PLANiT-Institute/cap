"""탄소 드라이버 확산+정책점프 혼합 (§04 #claim-policy-repricing).

σ²_carbon = σ²_diff + Σ_j p_j (ℓ_j − ℓ̄)² / ℓ̄²
점프는 분산 계층에만 추가된다 (regime-switching LSM 아님) — LEDGER 상시 표기 대상.
"""
from __future__ import annotations

import numpy as np


def scenario_mean_level(levels: np.ndarray, probs: np.ndarray) -> float:
    """ℓ̄ — 전 시나리오 확률가중 평균 수준."""
    return float(np.dot(probs, levels))


def binding_level(levels: np.ndarray, probs: np.ndarray, binds: np.ndarray) -> float:
    """E[ℓ | bind] — 예산이 구속하는 시나리오로 조건화한 탄소 수준.
    노출의 '수준'은 구속 조건부 (A2: p_bind는 수준에만), 분산은 전 시나리오 산포."""
    mask = binds.astype(bool)
    return float(np.dot(probs[mask], levels[mask]) / probs[mask].sum())


def sigma_carbon_combined(
    sigma_diff: float, levels: np.ndarray, probs: np.ndarray
) -> float:
    """reform-priced σ_carbon: 확산 + 시나리오 점프혼합."""
    l_bar = scenario_mean_level(levels, probs)
    jump_var = float(np.dot(probs, (levels - l_bar) ** 2)) / l_bar**2
    return float(np.sqrt(sigma_diff**2 + jump_var))


def sigma_carbon_binding(
    sigma_diff: float,
    levels: np.ndarray,
    probs: np.ndarray,
    binds: np.ndarray,
) -> float:
    """Conditional-on-binding carbon sigma.

    This statistic pairs with ``E[level | bind]``.  Binding probabilities are
    normalized inside the conditional distribution; a downstream unconditional
    charge may then multiply by ``p_bind`` exactly once.
    """
    mask = binds.astype(bool)
    bind_probs = probs[mask]
    conditional_probs = bind_probs / bind_probs.sum()
    bind_levels = levels[mask]
    l_bind = float(np.dot(conditional_probs, bind_levels))
    jump_var = float(
        np.dot(conditional_probs, (bind_levels - l_bind) ** 2) / l_bind**2
    )
    return float(np.sqrt(sigma_diff**2 + jump_var))
