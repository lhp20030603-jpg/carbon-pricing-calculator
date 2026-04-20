"""External validity caveats surfaced alongside the compute response.

SPEC §4.4 is the source of truth. The price-above-training-range threshold is
pinned at 100 CNY/tCO2 (§9 criterion 3) and must not drift.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

import numpy as np
from numpy.typing import ArrayLike

from app.schemas import Caveat

# Caveat IDs — stable, machine-readable, safe to reference from the frontend.
CAVEAT_PRICE_ABOVE_TRAINING: Final[str] = "price_above_training_range"
CAVEAT_EXTREME_PRICE: Final[str] = "price_extreme_extrapolation"
CAVEAT_POST_2030: Final[str] = "projection_past_2030"
CAVEAT_SCOPE_REGION_MISMATCH: Final[str] = "scope_region_mismatch"

# Pinned thresholds — changes here require a SPEC revision + regression test update.
TRAINING_RANGE_UPPER_CNY: Final[float] = 100.0
EXTREME_PRICE_UPPER_CNY: Final[float] = 500.0
STRUCTURAL_CHANGE_YEAR: Final[int] = 2030


def detect_caveats(
    *,
    prices_cny: ArrayLike,
    years: Sequence[int],
    coefficient_region: str,
    coefficient_sector: str,
) -> list[Caveat]:
    """Return the list of caveats applicable to this compute run.

    Args:
        prices_cny: Carbon price trajectory (any length).
        years: Year labels corresponding to the trajectory.
        coefficient_region: Region context of the selected coefficient
            (e.g. "China", "OECD average"). Drives scope_region_mismatch.
        coefficient_sector: Sector context of the selected coefficient
            (currently informational; V1 only surfaces the region mismatch).

    Returns:
        List of Caveat objects, potentially empty.
    """
    prices = np.asarray(prices_cny, dtype=np.float64)
    caveats: list[Caveat] = []

    max_price = float(prices.max()) if prices.size else 0.0
    if max_price > TRAINING_RANGE_UPPER_CNY:
        caveats.append(
            Caveat(
                id=CAVEAT_PRICE_ABOVE_TRAINING,
                severity="warning",
                message=(
                    "Carbon price exceeds the 100 CNY/tCO2 boundary of the DID "
                    "training sample. Response should be read as stylised "
                    "sensitivity rather than a validated elasticity."
                ),
            )
        )
    if max_price > EXTREME_PRICE_UPPER_CNY:
        caveats.append(
            Caveat(
                id=CAVEAT_EXTREME_PRICE,
                severity="critical",
                message=(
                    "Carbon price exceeds 500 CNY/tCO2 (upper edge of IEA "
                    "NZE-China scenarios). Treat the result as exploratory, "
                    "not a forecast."
                ),
            )
        )

    if any(y > STRUCTURAL_CHANGE_YEAR for y in years):
        caveats.append(
            Caveat(
                id=CAVEAT_POST_2030,
                severity="info",
                message=(
                    "Projections past 2030 assume an approximately stationary "
                    "fuel mix. China's power-sector transition (renewables ramp, "
                    "coal phase-down) may alter the price response."
                ),
            )
        )

    if coefficient_region.lower() != "china":
        caveats.append(
            Caveat(
                id=CAVEAT_SCOPE_REGION_MISMATCH,
                severity="warning",
                message=(
                    f"Selected coefficient was estimated on '{coefficient_region}' "
                    "data; applying it to China's national ETS involves regime "
                    "transfer risk beyond the V1 model's design."
                ),
            )
        )

    return caveats


__all__ = [
    "CAVEAT_EXTREME_PRICE",
    "CAVEAT_POST_2030",
    "CAVEAT_PRICE_ABOVE_TRAINING",
    "CAVEAT_SCOPE_REGION_MISMATCH",
    "EXTREME_PRICE_UPPER_CNY",
    "STRUCTURAL_CHANGE_YEAR",
    "TRAINING_RANGE_UPPER_CNY",
    "detect_caveats",
]
