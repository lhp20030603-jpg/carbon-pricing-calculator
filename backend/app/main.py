"""FastAPI entry point for the carbon pricing policy impact calculator.

Endpoints (SPEC §6.2):
  - POST /api/compute     — run the model for a scenario
  - GET  /api/scenarios   — curated preset library
  - GET  /api/references  — coefficient provenance library
  - GET  /api/health      — readiness probe (also pre-warms Render cold starts)

All types live in app.schemas; computation lives in app.compute. This module
is orchestration only — keep it lean (< 300 lines).
"""

from __future__ import annotations

import os
from importlib import metadata

import numpy as np
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.compute.caveats import detect_caveats
from app.compute.monte_carlo import ScenarioResult, compute_scenario
from app.db import queries
from app.schemas import (
    Caveat,
    CoefficientRecord,
    ComputeRequest,
    ComputeResponse,
    HealthResponse,
    ReferenceEntry,
    ScenarioInputs,
    ScenarioPreset,
)


def _version() -> str:
    try:
        return metadata.version("carbon-pricing-calculator-backend")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def _cors_origins() -> list[str]:
    """Allowed origins — CORS_ORIGINS env var (comma-separated) or safe default."""
    raw = os.environ.get("CORS_ORIGINS")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]


app = FastAPI(
    title="Carbon Pricing Policy Impact Calculator",
    description=(
        "Reduced-form prospective calculator for China's national ETS (2021+). "
        "See SPEC.md and docs/methodology.pdf for the model and its caveats."
    ),
    version=_version(),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# --- helpers ------------------------------------------------------------------


def _resolve_coefficient(source_id: str) -> ReferenceEntry:
    ref = queries.get_reference(source_id)
    if ref is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown coefficient_source '{source_id}'. See GET /api/references.",
        )
    if ref.method_type != "log_log_elasticity":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Reference '{source_id}' has method_type '{ref.method_type}' and "
                "is dimensionally incompatible with the reduced-form response "
                "function. Only log-log elasticity entries (currently "
                "'author_did_2026') can be used for compute. Other entries are "
                "served for external-validation context only."
            ),
        )
    if ref.coefficient is None or ref.std_err is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reference '{source_id}' is missing coefficient/std_err data.",
        )
    return ref


def _price_array(inputs: ScenarioInputs) -> np.ndarray:
    years = np.arange(2021, 2036, dtype=np.float64)
    supplied_years = np.asarray([p.year for p in inputs.price_path], dtype=np.float64)
    supplied_prices = np.asarray([p.price_cny for p in inputs.price_path], dtype=np.float64)
    return np.interp(years, supplied_years, supplied_prices)


def _response_from_result(
    result: ScenarioResult,
    caveats_payload: list[Caveat],
    coefficient: ReferenceEntry,
) -> ComputeResponse:
    return ComputeResponse(
        method="reduced_form",
        years=result.years,
        bau_mt=result.bau_mt.tolist(),
        deterministic_mt=result.deterministic_mt.tolist(),
        percentiles_mt=result.as_bands(),
        kpis=result.kpis,
        caveats=caveats_payload,
        coefficient=CoefficientRecord(
            source_id=coefficient.id,
            label=coefficient.citation.split(".")[0],
            # Guaranteed non-None by _resolve_coefficient's method_type guard.
            beta=coefficient.coefficient if coefficient.coefficient is not None else 0.0,
            std_err=coefficient.std_err if coefficient.std_err is not None else 0.0,
            region=coefficient.region,
            sector=coefficient.sector,
            citation=coefficient.citation,
            url=coefficient.url,
        ),
        mc_n_effective=result.mc_n_effective,
        mc_seed=result.mc_seed,
    )


# --- endpoints ----------------------------------------------------------------


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=_version())


@app.get("/api/references", response_model=list[ReferenceEntry])
def references() -> list[ReferenceEntry]:
    return queries.list_references()


@app.get("/api/scenarios", response_model=list[ScenarioPreset])
def scenarios() -> list[ScenarioPreset]:
    return queries.list_scenarios()


@app.post("/api/compute", response_model=ComputeResponse)
def compute(request: ComputeRequest) -> ComputeResponse:
    coefficient = _resolve_coefficient(request.inputs.coefficient_source)
    # _resolve_coefficient already guarantees these are not None and the
    # method_type is log-log elasticity; mypy can't see through that.
    assert coefficient.coefficient is not None
    assert coefficient.std_err is not None
    result = compute_scenario(
        inputs=request.inputs,
        beta=coefficient.coefficient,
        se=coefficient.std_err,
    )
    prices = _price_array(request.inputs)
    caveats_payload = detect_caveats(
        prices_cny=prices,
        years=result.years,
        coefficient_region=coefficient.region,
        coefficient_sector=coefficient.sector,
    )
    return _response_from_result(result, caveats_payload, coefficient)


__all__ = ["app"]
