"""Study 1, Phase B: does any death clock let most NF-kB-competent cells survive held TNF in the composite, while
NF-kB-deficient cells still die?

Each point runs Study 0's population builder (../s0-coupling-calibration/population.py, the established 200-cell
document: the NF-kB model shared by 200 independently seeded fate networks) at one death clock, with NF-kB intact
(kappa = ln 2 / 337 s, decision 25) or knocked out (kappa = 0: the NF-kB node never switches on), TNF held on from rest,
24 h, absorbing death (decision 28), Study 0's cell seeds 1-200. Per cell it records the fate code every 30 s
(Survival + 2*Apoptosis + 4*NonACD) to parquet-runs/<name>/timeseries.parquet, and writes data/phase_b.json: the
fraction alive (no death node ever on) and the median first-death time.

    uv run --project ~/viva/viva-multiscale-nfkb --no-sync python -I \
        workspace/investigations/tnf-fate-in-space/studies/s1-survival-validation/phase_b.py
"""

import json
import math
import statistics
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
POPULATION = HERE.parent / "s0-coupling-calibration" / "population.py"
KAPPA = {"intact": math.log(2) / 337.0, "knocked_out": 0.0}
MINUTES = (30, 120, 240, 480)
CELLS, HOURS, SEED = 200, 24.0, 1


def run_point(nfkb: str, minutes: int) -> dict:
    name = f"{nfkb}-{minutes}min"
    out = HERE / "parquet-runs" / name
    k_time = 1.0 / (60.0 * minutes)
    result = subprocess.run(
        ["uv", "run", "--project", str(ROOT / "compose"), "--frozen", "python", "-I", str(POPULATION),
         "--kappa", repr(KAPPA[nfkb]), "--k-time", repr(k_time), "--cells", str(CELLS), "--hours", str(HOURS),
         "--seed", str(SEED), "--out", str(out / "raw"), "--absorb-death=1.0"],
        cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{name}: population.py failed\n{result.stderr[-2000:]}")
    pber = Path(json.loads(result.stdout.strip().splitlines()[-1])["pber"])
    rows = json.loads(pber.read_text())["emitter"][1:]  # row 0 is t = 0, before any process has written
    cells = sorted(rows[0]["fate_codes"], key=lambda c: int(c[1:]))
    times = [r["global_time"] for r in rows]
    codes = {c: [round(r["fate_codes"][c]) for r in rows] for c in cells}
    pq.write_table(pa.table({"time_s": times, "nfkb_fraction": [r["nfkb_fraction"] for r in rows],
                             **{f"code_{c}": codes[c] for c in cells}}), out / "timeseries.parquet")
    deaths = [next((t for t, x in zip(times, codes[c], strict=True) if x & 6), None) for c in cells]
    dead = [t for t in deaths if t is not None]
    return {"name": name, "nfkb": nfkb, "minutes_per_unit": minutes, "k_time": k_time, "kappa": KAPPA[nfkb],
            "cells": len(cells), "alive": sum(t is None for t in deaths) / len(cells),
            "median_first_death_min": statistics.median(dead) / 60 if dead else None}


def main() -> None:
    summaries = []
    for minutes in MINUTES:
        for nfkb in KAPPA:
            s = run_point(nfkb, minutes)
            summaries.append(s)
            print(f"{s['name']:22s} alive {s['alive']:.3f}  median first death "
                  f"{s['median_first_death_min'] if s['median_first_death_min'] is None else round(s['median_first_death_min'])} min",
                  flush=True)
    (HERE / "data" / "phase_b.json").write_text(json.dumps(
        {"cells": CELLS, "hours": HOURS, "seed": SEED, "absorb_death": 1.0, "points": summaries}, indent=1) + "\n")
    print("wrote data/phase_b.json")


if __name__ == "__main__":
    main()
