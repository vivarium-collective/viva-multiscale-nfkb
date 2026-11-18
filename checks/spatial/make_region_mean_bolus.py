"""Generate checks/spatial/region-mean-bolus: the TNF at the cell, as the full composite computes it, against the exact
solution.

The document is tnf_field_cell.composite.json's own spatial layer, read from that file, so the check runs exactly what
the composite runs:
- the field: FVReactionDiffusion, a 2-D reflecting box [-100, 100]^2 um, dx 2 um, dt 0.05 s, D 100 um^2/s;
- the cell's surface: RegionMean over the ring of nodes 9 <= r < 11 um around the origin;
- the bolus: a Gaussian, sigma0 5 um, 40 um from the cell, scaled so the box's mean is 10 Kd.

The exact solution in a reflecting box is the free Gaussian (sigma^2 = sigma0^2 + 2 D t), summed over its mirror images
in each axis's walls. It is sampled at the ring's own nodes and averaged with RegionMean's own weights, so the check
measures the scheme's error and nothing else.
- Error measured 2026-11-18. It is first order in dt and does not depend on dx: dx 2 and dx 1 agree to 5%.
  - At dt 0.05 s: -1.7% at 2 s, on the rising front; -0.45% at the 4 s peak (29 Kd); +0.17% at 10 s; +0.10% at 30 s,
    the first coupling sample; +1.1e-4 at 60 s.
  - Halving dt halves each of these.
- Tolerances are three times those errors.
- At 990 s the field is uniform to e^-24. Mass is conserved exactly, so the ring reads the box's mean, 10 Kd, to rel
  1e-9.

The generator also checks that the composite's bolus is this Gaussian, so the oracle and the document cannot drift apart.

    uv run --project compose python -I checks/spatial/make_region_mean_bolus.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import yaml
from process_bigraph import allocate_core
from viva_pde_particle.steps.transfer import RegionMean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COMPOSITE = ROOT / "viva_multiscale_nfkb" / "composites" / "tnf_field_cell.composite.json"
NAME = "region-mean-bolus"
X_BOLUS, SIGMA0 = 40.0, 5.0  # um, as make_tnf_field_cell.py
END = 990
#: time (s) -> relative tolerance, three times the error measured at dt 0.05 s
ROWS = {2: 5e-2, 4: 1.5e-2, 10: 5e-3, 30: 3e-3, 60: 5e-4, END: 1e-9}


def images(u: np.ndarray, u0: float, low: float, length: float, s2: float) -> np.ndarray:
    """The 1-D Neumann heat kernel on [low, low + length]: the free Gaussian and its mirror images."""
    n_max = int(math.ceil(8 * math.sqrt(s2) / (2 * length))) + 2  # the next image adds less than e^-32
    total = np.zeros_like(u)
    for n in range(-n_max, n_max + 1):
        for centre in (u0 + 2 * n * length, 2 * low - u0 + 2 * n * length):
            total += np.exp(-((u - centre) ** 2) / (2 * s2))
    return total / math.sqrt(2 * math.pi * s2)


def main() -> None:
    state = json.loads(COMPOSITE.read_text())["state"]
    field, surface = state["field"], state["surface"]
    grid = field["config"]["grid"]
    diffusion = field["config"]["pde"]["species"]["TNF"]["diffusion"]
    nx, ny = grid["num"]
    (x_low, y_low), (x_len, y_len) = grid["origin"], grid["size"]
    xx, yy = np.meshgrid(x_low + np.arange(nx) * x_len / (nx - 1), y_low + np.arange(ny) * y_len / (ny - 1))
    initial = np.asarray(state["fields"]["TNF"])
    core = allocate_core()
    whole = RegionMean({"grid": grid, "species": ["TNF"], "region": {"mask": np.ones_like(initial, bool).tolist()}},
                       core=core)
    ring = RegionMean({"grid": grid, "species": ["TNF"], "region": surface["config"]["region"]}, core=core)
    c_mean = whole.update({"fields": {"TNF": initial}})["mean_conc"]["TNF"]
    shape = np.exp(-((xx - X_BOLUS) ** 2 + yy**2) / (2 * SIGMA0**2))
    if np.max(np.abs(initial - shape * initial.max())) > 1e-15 * initial.max():
        raise SystemExit("the composite's bolus is not the Gaussian this oracle solves")
    mass = c_mean * x_len * y_len
    expect = []
    for t, rel in ROWS.items():
        s2 = SIGMA0**2 + 2 * diffusion * t
        exact = mass * images(xx, X_BOLUS, x_low, x_len, s2) * images(yy, 0.0, y_low, y_len, s2)
        value = ring.update({"fields": {"TNF": exact}})["mean_conc"]["TNF"]
        expect.append({"kind": "scalar", "emitter": "emitter", "field": "tnf_at_cell.TNF", "row": t,
                       "expected": value, "rel": rel, "abs": 0.0})
    if not math.isclose(expect[-1]["expected"], c_mean, rel_tol=1e-12):
        raise SystemExit(f"the exact solution at {END} s is not the box's mean: {expect[-1]['expected']} vs {c_mean}")
    document = {
        "state": {
            "fields": state["fields"],
            "tnf_at_cell": {"TNF": 0.0},
            "field": field,
            "surface": surface,
            "emitter": {
                "_type": "step",
                "address": "local:RAMEmitter",
                "config": {"emit": {"tnf_at_cell": "map[float]", "global_time": "float"}},
                "inputs": {"tnf_at_cell": ["tnf_at_cell"], "global_time": ["global_time"]},
            },
        },
        "global_time_precision": 6,
    }
    case_dir = HERE / NAME
    case_dir.mkdir(exist_ok=True)
    (case_dir / "document.pbg").write_text(json.dumps(document) + "\n")
    case = {
        "description": (
            "The full composite's spatial layer (read from tnf_field_cell.composite.json): a TNF bolus (Gaussian, "
            "sigma0 5 um, 40 um from the cell) diffuses in a reflecting 200 x 200 um box (FVReactionDiffusion, dx 2 um, "
            "dt 0.05 s, D 100 um^2/s), and RegionMean reads it on the cell's surface ring (9 <= r < 11 um). Against the "
            "exact solution (the free Gaussian and its mirror images in the walls, sampled at the ring's nodes with "
            "RegionMean's weights) at 2, 4, 10, 30 and 60 s, with tolerances three times the measured first-order error "
            "in dt; at 990 s the field is uniform and the ring reads the box's mean, 10 Kd, to rel 1e-9 (mass is "
            "conserved). Generated by checks/spatial/make_region_mean_bolus.py."),
        "scale_level": "abstract",
        "document": "document.pbg",
        "interval": float(END),
        "expect": [{"kind": "rows", "emitter": "emitter", "min": END + 1}, *expect],
    }
    (case_dir / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote {NAME}: {len(expect)} expectations; peak oracle {max(e['expected'] for e in expect) / c_mean:.2f} x mean")


if __name__ == "__main__":
    main()
