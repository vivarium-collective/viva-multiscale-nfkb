"""Write tnf_field_cell.composite.json: one cell in a TNF field, the three layers in one composite.

The kinetic and Boolean layers and the nuclear-fraction adapter are kinetic_boolean's, read from
kinetic_boolean.composite.json (regenerate that first). This adds the spatial layer and the dose-response that joins it to both:

- **spatial:** viva-pde-particle's FVReactionDiffusion on a 2-D reflecting box of medium, 200 x 200 um at dx 2 um and
  dt 0.05 s, D = 100 um^2/s (Wu 2011). TNF starts as a Gaussian bolus (sigma0 5 um) 40 um from the cell, scaled so the
  well-mixed level is 10 Kd. dx and dt were chosen against the exact solution (checks/spatial/region-mean-bolus).
- **field -> cell:** RegionMean over the ring of grid nodes just outside the cell's disk (radius 9 um, NIH/3T3,
  BioNumbers 108905) writes `tnf_at_cell` (uM). The cell is a sampling region, not an obstacle: v1 has one domain.
- **dose-response (d1):** one MathExpressionStep, occ = c / (c + Kd), with Kd = 1.9e-5 uM (19 pM, Grell 1998: TNF on
  TNFR1 at 37 C). It writes:
  - `tnf_occupancy.TNF_R`, which Lipniacki's `parameters_in` reads directly;
  - u_TNF = occ and d_TNF = 1 - occ, MaBoSS's TNF rates, which its network scales by k_time.
  It writes them in one Step, as nuclear_fraction writes f and the NF-kB rates.
  The step also reads `kinetic_time`, so it runs whenever the kinetic layer updates: process-bigraph 1.9.1 does not
  re-run a Step that reads `tnf_at_cell.TNF` when RegionMean writes the whole map (measured 2026-11-18, the same rule as
  `nuclear_fraction`). It samples TNF at the coupling interval, which is when both readers take it.
  It has `priority` 1, so it runs before the emitter at each coupling instant. process-bigraph 1.9.1's scheduler does
  not release it as RegionMean's dependent: RegionMean produces `tnf_at_cell`, and `determine_steps` releases only
  prefixes of a producer's output. So it runs through the scheduler's fallback, the highest-priority blocked Step
  (scheduling.py:605). Among equal priorities that pick follows set order, which is Python's hash seed. A split Step
  for u_TNF and d_TNF went the same way, and MaBoSS then saw TNF one interval late for some seeds
  (process-bigraph#284).
- **Boolean start:** TNF is off; the bolus has not arrived.
- **Kinetic model:** the driven SBML is inline (`model`, `model_format: sbml`), so the document runs as one file.

Defaults are the MVP's live setting: k_time = 1/120 per s (Study 1's fastest clock) and sample_count = 100, so the
Boolean layer responds within compose-api's 1000 s limit. That is a demonstration setting, not a calibration.

    uv run --project compose python -I viva_multiscale_nfkb/composites/make_tnf_field_cell.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from process_bigraph import allocate_core
from viva_pde_particle.steps.transfer import RegionMean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KINETIC_BOOLEAN = HERE / "kinetic_boolean.composite.json"
SBML = ROOT / "workspace" / "datasets" / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
OUT = HERE / "tnf_field_cell.composite.json"

HALF, DX = 100.0, 2.0  # the box is [-HALF, HALF]^2 um
GRID = {"origin": [-HALF, -HALF], "size": [2 * HALF, 2 * HALF], "num": [int(2 * HALF / DX) + 1] * 2}
DT, FIELD_INTERVAL = 0.05, 1.0  # s
D_TNF = 100.0  # um^2/s, Wu et al. 2011
R_CELL = 9.0  # um, the cell at the origin
X_BOLUS, SIGMA0 = 40.0, 5.0  # um
KD = 1.9e-5  # uM, Grell et al. 1998
C_WELL_MIXED = 10 * KD  # uM: the bolus's mean over the box


def axes() -> tuple[np.ndarray, np.ndarray]:
    nx, ny = GRID["num"]
    x = GRID["origin"][0] + np.arange(nx) * GRID["size"][0] / (nx - 1)
    y = GRID["origin"][1] + np.arange(ny) * GRID["size"][1] / (ny - 1)
    return np.meshgrid(x, y)  # shape (ny, nx), the engine's order


def surface_mask() -> np.ndarray:
    """The ring of nodes just outside the cell's disk: R_CELL <= r < R_CELL + DX."""
    xx, yy = axes()
    r = np.hypot(xx, yy)
    return (r >= R_CELL) & (r < R_CELL + DX)


def mean_over(field: np.ndarray, mask: np.ndarray) -> float:
    """RegionMean's own volume-weighted mean, from the pinned viva-pde-particle."""
    step = RegionMean({"grid": GRID, "species": ["TNF"], "region": {"mask": mask.tolist()}}, core=allocate_core())
    return float(step.update({"fields": {"TNF": field}})["mean_conc"]["TNF"])


def bolus() -> np.ndarray:
    xx, yy = axes()
    shape = np.exp(-((xx - X_BOLUS) ** 2 + yy**2) / (2 * SIGMA0**2))
    return shape * (C_WELL_MIXED / mean_over(shape, np.ones_like(shape, dtype=bool)))


