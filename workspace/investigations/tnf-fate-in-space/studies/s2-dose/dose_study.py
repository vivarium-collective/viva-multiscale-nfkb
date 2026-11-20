"""The dose study (s2-dose): how cell fate depends on a uniform TNF bath, held or decaying, at three death clocks.

Each point is Study 1's population (Study 0's builder: one Lipniacki model shared by fate networks seeded 1..CELLS,
absorbing death, coupling every 30 s, 24 h) in a uniform bath applied at t = 0 to cells at rest:
- a held bath keeps the receptor occupancy at `occ`: Lipniacki's TNF_R = occ, and each fate network's TNF node
  switches on at rate occ and off at 1 - occ, as the field composite's dose-response maps it;
- a decaying bath has TNF c(t) = c0 exp(-lambda t). One Step turns it into occupancy, c / (c + Kd), at every kinetic
  update and writes TNF_R and the TNF node's rates, as the field composite's dose-response Step does with the TNF at
  the cell. Each matches one distance-study cell and bolus size: the same peak TNF and the same sensed dose, the
  occupancy-time the coupling delivers over 24 h (analysis/exposure-design/ring_exposure.json), so E4 compares the
  two directly and only the timing and shape of the TNF differ (decisions 50 and 56).
Every TNF node starts off, as in the field composite. MaBoSSProcess starts from the node_state store, so the store is
what is set (Study 1's builder seeds it with TNF on, which would give every cell a TNF pulse of about one clock unit
whatever the dose; decision 49). Both arms: NF-kB intact (kappa = ln 2 / 337 s, decision 25) and knocked out
(kappa = 0, the NF-kB node never on).

Decisions: clocks 30, 60 and 120 min per unit (38); about 1,700 cells per point (40b), run as 7 batches of 270
seeds, 1,890 cells; the readout is the fraction alive at 24 h, with the survival curve and death modes (41); held
baths from occupancy 0.005 up, denser below 0.2 (43); decaying baths matched to the distance study's cells by sensed
dose (50, 56).

Batch k holds the cells seeded 270 (k - 1) + 1 to 270 k. It writes
parquet-runs/<arm>-<min>min-<exposure>/batch<k>.parquet (time, NF-kB's nuclear fraction, and each cell's fate code
every 30 s: Survival + 2 Apoptosis + 4 NonACD; columns code_c0 to code_c269 in seed order), where <exposure> is
occ<occ> or bath-<cell>-M<bolus>. NF-kB's trajectory is deterministic and depends only on the bath (the fate networks
don't feed back), so it is the same in every batch. A batch already run is read back, not rerun; the summary checks
each point's NF-kB against a fresh run of its bath with one fate network, so a batch run with other bath settings is
never read back silently. data/dose.json gets, per point, over all batches: alive at 24 h (as a count and a
fraction), cells with no fate, apoptosis and necrosis at 24 h, the median first-death time, the survival curve
(fraction alive at each hour), and NF-kB's first nuclear peak (height, time).

    uv run --frozen --extra simulators python -I \
        workspace/investigations/tnf-fate-in-space/studies/s2-dose/dose_study.py [--workers N]

(the workspace environment, for pyarrow; each simulation runs in compose/ through population.run, as Study 1 did)
"""

import argparse
import importlib.util
import json
import math
import statistics
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from viva_multiscale_nfkb.composites.make_tnf_field_cell import KD  # uM, decision 32

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
POPULATION = HERE.parent / "s0-coupling-calibration" / "population.py"
RING_EXPOSURE = ROOT / "analysis" / "exposure-design" / "ring_exposure.json"
CLOCKS = (30, 60, 120)
OCCUPANCIES = (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0)
KAPPA = {"intact": math.log(2) / 337.0, "knocked_out": 0.0}
CELLS, BATCHES, SEED, HOURS, INTERVAL = 270, 7, 1, 24.0, 30.0  # CELLS per batch


