"""Study 1, Phase B: does any death clock let most NF-kB-competent cells survive held TNF in the composite, while
NF-kB-deficient cells still die?

Each point runs Study 0's population builder (../s0-coupling-calibration/population.py, the established 200-cell
document: the NF-kB model shared by 200 independently seeded fate networks) at one death clock, with NF-kB intact
(kappa = ln 2 / 337 s, decision 25) or knocked out (kappa = 0: the NF-kB node never switches on), TNF held on from rest,
24 h, absorbing death (decision 28), Study 0's cell seeds 1-200. Per cell it records the fate code every 30 s
(Survival + 2*Apoptosis + 4*NonACD) to parquet-runs/<name>/timeseries.parquet; a point already run is read back, not
rerun. data/phase_b.json gets, per clock and from those files: the fraction alive (no death node ever on), cells that
reached no fate at all, Survival on at 24 h and on throughout the last 2 h, the median first-death time, and the paired
comparison of each intact cell with its knocked-out twin (rescued, lost, exact McNemar p).

`--variant activation-anchored` reruns the same points with NF-kB's activation route on Lipniacki's clock
(population.py --anchor-activation=1.0; decision 30), as parquet-runs/anchored-<name>/, and writes
data/phase_b_anchored.json: the same summary, the pre-registered criterion per clock (study.yaml tests:
anchored-meets-standard, fixed before these runs), each anchored cell paired with its unanchored twin (intact and
knocked out), and the death mode (apoptosis, necrosis) in every arm.

    uv run --project ~/viva/viva-multiscale-nfkb --no-sync python -I \
        workspace/investigations/tnf-fate-in-space/studies/s1-survival-validation/phase_b.py
"""

import argparse
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
MINUTES = (30, 120, 180, 200, 240, 480)
CELLS, HOURS, SEED = 200, 24.0, 1


def run_point(nfkb: str, minutes: int, anchored: bool = False) -> Path:
    """Run one point unless its timeseries exists; return the timeseries path."""
    name = ("anchored-" if anchored else "") + f"{nfkb}-{minutes}min"
    out = HERE / "parquet-runs" / name
    if (out / "timeseries.parquet").exists():
        return out / "timeseries.parquet"
    result = subprocess.run(
        ["uv", "run", "--project", str(ROOT / "compose"), "--frozen", "python", "-I", str(POPULATION),
         "--kappa", repr(KAPPA[nfkb]), "--k-time", repr(1.0 / (60.0 * minutes)), "--cells", str(CELLS),
         "--hours", str(HOURS), "--seed", str(SEED), "--out", str(out / "raw"), "--absorb-death=1.0",
         *(["--anchor-activation=1.0"] if anchored else [])],
        cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{name}: population.py failed\n{result.stderr[-2000:]}")
    pber = Path(json.loads(result.stdout.strip().splitlines()[-1])["pber"])
    rows = json.loads(pber.read_text())["emitter"][1:]  # row 0 is t = 0, before any process has written
    cells = sorted(rows[0]["fate_codes"], key=lambda c: int(c[1:]))
    times = [r["global_time"] for r in rows]
    pq.write_table(pa.table({"time_s": times, "nfkb_fraction": [r["nfkb_fraction"] for r in rows],
                             **{f"code_{c}": [round(r["fate_codes"][c]) for r in rows] for c in cells}}),
                   out / "timeseries.parquet")
    return out / "timeseries.parquet"


def _cells(path: Path) -> tuple[list[float], list[list[int]]]:
    table = pq.read_table(path)
    columns = sorted((c for c in table.column_names if c.startswith("code_")), key=lambda c: int(c[len("code_c"):]))
    return table.column("time_s").to_pylist(), [table.column(c).to_pylist() for c in columns]


def _mcnemar_exact(gained: int, lost: int) -> float:
    n = gained + lost
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(gained, lost) + 1)) / 2**n)


def summarize(minutes: int, intact: Path, knocked_out: Path) -> dict:
    times, a = _cells(intact)
    _, k = _cells(knocked_out)
    step = times[1] - times[0]
    last_2h = round(2 * 3600 / step)
    dead = lambda s: any(x & 6 for x in s)
    first_death = [next((t for t, x in zip(times, s, strict=True) if x & 6), None) for s in a]
    rescued = sum(1 for x, y in zip(a, k, strict=True) if not dead(x) and dead(y))
    lost = sum(1 for x, y in zip(a, k, strict=True) if dead(x) and not dead(y))
    deaths = [t for t in first_death if t is not None]
    return {"minutes_per_unit": minutes, "k_time": 1.0 / (60.0 * minutes), "cells": len(a),
            "alive_intact": sum(not dead(s) for s in a) / len(a), "alive_knocked_out": sum(not dead(s) for s in k) / len(k),
            "no_fate_intact": sum(not any(s) for s in a), "no_fate_knocked_out": sum(not any(s) for s in k),
            "survival_on_at_24h_intact": sum(1 for s in a if not dead(s) and s[-1] == 1),
            "survival_on_last_2h_intact": sum(1 for s in a if not dead(s) and all(x == 1 for x in s[-last_2h:])),
            "median_first_death_min_intact": statistics.median(deaths) / 60 if deaths else None,
            "rescued_by_nfkb": rescued, "lost_with_nfkb": lost, "net_protection": (rescued - lost) / len(a),
            "p_mcnemar_exact": _mcnemar_exact(rescued, lost)}


