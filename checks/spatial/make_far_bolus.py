"""Generate `spatial/far-bolus`: the exposure studies' geometry (decision 39) against the open-medium solution.

The field: FVReactionDiffusion in a 6 mm box, dx 10 um, dt 0.25 s, D 100 um^2/s, coupled every 30 s. A Gaussian bolus
(sigma0 5 um, mass M) sits at the centre. An absorbing band 150 um wide at the walls is a local decay term whose rate
rises linearly to K = 0.05 /s at the wall (an `external_conc` mask, decision 8b), so the medium behaves as open.
Three cells' surfaces are RegionMean rings, 9 <= d < 11 um around points 100, 300 and 1000 um from the bolus.

The oracle is the open-medium (free-space) solution, c(r, t) = M / (4 pi D (t + t0)) exp(-r^2 / (4 D (t + t0))) with
sigma0^2 = 2 D t0, averaged with plain numpy over each ring's nodes (all interior, equal weights). Each cell is sampled
from about half its peak time (r^2 / 8D) to 1 h: the near cell at 30 s to 1 h, the middle one from 120 s, the far one
from 1200 s (peaks at about 25 s, 4 min and 41 min). Before a cell's front arrives, the exact value is vanishingly small
(e^-83 at 1000 um after 30 s), so its relative error there tests nothing.

Each tolerance is three times the error measured at that point, with a floor of rel 1e-3. The generator measures it by
running the same field at the process level before it writes the case. The measured errors go into the case's
description.

`--negative {D50,ring110}` writes `far-bolus-negative` with the mutated document and the same expectations; it must
fail.
- D50 halves D.
- ring110 moves the near cell from 100 to 110 um.

The band itself is not tested here. It acts only once TNF reaches the walls, after about L^2 / 4D = 6 h in this box,
so within this check's hour a box without it gives the same values (tried: that copy passes). Its effect over a day is
measured in the 24 h exposure runs that size the studies' pulses (decision 42).

    uv run --project compose python -I checks/spatial/make_far_bolus.py [--negative NAME]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from process_bigraph import allocate_core
from viva_pde_particle.processes.fv_reaction_diffusion import FVReactionDiffusion

HERE = Path(__file__).resolve().parent
L, DX = 6000.0, 10.0
N = round(L / DX) + 1
GRID = {"origin": [-L / 2, -L / 2], "size": [L, L], "num": [N, N]}
D, DT, STEP = 100.0, 0.25, 30.0  # decisions 33, 39 and 35
SIGMA0, M = 5.0, 1.0e4  # bolus width (um) and mass (uM um^2): peaks of about 0.12, 0.013 and 0.0012 uM
BAND_WIDTH, BAND_RATE = 150.0, 0.05
CELLS = {"near": 100.0, "middle": 300.0, "far": 1000.0}
TIMES = {"near": (30, 60, 120, 240, 600, 1800, 3600), "middle": (120, 240, 600, 1200, 1800, 3600),
         "far": (1200, 1800, 2490, 3600)}
ALL_TIMES = sorted({t for times in TIMES.values() for t in times})
END = float(ALL_TIMES[-1])
NEGATIVES = ("D50", "ring110")


def axes() -> tuple[np.ndarray, np.ndarray]:
    x = GRID["origin"][0] + np.arange(N) * DX
    return np.meshgrid(x, x)  # (ny, nx), the engine's order; the grid is square


def control_volumes() -> np.ndarray:
    cv = np.full((N, N), DX * DX)
    cv[0, :] /= 2; cv[-1, :] /= 2; cv[:, 0] /= 2; cv[:, -1] /= 2
    return cv


def initial_field() -> np.ndarray:
    X, Y = axes()
    t0 = SIGMA0 ** 2 / (2 * D)
    field = np.exp(-(X ** 2 + Y ** 2) / (4 * D * t0))
    return field * (M / float((field * control_volumes()).sum()))  # unresolved (sigma0 < dx): carry exactly M


def band() -> np.ndarray:
    X, Y = axes()
    edge = np.minimum.reduce([X + L / 2, L / 2 - X, Y + L / 2, L / 2 - Y])
    return np.clip((BAND_WIDTH - edge) / BAND_WIDTH, 0.0, 1.0)


def ring(distance: float) -> np.ndarray:
    X, Y = axes()
    d = np.hypot(X - distance, Y)
    return (d >= 9.0) & (d < 11.0)


def pde(diffusion: float, with_band: bool) -> dict:
    terms = [{"species": "TNF", "coeff": -1.0, "k": BAND_RATE, "reactants": {"TNF": 1, "BAND": 1}}] if with_band else []
    return {"species": {"TNF": {"diffusion": diffusion}}, "terms": terms,
            "external_species": ["BAND"] if with_band else []}


def oracle(distance: float, t: float) -> float:
    X, Y = axes()
    mask = ring(distance)
    rr = np.hypot(X[mask], Y[mask])
    t0 = SIGMA0 ** 2 / (2 * D)
    return float(np.mean(M / (4 * np.pi * D * (t + t0)) * np.exp(-rr ** 2 / (4 * D * (t + t0)))))


def measure() -> dict[tuple[str, int], float]:
    """The scheme's relative error against the oracle at each cell and time, from a process-level run."""
    proc = FVReactionDiffusion({"grid": GRID, "pde": pde(D, True), "dt": DT}, core=allocate_core())
    field, ext, t, errors = initial_field(), {"BAND": band()}, 0.0, {}
    masks = {name: ring(r) for name, r in CELLS.items()}
    for target in ALL_TIMES:
        while t < target - 1e-9:
            field = proc.step({"TNF": field}, ext)["TNF"]
            t += DT
        for name, r in CELLS.items():
            if target in TIMES[name]:
                errors[(name, target)] = float(field[masks[name]].mean()) / oracle(r, target) - 1.0
    return errors


