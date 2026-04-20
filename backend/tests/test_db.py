"""Smoke tests for the SQLite read layer."""

from __future__ import annotations

from app.db import queries


class TestCoefficients:
    def test_e_2020_value(self) -> None:
        c = queries.get_coefficients()
        assert c["e_2020_mt"] == 5_150.0
        assert c["default_coefficient_id"] == "author_did_2026"


class TestReferences:
    def test_author_default_present(self) -> None:
        refs = queries.list_references()
        ids = [r.id for r in refs]
        assert "author_did_2026" in ids
        assert len(refs) >= 2  # SPEC §5.2: V1 ships >= 2 alternates

    def test_author_coefficient_matches_dissertation(self) -> None:
        r = queries.get_reference("author_did_2026")
        assert r is not None
        assert r.coefficient == -0.2273
        assert r.std_err == 0.0793
        assert r.region == "China"

    def test_missing_reference_returns_none(self) -> None:
        assert queries.get_reference("does_not_exist") is None


class TestScenarios:
    def test_five_presets_shipped(self) -> None:
        presets = queries.list_scenarios()
        ids = {p.id for p in presets}
        assert {"current", "ndc", "nze_china", "bau", "peak"}.issubset(ids)

    def test_current_preset_has_valid_inputs(self) -> None:
        presets = queries.list_scenarios()
        current = next(p for p in presets if p.id == "current")
        assert len(current.inputs.price_path) == 15
        assert current.inputs.free_allocation_share == 0.90
