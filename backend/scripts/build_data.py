"""Build the three SQLite DBs shipped with the backend.

Usage:
    uv run python -m scripts.build_data

Produces (overwriting) under ``app/data/``:
  - coefficients.db  — versioned numeric constants (E_2020, default coefficient id)
  - references.db    — literature library (author's DID + external-validity refs)
  - scenarios.db     — curated preset scenarios (SPEC §8.1)

SPEC §5 is source of truth for schemas. The v1.2 schema extension on
`references` adds `method_type`, `headline_finding`, `comparison_note`, and
`warning_label` so the frontend can render dimensional compatibility warnings
next to each citation. Only `log_log_elasticity` entries are ever used for
`/api/compute`; everything else is external validation context.
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
                    "Liu 2026 dissertation DID estimate — sole coefficient used for compute",
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


# --- references.db ------------------------------------------------------------


# Only `author_did_2026` is used by /api/compute; everything else is
# external-validity context with a different functional form.
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
        "method_type": "log_log_elasticity",
        "headline_finding": (
            "Log-log price semi-elasticity of emissions, β̂ = −0.2273 "
            "(SE 0.0793, p = 0.006) estimated from the pilot ETS window."
        ),
        "comparison_note": (
            "Sole coefficient used for this tool's simulation. All scenarios "
            "run with this estimate; other entries on this list are shown for "
            "external validation only."
        ),
        "warning_label": None,
        "notes": (
            "Default coefficient. Pilot ETS period; see §4.4 for extrapolation "
            "caveats when prices exceed the training range."
        ),
        "url": None,
    },
    {
        "id": "dobbeling_hildebrandt_2024",
        "citation": (
            "Döbbeling-Hildebrandt, N., Miersch, K., Khanna, T. M., Bachelet, M., "
            "Bruns, S. B., Callaghan, M., Edenhofer, O., Flachsland, C., Forster, "
            "P. M., Kalkuhl, M., Koch, N., Lamb, W. F., Ohlendorf, N., Steckel, "
            "J. C., & Minx, J. C. (2024). Systematic review and meta-analysis of "
            "ex-post evaluations on the effectiveness of carbon pricing. Nature "
            "Communications, 15, 4147."
        ),
        "region": "Global (21 carbon-pricing schemes)",
        "sector": "Cross-sector (aggregated)",
        "coefficient": None,
        "std_err": None,
        "method": "Meta-analysis of 483 effect sizes across 80 causal evaluations",
        "method_type": "att_pct_reduction",
        "headline_finding": (
            "Introducing a carbon price reduces emissions by 5–21% "
            "(4–15% after publication-bias correction) across 80 causal "
            "evaluations of 21 carbon-pricing schemes."
        ),
        "comparison_note": (
            "This tool's ~12% cumulative reduction under the Current Policy "
            "preset (P 80→100 CNY/tCO₂, f=0.90) sits inside the 5–21% range "
            "reported by this meta-analysis, providing convergent validity."
        ),
        "warning_label": (
            "Meta-analysis ATT — reports average treatment effects on the "
            "treated, not a log-log price elasticity. Do not substitute."
        ),
        "notes": "Nature Communications, open access.",
        "url": "https://doi.org/10.1038/s41467-024-48512-w",
    },
    {
        "id": "rafaty_dolphin_pretis_2025",
        "citation": (
            "Rafaty, R., Dolphin, G., & Pretis, F. (2025). Carbon pricing and "
            "the elasticity of CO₂ emissions. Energy Economics, 144, 108325."
        ),
        "region": "Cross-country panel",
        "sector": "Multi-sector (electricity & heat subset)",
        "coefficient": None,
        "std_err": None,
        "method": "Reduced-form, growth-rate semi-elasticity",
        "method_type": "semi_elasticity_growth",
        "headline_finding": (
            "Each additional US$1/tCO₂ lowers the emissions growth rate by "
            "≈0.06 percentage points. Carbon-pricing introduction reduces "
            "growth by 1–2 pp overall; electricity & heat ATT reaches −6.5 pp."
        ),
        "comparison_note": (
            "Units are 'growth-rate percentage points per $1/tCO₂', not the "
            "log-log semi-elasticity used here. Sign and order of magnitude "
            "align with the tool's direction of effect, but direct numerical "
            "substitution is not meaningful."
        ),
        "warning_label": (
            "Different functional form (growth-rate pp per $1). For direction "
            "check only — not a log-log elasticity."
        ),
        "notes": "Energy Economics, 2025.",
        "url": "https://doi.org/10.1016/j.eneco.2025.108325",
    },
    {
        "id": "best_burke_jotzo_2020",
        "citation": (
            "Best, R., Burke, P. J., & Jotzo, F. (2020). Carbon Pricing "
            "Efficacy: Cross-Country Evidence. Environmental and Resource "
            "Economics, 77(1), 69–94."
        ),
        "region": "Cross-country panel (142 countries)",
        "sector": "Economy-wide",
        "coefficient": None,
        "std_err": None,
        "method": "Panel fixed effects, growth-rate semi-elasticity, 1997–2017",
        "method_type": "semi_elasticity_growth",
        "headline_finding": (
            "Countries with a carbon price see annual CO₂ emissions growth "
            "≈2 pp lower than countries without. Each €1/tCO₂ reduces annual "
            "growth by ≈0.3 pp."
        ),
        "comparison_note": (
            "Economy-wide, cross-country evidence across 142 nations; this "
            "tool focuses on China's thermal-power sector. The operating scale "
            "and functional form differ, so this is a qualitative comparison."
        ),
        "warning_label": (
            "Economy-wide, cross-country growth-rate semi-elasticity. Not "
            "directly comparable with sector-specific log-log elasticity."
        ),
        "notes": "Environmental and Resource Economics, 2020.",
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
                coefficient REAL,
                std_err REAL,
                method TEXT NOT NULL,
                method_type TEXT NOT NULL
                    CHECK (method_type IN (
                        'log_log_elasticity',
                        'att_pct_reduction',
                        'semi_elasticity_growth'
                    )),
                headline_finding TEXT,
                comparison_note TEXT,
                warning_label TEXT,
                notes TEXT,
                url TEXT
            );
            """
        )
        for ref in _REFERENCES:
            conn.execute(
                'INSERT INTO "references"('
                "id, citation, region, sector, coefficient, std_err, method, "
                "method_type, headline_finding, comparison_note, warning_label, "
                "notes, url) VALUES ("
                ":id, :citation, :region, :sector, :coefficient, :std_err, "
                ":method, :method_type, :headline_finding, :comparison_note, "
                ":warning_label, :notes, :url)",
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
        out.extend(tail_segment[1:])
    return out


def _policy_years() -> list[int]:
    return list(range(2021, 2036))


def _build_preset_inputs(prices: list[float], free_alloc: float) -> dict[str, Any]:
    years = _policy_years()
    assert len(prices) == len(years), f"expected {len(years)} prices, got {len(prices)}"
    return {
        "price_path": [
            {"year": y, "price_cny": round(p, 3)}
            for y, p in zip(years, prices, strict=True)
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
