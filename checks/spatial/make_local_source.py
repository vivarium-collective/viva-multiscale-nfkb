"""Generate `spatial/local-source`: a TNF source confined to a small patch of the grid, through a full Composite.

`FVReactionDiffusion`'s reaction terms are mass action over any species, and the species in its `external_conc` input
are arrays over the grid. So a mask species (1 on a patch, 0 elsewhere) makes a term local: a source here, or uptake
by a cell (decision 8b). This check runs one such source, with first-order decay, through process-bigraph as the
studies would. The mask is seeded in its own store and wired into the field's `external_conc` port.

The oracle is the field's total mass, an exact property of the scheme.
- Each step adds dt·(s·A − λ·M), where M = Σᵢ Vᵢ·cᵢ and A = Σ Vᵢ over the patch. Diffusion moves mass but conserves
  it, and the reaction step is explicit.
- So after n steps, M_n = (s·A/λ)·(1 − (1 − λ·dt)ⁿ).
- `RegionTotal` over the whole grid reports M × 602.214076 molecules (Avogadro × 1e-21), checked every 10 s to 60 s, rel 1e-9.
- The volumes Vᵢ come from the grid's geometry (`CartesianGrid.element_volumes`), not from the scheme under test.

A mask that was ignored would give s × the whole box's area, about 1,000 times A. An unseeded or unwired mask is
silently zero (`fv_reaction_diffusion.py` fills a missing external species with zeros). `--negative {unseeded,
unwired}` writes `local-source-negative` with that mutation and the same expectations; it must fail.

    uv run --project compose python -I checks/spatial/make_local_source.py [--negative NAME]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from viva_pde_particle.grid import CartesianGrid

HERE = Path(__file__).resolve().parent
GRID = {"origin": [-100.0, -100.0], "size": [200.0, 200.0], "num": [101, 101]}  # the MVP's grid, dx 2 um
D, DT, STEP, END = 100.0, 0.05, 1.0, 60.0  # D: decision 33; dt: decision 34
S, LAMBDA = 0.01, 0.01  # source rate on the patch (uM/s) and decay rate (1/s), round numbers for the check
PATCH = (40.0, 0.0, 2.0)  # centre x, y and half-width (um): a 3 x 3-node patch away from the centre
CHECK_ROWS = (10, 20, 30, 40, 50, 60)  # row k is t = k s
MOLECULES_PER_UM3_PER_UM = 602.214076  # molecules per µM·µm³: Avogadro 6.02214076e23 (exact, SI 2019) × 1e-21
NEGATIVES = ("unseeded", "unwired")


def patch_mask() -> np.ndarray:
    x = GRID["origin"][0] + np.arange(GRID["num"][0]) * GRID["size"][0] / (GRID["num"][0] - 1)
    y = GRID["origin"][1] + np.arange(GRID["num"][1]) * GRID["size"][1] / (GRID["num"][1] - 1)
    X, Y = np.meshgrid(x, y)  # (ny, nx), the engine's order
    cx, cy, half = PATCH
    return (np.abs(X - cx) <= half) & (np.abs(Y - cy) <= half)


def document(mask: np.ndarray, negative: str | None) -> dict:
    shape = mask.shape
    pde_inputs = {"fields": ["fields"], "external_conc": ["external"]}
    if negative == "unwired":
        del pde_inputs["external_conc"]
    return {"state": {
        "fields": {"TNF": np.zeros(shape).tolist()},
        "external": {} if negative == "unseeded" else {"SRC": mask.astype(float).tolist()},
        "pde": {
            "_type": "process",
            "address": "local:viva_pde_particle.processes.fv_reaction_diffusion.FVReactionDiffusion",
            "config": {"grid": GRID, "dt": DT, "pde": {
                "species": {"TNF": {"diffusion": D}},
                "terms": [{"species": "TNF", "coeff": 1.0, "k": S, "reactants": {"SRC": 1}},
                          {"species": "TNF", "coeff": -1.0, "k": LAMBDA, "reactants": {"TNF": 1}}],
                "external_species": ["SRC"]}},
            "interval": STEP,
            "inputs": pde_inputs,
            "outputs": {"fields": ["fields"]},
        },
        "total": {"TNF": 0.0},
        "whole_box": {
            "_type": "step",
            "address": "local:viva_pde_particle.steps.transfer.RegionTotal",
            "config": {"grid": GRID, "species": ["TNF"], "region": {"mask": np.ones(shape, dtype=bool).tolist()}},
            "inputs": {"fields": ["fields"]},
            "outputs": {"molecules": ["total"]},
        },
        "emitter": {
            "_type": "step",
            "address": "local:RAMEmitter",
            "config": {"emit": {"total": "map[float]", "global_time": "float"}},
            "inputs": {"total": ["total"], "global_time": ["global_time"]},
        },
    }}


def expected_molecules(mask: np.ndarray, seconds: float) -> float:
    volumes = np.asarray(CartesianGrid.from_config(GRID).element_volumes, dtype=float).reshape(mask.shape)
    area = float(volumes[mask].sum())
    n = round(seconds / DT)
    return S * area / LAMBDA * (1.0 - (1.0 - LAMBDA * DT) ** n) * MOLECULES_PER_UM3_PER_UM


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", choices=NEGATIVES, help="write a mutated copy that must fail")
    args = parser.parse_args()
    mask = patch_mask()
    if int(mask.sum()) != 9:
        raise SystemExit(f"the patch selects {int(mask.sum())} nodes, not 3 x 3")
    expect = [{"kind": "rows", "emitter": "emitter", "min": int(END / STEP) + 1}] + [
        {"kind": "scalar", "emitter": "emitter", "field": "total.TNF", "row": row,
         "expected": expected_molecules(mask, row * STEP), "rel": 1.0e-9, "abs": 1.0e-12}
        for row in CHECK_ROWS]
    name = "local-source" + ("-negative" if args.negative else "")
    description = (
        f"NEGATIVE ({args.negative}): must fail. Delete after running." if args.negative else
        "A TNF source confined to a 3 x 3-node patch through FVReactionDiffusion's external_conc mask, with decay, "
        "through a full Composite (viva-pde-particle 25e8a05): the field's total mass from RegionTotal over the whole "
        "box equals the scheme's exact (s A / lambda)(1 - (1 - lambda dt)^n) every 10 s to 60 s, rel 1e-9. An "
        "ignored mask would give about 1,000 times more; an unseeded or unwired one gives zero. Generated by "
        "checks/spatial/make_local_source.py.")
    case_dir = HERE / name
    case_dir.mkdir(exist_ok=True)
    (case_dir / "document.pbg").write_text(json.dumps(document(mask, args.negative)) + "\n")
    case = {"description": description, "scale_level": "abstract", "document": "document.pbg", "interval": END,
            "expect": expect}
    (case_dir / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote {name}: {len(expect)} expectations; at 60 s, {expect[-1]['expected']:.6g} molecules")


if __name__ == "__main__":
    main()
