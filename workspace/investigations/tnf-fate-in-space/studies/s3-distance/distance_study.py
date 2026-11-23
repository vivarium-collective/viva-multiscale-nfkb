"""The distance study (s3-distance): how cell fate depends on distance from a TNF bolus in an open medium, at three
death clocks, with NF-kB intact and knocked out.

Cells sit 100, 300 and 1000 um (near, middle, far) from a bolus of 1, 10 or 100 uM um^2 (decision 51) in decision 39's
field: a 6 mm box, D 100 um^2/s, an absorbing band at the walls. Cells only sample the field and never change it, so
each cell population is driven by the TNF its ring of surface nodes records in one 24 h run of that field
(analysis/exposure-design/exposure_24h.py, `exposure_24h_band1.json`), scaled by the bolus, since the field is linear in
it (decision 59). Replaying it is exact: the coupling samples the field every 30 s and holds the value, and the replay
holds the same samples. Building one composite of the field and 4,860 cells is roughly quadratic in its processes
(measured, 2026-11-20), so the field is run once and replayed.

Each point (ring, bolus size, clock, arm) is the dose study's population with the replayed TNF in place of a bath, so
E4 compares the two with nothing else different but the seeds (decision 57): Study 1's population (Study 0's builder, one Lipniacki model shared by
270 fate networks, absorbing death, coupling every 30 s, 24 h), every TNF node off at the start (decision 49), clocks
30, 60 and 120 min per unit (38), NF-kB intact (kappa = ln 2 / 337 s) and knocked out (kappa = 0) (52), 7 batches of
270 cells seeded from 1891 (40b, 57: disjoint from the dose study's 1 to 1890). One TimeSeriesStep
(viva-basic-processes) reads the kinetic time and writes, from the replayed TNF c at that instant, Lipniacki's TNF_R =
occ and the TNF node's rates u = occ and d = 1 - occ, with occ = c / (c + Kd) (Kd 19 pM, decision 32), as the field
composite's dose-response Step does.

Batch k writes parquet-runs/<arm>-<min>min-ring-<ring>-M<bolus>/batch<k>.parquet (as the dose study's: time, NF-kB's
nuclear fraction, each cell's fate code every 30 s); a batch already run is read back, not rerun, and each point's
NF-kB is checked against a fresh run of its exposure with one fate network. data/distance.json gets the seeds and,
per point, arm, minutes_per_unit, ring, bolus, cells and alive_cells (what s2-dose/e4_verdict.py scores), with the
survival curve and death modes.

    uv run --frozen --extra simulators python -I \\
        workspace/investigations/tnf-fate-in-space/studies/s3-distance/distance_study.py \\
        [--workers N] [--write-only DIR]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from viva_multiscale_nfkb.composites.make_tnf_field_cell import KD  # uM, decision 32

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
POPULATION = HERE.parent / "s0-coupling-calibration" / "population.py"
FIELD = ROOT / "analysis" / "exposure-design" / "exposure_24h_band1.json"
RINGS = ("near", "middle", "far")
BOLUS_SIZES = (1.0, 10.0, 100.0)  # uM um^2, decision 51
CLOCKS = (30, 60, 120)  # min per unit, decision 38
KAPPA = {"intact": math.log(2) / 337.0, "knocked_out": 0.0}  # decisions 25 and 52
CELLS, BATCHES, SEED, HOURS, INTERVAL = 270, 7, 1891, 24.0, 30.0  # decisions 40b, 41 and 57


def _population():
    spec = importlib.util.spec_from_file_location("population", POPULATION)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {POPULATION}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exposure_name(ring: str, bolus: float) -> str:
    return f"ring-{ring}-M{bolus:g}"


def point_name(arm: str, minutes: int, ring: str, bolus: float) -> str:
    return f"{arm}-{minutes}min-{exposure_name(ring, bolus)}"


def replayed(ring: str, bolus: float) -> tuple[list[float], list[float]]:
    """The TNF at the ring's surface at every coupling instant 0, 30, ..., 86400 s: none at t = 0, then the field run's
    samples (per unit bolus) times the bolus."""
    field = json.loads(FIELD.read_text())
    times, instants = field["time_s"], round(HOURS * 3600.0 / INTERVAL)
    if (not field["band"] or field["sample_s"] != INTERVAL or times != [INTERVAL * k for k in range(1, instants + 1)]
            or len(field["tnf_at_cell"][ring]) != instants):
        # a short series would leave TimeSeriesStep holding its last value for the rest of the run
        raise SystemExit(f"{FIELD} is not the banded field sampled every {INTERVAL} s from {INTERVAL} s to {HOURS} h")
    return [0.0, *field["time_s"]], [0.0, *(bolus * c for c in field["tnf_at_cell"][ring])]


def document(arm: str, minutes: int, ring: str, bolus: float, batch: int, cells: int = CELLS) -> dict:
    """One batch of one point: Study 1's population driven by its ring's replayed TNF, every TNF node off at t = 0."""
    times, tnf = replayed(ring, bolus)
    occ = [c / (c + KD) for c in tnf]
    doc = _population().build(KAPPA[arm], 1.0 / (60.0 * minutes), cells, SEED + (batch - 1) * CELLS, INTERVAL, (),
                              1.0, 0.0)
    state = doc["state"]
    for cell in state["cells"].values():
        # as the dose study does: the process starts from the stores; initial_state only seeds a new one
        del cell["fate"]["config"]["initial_state"]["TNF"]
        cell["node_state"]["TNF"] = 0.0
        cell["node_probabilities"]["TNF"] = 0.0
        cell["fate"]["config"]["parameters"].update({"u_TNF": occ[0], "d_TNF": 1.0 - occ[0]})
    # every key the Step writes is seeded with its value at t = 0 (process-bigraph 1.9.1 drops a write to a key the
    # store lacks); the shared parameters store wins over each fate network's own
    state["stimulus"]["TNF_R"] = occ[0]
    state["parameters"].update({"u_TNF": occ[0], "d_TNF": 1.0 - occ[0]})
    state["tnf_at_cell"] = {"TNF": tnf[0]}
    state["replay"] = {
        "_type": "step",
        "address": "local:viva_basic_processes.time_series.TimeSeriesStep",
        "config": {"times": times, "values": {"c": tnf, "occ": occ, "u_TNF": occ, "d_TNF": [1.0 - o for o in occ]}},
        # kinetic_time: it runs on each kinetic update, every coupling interval, as the dose study's bath does
        "inputs": {"time": ["kinetic_time"]},
        "outputs": {"c": ["tnf_at_cell", "TNF"], "occ": ["stimulus", "TNF_R"], "u_TNF": ["parameters", "u_TNF"],
                    "d_TNF": ["parameters", "d_TNF"]},
    }
    return doc


def points() -> list[tuple[str, int, str, float]]:
    return [(arm, m, ring, bolus) for arm in KAPPA for m in CLOCKS for ring in RINGS for bolus in BOLUS_SIZES]


def run_point(arm: str, minutes: int, ring: str, bolus: float, batch: int) -> Path:
    """Run one batch of one point unless it exists; return its path."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    out = HERE / "parquet-runs" / point_name(arm, minutes, ring, bolus) / f"batch{batch}.parquet"
    if out.exists():
        return out
    with tempfile.TemporaryDirectory() as tmp:
        result = _population().run(document(arm, minutes, ring, bolus, batch), HOURS, Path(tmp))
        rows = json.loads(result.read_text())["emitter"][1:]  # row 0: t = 0, nothing written
    cells = sorted(rows[0]["fate_codes"], key=lambda c: int(c[1:]))
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_suffix(".partial")  # renamed only when complete, so an interrupted write is never read back
    pq.write_table(pa.table({"time_s": [r["global_time"] for r in rows],
                             "nfkb_fraction": [r["nfkb_fraction"] for r in rows],
                             **{f"code_{c}": [round(r["fate_codes"][c]) for r in rows] for c in cells}}), partial)
    partial.replace(out)
    return out


