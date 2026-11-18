"""Generate the bolus checks: TNF at the cell against the exact solution, and the occupancy the cell takes from it.

Both read tnf_field_cell.composite.json, so they check exactly what the composite runs.
- the field: FVReactionDiffusion, a 2-D reflecting box [-100, 100]^2 um, dx 2 um, dt 0.05 s, D 100 um^2/s;
- the cell's surface: RegionMean over the ring of nodes 9 <= r < 11 um around the origin;
- the bolus: a Gaussian, sigma0 5 um, 40 um from the cell, scaled so the box's mean is 10 Kd.
The generator asserts those values against the composite before it writes anything, so a wrong mask, D or bolus in
the composite cannot regenerate matching expectations.

The exact solution in a reflecting box is the free Gaussian (sigma^2 = sigma0^2 + 2 D t), summed over its mirror images
in each axis's walls. The oracle samples it at the ring's nodes and averages them with plain numpy weights, not
RegionMean. Every ring node is interior, so each weighs the same. The box's mean uses the control volumes: edges
weigh 1/2 and corners 1/4.

- **spatial/region-mean-bolus** (field and surface only): `tnf_at_cell` at 2, 4, 10, 30 and 60 s.
  - The tolerances are three times the error measured at dt 0.05 s (2026-11-18): -1.7% at 2 s, on the rising front;
    -0.45% at the 4 s peak (29 Kd); +0.17% at 10 s; +0.10% at 30 s; +1.1e-4 at 60 s.
  - The error is first order in dt and does not depend on dx: dx 2 and dx 1 agree to 5%.
  - At 990 s the field is uniform to e^-24. Mass is conserved exactly, so the ring reads the box's mean, 10 Kd, to rel
    1e-9.
- **coupled/bolus-occupancy** (the full composite): `tnf_occupancy.TNF_R` every 15 s from 15 to 990 s. It must be
  c/(c + Kd) of the TNF at the cell at the last coupling instant, 30 floor(t/30). This checks that the dose-response
  Step re-runs at every kinetic update (decision 35), which a flat field cannot show.
  - Before 30 s, c is the initial field's ring mean, which is exact, so the tolerance is rel 1e-9.
  - From 30 s on, c is the exact solution. Its error, 1.0e-3 at 30 s and at most 1.1e-4 from 60 s on, shrinks to
    (1 - occ) times that in occ. The tolerance is three times it.

`--negative {D50,ring15,untriggered}` writes `<case>-negative` with the mutated document and the same expectations.
It must fail; run it, then delete it.
- D50 halves D (region-mean-bolus).
- ring15 moves the surface ring out to 15-17 um (region-mean-bolus).
- untriggered removes `kinetic_time` from the dose-response Step (bolus-occupancy).

    uv run --project compose python -I checks/spatial/make_region_mean_bolus.py [--negative NAME]
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np
import yaml
from process_bigraph.composite_spec import CompositeSpec

HERE = Path(__file__).resolve().parent
CHECKS = HERE.parent
COMPOSITE = CHECKS.parent / "viva_multiscale_nfkb" / "composites" / "tnf_field_cell.composite.json"
X_BOLUS, SIGMA0, D, R_CELL, DX, HALF = 40.0, 5.0, 100.0, 9.0, 2.0, 100.0  # um, um^2/s: make_tnf_field_cell.py's
END = 990
COUPLING = 30
#: time (s) -> relative tolerance on tnf_at_cell: three times the error measured at dt 0.05 s
SPATIAL_ROWS = {2: 5.2e-2, 4: 1.4e-2, 10: 5.1e-3, 30: 3.0e-3, 60: 3.4e-4, END: 1e-9}
C_ERROR = {COUPLING: 1.0e-3}  # the exact solution's relative error at 30 s; at most 1.1e-4 from 60 s on
NEGATIVES = {"D50": "region-mean-bolus", "ring15": "region-mean-bolus", "untriggered": "bolus-occupancy"}


def images(u: np.ndarray, u0: float, low: float, length: float, s2: float) -> np.ndarray:
    """The 1-D Neumann heat kernel on [low, low + length]: the free Gaussian and its mirror images."""
    n_max = int(math.ceil(8 * math.sqrt(s2) / (2 * length))) + 2  # the next image adds less than e^-32
    total = np.zeros_like(u)
    for n in range(-n_max, n_max + 1):
        for centre in (u0 + 2 * n * length, 2 * low - u0 + 2 * n * length):
            total += np.exp(-((u - centre) ** 2) / (2 * s2))
    return total / math.sqrt(2 * math.pi * s2)


def fail(message: str) -> None:
    raise SystemExit(f"the composite is not what this oracle solves: {message}")


def write(group: str, name: str, description: str, scale: str, document: dict, expect: list[dict]) -> None:
    case_dir = CHECKS / group / name
    case_dir.mkdir(exist_ok=True)
    (case_dir / "document.pbg").write_text(json.dumps(document) + "\n")
    case = {"description": description, "scale_level": scale, "document": "document.pbg", "interval": float(END),
            "expect": [{"kind": "rows", "emitter": "emitter", "min": END + 1}, *expect]}
    (case_dir / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote {group}/{name}: {len(expect)} expectations")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", choices=sorted(NEGATIVES), help="write a mutated copy that must fail")
    args = parser.parse_args()
    spec = json.loads(COMPOSITE.read_text())
    state = spec["state"]
    field, surface = state["field"], state["surface"]
    grid = field["config"]["grid"]
    kd = spec["parameters"]["Kd"]["default"]
    n = int(2 * HALF / DX) + 1
    if grid != {"origin": [-HALF, -HALF], "size": [2 * HALF, 2 * HALF], "num": [n, n]}:
        fail(f"grid {grid}")
    if field["config"]["pde"]["species"]["TNF"]["diffusion"] != D or field["config"]["pde"]["terms"]:
        fail("D or the reaction terms")
    axis = -HALF + np.arange(n) * DX
    xx, yy = np.meshgrid(axis, axis)
    r = np.hypot(xx, yy)
    ring = (r >= R_CELL) & (r < R_CELL + DX)
    if not np.array_equal(np.asarray(surface["config"]["region"]["mask"], bool), ring):
        fail("the surface ring is not 9 <= r < 11 um")
    if ring[[0, -1], :].any() or ring[:, [0, -1]].any():
        fail("a ring node is on the boundary, where its weight is not 1")
    weights = np.ones((n, n))
    weights[[0, -1], :] *= 0.5
    weights[:, [0, -1]] *= 0.5
    initial = np.asarray(state["fields"]["TNF"])
    c_mean = float((weights * initial).sum() / weights.sum())
    shape = np.exp(-((xx - X_BOLUS) ** 2 + yy**2) / (2 * SIGMA0**2))
    if np.max(np.abs(initial - shape * initial.max())) > 1e-15 * initial.max() or not math.isclose(c_mean, 10 * kd):
        fail("the bolus is not the Gaussian at 40 um scaled to a 10 Kd mean")
    mass = c_mean * (2 * HALF) ** 2

    def at_cell(t: float) -> float:
        if t == 0:
            return float(initial[ring].mean())
        s2 = SIGMA0**2 + 2 * D * t
        return float((mass * images(xx, X_BOLUS, -HALF, 2 * HALF, s2) * images(yy, 0.0, -HALF, 2 * HALF, s2))[ring].mean())

    spatial = [{"kind": "scalar", "emitter": "emitter", "field": "tnf_at_cell.TNF", "row": t,
                "expected": at_cell(t), "rel": rel, "abs": 0.0} for t, rel in SPATIAL_ROWS.items()]
    if not math.isclose(spatial[-1]["expected"], c_mean, rel_tol=1e-12):
        fail(f"the exact solution at {END} s is not the box's mean")
    occupancy = []
    for t in range(15, END + 1, 15):
        sample = COUPLING * (t // COUPLING)
        c = at_cell(sample)
        occ = c / (c + kd)
        rel = 1e-9 if sample == 0 else 3 * (1 - occ) * C_ERROR.get(sample, 1.12e-4)
        occupancy.append({"kind": "scalar", "emitter": "emitter", "field": "tnf_occupancy.TNF_R", "row": t,
                          "expected": occ, "rel": rel, "abs": 0.0})

    spatial_doc = {"state": {
        "fields": state["fields"], "tnf_at_cell": {"TNF": 0.0}, "field": field, "surface": surface,
        "emitter": {"_type": "step", "address": "local:RAMEmitter",
                    "config": {"emit": {"tnf_at_cell": "map[float]", "global_time": "float"}},
                    "inputs": {"tnf_at_cell": ["tnf_at_cell"], "global_time": ["global_time"]}},
    }, "global_time_precision": 6}
    full_doc = CompositeSpec.from_file(str(COMPOSITE)).to_document()
    if args.negative:
        target = NEGATIVES[args.negative]
        doc = copy.deepcopy(spatial_doc if target == "region-mean-bolus" else full_doc)
        s = doc["state"]
        if args.negative == "D50":
            s["field"]["config"]["pde"]["species"]["TNF"]["diffusion"] = D / 2
        elif args.negative == "ring15":
            s["surface"]["config"]["region"]["mask"] = ((r >= 15) & (r < 17)).tolist()
        else:
            dr = s["dose_response"]
            dr["inputs"].pop("kinetic_time")
            dr["outputs"].pop("occ_time")
            dr["config"]["expressions"] = [e for e in dr["config"]["expressions"] if e["out"] != "occ_time"]
        group = "spatial" if target == "region-mean-bolus" else "coupled"
        write(group, f"{target}-negative", f"NEGATIVE ({args.negative}): must fail. Delete after running.",
              "abstract", doc, spatial if target == "region-mean-bolus" else occupancy)
        return
    write("spatial", "region-mean-bolus", (
        "The full composite's spatial layer (read from tnf_field_cell.composite.json): a TNF bolus (Gaussian, sigma0 "
        "5 um, 40 um from the cell) diffuses in a reflecting 200 x 200 um box (FVReactionDiffusion, dx 2 um, dt 0.05 s, "
        "D 100 um^2/s), and RegionMean reads it on the cell's surface ring (9 <= r < 11 um). Against the exact solution "
        "(the free Gaussian and its mirror images in the walls, averaged over the ring's nodes with numpy) at 2, 4, 10, "
        "30 and 60 s, with tolerances three times the measured first-order error in dt; at 990 s the field is uniform "
        "and the ring reads the box's mean, 10 Kd, to rel 1e-9 (mass is conserved). Generated by "
        "checks/spatial/make_region_mean_bolus.py."), "abstract", spatial_doc, spatial)
    write("coupled", "bolus-occupancy", (
        "The full composite (tnf_field_cell.composite.json, its defaults) with its TNF bolus: the occupancy the cell "
        "takes, every 15 s, is c / (c + Kd) of the TNF at the cell at the last coupling instant (30 s steps), with c "
        "the exact solution of region-mean-bolus (the initial field's ring mean before 30 s). So the dose-response Step "
        "re-runs at every kinetic update (decision 35). Tolerances: rel 1e-9 before 30 s; three times the exact "
        "solution's error times (1 - occ) after. Generated by checks/spatial/make_region_mean_bolus.py."),
        "cell", full_doc, occupancy)


if __name__ == "__main__":
    main()