def field_layer(field: np.ndarray) -> dict:
    """The spatial layer and the field -> cell step, given the field's initial state."""
    return {
        "fields": {"TNF": field.tolist()},
        "tnf_at_cell": {"TNF": 0.0},
        "field": {
            "_type": "process",
            "address": "local:viva_pde_particle.processes.fv_reaction_diffusion.FVReactionDiffusion",
            "config": {"grid": GRID, "pde": {"species": {"TNF": {"diffusion": D_TNF}}, "terms": []}, "dt": DT},
            "interval": FIELD_INTERVAL,
            "inputs": {"fields": ["fields"]},
            "outputs": {"fields": ["fields"]},
        },
        "surface": {
            "_type": "step",
            "address": "local:viva_pde_particle.steps.transfer.RegionMean",
            "config": {"grid": GRID, "species": ["TNF"], "region": {"mask": surface_mask().tolist()}},
            "inputs": {"fields": ["fields"]},
            "outputs": {"mean_conc": ["tnf_at_cell"]},
        },
    }


def build(field_state: dict | None) -> dict:
    """The spec. `field_state` is the field layer's stores and processes (field_layer), or None for the ablated
    document, where `tnf_at_cell` is a seeded store and nothing writes it (checks/coupled/field-ablation)."""
    spec = json.loads(KINETIC_BOOLEAN.read_text())
    state = spec["state"]
    state.pop("stimulus")
    kinetic = state["kinetic"]
    if kinetic["config"]["model_file"] != SBML.name:
        raise SystemExit(f"kinetic_boolean runs {kinetic['config']['model_file']}, not {SBML.name}")
    config = {k: v for k, v in kinetic["config"].items() if k != "model_file"}
    kinetic["config"] = {"model": SBML.read_text(), "model_format": "sbml", **config}
    kinetic["inputs"] = {"parameters_in": ["tnf_occupancy"]}
    state.update(field_state or {"tnf_at_cell": {"TNF": 0.0}})
    state["tnf_occupancy"] = {"TNF_R": 0.0}
    state["tnf_occupancy_time"] = 0.0
    state["dose_response"] = {
        "_type": "step",
        "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
        "priority": 1.0,  # first among blocked Steps, whatever the hash seed (see the module docstring)
        "config": {
            "expressions": [
                {"out": "occ", "expr": "c / (c + Kd)"},
                # the fate network's TNF node rates, from occ in this same Step, as nuclear_fraction writes the
                # NF-kB node's
                {"out": "u_TNF", "expr": "occ"},
                {"out": "d_TNF", "expr": "1 - occ"},
                # read so that this Step runs on every kinetic update (see the module docstring)
                {"out": "occ_time", "expr": "kinetic_time"},
            ],
            "params": {"Kd": "${Kd}"},
        },
        "inputs": {"c": ["tnf_at_cell", "TNF"], "kinetic_time": ["kinetic_time"]},
        "outputs": {"occ": ["tnf_occupancy", "TNF_R"], "u_TNF": ["parameters", "u_TNF"],
                    "d_TNF": ["parameters", "d_TNF"], "occ_time": ["tnf_occupancy_time"]},
    }
    state["parameters"].update({"u_TNF": 0.0, "d_TNF": 0.0})
    on_at_start = [n for n in state["cellfate"]["config"]["initial_state"] if n != "TNF"]
    for store in ("node_state", "node_probabilities"):
        state[store] = {n: float(n in on_at_start) for n in state[store]}
    state["cellfate"]["config"]["initial_state"] = {n: 1.0 for n in on_at_start}
    emit = {"tnf_at_cell": "map[float]", "tnf_occupancy": "map[float]", "nfkb_fraction": "float",
            "nfkb_fraction_time": "float", "node_probabilities": "map[float]", "global_time": "float"}
    state["emitter"]["config"]["emit"] = emit
    state["emitter"]["inputs"] = {k: [k] for k in emit}
    spec["global_time_precision"] = 6  # the field's 1 s and the coupling's 30 s steps meet exactly
    spec["name"] = "tnf-field-cell"
    spec["description"] = (
        "One cell in a TNF field: a TNF bolus diffuses in the medium (FVReactionDiffusion), RegionMean reads it at the "
        "cell's surface, one-site occupancy (Kd 19 pM) drives Lipniacki 2004 NF-kB's TNF_R and Calzone 2010's TNF "
        "node, and NF-kB's nuclear fraction drives Calzone's NF-kB node.")
    spec["tags"] = [*spec["tags"], "spatial", "pde", "multiscale"]
    spec["requires"]["processes"] = [*spec["requires"]["processes"], "FVReactionDiffusion", "RegionMean"]
    params = spec["parameters"]
    params["Kd"] = {"type": "float", "default": KD,
                    "description": "TNF-TNFR1 dissociation constant (uM): 1.9e-11 M at 37 C, Grell et al. 1998"}
    params["k_time"]["default"] = 1.0 / 120.0
    params["k_time"]["description"] += "; 1/120 here, Study 1's fastest clock, so the fate network responds within 1000 s"
    params["sample_count"]["default"] = 100
    return spec


def main() -> None:
    spec = build(field_layer(bolus()))
    OUT.write_text(json.dumps(spec, indent=1) + "\n")
    print(f"wrote {OUT.name}: {int(surface_mask().sum())} surface nodes, well-mixed TNF {C_WELL_MIXED:.3g} uM")


if __name__ == "__main__":
    main()
