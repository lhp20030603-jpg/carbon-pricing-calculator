"""Tests for the Monte Carlo orchestration layer.

SPEC §4.3:
- beta ~ Normal(beta_hat, se^2) truncated to beta < 0 (sign preservation)
- alpha ~ Uniform(max(0.10, alpha_user - 0.10), min(0.60, alpha_user + 0.10))
- g, e, eta ~ Uniform(point +/- 0.5pp) clipped to slider ranges
- N = 0 disables MC -> deterministic-only (determinism acceptance gate, §9 criterion 2)
- Seed-based reproducibility
"""

from __future__ import annotations

import numpy as np

from app.compute.monte_carlo import ScenarioResult, compute_scenario
from app.schemas import PricePoint, ScenarioInputs

YEARS_FULL = list(range(2020, 2036))


def _build_inputs(mc_n: int = 10_000, seed: int = 42, price: float = 100.0) -> ScenarioInputs:
    return ScenarioInputs(
        price_path=[PricePoint(year=y, price_cny=price) for y in range(2021, 2036)],
        free_allocation_share=0.90,
        coefficient_source="author_did_2026",
        alpha=0.30,
        gdp_growth=0.045,
        energy_intensity_improvement=0.020,
        electrification_rate=0.005,
        mc_n=mc_n,
        mc_seed=seed,
    )


def _run(mc_n: int = 10_000, seed: int = 42, price: float = 100.0) -> ScenarioResult:
    return compute_scenario(
        inputs=_build_inputs(mc_n=mc_n, seed=seed, price=price),
        beta=-0.2273,
        se=0.0793,
    )


class TestDeterminismGate:
    """SPEC §9 criterion 2: mc_n=0 -> identical output across calls to 6dp."""

    def test_mc_n_zero_disables_sampling(self) -> None:
        res = _run(mc_n=0)
        assert res.percentiles_mt is None
        assert res.mc_n_effective == 0

    def test_mc_n_zero_is_reproducible_to_six_decimals(self) -> None:
        a = _run(mc_n=0)
        b = _run(mc_n=0)
        np.testing.assert_array_almost_equal(a.deterministic_mt, b.deterministic_mt, decimal=6)

    def test_mc_n_zero_equals_mc_n_positive_deterministic(self) -> None:
        """The deterministic trajectory does not depend on mc_n — only percentiles do."""
        det_only = _run(mc_n=0)
        with_mc = _run(mc_n=500)
        np.testing.assert_array_almost_equal(
            det_only.deterministic_mt, with_mc.deterministic_mt, decimal=10
        )


class TestSeedReproducibility:
    def test_same_seed_same_percentiles(self) -> None:
        a = _run(mc_n=2_000, seed=123)
        b = _run(mc_n=2_000, seed=123)
        assert a.percentiles_mt is not None and b.percentiles_mt is not None
        np.testing.assert_array_equal(a.percentiles_mt["p50"], b.percentiles_mt["p50"])

    def test_different_seeds_diverge(self) -> None:
        a = _run(mc_n=2_000, seed=1)
        b = _run(mc_n=2_000, seed=2)
        assert a.percentiles_mt is not None and b.percentiles_mt is not None
        # Different seeds should yield different MC samples -> slightly different percentiles
        assert not np.allclose(a.percentiles_mt["p5"], b.percentiles_mt["p5"])


class TestPercentileOrdering:
    def test_bands_are_ordered(self) -> None:
        res = _run(mc_n=5_000, seed=42)
        assert res.percentiles_mt is not None
        p = res.percentiles_mt
        for i in range(len(res.years)):
            assert p["p5"][i] <= p["p25"][i] <= p["p50"][i] <= p["p75"][i] <= p["p95"][i]

    def test_baseline_year_bands_collapse(self) -> None:
        """At baseline year (2020), Delta ln == 0 so all percentiles equal BAU."""
        res = _run(mc_n=2_000, seed=42)
        assert res.percentiles_mt is not None
        p = res.percentiles_mt
        assert p["p5"][0] == p["p95"][0] == res.bau_mt[0]


class TestBandsWiden:
    """SPEC §9 criterion 3: fan band widens as price path moves farther from training range."""

    def test_extreme_price_produces_wider_band(self) -> None:
        low = _run(mc_n=5_000, seed=42, price=60.0)
        high = _run(mc_n=5_000, seed=42, price=400.0)
        assert low.percentiles_mt is not None and high.percentiles_mt is not None
        width_low = low.percentiles_mt["p95"][-1] - low.percentiles_mt["p5"][-1]
        width_high = high.percentiles_mt["p95"][-1] - high.percentiles_mt["p5"][-1]
        assert width_high > width_low


class TestKPIDistribution:
    def test_median_cumulative_reduction_nonzero(self) -> None:
        """Preset `current`-like inputs yield non-zero median reduction (v1.0 bug guard)."""
        res = compute_scenario(
            inputs=ScenarioInputs(
                price_path=[
                    PricePoint(year=y, price_cny=p)
                    for y, p in zip(range(2021, 2036), np.linspace(80.0, 100.0, 15), strict=True)
                ],
                free_allocation_share=0.90,
            ),
            beta=-0.2273,
            se=0.0793,
        )
        assert res.kpis.cumulative_reduction_mt_median > 0.0
        # KPI bands must be ordered (p5 <= median <= p95)
        assert res.kpis.cumulative_reduction_mt_p5 <= res.kpis.cumulative_reduction_mt_median
        assert res.kpis.cumulative_reduction_mt_median <= res.kpis.cumulative_reduction_mt_p95

    def test_peak_year_within_range(self) -> None:
        res = _run(mc_n=2_000, seed=42)
        assert 2021 <= res.kpis.peak_year_median <= 2035
        assert 2021 <= res.kpis.peak_year_p5 <= 2035
        assert 2021 <= res.kpis.peak_year_p95 <= 2035


class TestDistributionShapes:
    def test_sampled_betas_are_negative(self) -> None:
        # Indirect test via result: with beta=-0.01 and se=1.0, lots of raw draws would be > 0,
        # but truncation should still yield negative response (reduction) across the fan.
        res = compute_scenario(
            inputs=_build_inputs(mc_n=5_000, seed=42, price=200.0),
            beta=-0.01,
            se=1.0,
        )
        assert res.percentiles_mt is not None
        # Median reduction should still be non-positive relative to BAU
        assert res.percentiles_mt["p50"][-1] <= res.bau_mt[-1]
