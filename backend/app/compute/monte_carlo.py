"""Monte Carlo orchestration for the deterministic reduced-form model.

SPEC §4.3:
- beta ~ Normal(beta_hat, se^2) truncated to beta < 0 (sign preservation)
- alpha ~ Uniform(max(0.10, alpha_user - 0.10), min(0.60, alpha_user + 0.10))
- g, e, eta ~ Uniform(point +/- 0.5pp) clipped to their slider ranges
- Parameters treated as independent (methodology.pdf Limitations)
- N = 0 disables MC and returns a deterministic-only result (§9 criterion 2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray

from app.compute.bau import compute_bau_trajectory
from app.compute.reduced_form import (
    EPSILON,
    LAMBDA_FREE,
    P_REF,
)
from app.schemas import (
    BASELINE_YEAR,
    FIRST_POLICY_YEAR,
    LAST_POLICY_YEAR,
    KPIBundle,
    PercentileBands,
    ScenarioInputs,
)

# Slider bounds for MC clipping (SPEC §4.1)
ALPHA_LOW: Final[float] = 0.10
ALPHA_HIGH: Final[float] = 0.60
GROWTH_LOW: Final[float] = 0.02
GROWTH_HIGH: Final[float] = 0.06
ENERGY_IMPROVE_LOW: Final[float] = 0.0
ENERGY_IMPROVE_HIGH: Final[float] = 0.03
ELECTRIFY_LOW: Final[float] = 0.0
ELECTRIFY_HIGH: Final[float] = 0.02

# Half-width of the local uniform around point estimates (SPEC §4.3: "+/- 0.5pp")
HALF_WIDTH_PP: Final[float] = 0.005
# Local +/- 0.10 window on alpha (SPEC §4.3)
ALPHA_HALF_WIDTH: Final[float] = 0.10
# Truncated-normal safety cap: reject draws above this many standard deviations.
# Purely a numerical guard; the operational truncation is beta < 0.
MAX_BETA_DRAW_TRIES: Final[int] = 32


@dataclass(frozen=True)
class ScenarioResult:
    """Bundle returned by `compute_scenario`, consumed by the API layer."""

    years: list[int]
    bau_mt: NDArray[np.float64]
    deterministic_mt: NDArray[np.float64]
    percentiles_mt: dict[str, NDArray[np.float64]] | None
    kpis: KPIBundle
    mc_n_effective: int
    mc_seed: int

    def as_bands(self) -> PercentileBands | None:
        if self.percentiles_mt is None:
            return None
        return PercentileBands(
            p5=self.percentiles_mt["p5"].tolist(),
            p25=self.percentiles_mt["p25"].tolist(),
            p50=self.percentiles_mt["p50"].tolist(),
            p75=self.percentiles_mt["p75"].tolist(),
            p95=self.percentiles_mt["p95"].tolist(),
        )


def _build_price_array(inputs: ScenarioInputs) -> NDArray[np.float64]:
    """Turn the sparse PricePoint list into a dense array aligned to policy years.

    Linearly interpolates between supplied points and extends endpoints flat.
    """
    years = np.arange(FIRST_POLICY_YEAR, LAST_POLICY_YEAR + 1, dtype=np.float64)
    supplied_years = np.asarray([p.year for p in inputs.price_path], dtype=np.float64)
    supplied_prices = np.asarray([p.price_cny for p in inputs.price_path], dtype=np.float64)
    return np.interp(years, supplied_years, supplied_prices)


def _simulate_trajectory(
    *,
    bau: NDArray[np.float64],
    prices: NDArray[np.float64],
    beta: float,
    alpha: float,
    f: float,
    p_ref: float,
    epsilon: float,
    lambda_free: float,
) -> NDArray[np.float64]:
    """Fast path that mirrors compute_deterministic_emissions, skipping input checks."""
    rho = np.log((prices + epsilon) / p_ref)
    rho = np.where(prices > p_ref, rho, 0.0)
    short = beta * rho * (1.0 - lambda_free * f)

    delta = np.zeros_like(bau)
    for i in range(1, bau.shape[0]):
        delta[i] = alpha * short[i - 1] + (1.0 - alpha) * delta[i - 1]
    return bau * np.exp(delta)


def _sample_beta(
    rng: np.random.Generator, beta_hat: float, se: float, n: int
) -> NDArray[np.float64]:
    """Normal(beta_hat, se) truncated to beta < 0.

    Rejection sampling with a bounded number of retries; any residual positives
    are reflected to stay strictly negative (belt-and-braces).
    """
    draws = rng.normal(loc=beta_hat, scale=se, size=n)
    tries = 0
    while True:
        mask = draws >= 0.0
        count = int(mask.sum())
        if count == 0 or tries >= MAX_BETA_DRAW_TRIES:
            break
        draws[mask] = rng.normal(loc=beta_hat, scale=se, size=count)
        tries += 1
    # Any residual positives -> reflect to negative (preserve magnitude)
    positive_residual = draws >= 0.0
    if positive_residual.any():
        draws[positive_residual] = -np.abs(draws[positive_residual]) - 1e-9
    return draws


def _sample_uniform_window(
    rng: np.random.Generator,
    point: float,
    half_width: float,
    low: float,
    high: float,
    n: int,
) -> NDArray[np.float64]:
    """Uniform(point +/- half_width) then clipped to [low, high]."""
    lo = max(low, point - half_width)
    hi = min(high, point + half_width)
    if hi <= lo:
        return np.full(n, lo)
    return rng.uniform(lo, hi, size=n)


def _kpis_from_samples(
    *,
    years: list[int],
    bau: NDArray[np.float64],
    deterministic: NDArray[np.float64],
    mc_samples: NDArray[np.float64] | None,
) -> KPIBundle:
    """Compute median + 5/95 KPIs.

    Falls back to deterministic values when no MC samples are available.
    Cumulative reduction excludes the baseline year.
    """
    idx_2035 = years.index(LAST_POLICY_YEAR)
    bau_policy = bau[1:]
    det_policy = deterministic[1:]

    det_cumulative_reduction = float((bau_policy - det_policy).sum())
    det_peak_year = int(years[int(np.argmax(deterministic))])

    if mc_samples is None or mc_samples.size == 0:
        return KPIBundle(
            cumulative_reduction_mt_median=det_cumulative_reduction,
            cumulative_reduction_mt_p5=det_cumulative_reduction,
            cumulative_reduction_mt_p95=det_cumulative_reduction,
            peak_year_median=det_peak_year,
            peak_year_p5=det_peak_year,
            peak_year_p95=det_peak_year,
            emissions_2035_mt_median=float(deterministic[idx_2035]),
            relative_reduction_2035_median=float(
                (deterministic[idx_2035] - bau[idx_2035]) / bau[idx_2035]
            ),
        )

    cumulative_samples = (bau_policy - mc_samples[:, 1:]).sum(axis=1)
    peak_idx_samples = mc_samples.argmax(axis=1)
    peak_year_samples = np.asarray(years)[peak_idx_samples]
    e_2035_samples = mc_samples[:, idx_2035]

    return KPIBundle(
        cumulative_reduction_mt_median=float(np.percentile(cumulative_samples, 50)),
        cumulative_reduction_mt_p5=float(np.percentile(cumulative_samples, 5)),
        cumulative_reduction_mt_p95=float(np.percentile(cumulative_samples, 95)),
        peak_year_median=int(np.percentile(peak_year_samples, 50, method="nearest")),
        peak_year_p5=int(np.percentile(peak_year_samples, 5, method="nearest")),
        peak_year_p95=int(np.percentile(peak_year_samples, 95, method="nearest")),
        emissions_2035_mt_median=float(np.percentile(e_2035_samples, 50)),
        relative_reduction_2035_median=float(
            (np.percentile(e_2035_samples, 50) - bau[idx_2035]) / bau[idx_2035]
        ),
    )


def compute_scenario(
    *,
    inputs: ScenarioInputs,
    beta: float,
    se: float,
    p_ref: float = P_REF,
    epsilon: float = EPSILON,
    lambda_free: float = LAMBDA_FREE,
) -> ScenarioResult:
    """Full scenario run: BAU + deterministic + (optional) MC fan + KPIs.

    Args:
        inputs: Validated user inputs.
        beta: Point estimate of the price semi-elasticity.
        se: Standard error of `beta`.
        p_ref, epsilon, lambda_free: Calibration constants.

    Returns:
        ScenarioResult with the full trajectory, percentile bands (if MC run),
        and headline KPIs.
    """
    years = list(range(BASELINE_YEAR, LAST_POLICY_YEAR + 1))

    bau = compute_bau_trajectory(
        e_2020_mt=inputs.e_2020_mt,
        g=inputs.gdp_growth,
        e=inputs.energy_intensity_improvement,
        eta=inputs.electrification_rate,
        years=years,
    )
    prices = _build_price_array(inputs)

    deterministic = _simulate_trajectory(
        bau=bau,
        prices=prices,
        beta=beta,
        alpha=inputs.alpha,
        f=inputs.free_allocation_share,
        p_ref=p_ref,
        epsilon=epsilon,
        lambda_free=lambda_free,
    )

    mc_samples: NDArray[np.float64] | None = None
    percentiles: dict[str, NDArray[np.float64]] | None = None

    if inputs.mc_n > 0:
        rng = np.random.default_rng(inputs.mc_seed)
        n = inputs.mc_n

        beta_draws = _sample_beta(rng, beta, se, n)
        alpha_draws = _sample_uniform_window(
            rng, inputs.alpha, ALPHA_HALF_WIDTH, ALPHA_LOW, ALPHA_HIGH, n
        )
        g_draws = _sample_uniform_window(
            rng, inputs.gdp_growth, HALF_WIDTH_PP, GROWTH_LOW, GROWTH_HIGH, n
        )
        e_draws = _sample_uniform_window(
            rng,
            inputs.energy_intensity_improvement,
            HALF_WIDTH_PP,
            ENERGY_IMPROVE_LOW,
            ENERGY_IMPROVE_HIGH,
            n,
        )
        eta_draws = _sample_uniform_window(
            rng, inputs.electrification_rate, HALF_WIDTH_PP, ELECTRIFY_LOW, ELECTRIFY_HIGH, n
        )

        mc_samples = np.empty((n, bau.shape[0]), dtype=np.float64)
        for i in range(n):
            sample_bau = compute_bau_trajectory(
                e_2020_mt=inputs.e_2020_mt,
                g=float(g_draws[i]),
                e=float(e_draws[i]),
                eta=float(eta_draws[i]),
                years=years,
            )
            mc_samples[i] = _simulate_trajectory(
                bau=sample_bau,
                prices=prices,
                beta=float(beta_draws[i]),
                alpha=float(alpha_draws[i]),
                f=inputs.free_allocation_share,
                p_ref=p_ref,
                epsilon=epsilon,
                lambda_free=lambda_free,
            )

        percentiles = {
            "p5": np.percentile(mc_samples, 5, axis=0),
            "p25": np.percentile(mc_samples, 25, axis=0),
            "p50": np.percentile(mc_samples, 50, axis=0),
            "p75": np.percentile(mc_samples, 75, axis=0),
            "p95": np.percentile(mc_samples, 95, axis=0),
        }

    kpis = _kpis_from_samples(
        years=years, bau=bau, deterministic=deterministic, mc_samples=mc_samples
    )

    return ScenarioResult(
        years=years,
        bau_mt=bau,
        deterministic_mt=deterministic,
        percentiles_mt=percentiles,
        kpis=kpis,
        mc_n_effective=inputs.mc_n,
        mc_seed=inputs.mc_seed,
    )


__all__ = ["ScenarioResult", "compute_scenario"]
