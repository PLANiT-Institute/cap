"""Pure mathematics for the reconciled joint risk-premium lane."""
from __future__ import annotations

import math
from typing import Any

import numpy as np


TOL = 1e-12


def validate_correlation_matrix(rho: np.ndarray, *, tolerance: float = 1e-10) -> None:
    matrix = np.asarray(rho, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("correlation matrix must be square")
    if not np.allclose(matrix, matrix.T, atol=tolerance, rtol=0):
        raise ValueError("correlation matrix must be symmetric")
    if not np.allclose(np.diag(matrix), 1.0, atol=tolerance, rtol=0):
        raise ValueError("correlation matrix diagonal must equal one")
    minimum_eigenvalue = float(np.linalg.eigvalsh(matrix).min())
    if minimum_eigenvalue < -tolerance:
        raise ValueError(
            f"correlation matrix must be PSD; min eigenvalue={minimum_eigenvalue}"
        )


def weighted_correlation(
    x: np.ndarray, y: np.ndarray, probabilities: np.ndarray
) -> float | None:
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    probs = np.asarray(probabilities, dtype=float)
    if x_arr.shape != y_arr.shape or x_arr.shape != probs.shape:
        raise ValueError("values and probabilities must have identical shapes")
    if np.any(probs < 0) or not np.isclose(probs.sum(), 1.0):
        raise ValueError("probabilities must be nonnegative and sum to one")
    x_mean = float(probs @ x_arr)
    y_mean = float(probs @ y_arr)
    x_centered = x_arr - x_mean
    y_centered = y_arr - y_mean
    x_var = float(probs @ (x_centered**2))
    y_var = float(probs @ (y_centered**2))
    if x_var <= TOL or y_var <= TOL:
        return None
    corr = float(probs @ (x_centered * y_centered) / math.sqrt(x_var * y_var))
    return float(np.clip(corr, -1.0, 1.0))


def factor_dependence(
    w: np.ndarray,
    rho: np.ndarray,
    carbon_gap_correlation: float | None,
    *,
    carbon_index: int = 0,
) -> dict[str, float | None]:
    weights = np.asarray(w, dtype=float)
    matrix = np.asarray(rho, dtype=float)
    if weights.ndim != 1 or matrix.shape != (len(weights), len(weights)):
        raise ValueError("factor weights and correlation matrix dimensions do not match")
    validate_correlation_matrix(matrix)
    variance = float(weights @ matrix @ weights)
    if variance <= TOL:
        return {
            "transition_sigma": 0.0,
            "rho_transition_carbon": None,
            "rho_carbon_gap": carbon_gap_correlation,
            "rho_transition_gap": None,
        }
    sigma = math.sqrt(variance)
    rho_transition_carbon = float((matrix @ weights)[carbon_index] / sigma)
    rho_transition_carbon = float(np.clip(rho_transition_carbon, -1.0, 1.0))
    rho_transition_gap = (
        None
        if carbon_gap_correlation is None
        else float(
            np.clip(
                rho_transition_carbon * float(carbon_gap_correlation), -1.0, 1.0
            )
        )
    )
    return {
        "transition_sigma": sigma,
        "rho_transition_carbon": rho_transition_carbon,
        "rho_carbon_gap": carbon_gap_correlation,
        "rho_transition_gap": rho_transition_gap,
    }


def combine_premiums_bps(
    transition_bps: float, gap_bps: float, rho_transition_gap: float | None
) -> dict[str, Any]:
    transition = float(transition_bps)
    gap = float(gap_bps)
    if transition < 0 or gap < 0:
        raise ValueError("risk-premium components must be nonnegative")
    independence = math.hypot(transition, gap)
    lower = abs(transition - gap)
    upper = transition + gap
    if transition <= TOL or gap <= TOL:
        effective_rho = None
        central = upper
    else:
        if rho_transition_gap is None:
            raise ValueError("nonzero components require an identified correlation")
        effective_rho = float(rho_transition_gap)
        if not -1.0 <= effective_rho <= 1.0:
            raise ValueError("correlation must be between -1 and one")
        variance = (
            transition**2
            + gap**2
            + 2.0 * effective_rho * transition * gap
        )
        central = math.sqrt(max(variance, 0.0))
    if central < lower - 1e-9 or central > upper + 1e-9:
        raise AssertionError("combined premium violates correlation bounds")
    return {
        "mathematical_lower_bps": lower,
        "independence_bps": independence,
        "central_bps": central,
        "perfect_positive_upper_bps": upper,
        "component_sum_bps": upper,
        "covariance_credit_vs_sum_bps": upper - central,
        "rho_transition_gap": effective_rho,
        "combined_total_bps": central,
    }

