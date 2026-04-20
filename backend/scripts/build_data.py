"""Build the three SQLite DBs shipped with the backend.

Usage:
    uv run python -m scripts.build_data

Produces (overwriting) under ``app/data/``:
  - coefficients.db  — versioned numeric constants (E_2020, default coefficient id)
  - references.db    — literature coefficient library (author's DID + alternates)
  - scenarios.db     — curated preset scenarios (SPEC §8.1)

SPEC §5 is source of truth for schemas; the literature alternates are stylised
summary values pending a full review and are clearly labelled as such via the
`notes` field.
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# --- coefficients.db ----------------------------------------------------------


def _build_coefficients_db() -> None:
    path = DATA_DIR / "coefficients.db"
    path.unlink(missing_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE constants (
                name TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                kind TEXT NOT NULL,
                source TEXT NOT NULL
            );
            """
        )
        conn.executemany(
            "INSERT INTO constants(name, value, kind, source) VALUES (?, ?, ?, ?)",
            [
                (
                    "e_2020_mt",
                    "5150.0",
                    "float",
                    "CEADs provincial inventory, Thermal Power & Heat Supply, 2020",
                ),
                (
                    "default_coefficient_id",
                    "author_did_2026",
                    "str",
                    "Liu 2026 dissertation DID estimate",
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


# --- references.db ------------------------------------------------------------


_REFERENCES: list[dict[str, Any]] = [
    {
        "id": "author_did_2026",
        "citation": (
            "Liu, H. (2026). The Impacts of Carbon Emissions Trading on "
            "Decoupling in China's Provincial Power Sector. BSc dissertation, "
            "University of Glasgow."
        ),
        "region": "China",
        "sector": "Thermal Power",
        "coefficient": -0.2273,
        "std_err": 0.0793,
        "method": "Matched DID, 6 treated provinces, 2013–2020",
        "notes": "Default coefficient. Pilot ETS period; see §4.4 caveats.",
        "url": None,
    },
    {
        "id": "green_2021_review",
        "citation": (
            "Green, J. F. (2021). Does carbon pricing reduce emissions? A review "
            "of ex-post analyses. Environmental Research Letters, 16(4), 043004."
        ),
        "region": "OECD average",
        "sector": "Cross-sector",
        "coefficient": -0.05,
        "std_err": 0.03,
        "method": "Systematic review (stylised mid-range)",
        "notes": (
            "Illustrative mid-range summary of reviewed effect sizes. Scope "
            "mismatch warning will fire when applied to China."
        ),
        "url": "https://doi.org/10.1088/1748-9326/abdae9",
    },
    {
        "id": "best_2020_cross_country",
        "citation": (
            "Best, R., Burke, P. J., & Jotzo, F. (2020). Carbon pricing efficacy: "
            "Cross-country evidence. Environmental and Resource Economics, 77(1), 69–94."
        ),
        "region": "Cross-country panel",
        "sector": "Cross-sector",
        "coefficient": -0.08,
        "std_err": 0.025,
        "method": "Panel fixed-effects, 1997–2017",
        "notes": (
            "Stylised translation of the headline price-on-emissions effect to a "
            "log-log semi-elasticity; see notes in methodology.pdf."
        ),
        "url": "https://doi.org/10.1007/s10640-020-00436-x",
    },
]


def _build_references_db() -> None:
    path = DATA_DIR / "references.db"
    path.unlink(missing_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE "references" (
                id TEXT PRIMARY KEY,
                citation TEXT NOT NULL,
                region TEXT NOT NULL,
                sector TEXT NOT NULL,
                coefficient REAL NOT NULL,
                std_err REAL NOT NULL,
                method TEXT NOT NULL,
                notes TEXT,
                url TEXT
            );
            """
        )
        for ref in _REFERENCES:
            conn.execute(
                'INSERT INTO "references"(id, citation, region, sector, coefficient, '
                "std_err, method, notes, url) VALUES "
                "(:id, :citation, :region, :sector, :coefficient, :std_err, :method, :notes, :url)",
                ref,
            )
        conn.commit()
    finally:
        conn.close()


# --- scenarios.db -------------------------------------------------------------


def _linear(start: float, end: float, n: int) -> list[float]:
    if n == 1:
        return [end]
    step = (end - start) / (n - 1)
    return [start + step * i for i in range(n)]


def _convex_exp(start: float, end: float, n: int) -> list[float]:
    """Exponential ramp: P_i = start * (end/start)^(i/(n-1))."""
    if start <= 0:
        raise ValueError("convex_exp requires positive start")
    if n == 1:
        return [end]
    ratio = end / start
    return [start * math.pow(ratio, i / (n - 1)) for i in range(n)]


def _peak_ramp(start: float, peak: float, tail: float, peak_year_index: int, n: int) -> list[float]:
    """Two-phase: linear ramp from start -> peak over [0, peak_year_index],
    then linear drift from peak -> tail over (peak_year_index, n-1]."""
    out = _linear(start, peak, peak_year_index + 1)
    if peak_year_index + 1 < n:
        tail_segment = _linear(peak, tail, n - peak_year_index)
        out.extend(tail_segment[1:])  # skip repeated peak point
    return out


def _policy_years() -> list[int]:
    return list(range(2021, 2036))


def _build_preset_inputs(prices: list[float], free_alloc: float) -> dict[str, Any]:
    years = _policy_years()
    assert len(prices) == len(years), f"expected {len(years)} prices, got {len(prices)}"
    return {
        "price_path": [
            {"year": y, "price_cny": round(p, 3)} for y, p in zip(years, prices, strict=True)
        ],
        "free_allocation_share": free_alloc,
        "coefficient_source": "author_did_2026",
        "alpha": 0.30,
        "gdp_growth": 0.045,
        "energy_intensity_improvement": 0.020,
        "electrification_rate": 0.005,
        "mc_n": 10_000,
        "mc_seed": 42,
        "e_2020_mt": 5150.0,
    }


_PRESETS: list[dict[str, Any]] = [
    {
        "id": "current",
        "name": "Current policy (2024)",
        "description": (
            "Baseline reality: ETS price around 80 CNY/tCO2 today, drifting to "
            "100 by 2035 with 90% free allocation. Expect modest reductions."
        ),
        "inputs": _build_preset_inputs(prices=_linear(80.0, 100.0, 15), free_alloc=0.90),
    },
    {
        "id": "ndc",
        "name": "NDC-aligned",
        "description": (
            "Plausible policy tightening consistent with China's Nationally "
            "Determined Contribution: price climbs from 90 to 200 CNY/tCO2 and "
            "free allocation relaxes to 80%."
        ),
        "inputs": _build_preset_inputs(prices=_linear(90.0, 200.0, 15), free_alloc=0.80),
    },
    {
        "id": "nze_china",
        "name": "IEA NZE-China",
        "description": (
            "1.5°C-consistent aggressive path: exponential ramp from 100 to 500 "
            "CNY/tCO2 by 2035 with 50% free allocation. Results are exploratory "
            "— well outside the training range."
        ),
        "inputs": _build_preset_inputs(prices=_convex_exp(100.0, 500.0, 15), free_alloc=0.50),
    },
    {
        "id": "bau",
        "name": "BAU (no ETS)",
        "description": (
            "Counterfactual reference: no carbon price, full free allocation. "
            "Used to visualise the emissions trajectory absent any ETS signal."
        ),
        "inputs": _build_preset_inputs(prices=[0.0] * 15, free_alloc=1.00),
    },
    {
        "id": "peak",
        "name": "Ambitious peak-2028",
        "description": (
            "Story-driven 'what if': rapid ramp from 120 to 300 CNY/tCO2 by "
            "2028, then gentle drift to 320 by 2035. 70% free allocation."
        ),
        "inputs": _build_preset_inputs(
            prices=_peak_ramp(120.0, 300.0, 320.0, peak_year_index=7, n=15),
            free_alloc=0.70,
        ),
    },
]


def _build_scenarios_db() -> None:
    path = DATA_DIR / "scenarios.db"
    path.unlink(missing_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE scenarios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                inputs_json TEXT NOT NULL,
                display_order INTEGER NOT NULL
            );
            """
        )
        for order, preset in enumerate(_PRESETS):
            conn.execute(
                "INSERT INTO scenarios(id, name, description, inputs_json, display_order) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    preset["id"],
                    preset["name"],
                    preset["description"],
                    json.dumps(preset["inputs"]),
                    order,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    _build_coefficients_db()
    _build_references_db()
    _build_scenarios_db()
    print(f"Built {DATA_DIR}/coefficients.db, references.db, scenarios.db")


if __name__ == "__main__":
    main()