def _population():
    spec = importlib.util.spec_from_file_location("population", POPULATION)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {POPULATION}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exposures() -> dict[str, dict]:
    """Every bath by name: held ({"occupancy"}) or decaying ({"c0_uM", "decay_per_s"}, matched to a distance cell)."""
    held = {f"occ{o:g}": {"occupancy": o} for o in OCCUPANCIES}
    rings = json.loads(RING_EXPOSURE.read_text())
    if rings["kd_uM"] != KD:
        raise SystemExit(f"{RING_EXPOSURE} was computed with Kd {rings['kd_uM']}, not the composite's {KD}")
    # lambda gives the bath the ring cell's sensed dose (decision 56); ring_exposure.py solves it
    decaying = {f"bath-{r['cell']}-M{r['bolus']:g}": {"c0_uM": r["peak_uM"], "decay_per_s": r["bath_decay_per_s"]}
                for r in rings["rows"]}
    return held | decaying


def add_decaying_bath(state: dict, c0: float, decay: float) -> None:
    """Drive the population with c(t) = c0 exp(-decay t), turned into occupancy as the field composite does."""
    occ0 = c0 / (c0 + KD)
    # seeded with the value at t = 0, so the bath acts from t = 0 whether or not the Step runs before the first
    # interval (and process-bigraph drops a write to a key the store lacks)
    state["stimulus"]["TNF_R"] = occ0
    state["parameters"].update({"u_TNF": occ0, "d_TNF": 1.0 - occ0})
    state["decaying_bath"] = {
        "_type": "step",
        "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
        "config": {
            "expressions": [
                {"out": "occ", "expr": "c0 * exp(-decay * kinetic_time) / (c0 * exp(-decay * kinetic_time) + Kd)"},
                {"out": "u_TNF", "expr": "occ"},
                {"out": "d_TNF", "expr": "1 - occ"},
            ],
            "params": {"c0": c0, "decay": decay, "Kd": KD},
        },
        # kinetic_time: this Step runs on each kinetic update, every coupling interval, as the dose-response Step does
        "inputs": {"kinetic_time": ["kinetic_time"]},
        # the shared parameters store wins over each fate network's own, so these rates reach every cell
        "outputs": {"occ": ["stimulus", "TNF_R"], "u_TNF": ["parameters", "u_TNF"],
                    "d_TNF": ["parameters", "d_TNF"]},
    }


def point_name(arm: str, minutes: int, exposure: str) -> str:
    return f"{arm}-{minutes}min-{exposure}"


def document(arm: str, minutes: int, exposure: str, batch: int, cells: int = CELLS) -> dict:
    """One batch of one point: Study 1's population in the named bath, every TNF node off at t = 0."""
    bath = exposures()[exposure]
    doc = _population().build(KAPPA[arm], 1.0 / (60.0 * minutes), cells, SEED + (batch - 1) * CELLS, INTERVAL, (),
                              1.0, 0.0)
    state = doc["state"]
    occ = bath["occupancy"] if "occupancy" in bath else bath["c0_uM"] / (bath["c0_uM"] + KD)  # at t = 0
    state["stimulus"]["TNF_R"] = occ
    for cell in state["cells"].values():
        # As make_tnf_field_cell.py does: the process starts from the stores; initial_state only seeds a new one
        del cell["fate"]["config"]["initial_state"]["TNF"]
        cell["node_state"]["TNF"] = 0.0
        cell["node_probabilities"]["TNF"] = 0.0
        cell["fate"]["config"]["parameters"]["u_TNF"] = occ
        cell["fate"]["config"]["parameters"]["d_TNF"] = 1.0 - occ
    if "c0_uM" in bath:
        add_decaying_bath(state, bath["c0_uM"], bath["decay_per_s"])
    return doc


def run_point(arm: str, minutes: int, exposure: str, batch: int) -> Path:
    """Run one batch of one point unless it exists; return its path."""
    out = HERE / "parquet-runs" / point_name(arm, minutes, exposure) / f"batch{batch}.parquet"
    if out.exists():
        return out
    with tempfile.TemporaryDirectory() as tmp:
        rows = json.loads(_population().run(document(arm, minutes, exposure, batch), HOURS, Path(tmp)).read_text())[
            "emitter"][1:]  # row 0: t = 0, nothing written
    cells = sorted(rows[0]["fate_codes"], key=lambda c: int(c[1:]))
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_suffix(".partial")  # renamed only when complete, so an interrupted write is never read back
    pq.write_table(pa.table({"time_s": [r["global_time"] for r in rows],
                             "nfkb_fraction": [r["nfkb_fraction"] for r in rows],
                             **{f"code_{c}": [round(r["fate_codes"][c]) for r in rows] for c in cells}}), partial)
    partial.replace(out)
    return out


