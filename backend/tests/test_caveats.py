"""Tests for external validity / sanity caveats.

SPEC §4.4 and §9 criterion 3: `price_above_training_range` pinned at 100 CNY/tCO2.
"""

from __future__ import annotations

import numpy as np

from app.compute.caveats import (
    CAVEAT_EXTREME_PRICE,
    CAVEAT_POST_2030,
    CAVEAT_PRICE_ABOVE_TRAINING,
    CAVEAT_SCOPE_REGION_MISMATCH,
    detect_caveats,
)


def _ids(caveats) -> set[str]:
    return {c.id for c in caveats}


class TestTrainingRangeThreshold:
    """SPEC §9 criterion 3: trigger iff max(P_t) > 100 CNY/tCO2. Pinned threshold."""

    def test_not_triggered_at_exactly_100(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([80.0, 90.0, 100.0]),
            years=[2021, 2022, 2023],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_PRICE_ABOVE_TRAINING not in _ids(caveats)

    def test_triggered_just_above_100(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([80.0, 100.01, 90.0]),
            years=[2021, 2022, 2023],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_PRICE_ABOVE_TRAINING in _ids(caveats)

    def test_not_triggered_when_all_below(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([40.0, 50.0, 80.0]),
            years=[2021, 2022, 2023],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_PRICE_ABOVE_TRAINING not in _ids(caveats)


class TestExtremePrice:
    def test_triggered_above_500(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([80.0, 600.0]),
            years=[2021, 2022],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_EXTREME_PRICE in _ids(caveats)

    def test_not_triggered_at_500(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([500.0, 450.0]),
            years=[2021, 2022],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_EXTREME_PRICE not in _ids(caveats)


class TestPost2030:
    def test_triggered_when_year_above_2030(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([80.0, 90.0]),
            years=[2021, 2032],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_POST_2030 in _ids(caveats)

    def test_not_triggered_when_range_ends_2030(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([80.0, 90.0]),
            years=[2021, 2030],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_POST_2030 not in _ids(caveats)


class TestScopeMismatch:
    def test_non_china_region_triggers_warning(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([80.0]),
            years=[2021],
            coefficient_region="OECD average",
            coefficient_sector="Power",
        )
        assert CAVEAT_SCOPE_REGION_MISMATCH in _ids(caveats)

    def test_china_region_clean(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([80.0]),
            years=[2021],
            coefficient_region="China",
            coefficient_sector="Power",
        )
        assert CAVEAT_SCOPE_REGION_MISMATCH not in _ids(caveats)


class TestSeverity:
    def test_severities_are_valid(self) -> None:
        caveats = detect_caveats(
            prices_cny=np.array([600.0]),
            years=[2021, 2035],
            coefficient_region="OECD average",
            coefficient_sector="Power",
        )
        for c in caveats:
            assert c.severity in {"info", "warning", "critical"}
            assert c.id
            assert c.message
