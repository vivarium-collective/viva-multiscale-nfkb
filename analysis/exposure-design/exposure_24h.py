"""What each cell of the distance study is exposed to over 24 h, per unit of bolus, with and without the absorbing band.

The field is decision 39's: a 6 mm box, dx 10 um, dt 0.25 s, D 100 um^2/s. A Gaussian bolus (sigma0 5 um) of unit mass
(1 uM um^2) sits at the centre. With the band, a local decay term rises to 0.05 /s over the 150 um next to each wall.
Every 30 s (the coupling interval) the script records the TNF at each cell's surface ring (9 <= d < 11 um around
points 100, 300 and 1000 um from the bolus), as RegionMean averages it, and the open-medium (free-space) value there.

The field is linear in the bolus, so a bolus of mass M gives M times these series. They size the studies' pulses
(decision 42) and the dose study's decaying baths (decisions 43 and 50), and they show what the band does over a day:
in a closed box the TNF that reaches the walls stays and spreads back, so every cell ends near the box's mean, 1/A.

    uv run --project compose --frozen python -I analysis/exposure-design/exposure_24h.py BAND(0|1)   # writes exposure_24h_band<B>.json
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from process_bigraph import allocate_core
from viva_pde_particle.processes.fv_reaction_diffusion import FVReactionDiffusion

HERE = Path(__file__).resolve().parent
L, DX, D, DT, STEP, HOURS = 6000.0, 10.0, 100.0, 0.25, 30.0, 24.0
SIGMA0, BAND_WIDTH, BAND_RATE = 5.0, 150.0, 0.05
CELLS = {"near": 100.0, "middle": 300.0, "far": 1000.0}


def main(band: bool) -> None:
    n = round(L / DX) + 1
    x = -L / 2 + np.arange(n) * DX
    X, Y = np.meshgrid(x, x)
    cv = np.full((n, n), DX * DX)
    cv[0, :] /= 2; cv[-1, :] /= 2; cv[:, 0] /= 2; cv[:, -1] /= 2
    t0 = SIGMA0 ** 2 / (2 * D)
    field = np.exp(-(X ** 2 + Y ** 2) / (4 * D * t0))
    field /= float((field * cv).sum())  # unit mass, exactly, though the bolus is narrower than dx
    edge = np.minimum.reduce([X + L / 2, L / 2 - X, Y + L / 2, L / 2 - Y])
    ext = {"BAND": np.clip((BAND_WIDTH - edge) / BAND_WIDTH, 0.0, 1.0)} if band else {}
    terms = [{"species": "TNF", "coeff": -1.0, "k": BAND_RATE, "reactants": {"TNF": 1, "BAND": 1}}] if band else []
    proc = FVReactionDiffusion({"grid": {"origin": [-L / 2, -L / 2], "size": [L, L], "num": [n, n]},
                                "pde": {"species": {"TNF": {"diffusion": D}}, "terms": terms,
                                        "external_species": ["BAND"] if band else []}, "dt": DT}, core=allocate_core())
    rings = {}
    for name, r in CELLS.items():
        d = np.hypot(X - r, Y)
        mask = (d >= 9.0) & (d < 11.0)
        rings[name] = (mask, np.hypot(X[mask], Y[mask]))
    series = {name: [] for name in CELLS}
    free = {name: [] for name in CELLS}
    times, mass = [], []
    start, steps = time.monotonic(), round(STEP / DT)
    for k in range(1, round(HOURS * 3600 / STEP) + 1):
        for _ in range(steps):
            field = proc.step({"TNF": field}, ext)["TNF"]
        t = k * STEP
        times.append(t)
        mass.append(float((field * cv).sum()))
        for name, (mask, rr) in rings.items():
            series[name].append(float(field[mask].mean()))
            free[name].append(float(np.mean(np.exp(-rr ** 2 / (4 * D * (t + t0))) / (4 * np.pi * D * (t + t0)))))
    out = {"band": band, "box_um": L, "dx_um": DX, "dt_s": DT, "D_um2_per_s": D, "bolus_mass": 1.0,
           "sample_s": STEP, "wall_s": round(time.monotonic() - start), "box_mean_closed": 1.0 / (L * L),
           "cells_um": CELLS, "time_s": times, "mass": mass, "tnf_at_cell": series, "free_space": free}
    (HERE / f"exposure_24h_band{int(band)}.json").write_text(json.dumps(out) + "\n")
    print(f"band={band}: wrote {len(times)} samples in {out['wall_s']} s; mass left {mass[-1]:.3f}")


if __name__ == "__main__":
    main(sys.argv[1] == "1")
