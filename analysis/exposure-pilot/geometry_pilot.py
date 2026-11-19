"""The exposure studies' geometry pilot: TNF at cells 100, 300 and 1000 µm from a bolus in a box BOX_UM across.

For each configuration (dx, dt, with or without the absorbing edge band), FVReactionDiffusion (viva-pde-particle
25e8a05) runs a Gaussian bolus (σ0 5 µm, as the MVP's) at the box centre for HOURS. Every 30 s (the coupling interval)
it reads the volume-weighted mean over each cell's ring (9 ≤ |x - cell| < 11 µm, the MVP's surface), as RegionMean
does. Reference: the free-space solution c(r, t) = M / (4πD(t + t0)) · exp(-r² / (4D(t + t0))), with σ0² = 2Dt0,
averaged over the same ring nodes. The band is a local uptake term (`external_conc` mask) on the nodes within W of the
walls, rising linearly from 0 at its inner edge to K at the wall.

Reported per cell: the peak (relative to free space), its time, the half-rise arrival time, and the 0-HOURS integral
(relative to free space over the same window), plus the late plateau (the last sample, as a fraction of the peak).

usage: BOX_UM=3000 uv run --project compose --frozen python -I analysis/exposure-pilot/geometry_pilot.py DX DT BAND HOURS OUT.json

geometry_pilot.json collects the configurations run on 2026-11-19 (each one this script's output, unedited):
BOX_UM 3000 at (dx 10, dt 0.25, band), (dx 10, dt 0.25, closed), (dx 10, dt 0.05, band), (dx 5, dt 0.25, band), and
BOX_UM 6000 at (dx 10, dt 0.25, band); all 3 h. It chose the exposure studies' grid and box
(docs/design/plan-exposure-studies.md, finding 4 and E1b).
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from process_bigraph import allocate_core
from viva_pde_particle.processes.fv_reaction_diffusion import FVReactionDiffusion

dx, dt, band, hours, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3] == "1", float(sys.argv[4]), sys.argv[5]
D, L, SIGMA0, M = 100.0, float(os.environ.get("BOX_UM", "3000")), 5.0, 1.0
W, K = 150.0, 0.05  # band width (µm) and wall rate (1/s): diffusion length sqrt(D/K) ≈ 45 µm, K·dt ≪ 1
CELLS = (100.0, 300.0, 1000.0)
n = round(L / dx) + 1
x = np.linspace(-L / 2, L / 2, n)
X, Y = np.meshgrid(x, x, indexing="ij")
grid = {"origin": [-L / 2, -L / 2], "size": [L, L], "num": [n, n]}
cv = np.full((n, n), dx * dx)  # control volumes: halved on edges, quartered at corners
cv[0, :] /= 2; cv[-1, :] /= 2; cv[:, 0] /= 2; cv[:, -1] /= 2

edge = np.minimum.reduce([X + L / 2, L / 2 - X, Y + L / 2, L / 2 - Y])  # distance to the nearest wall
ramp = np.clip((W - edge) / W, 0.0, 1.0)  # 0 inside, 1 at the wall
terms = [{"species": "TNF", "coeff": -1.0, "k": K, "reactants": {"TNF": 1, "BAND": 1}}] if band else []
proc = FVReactionDiffusion({"grid": grid, "pde": {"species": {"TNF": {"diffusion": D}}, "terms": terms,
                                                 "external_species": ["BAND"] if band else []}, "dt": dt},
                           core=allocate_core())
ext = {"BAND": ramp} if band else {}

t0 = SIGMA0 ** 2 / (2 * D)
field = M / (4 * np.pi * D * t0) * np.exp(-(X ** 2 + Y ** 2) / (4 * D * t0))
field *= M / float((field * cv).sum())  # an unresolved bolus (σ0 < dx) still carries exactly M
rings = []
for r in CELLS:
    d = np.hypot(X - r, Y)
    mask = (d >= 9.0) & (d < 11.0)
    if not mask.any():
        raise SystemExit(f"dx {dx}: no node in the ring at {r} µm")
    rings.append((mask, np.hypot(X[mask], Y[mask])))

def free(rr, t):
    return M / (4 * np.pi * D * (t + t0)) * np.exp(-rr ** 2 / (4 * D * (t + t0)))

samples, ref, times = [[] for _ in CELLS], [[] for _ in CELLS], []
start, t, steps_per_sample = time.monotonic(), 0.0, round(30.0 / dt)
while t < hours * 3600 - 1e-9:
    for _ in range(steps_per_sample):
        field = proc.step({"TNF": field}, ext)["TNF"]
    t += steps_per_sample * dt
    times.append(t)
    for i, (mask, rr) in enumerate(rings):
        w = cv[mask]
        samples[i].append(float((field[mask] * w).sum() / w.sum()))
        ref[i].append(float((free(rr, t) * w).sum() / w.sum()))

result = {"box_um": L, "dx": dx, "dt": dt, "band": band, "hours": hours, "nodes": n * n,
          "wall_s": round(time.monotonic() - start, 1), "cells": []}
for r, s, f in zip(CELLS, samples, ref):
    s, f = np.array(s), np.array(f)
    i, j = int(s.argmax()), int(f.argmax())
    half = next(times[k] for k in range(len(s)) if s[k] >= s[i] / 2)
    result["cells"].append({
        "r_um": r, "peak_rel_free": round(s[i] / f[j], 4), "peak_time_s": times[i], "free_peak_time_s": times[j],
        "half_rise_s": half, "integral_rel_free": round(float(s.sum() / f.sum()), 4),
        "last_over_peak": round(float(s[-1] / s[i]), 4),
    })
Path(out).write_text(json.dumps(result, indent=1))
print(json.dumps(result))
