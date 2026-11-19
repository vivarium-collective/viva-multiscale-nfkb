"""The exposure studies' dose pilot: how many cells survive 24 h of held, sub-saturating TNF, at three death clocks.

Each point is Study 1's population (Study 0's builder: one Lipniacki model shared by 200 independently seeded fate
networks, seeds 1-200, NF-kB intact, absorbing death, coupling every 30 s, 24 h), with the receptor occupancy held at
`occ` instead of 1: Lipniacki's TNF_R = occ, and the fate network's TNF node switches on at rate occ and off at 1 - occ,
as the field composite's dose-response maps occupancy. Each point records the fraction of cells alive at 24 h (no
death node ever on), the cells that reached no fate at all, and the median time of first death.

It chose the exposure studies' clocks and dose range (docs/design/plan-exposure-studies.md, finding 2).

    uv run --project compose --frozen python -I analysis/exposure-pilot/dose_pilot.py   # writes dose_pilot.json
"""

import importlib.util
import json
import math
import statistics
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
POPULATION = ROOT / "workspace/investigations/tnf-fate-in-space/studies/s0-coupling-calibration/population.py"
CLOCKS = (30, 60, 120)  # minutes per Calzone unit
OCCUPANCIES = (0.05, 0.2, 0.5, 1.0)
CELLS, SEED, HOURS, INTERVAL = 200, 1, 24.0, 30.0
KAPPA = math.log(2) / 337.0  # decision 25


def _population():
    spec = importlib.util.spec_from_file_location("population", POPULATION)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {POPULATION}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def point(minutes: int, occ: float) -> dict:
    pop = _population()
    doc = pop.build(KAPPA, 1.0 / (60.0 * minutes), CELLS, SEED, INTERVAL, (), 1.0, 0.0)
    state = doc["state"]
    state["stimulus"]["TNF_R"] = occ
    for cell in state["cells"].values():
        cell["fate"]["config"]["parameters"]["u_TNF"] = occ
        cell["fate"]["config"]["parameters"]["d_TNF"] = 1.0 - occ
    with tempfile.TemporaryDirectory() as tmp:
        rows = json.loads(pop.run(doc, HOURS, Path(tmp)).read_text())["emitter"][1:]
    cells = sorted(rows[0]["fate_codes"], key=lambda c: int(c[1:]))
    times = [r["global_time"] for r in rows]
    codes = [[round(r["fate_codes"][c]) for r in rows] for c in cells]
    dead = [any(x & 6 for x in s) for s in codes]
    deaths = [next(t for t, x in zip(times, s, strict=True) if x & 6) for s, d in zip(codes, dead, strict=True) if d]
    return {"minutes_per_unit": minutes, "occupancy": occ, "cells": len(cells),
            "alive": round(1 - sum(dead) / len(dead), 4), "no_fate": sum(not any(s) for s in codes),
            "median_first_death_min": statistics.median(deaths) / 60 if deaths else None}


def main() -> None:
    grid = [(m, o) for m in CLOCKS for o in OCCUPANCIES]
    with ProcessPoolExecutor(max_workers=4) as pool:
        points = list(pool.map(point, *zip(*grid, strict=True)))
    out = {"cells": CELLS, "seed": SEED, "hours": HOURS, "kappa": "ln2/337", "absorb_death": 1, "points": points}
    (HERE / "dose_pilot.json").write_text(json.dumps(out, indent=1) + "\n")
    for p in points:
        print(p, flush=True)


if __name__ == "__main__":
    sys.exit(main())
