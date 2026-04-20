"""Business-as-usual emissions trajectory.

SPEC §4.2 Step 1:

    BAU_t = E_2020 * (1 + g - e - eta)^(t - 2020)

where g is real GDP growth, e is energy-intensity improvement, eta is
power-sector decarbonisation. All three are annual rates expressed as
fractions (e.g. 0.045 = 4.5 %/yr).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from app.schemas import BASELINE_YEAR


def compute_bau_trajectory(
    *,
    e_2020_mt: float,
    g: float,
    e: float,
    eta: float,
    years: Sequence[int],
    baseline_year: int = BASELINE_YEAR,
) -> NDArray[np.float64]:
    """Compute the counterfactual (no-ETS) CO2 trajectory.

    Args:
        e_2020_mt: Baseline 2020 emissions (Mt CO2).
        g: Real GDP growth rate.
        e: Energy-intensity improvement rate.
        eta: Power-sector decarbonisation rate.
        years: Years to produce output for (must include or follow baseline_year).
        baseline_year: Reference year where trajectory equals e_2020_mt.

    Returns:
        BAU emissions (Mt CO2) per requested year, same order.
    """
    offsets = np.asarray([y - baseline_year for y in years], dtype=np.float64)
    growth_factor = 1.0 + g - e - eta
    return e_2020_mt * np.power(growth_factor, offsets)


__all__ = ["compute_bau_trajectory"]
