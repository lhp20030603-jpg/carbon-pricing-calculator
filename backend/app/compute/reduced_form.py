"""Deterministic reduced-form emissions response.

SPEC §4.2 Steps 2–4; calibration locks mirrored from CLAUDE.md:

    rho_t     = ln((P_t + EPSILON) / P_REF)               # log-price signal
                clamped to 0 when P_t <= P_REF            # no reverse-ETS artefact
    short_t   = BETA * rho_t * (1 - LAMBDA_FREE * f)      # short-run response
    Delta_t   = alpha * short_t + (1 - alpha) * Delta_{t-1}
                with initial condition Delta_{2020} = 0
    E_t       = BAU_t * exp(Delta_t)

Free allocation is a dampener on response magnitude (behavioural channel), not a
discount on the marginal price faced by the firm. This deliberately deviates
from the incorrect v1.0 formulation `EC = P * (1 - f)`.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from app.schemas import BASELINE_YEAR

# Calibration constants — see SPEC §4.1 / CLAUDE.md
P_REF: float = 45.0
EPSILON: float = 1.0
LAMBDA_FREE: float = 0.30


def _log_price_signal(
    prices_cny: NDArray[np.float64],
    *,
    p_ref: float = P_REF,
    epsilon: float = EPSILON,
) -> NDArray[np.float64]:
    """rho_t with the P_t <= P_ref calibration clamp applied."""
    prices = np.asarray(prices_cny, dtype=np.float64)
    rho = np.log((prices + epsilon) / p_ref)
    rho = np.where(prices > p_ref, rho, 0.0)
    return rho


def compute_deterministic_emissions(
    *,
    bau_mt: NDArray[np.float64],
    years: Sequence[int],
    prices_cny: Sequence[float],
    free_allocation_share: float,
    alpha: float,
    beta: float,
    baseline_year: int = BASELINE_YEAR,
    p_ref: float = P_REF,
    epsilon: float = EPSILON,
    lambda_free: float = LAMBDA_FREE,
) -> NDArray[np.float64]:
    """Compute the deterministic policy-adjusted emissions trajectory.

    Args:
        bau_mt: BAU trajectory including baseline_year (length n).
        years: Full year sequence including baseline_year (length n).
        prices_cny: Carbon price per policy year (length n - 1, aligned to
            years[1:]).
        free_allocation_share: f in [0, 1].
        alpha: Partial-adjustment coefficient (SPEC §4.1).
        beta: Price semi-elasticity of emissions (negative value, e.g. -0.2273).
        baseline_year: Anchor year where Delta ln(E) = 0.
        p_ref: Log reference price, default SPEC-pinned 45 CNY/tCO2.
        epsilon: Numerical-stability offset for ln, default 1.
        lambda_free: Free-allocation dampening factor, default SPEC-pinned 0.30.

    Returns:
        E_t trajectory (Mt CO2), same length as `bau_mt`.
    """
    bau = np.asarray(bau_mt, dtype=np.float64)
    years_arr = np.asarray(years, dtype=np.int64)
    if bau.shape != years_arr.shape:
        raise ValueError("bau_mt and years must be the same length")
    if years_arr[0] != baseline_year:
        raise ValueError(
            f"years must start at baseline_year={baseline_year}; got {int(years_arr[0])}"
        )

    prices = np.asarray(prices_cny, dtype=np.float64)
    expected_price_len = bau.shape[0] - 1
    if prices.shape[0] != expected_price_len:
        raise ValueError(
            f"prices_cny must cover {expected_price_len} policy years; got {prices.shape[0]}"
        )

    rho = _log_price_signal(prices, p_ref=p_ref, epsilon=epsilon)
    dampener = 1.0 - lambda_free * free_allocation_share
    short = beta * rho * dampener

    delta = np.zeros_like(bau)  # delta[0] = 0 -> initial condition for 2020
    for i in range(1, bau.shape[0]):
        delta[i] = alpha * short[i - 1] + (1.0 - alpha) * delta[i - 1]

    return bau * np.exp(delta)


__all__ = [
    "EPSILON",
    "LAMBDA_FREE",
    "P_REF",
    "compute_deterministic_emissions",
]