def nfkb_trajectory(arm: str, minutes: int, ring: str, bolus: float) -> tuple[list[float], list[float]]:
    """NF-kB's nuclear fraction every 30 s in this point's exposure, from a run with one fate network: NF-kB doesn't
    depend on the fate networks, so every batch of the point reproduces it exactly."""
    with tempfile.TemporaryDirectory() as tmp:
        result = _population().run(document(arm, minutes, ring, bolus, 1, cells=1), HOURS, Path(tmp))
        rows = json.loads(result.read_text())["emitter"][1:]
    return [r["global_time"] for r in rows], [r["nfkb_fraction"] for r in rows]


def summarize(arm: str, minutes: int, ring: str, bolus: float) -> dict:
    import pyarrow.parquet as pq

    name = point_name(arm, minutes, ring, bolus)
    tables = [pq.read_table(run_point(arm, minutes, ring, bolus, b)).to_pydict() for b in range(1, BATCHES + 1)]
    times, f = tables[0]["time_s"], tables[0]["nfkb_fraction"]
    if any(t["time_s"] != times or t["nfkb_fraction"] != f for t in tables):
        raise SystemExit(f"{name}: batches differ in time or NF-kB")
    if (times, f) != nfkb_trajectory(arm, minutes, ring, bolus):
        raise SystemExit(f"{name}: its batches' NF-kB is not this exposure's, so they were run with other settings; "
                         "move them aside and rerun the point")
    codes = [t[k] for t in tables for k in t if k.startswith("code_")]
    dead = [any(x & 6 for x in s) for s in codes]
    first_death = [next((t for t, x in zip(times, s, strict=True) if x & 6), None) for s in codes]
    deaths = sorted(t for t in first_death if t is not None)
    curve = [round(sum(1 for t in first_death if t is None or t > h * 3600) / len(codes), 4)
             for h in range(int(HOURS) + 1)]
    alive = len(codes) - sum(dead)
    return {"arm": arm, "minutes_per_unit": minutes, "ring": ring, "bolus": bolus, "cells": len(codes),
            "alive_cells": alive, "alive_24h": round(alive / len(codes), 4),
            "apoptosis_24h": round(sum(1 for s in codes if s[-1] & 2) / len(codes), 4),
            "necrosis_24h": round(sum(1 for s in codes if s[-1] & 4) / len(codes), 4),
            "median_first_death_min": deaths[len(deaths) // 2] / 60 if deaths else None,
            "survival_curve_hourly": curve}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4, help="simulations at once (the machine is shared)")
    parser.add_argument("--write-only", type=Path,
                        help="write every batch's archive (document and SBML model, for compose-api) here and stop")
    args = parser.parse_args()
    tasks = [(*p, b) for b in range(1, BATCHES + 1) for p in points()]  # batch by batch, so each finishes whole
    if args.write_only:
        population = _population()
        for arm, m, ring, bolus, b in tasks:
            archive = args.write_only / f"{point_name(arm, m, ring, bolus)}-batch{b}.omex"
            population.pack(document(arm, m, ring, bolus, b), archive)
        print(f"wrote {len(tasks)} archives to {args.write_only}")
        return
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run_point, *zip(*tasks, strict=True)))
    summary = [summarize(*p) for p in points()]
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "distance.json").write_text(json.dumps(
        {"cells": CELLS * BATCHES, "batches": BATCHES, "seeds": [SEED, SEED + CELLS * BATCHES - 1], "hours": HOURS,
         "interval_s": INTERVAL, "kd_uM": KD, "field": FIELD.name, "points": summary}, indent=1) + "\n")
    for p in summary:
        print(p["arm"], p["minutes_per_unit"], p["ring"], p["bolus"], p["alive_24h"], flush=True)


if __name__ == "__main__":
    sys.exit(main())
