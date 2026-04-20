"""Tests for BAU trajectory module.

SPEC §4.2 Step 1: BAU_t = E_2020 * (1 + g - e - eta)^(t - 2020)
"""

from __future__ import annotations

import numpy as np
import pytest

from app.compute.bau import compute_bau_trajectory


class TestBAUBasicBehavior:
    def test_baseline_year_returns_e_2020(self) -> None:
        years = [2020, 2021, 2022]
        bau = compute_bau_trajectory(e_2020_mt=5_150.0, g=0.045, e=0.020, eta=0.005, years=years)
        assert bau[0] == pytest.approx(5_150.0)

    def test_all_zero_rates_returns_flat(self) -> None:
        years = list(range(2020, 2036))
        bau = compute_bau_trajectory(e_2020_mt=5_000.0, g=0.0, e=0.0, eta=0.0, years=years)
        assert np.allclose(bau, 5_000.0)

    def test_default_params_monotone_growing(self) -> None:
        # g=0.045, e=0.020, eta=0.005 -> net 0.020 > 0 -> growing
        years = list(range(2020, 2036))
        bau = compute_bau_trajectory(e_2020_mt=5_150.0, g=0.045, e=0.020, eta=0.005, years=years)
        diffs = np.diff(bau)
        assert np.all(diffs > 0)

    def test_net_negative_rate_monotone_declining(self) -> None:
        # e+eta > g -> declining
        years = list(range(2020, 2036))
        bau = compute_bau_trajectory(e_2020_mt=5_150.0, g=0.02, e=0.03, eta=0.01, years=years)
        diffs = np.diff(bau)
        assert np.all(diffs < 0)

    def test_output_length_matches_years(self) -> None:
        years = list(range(2020, 2036))
        bau = compute_bau_trajectory(e_2020_mt=5_150.0, g=0.045, e=0.02, eta=0.005, years=years)
        assert len(bau) == len(years)

    def test_known_value_at_t_plus_1(self) -> None:
        # BAU_{2021} = E_2020 * (1 + 0.02) = 5150 * 1.02 = 5253.0
        years = [2020, 2021]
        bau = compute_bau_trajectory(e_2020_mt=5_150.0, g=0.045, e=0.020, eta=0.005, years=years)
        assert bau[1] == pytest.approx(5_150.0 * 1.02)


class TestBAUEdgeCases:
    def test_years_without_baseline_start(self) -> None:
        # If years start from 2021, BAU_{2021} = E_2020 * (1 + net)
        years = [2021, 2022, 2023]
        bau = compute_bau_trajectory(
            e_2020_mt=5_150.0, g=0.045, e=0.020, eta=0.005, years=years, baseline_year=2020
        )
        assert bau[0] == pytest.approx(5_150.0 * 1.02)
        assert bau[1] == pytest.approx(5_150.0 * 1.02**2)

    def test_single_year_baseline(self) -> None:
        bau = compute_bau_trajectory(e_2020_mt=5_150.0, g=0.045, e=0.020, eta=0.005, years=[2020])
        assert len(bau) == 1
        assert bau[0] == pytest.approx(5_150.0)

    def test_returns_numpy_array(self) -> None:
        bau = compute_bau_trajectory(e_2020_mt=5_150.0, g=0.045, e=0.02, eta=0.005, years=[2020])
        assert isinstance(bau, np.ndarray)