def nfkb_trajectory(arm: str, minutes: int, exposure: str) -> tuple[list[float], list[float]]:
    """NF-kB's nuclear fraction every 30 s over 24 h in this point's bath, from a run with one fate network (8 s):
    NF-kB doesn't depend on the fate networks, so every batch of the point reproduces it exactly."""
    with tempfile.TemporaryDirectory() as tmp:
        result = _population().run(document(arm, minutes, exposure, 1, cells=1), HOURS, Path(tmp))
        rows = json.loads(result.read_text())["emitter"][1:]
    return [r["global_time"] for r in rows], [r["nfkb_fraction"] for r in rows]


def summarize(arm: str, minutes: int, exposure: str) -> dict:
    tables = [pq.read_table(run_point(arm, minutes, exposure, b)).to_pydict() for b in range(1, BATCHES + 1)]
    times, f = tables[0]["time_s"], tables[0]["nfkb_fraction"]
    if any(t["time_s"] != times or t["nfkb_fraction"] != f for t in tables):
        raise SystemExit(f"{point_name(arm, minutes, exposure)}: batches differ in time or NF-kB")
    if (times, f) != nfkb_trajectory(arm, minutes, exposure):
        raise SystemExit(f"{point_name(arm, minutes, exposure)}: its batches' NF-kB is not this bath's, so they were "
                         "run with other bath settings; move them aside and rerun the point")
    codes = [t[k] for t in tables for k in t if k.startswith("code_")]
    dead = [any(x & 6 for x in s) for s in codes]
    first_death = [next((t for t, x in zip(times, s, strict=True) if x & 6), None) for s in codes]
    deaths = [t for t in first_death if t is not None]
    curve = [round(sum(1 for t in first_death if t is None or t > h * 3600) / len(codes), 4)
             for h in range(int(HOURS) + 1)]
    peak = next((i for i in range(1, len(f) - 1) if f[i - 1] < f[i] >= f[i + 1]), None)  # NF-kB's first nuclear peak
    return {"arm": arm, "minutes_per_unit": minutes, "exposure": exposure, **exposures()[exposure], "cells": len(codes),
            "alive_cells": len(codes) - sum(dead),  # the count E4 tests (e4_verdict.py); alive_24h is rounded
            "alive_24h": round(1 - sum(dead) / len(codes), 4), "no_fate": sum(not any(s) for s in codes),
            "apoptosis_24h": round(sum(1 for s in codes if s[-1] & 2) / len(codes), 4),
            "necrosis_24h": round(sum(1 for s in codes if s[-1] & 4) / len(codes), 4),
            "median_first_death_min": statistics.median(deaths) / 60 if deaths else None,
            "survival_curve_hourly": curve,
            "nfkb_first_peak": None if peak is None else {"time_min": times[peak] / 60, "nuclear_fraction": f[peak]}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4, help="simulations at once (the machine is shared)")
    args = parser.parse_args()
    grid = [(arm, m, e) for arm in KAPPA for m in CLOCKS for e in exposures()]
    tasks = [(*g, b) for b in range(1, BATCHES + 1) for g in grid]  # batch by batch, so each finishes whole
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run_point, *zip(*tasks, strict=True)))
    points = [summarize(*g) for g in grid]
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "dose.json").write_text(json.dumps(
        {"cells": CELLS * BATCHES, "batches": BATCHES, "seeds": [SEED, SEED + CELLS * BATCHES - 1], "hours": HOURS,
         "interval_s": INTERVAL, "kappa": {"intact": "ln2/337", "knocked_out": 0}, "absorb_death": 1, "kd_uM": KD,
         "points": points}, indent=1) + "\n")
    for p in points:
        print(p["arm"], p["minutes_per_unit"], p["exposure"], p["alive_24h"], p["no_fate"], flush=True)


if __name__ == "__main__":
    sys.exit(main())
