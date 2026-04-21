"""Pydantic v2 request/response schemas.

SPEC source of truth:
- §4.1 parameter ranges
- §4.3 Monte Carlo (N=0 disables; seed=42 default)
- §4.4 caveats shape
- §8.2 Scenario JSON schema v1.0
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION: Literal["1.0"] = "1.0"
BASELINE_YEAR = 2020
FIRST_POLICY_YEAR = 2021
LAST_POLICY_YEAR = 2035
DEFAULT_E_2020_MT = 5_150.0


class PricePoint(BaseModel):
    """Single year/price pair in a price path."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    year: int = Field(ge=FIRST_POLICY_YEAR, le=LAST_POLICY_YEAR)
    price_cny: float = Field(ge=0.0, le=10_000.0, description="Carbon price CNY/tCO2")


class ScenarioInputs(BaseModel):
    """User inputs per SPEC §8.2.

    Field ranges match the sliders declared in SPEC §4.1. `mc_n = 0` disables
    Monte Carlo per SPEC §4.3 and is the canonical determinism gate
    (§9 criterion 2).
    """

    model_config = ConfigDict(extra="forbid")

    price_path: list[PricePoint] = Field(min_length=1)
    free_allocation_share: float = Field(ge=0.0, le=1.0, default=0.90)
    coefficient_source: str = Field(default="author_did_2026", min_length=1)
    alpha: float = Field(ge=0.10, le=0.60, default=0.30)
    gdp_growth: float = Field(ge=0.02, le=0.06, default=0.045)
    energy_intensity_improvement: float = Field(ge=0.0, le=0.03, default=0.020)
    electrification_rate: float = Field(ge=0.0, le=0.02, default=0.005)
    mc_n: int = Field(ge=0, le=100_000, default=10_000)
    mc_seed: int = Field(ge=0, le=2**31 - 1, default=42)
    e_2020_mt: float = Field(gt=0.0, default=DEFAULT_E_2020_MT)

    @field_validator("price_path")
    @classmethod
    def _years_unique_and_sorted(cls, v: list[PricePoint]) -> list[PricePoint]:
        years = [p.year for p in v]
        if len(set(years)) != len(years):
            raise ValueError("price_path years must be unique")
        if years != sorted(years):
            raise ValueError("price_path must be sorted by year")
        return v


class ScenarioMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="Untitled scenario", max_length=200)
    created_at: str | None = None
    notes: str | None = Field(default=None, max_length=2_000)


class ScenarioDocument(BaseModel):
    """Full JSON document per SPEC §8.2 for import/export round-tripping."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    meta: ScenarioMeta = Field(default_factory=ScenarioMeta)
    inputs: ScenarioInputs


class ComputeRequest(BaseModel):
    """POST /api/compute body — currently a thin wrapper around ScenarioInputs."""

    model_config = ConfigDict(extra="forbid")

    inputs: ScenarioInputs


class PercentileBands(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    p5: list[float]
    p25: list[float]
    p50: list[float]
    p75: list[float]
    p95: list[float]


class KPIBundle(BaseModel):
    """Headline metrics surfaced in the UI card row."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cumulative_reduction_mt_median: float
    cumulative_reduction_mt_p5: float
    cumulative_reduction_mt_p95: float
    peak_year_median: int
    peak_year_p5: int
    peak_year_p95: int
    emissions_2035_mt_median: float
    relative_reduction_2035_median: float


class Caveat(BaseModel):
    """External validity / sanity caveat entry (SPEC §4.4)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    severity: Literal["info", "warning", "critical"]
    message: str


class CoefficientRecord(BaseModel):
    """The coefficient used for the compute call (plus citation)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    label: str
    beta: float
    std_err: float
    region: str
    sector: str
    citation: str
    url: str | None = None


class ComputeResponse(BaseModel):
    """POST /api/compute response.

    `method` is pinned to "reduced_form" in V1 so V2 can add "mac_curve"
    without breaking the contract (§4.5).
    """

    model_config = ConfigDict(extra="forbid")

    method: Literal["reduced_form"] = "reduced_form"
    years: list[int]
    bau_mt: list[float]
    deterministic_mt: list[float]
    percentiles_mt: PercentileBands | None
    kpis: KPIBundle
    caveats: list[Caveat]
    coefficient: CoefficientRecord
    mc_n_effective: int
    mc_seed: int


class ScenarioPreset(BaseModel):
    """A curated preset served from scenarios.db."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str
    inputs: ScenarioInputs


MethodType = Literal[
    "log_log_elasticity",
    "att_pct_reduction",
    "semi_elasticity_growth",
]


class ReferenceEntry(BaseModel):
    """Literature reference served from references.db (SPEC §5.2).

    Extended in v1.2: `method_type`, `headline_finding`, `comparison_note`,
    `warning_label`. Only `log_log_elasticity` entries are usable for
    `/api/compute`; the other types (meta-analysis ATT, growth-rate
    semi-elasticities) are carried purely as external-validation context and
    are dimensionally incompatible with the reduced-form response function.
    `coefficient` / `std_err` are optional because the scalar interpretation
    varies across method types and is not defined for meta-analyses.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    citation: str
    region: str
    sector: str
    coefficient: float | None = None
    std_err: float | None = None
    method: str
    method_type: MethodType
    headline_finding: str | None = None
    comparison_note: str | None = None
    warning_label: str | None = None
    notes: str | None = None
    url: str | None = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: Literal["ok"]
    version: str


__all__ = [
    "BASELINE_YEAR",
    "Caveat",
    "CoefficientRecord",
    "ComputeRequest",
    "ComputeResponse",
    "DEFAULT_E_2020_MT",
    "FIRST_POLICY_YEAR",
    "HealthResponse",
    "KPIBundle",
    "LAST_POLICY_YEAR",
    "PercentileBands",
    "PricePoint",
    "ReferenceEntry",
    "ScenarioDocument",
    "ScenarioInputs",
    "ScenarioMeta",
    "ScenarioPreset",
    "SCHEMA_VERSION",
]
