"""Read-only SQLite accessors.

Keeps DB handles open for the lifetime of the process. All DBs are shipped
alongside the application code (SPEC §6.4) and treated as read-only.
"""

from __future__ import annotations

import sqlite3
from functools import cache
from pathlib import Path
from typing import Any

from app.schemas import ReferenceEntry, ScenarioInputs, ScenarioPreset

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@cache
def _connect(db_name: str) -> sqlite3.Connection:
    path = DATA_DIR / db_name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run python -m scripts.build_data` first."
        )
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}  # noqa: SIM118 - sqlite3.Row requires explicit .keys()


def get_coefficients() -> dict[str, Any]:
    """Return the raw coefficients table keyed by constant name.

    Values are decoded to their declared `kind` (float/int/str).
    """
    conn = _connect("coefficients.db")
    out: dict[str, Any] = {}
    for row in conn.execute("SELECT name, value, kind FROM constants"):
        value_str = row["value"]
        kind = row["kind"]
        if kind == "float":
            out[row["name"]] = float(value_str)
        elif kind == "int":
            out[row["name"]] = int(value_str)
        else:
            out[row["name"]] = str(value_str)
    return out


_REFERENCE_COLS = (
    "id, citation, region, sector, coefficient, std_err, method, method_type, "
    "headline_finding, comparison_note, warning_label, notes, url"
)


def list_references() -> list[ReferenceEntry]:
    conn = _connect("references.db")
    rows = conn.execute(
        f'SELECT {_REFERENCE_COLS} FROM "references" ORDER BY id'
    )
    return [ReferenceEntry(**_row_to_dict(r)) for r in rows]


def get_reference(reference_id: str) -> ReferenceEntry | None:
    conn = _connect("references.db")
    row = conn.execute(
        f'SELECT {_REFERENCE_COLS} FROM "references" WHERE id = ?',
        (reference_id,),
    ).fetchone()
    if row is None:
        return None
    return ReferenceEntry(**_row_to_dict(row))


def list_scenarios() -> list[ScenarioPreset]:
    conn = _connect("scenarios.db")
    rows = conn.execute(
        "SELECT id, name, description, inputs_json FROM scenarios ORDER BY display_order, id"
    ).fetchall()
    return [
        ScenarioPreset(
            id=r["id"],
            name=r["name"],
            description=r["description"],
            inputs=ScenarioInputs.model_validate_json(r["inputs_json"]),
        )
        for r in rows
    ]


__all__ = [
    "get_coefficients",
    "get_reference",
    "list_references",
    "list_scenarios",
]
