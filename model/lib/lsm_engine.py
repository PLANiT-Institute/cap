"""교환옵션 LSM (§01 #claim-wedge-conjunction).

BF 계속 vs route 전환의 American exchange option. 상태 = 4 상관 GBM 드라이버
(carbon, h2, elec, capex). 예산 없는 measure에서 푼다 — p_bind는 밖에서 곱한다 (A2).
p_bind_in_exercise 실험 플래그(R5)는 행사 문턱을 p_bind로 완화하는 변형.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .finance import annuity


@dataclass
class LsmSpec:
    """자산 하나의 LSM 입력. 전 필드 config 유래 — 리터럴 없음."""
    x0: np.ndarray          # [p_C, p_H2, p_elec, K] 초기 수준
    sigma: np.ndarray       # 드라이버 연변동성
    mu: np.ndarray          # 드라이버 drift (config sigmas.mu)
    rho: np.ndarray         # 4×4 상관
    delta_intensity: float  # 회피 배출강도 (현재 − 잔여) tCO2/t
    q_h2: float             # kg/t
    q_elec: float           # MWh/t
    avoided_opex: float     # USD/t (BF 회피 opex: 석탄+광석+고정비)
    route_opex_other: float # USD/t (신 route 비드라이버 opex: 고철/펠릿/고정비)
    k_reline_mult: float    # reline 시점 K 배수 (K11/K)
    k_offcycle_mult: float  # off-cycle K 배수 (K12/K)
    reline_t: int           # base_year 기준 reline까지 연수
    rate: float             # 할인율
    horizon: int
    n_paths: int
    basis_degree: int
    seed: int


def simulate_paths(spec: LsmSpec, sigma_scale: float = 1.0) -> np.ndarray:
    """(n_paths, horizon+1, 4) GBM 경로. drift = config sigmas.mu."""
    rng = np.random.default_rng(spec.seed)
    n_d = len(spec.x0)
    chol = np.linalg.cholesky(spec.rho + np.eye(n_d) * np.finfo(float).eps)
    sig = spec.sigma * sigma_scale
    z = rng.standard_normal((spec.n_paths, spec.horizon, n_d))
    dw = z @ chol.T
    log_inc = spec.mu - sig**2 / 2.0 + sig * dw
    log_paths = np.concatenate(
        [np.zeros((spec.n_paths, 1, n_d)), np.cumsum(log_inc, axis=1)], axis=1
    )
    return spec.x0 * np.exp(log_paths)


def exercise_value(spec: LsmSpec, x: np.ndarray, t: int) -> np.ndarray:
    """t에 전환 시 즉시가치 (USD/t steel). x: (n_paths, 4)."""
    p_c, p_h2, p_elec, k = x[:, 0], x[:, 1], x[:, 2], x[:, 3]
    remaining = annuity(spec.rate, spec.horizon - t)
    annual = (
        spec.delta_intensity * p_c
        + spec.avoided_opex
        - spec.route_opex_other
        - spec.q_h2 * p_h2      # kg/t × USD/kg = USD/t
        - spec.q_elec * p_elec  # MWh/t × USD/MWh = USD/t
    )
    k_mult = spec.k_reline_mult if t >= spec.reline_t else spec.k_offcycle_mult
    return annual * remaining - k * k_mult


def lsm_tau_star(
    spec: LsmSpec, sigma_scale: float = 1.0, exercise_relax: float = 1.0
) -> dict:
    """LSM 후진귀납 → 경로별 τ*, 옵션가치.

    exercise_relax < 1이면 계속가치를 그만큼 할인해 조기 행사 유도
    (p_bind_in_exercise 실험 변형, R5).
    """
    paths = simulate_paths(spec, sigma_scale)
    n, t_max = spec.n_paths, spec.horizon
    disc = 1.0 / (1.0 + spec.rate)

    cashflow = np.maximum(exercise_value(spec, paths[:, t_max, :], t_max), 0.0)
    tau = np.full(n, t_max + 1, dtype=float)  # t_max+1 = 미행사
    tau[cashflow > 0] = t_max

    for t in range(t_max - 1, 0, -1):
        ev = exercise_value(spec, paths[:, t, :], t)
        itm = ev > 0
        cashflow *= disc
        if itm.sum() > spec.basis_degree + 1:
            x_reg = np.log(paths[itm, t, :])
            basis = np.column_stack(
                [np.ones(itm.sum())]
                + [x_reg**d for d in range(1, spec.basis_degree + 1)]
            )
            coef, *_ = np.linalg.lstsq(basis, cashflow[itm], rcond=None)
            cont = basis @ coef
            exercise_now = ev[itm] > cont * exercise_relax
            idx = np.where(itm)[0][exercise_now]
            cashflow[idx] = ev[itm][exercise_now]
            tau[idx] = t
    value = float(np.mean(cashflow * disc))
    exercised = tau <= t_max
    return {
        "option_value": value,
        "tau_mean": float(np.mean(tau[exercised])) if exercised.any() else None,
        "tau_median": float(np.median(tau[exercised])) if exercised.any() else None,
        "p_exercised": float(exercised.mean()),
    }
