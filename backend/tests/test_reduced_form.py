"""Tests for the deterministic reduced-form response.

SPEC §4.2 Steps 2–4 plus calibration locks in CLAUDE.md:

- P_ref = 45, lambda = 0.3, epsilon = 1
- Free allocation acts on response magnitude (1 - lambda * f), NOT as (P * (1 - f))
- Delta ln(E_{2020}) = 0
- If P_t <= P_ref, rho_t clamps to 0 (no reverse-ETS artefact)
- Preset `current` (P 80->100, f=0.90) must produce non-zero median reduction
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.compute.bau import compute_bau_trajectory
from app.compute.reduced_form import (
    P_REF,
    compute_deterministic_emissions,
)

YEARS_FULL = list(range(2020, 2036))


def _bau(e_2020: float = 5_150.0) -> np.ndarray:
    return compute_bau_trajectory(
        e_2020_mt=e_2020,
        g=0.045,
        e=0.020,
        eta=0.005,
        years=YEARS_FULL,
    )


class TestIllustrativeCalibration:
    """SPEC §4.2 sanity-check: P=100 constant, f=0.90, lambda=0.3, alpha=0.3, beta=-0.2273.

    Expected: after partial-adjustment convergence, E_t / BAU_t -> exp(Delta ln_short)
    with Delta ln_short = -0.2273 * ln(101 / 45) * (1 - 0.3 * 0.9) approx -0.134,
    so ~12.5% long-run reduction vs BAU.
    """

    def test_short_run_delta_ln(self) -> None:
        rho = math.log(101.0 / 45.0)
        dampener = 1.0 - 0.3 * 0.9
        expected_delta_ln_short = -0.2273 * rho * dampener
        assert expected_delta_ln_short == pytest.approx(-0.134, abs=5e-4)

    def test_long_run_convergence(self) -> None:
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, 100.0)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.90,
            alpha=0.30,
            beta=-0.2273,
        )
        rho = math.log(101.0 / 45.0)
        dampener = 1.0 - 0.3 * 0.9
        delta_ln_long_target = -0.2273 * rho * dampener
        ratio_2035 = e[-1] / bau[-1]
        assert ratio_2035 == pytest.approx(math.exp(delta_ln_long_target), abs=5e-3)
        assert ratio_2035 < 0.90

    def test_initial_year_matches_bau(self) -> None:
        """Delta ln(E_{2020}) = 0 -> E_{2020} == BAU_{2020}."""
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, 100.0)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.90,
            alpha=0.30,
            beta=-0.2273,
        )
        assert e[0] == pytest.approx(bau[0])


class TestClamping:
    def test_price_at_pref_no_effect(self) -> None:
        """P_t <= P_ref -> rho_t = 0 -> E_t == BAU_t (calibration lock)."""
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, P_REF)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.90,
            alpha=0.30,
            beta=-0.2273,
        )
        assert np.allclose(e, bau)

    def test_zero_price_no_effect(self) -> None:
        bau = _bau()
        prices = np.zeros(len(YEARS_FULL) - 1)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.90,
            alpha=0.30,
            beta=-0.2273,
        )
        assert np.allclose(e, bau)

    def test_price_just_above_pref_produces_effect(self) -> None:
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, P_REF + 5.0)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.90,
            alpha=0.30,
            beta=-0.2273,
        )
        assert e[-1] < bau[-1]


class TestFreeAllocationDampener:
    """(1 - lambda * f) is a dampener on *response magnitude* (not a marginal discount)."""

    def test_f_zero_gives_full_response(self) -> None:
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, 200.0)
        e_full = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.0,
            alpha=0.30,
            beta=-0.2273,
        )
        e_partial = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=1.0,
            alpha=0.30,
            beta=-0.2273,
        )
        # Full auctioning (f=0) should cut emissions more than full free (f=1)
        assert e_full[-1] < e_partial[-1]

    def test_f_one_response_is_70pct_of_f_zero(self) -> None:
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, 200.0)
        e_f0 = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.0,
            alpha=0.30,
            beta=-0.2273,
        )
        e_f1 = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=1.0,
            alpha=0.30,
            beta=-0.2273,
        )
        delta_ln_f0 = math.log(e_f0[-1] / bau[-1])
        delta_ln_f1 = math.log(e_f1[-1] / bau[-1])
        # lambda=0.3: f=1 response is (1 - 0.3) = 0.7 of f=0 response
        assert delta_ln_f1 / delta_ln_f0 == pytest.approx(0.70, abs=1e-6)


class TestPresetCurrentRegression:
    """Regression test for the v1.0 zero-reduction bug.

    SPEC §9 criterion 9 / CLAUDE.md calibration lock:
    preset `current` (P 80->100, f=0.90) must produce non-zero median reduction.
    """

    def test_current_preset_produces_nonzero_reduction(self) -> None:
        bau = _bau()
        prices = np.linspace(80.0, 100.0, len(YEARS_FULL) - 1)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.90,
            alpha=0.30,
            beta=-0.2273,
        )
        total_bau = float(bau[1:].sum())
        total_e = float(e[1:].sum())
        reduction_mt = total_bau - total_e
        assert reduction_mt > 100.0, f"expected meaningful reduction, got {reduction_mt:.2f} Mt"
        # Sanity: should not exceed BAU (no reverse effect)
        assert (e[1:] <= bau[1:]).all()


class TestSanity:
    def test_extreme_price_keeps_emissions_positive(self) -> None:
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, 1_500.0)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.50,
            alpha=0.30,
            beta=-0.2273,
        )
        assert np.all(e > 0)
        # E[0] == BAU[0] by initial condition; policy effect applies from year 2021 onward
        assert np.all(e[1:] < bau[1:])

    def test_length_matches_bau(self) -> None:
        bau = _bau()
        prices = np.full(len(YEARS_FULL) - 1, 80.0)
        e = compute_deterministic_emissions(
            bau_mt=bau,
            years=YEARS_FULL,
            prices_cny=prices,
            free_allocation_share=0.90,
            alpha=0.30,
            beta=-0.2273,
        )
        assert e.shape == bau.shape
