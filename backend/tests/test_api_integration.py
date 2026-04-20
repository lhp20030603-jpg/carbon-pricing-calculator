"""End-to-end API integration tests.

SPEC §9 acceptance criteria exercised here:
  - criterion 1: /compute returns schema-valid fan-chart data
  - criterion 2: determinism with mc_n = 0 (canonical gate)
  - criterion 3: price_above_training_range caveat fires iff max(P_t) > 100
  - criterion 9: current-preset integration (non-zero reduction, peak year in range)
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.compute.caveats import CAVEAT_PRICE_ABOVE_TRAINING
from app.db import queries
from app.main import app

client = TestClient(app)


def _current_preset_inputs() -> dict:
    presets = queries.list_scenarios()
    current = next(p for p in presets if p.id == "current")
    return current.inputs.model_dump(mode="json")


class TestHealth:
    def test_health_ok(self) -> None:
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestReferences:
    def test_references_listed(self) -> None:
        r = client.get("/api/references")
        assert r.status_code == 200
        data = r.json()
        assert any(ref["id"] == "author_did_2026" for ref in data)


class TestScenarios:
    def test_scenarios_listed(self) -> None:
        r = client.get("/api/scenarios")
        assert r.status_code == 200
        data = r.json()
        assert {p["id"] for p in data}.issuperset({"current", "ndc", "nze_china", "bau"})


class TestComputeGoldenPath:
    """SPEC §9 criterion 9."""

    def test_current_preset_compute_schema_and_nonzero_reduction(self) -> None:
        inputs = _current_preset_inputs()
        r = client.post("/api/compute", json={"inputs": inputs})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["method"] == "reduced_form"
        assert len(data["years"]) == len(data["bau_mt"]) == len(data["deterministic_mt"])
        assert data["percentiles_mt"] is not None
        assert data["kpis"]["cumulative_reduction_mt_median"] > 100.0
        assert 2021 <= data["kpis"]["peak_year_median"] <= 2035
        # Coefficient provenance surfaced
        assert data["coefficient"]["source_id"] == "author_did_2026"
        assert data["coefficient"]["beta"] == -0.2273


class TestDeterminismGate:
    """SPEC §9 criterion 2: mc_n=0 -> identical output across calls (6dp)."""

    def test_mc_n_zero_reproducible(self) -> None:
        inputs = _current_preset_inputs()
        inputs["mc_n"] = 0
        r1 = client.post("/api/compute", json={"inputs": inputs}).json()
        r2 = client.post("/api/compute", json={"inputs": inputs}).json()
        assert r1["percentiles_mt"] is None
        assert r2["percentiles_mt"] is None
        for a, b in zip(r1["deterministic_mt"], r2["deterministic_mt"], strict=True):
            assert round(a, 6) == round(b, 6)


class TestCaveatThresholdPinned:
    """SPEC §9 criterion 3 — caveat threshold = 100 CNY/tCO2 exactly."""

    def test_max_price_100_does_not_trigger(self) -> None:
        inputs = _current_preset_inputs()
        inputs["price_path"] = [{"year": y, "price_cny": 100.0} for y in range(2021, 2036)]
        r = client.post("/api/compute", json={"inputs": inputs}).json()
        assert CAVEAT_PRICE_ABOVE_TRAINING not in {c["id"] for c in r["caveats"]}

    def test_max_price_just_above_100_triggers(self) -> None:
        inputs = _current_preset_inputs()
        inputs["price_path"] = [{"year": y, "price_cny": 100.01} for y in range(2021, 2036)]
        r = client.post("/api/compute", json={"inputs": inputs}).json()
        assert CAVEAT_PRICE_ABOVE_TRAINING in {c["id"] for c in r["caveats"]}


class TestComputeBadInput:
    def test_unknown_coefficient_source_returns_400(self) -> None:
        inputs = _current_preset_inputs()
        inputs["coefficient_source"] = "does_not_exist"
        r = client.post("/api/compute", json={"inputs": inputs})
        assert r.status_code == 400

    def test_out_of_range_alpha_rejected_by_pydantic(self) -> None:
        inputs = _current_preset_inputs()
        inputs["alpha"] = 0.9  # outside [0.10, 0.60]
        r = client.post("/api/compute", json={"inputs": inputs})
        assert r.status_code == 422