def main_anchored() -> None:
    """The activation-anchored variant, evaluated against the criterion fixed before it ran."""
    summaries = []
    for minutes in MINUTES:
        paths = {nfkb: run_point(nfkb, minutes, anchored=True) for nfkb in KAPPA}
        r = summarize(minutes, paths["intact"], paths["knocked_out"])
        r["held_survival_intact"] = r["survival_on_last_2h_intact"] / r["cells"]
        r["meets_standard"] = r["held_survival_intact"] >= 0.5 and r["alive_knocked_out"] <= 0.5
        _, anchored_cells = _cells(paths["intact"])
        _, baseline_cells = _cells(run_point("intact", minutes))
        dead = lambda s: any(x & 6 for x in s)
        saved = sum(1 for x, y in zip(anchored_cells, baseline_cells, strict=True) if not dead(x) and dead(y))
        lost = sum(1 for x, y in zip(anchored_cells, baseline_cells, strict=True) if dead(x) and not dead(y))
        r.update({"alive_by_anchoring": saved, "dead_by_anchoring": lost,
                  "anchoring_net": (saved - lost) / r["cells"], "anchoring_p_mcnemar_exact": _mcnemar_exact(saved, lost)})
        # Death mode at 24 h (death is absorbing, so on at the end = ever on; the two are not exclusive), both arms:
        # anchoring RIP1 also speeds RIP1K, necrosis's start, so saved apoptosis could reappear as necrosis.
        _, ko_cells = _cells(paths["knocked_out"])
        _, ko_baseline = _cells(run_point("knocked_out", minutes))
        for arm, cells in (("intact", anchored_cells), ("knocked_out", ko_cells),
                           ("intact_unanchored", baseline_cells), ("knocked_out_unanchored", ko_baseline)):
            r[f"apoptosis_{arm}"] = sum(1 for c in cells if c[-1] & 2) / len(cells)
            r[f"necrosis_{arm}"] = sum(1 for c in cells if c[-1] & 4) / len(cells)
        ko_saved = sum(1 for x, y in zip(ko_cells, ko_baseline, strict=True) if not dead(x) and dead(y))
        ko_lost = sum(1 for x, y in zip(ko_cells, ko_baseline, strict=True) if dead(x) and not dead(y))
        r.update({"knocked_out_alive_by_anchoring": ko_saved, "knocked_out_dead_by_anchoring": ko_lost,
                  "knocked_out_anchoring_p_mcnemar_exact": _mcnemar_exact(ko_saved, ko_lost)})
        # How the cells anchoring killed (dead anchored, alive unanchored) died: NonACD (necrosis) on at 24 h.
        for key, cells, twins in (("dead_by_anchoring_necrosis", anchored_cells, baseline_cells),
                                  ("knocked_out_dead_by_anchoring_necrosis", ko_cells, ko_baseline)):
            r[key] = sum(1 for x, y in zip(cells, twins, strict=True) if dead(x) and not dead(y) and x[-1] & 4)
        summaries.append(r)
        print(f"{minutes:4d} min/unit: alive intact {r['alive_intact']:.3f}, knocked out {r['alive_knocked_out']:.3f}; "
              f"held {r['held_survival_intact']:.3f}; meets {r['meets_standard']}; net protection "
              f"{r['net_protection']:.3f}; vs unanchored +{saved}/-{lost}; apoptosis/necrosis intact "
              f"{r['apoptosis_intact']:.3f}/{r['necrosis_intact']:.3f} (unanchored {r['apoptosis_intact_unanchored']:.3f}/"
              f"{r['necrosis_intact_unanchored']:.3f})", flush=True)
    (HERE / "data" / "phase_b_anchored.json").write_text(json.dumps(
        {"cells": CELLS, "hours": HOURS, "seed": SEED, "absorb_death": 1.0, "anchor_activation": 1.0,
         "criterion": "held_survival_intact >= 0.5 and alive_knocked_out <= 0.5 at one or more clocks (fixed before "
                      "the runs; study.yaml tests: anchored-meets-standard)",
         "meets_standard": any(r["meets_standard"] for r in summaries), "points": summaries}, indent=1) + "\n")
    print("wrote data/phase_b_anchored.json")


def main() -> None:
    summaries = []
    for minutes in MINUTES:
        paths = {nfkb: run_point(nfkb, minutes) for nfkb in KAPPA}
        r = summarize(minutes, paths["intact"], paths["knocked_out"])
        summaries.append(r)
        print(f"{minutes:4d} min/unit: alive intact {r['alive_intact']:.3f}, knocked out {r['alive_knocked_out']:.3f}; "
              f"rescued {r['rescued_by_nfkb']}, lost {r['lost_with_nfkb']}, p {r['p_mcnemar_exact']:.3g}; "
              f"no fate {r['no_fate_intact']}/{r['no_fate_knocked_out']}; Survival on at 24 h "
              f"{r['survival_on_at_24h_intact']}, last 2 h {r['survival_on_last_2h_intact']}", flush=True)
    (HERE / "data" / "phase_b.json").write_text(json.dumps(
        {"cells": CELLS, "hours": HOURS, "seed": SEED, "absorb_death": 1.0, "points": summaries}, indent=1) + "\n")
    print("wrote data/phase_b.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("baseline", "activation-anchored"), default="baseline")
    if parser.parse_args().variant == "activation-anchored":
        main_anchored()
    else:
        main()
