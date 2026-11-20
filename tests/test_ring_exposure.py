"""The dose study's fading baths give each distance-study cell its sensed dose (decision 56).

Both sides are recomputed here from the data, not from ring_exposure.py: the cell's TNF from the 24 h field
(exposure_24h_band1.json, per unit bolus, linear in the bolus) and the bath from its parameters (ring_exposure.json).
The coupling samples occupancy c / (c + Kd) every 30 s and holds it for the interval, at t = 0, 30, ..., 86370 s; the
cell has no TNF at t = 0.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

DESIGN = Path(__file__).resolve().parents[1] / "analysis" / "exposure-design"


@pytest.fixture(scope="module")
def data():
    rings = json.loads((DESIGN / "ring_exposure.json").read_text())
    field = json.loads((DESIGN / "exposure_24h_band1.json").read_text())
    assert field["sample_s"] == 30 and field["time_s"][0] == 30 and len(field["time_s"]) == 2880
    return rings, field


def _sensed(c: np.ndarray, kd: float) -> float:
    return float((c / (c + kd)).sum() * 30)


def _cell(field: dict, row: dict) -> np.ndarray:
    """The cell's TNF as the coupling holds it: 0 at t = 0, then the field's samples up to 86370 s."""
    tnf = row["bolus"] * np.array(field["tnf_at_cell"][row["cell"]])
    return np.concatenate([[0.0], tnf[:-1]])


def _bath(row: dict, decay: float) -> np.ndarray:
    return row["peak_uM"] * np.exp(-decay * 30 * np.arange(2880))


def test_each_bath_has_its_cells_peak_and_sensed_dose(data):
    rings, field = data
    assert len(rings["rows"]) == 9
    for row in rings["rows"]:
        cell = _cell(field, row)
        bath = _bath(row, row["bath_decay_per_s"])
        assert bath[0] == pytest.approx(cell.max(), rel=1e-12), row
        assert _sensed(bath, rings["kd_uM"]) == pytest.approx(_sensed(cell, rings["kd_uM"]), rel=1e-9), row


def test_the_concentration_match_gave_the_near_cell_a_fraction_of_its_sensed_dose(data):
    """Decision 50's first rule, lambda = peak / the 24 h concentration integral, which decision 56 replaced."""
    rings, field = data
    (row,) = [r for r in rings["rows"] if r["cell"] == "near" and r["bolus"] == 100]
    old = _bath(row, row["peak_uM"] / row["c_integral_uM_s"])
    assert _sensed(old, rings["kd_uM"]) / _sensed(_cell(field, row), rings["kd_uM"]) < 0.25