def document(negative: str | None) -> dict:
    with_band = negative != "noband"
    state = {
        "fields": {"TNF": initial_field().tolist()},
        "field": {
            "_type": "process",
            "address": "local:viva_pde_particle.processes.fv_reaction_diffusion.FVReactionDiffusion",
            "config": {"grid": GRID, "pde": pde(50.0 if negative == "D50" else D, with_band), "dt": DT},
            "interval": STEP,
            "inputs": {"fields": ["fields"], **({"external_conc": ["external"]} if with_band else {})},
            "outputs": {"fields": ["fields"]},
        },
        "emitter": {
            "_type": "step",
            "address": "local:RAMEmitter",
            "config": {"emit": {**{f"tnf_{name}": "map[float]" for name in CELLS}, "global_time": "float"}},
            "inputs": {**{f"tnf_{name}": [f"tnf_{name}"] for name in CELLS}, "global_time": ["global_time"]},
        },
    }
    if with_band:
        state["external"] = {"BAND": band().tolist()}
    for name, r in CELLS.items():
        placed = 110.0 if (negative == "ring110" and name == "near") else r
        state[f"tnf_{name}"] = {"TNF": 0.0}
        state[f"surface_{name}"] = {
            "_type": "step",
            "address": "local:viva_pde_particle.steps.transfer.RegionMean",
            "config": {"grid": GRID, "species": ["TNF"], "region": {"mask": ring(placed).astype(int).tolist()}},
            "inputs": {"fields": ["fields"]},
            "outputs": {"mean_conc": [f"tnf_{name}"]},
        }
    return {"state": state}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", choices=NEGATIVES, help="write a mutated copy that must fail")
    args = parser.parse_args()
    for name, r in CELLS.items():
        if int(ring(r).sum()) == 0:
            raise SystemExit(f"no grid node in the {name} cell's ring at dx {DX}")
    errors = measure()
    expect = [{"kind": "rows", "emitter": "emitter", "min": int(END / STEP) + 1}]
    for name, r in CELLS.items():
        for t in TIMES[name]:
            tol = max(3.0 * abs(errors[(name, t)]), 1.0e-3)
            expect.append({"kind": "scalar", "emitter": "emitter", "field": f"tnf_{name}.TNF", "row": int(t / STEP),
                           "expected": oracle(r, t), "rel": round(tol, 6), "abs": 1.0e-15})
    worst = {name: max(abs(errors[(name, t)]) for t in TIMES[name]) for name in CELLS}
    for (name, t), err in sorted(errors.items(), key=lambda kv: (CELLS[kv[0][0]], kv[0][1])):
        print(f"  {name:6} t={t:5d}s  error {err:+.2e}")
    measured = ", ".join(f"{name} ({CELLS[name]:.0f} um) {worst[name]:.2e}" for name in CELLS)
    case_name = "far-bolus" + ("-negative" if args.negative else "")
    description = (
        f"NEGATIVE ({args.negative}): must fail. Delete after running." if args.negative else
        "The exposure studies' geometry (decision 39): a TNF bolus at the centre of a 6 mm box with an absorbing edge "
        "band, dx 10 um, dt 0.25 s, coupled every 30 s, through a full Composite (viva-pde-particle 25e8a05). TNF at "
        "three cells' surface rings (RegionMean, 100, 300 and 1000 um from the bolus) matches the open-medium "
        "solution from about half of each cell's peak time to 1 h, within three times the measured error (floor rel "
        "1e-3). Largest measured errors: "
        f"{measured}. Generated by checks/spatial/make_far_bolus.py.")
    case_dir = HERE / case_name
    case_dir.mkdir(exist_ok=True)
    (case_dir / "document.pbg").write_text(json.dumps(document(args.negative), separators=(",", ":")) + "\n")
    case = {"description": description, "scale_level": "abstract", "document": "document.pbg", "interval": END,
            "expect": expect}
    (case_dir / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    size = (case_dir / "document.pbg").stat().st_size / 1e6
    print(f"wrote {case_name}: {len(expect)} expectations, document {size:.1f} MB; worst errors {measured}")


if __name__ == "__main__":
    main()
