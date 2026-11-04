"""Study 0's canonical runner (study.yaml canonical_runs): run the calibration grid and record it in the workbench.

Split by design (Alex, 2026-11-04: "Pinned env; workbench records"):
- SIMULATION runs in the workspace's pinned compose/ environment (process-bigraph 1.9.1, the simulators at the commits
  compose-api pins) through compose-api's own runner, via population.py, exactly as the workspace's checks run.
- RECORDING runs here, in the workbench's environment: each grid point is registered in the study's runs.db through
  discovery_engine.run_registry (running, then complete, with its full parameters), its population time series is
  written to parquet-runs/<run_id>/timeseries.parquet, and the workbench is asked to sync runs.db into study.yaml.

Every grid point uses the same cell seeds (common random numbers), so differences between points come from kappa and
k_time, not from different random draws.

    /viva-study run-script s0-coupling-calibration            # the full grid (default entry)
    /viva-study run-script s0-coupling-calibration --entry smoke
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SPEC_ID = "viva_multiscale_nfkb.composites.kinetic_boolean.kinetic-boolean"
BASE_SEED = 1
FATES = ("Survival", "Apoptosis", "NonACD")
KAPPA = {  # name -> rate (1/s), or None for Calzone's own flicker (kappa = k_time)
    "calzone-flicker": None,
    "lipniacki-nfkb": math.log(2) / 337.0,   # NF-kB's own nuclear half-rise (transcription_anchor.json)
    "lipniacki-gene": math.log(2) / 2107.0,  # the NF-kB -> target-protein delay (a slow bracket)
}
MINUTES = (2, 10, 30, 120)


def _relaunch_in_workbench_env() -> None:
    """Re-exec with an interpreter that has the workbench's discovery_engine and pyarrow, if this one lacks them."""
    try:
        import discovery_engine  # noqa: F401
        import pyarrow  # noqa: F401
        return
    except ImportError:
        pass
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    for venv in (ROOT / ".venv", Path(common).parent / ".venv"):
        python = venv / "bin" / "python"
        if python.exists() and Path(sys.executable).resolve() != python.resolve():
            os.execv(str(python), [str(python), __file__, *sys.argv[1:]])
    sys.exit("run_grid.py needs the workbench environment (discovery_engine, pyarrow); none found")


def _wilson(k: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def run_point(name: str, kappa_name: str, minutes: float, cells: int, hours: float, runs_db: Path) -> dict:
    from discovery_engine import run_registry
    import pyarrow as pa
    import pyarrow.parquet as pq

    k_time = 1.0 / (60.0 * minutes)
    kappa = k_time if KAPPA[kappa_name] is None else KAPPA[kappa_name]
    params = {"kappa_name": kappa_name, "kappa": kappa, "minutes_per_calzone_unit": minutes, "k_time": k_time,
              "cells": cells, "hours": hours, "interval": 30.0, "base_seed": BASE_SEED,
              "environment": "compose/ (pinned to compose-api's production mash-up; process-bigraph 1.9.1)"}
    out = HERE / "parquet-runs" / name
    run_registry.register_run(runs_db, name, spec_id=SPEC_ID, status="running", params=params,
                              started_at=time.time(), ws_root=ROOT)
    result = subprocess.run(
        ["uv", "run", "--project", str(ROOT / "compose"), "--frozen", "python", "-I", str(HERE / "population.py"),
         "--kappa", repr(kappa), "--k-time", repr(k_time), "--cells", str(cells), "--hours", str(hours),
         "--seed", str(BASE_SEED), "--out", str(out / "raw")],
        cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        run_registry.register_run(runs_db, name, status="failed", completed_at=time.time())
        raise RuntimeError(f"{name}: population.py failed\n{result.stderr[-2000:]}")
    pber = Path(json.loads(result.stdout.strip().splitlines()[-1])["pber"])
    # raw/ (document, omex, runner log, pber) is regenerable from params and is not committed (.gitignore); its
    # document's sha256 is recorded instead, so a rerun can be checked against it
    import hashlib
    document_sha256 = hashlib.sha256((out / "raw" / "document.pbg").read_bytes()).hexdigest()
    rows = json.loads(pber.read_text())["emitter"][1:]  # row 0 is t = 0, before any process has written
    table = pa.table({
        "time_s": [r["global_time"] for r in rows],
        "nfkb_fraction": [r["nfkb_fraction"] for r in rows],
        "nfkb_fraction_time_s": [r["nfkb_fraction_time"] for r in rows],
        "counted_at_s": [r["counted_at"] for r in rows],
        **{f"n_{fate}": [r["counts"][f"n_{fate}"] for r in rows] for fate in FATES},
    })
    pq.write_table(table, out / "timeseries.parquet")
    last = rows[-1]
    decided = sum(last["counts"][f"n_{fate}"] for fate in FATES)
    f_series = table.column("nfkb_fraction").to_pylist()
    peak = max(range(len(f_series)), key=f_series.__getitem__)
    summary = {
        "run_id": name, **params,
        **{f"{fate}_fraction": last["counts"][f"n_{fate}"] / cells for fate in FATES},
        **{f"{fate}_ci95": _wilson(last["counts"][f"n_{fate}"], cells) for fate in FATES},
        "undecided_fraction": 1.0 - decided / cells,
        "nfkb_first_peak_time_s": table.column("time_s")[peak].as_py(),
        "nfkb_first_peak_f": f_series[peak],
        "document_sha256": document_sha256,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    run_registry.register_run(runs_db, name, status="complete", n_steps=len(rows), completed_at=time.time(),
                              emitter_path=str((out / "timeseries.parquet").relative_to(HERE)))
    return summary


def _sync_workbench() -> None:
    info = ROOT / ".pbg" / "server" / "server-info"
    if not info.exists():
        print("workbench not running; sync skipped (run POST /api/study-sync-runs later)")
        return
    url = json.loads(info.read_text())["url"]
    import urllib.request
    request = urllib.request.Request(f"{url}/api/study-sync-runs", data=json.dumps({"study": HERE.name}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - the local workbench
        print("study-sync-runs:", response.status)


def main() -> None:
    _relaunch_in_workbench_env()
    a = argparse.ArgumentParser()
    a.add_argument("--smoke", action="store_true", help="2 kappa x 1 k_time x 10 cells, 1 h")
    args = a.parse_args()
    if args.smoke:
        grid = [(k, 10) for k in ("calzone-flicker", "lipniacki-nfkb")]
        cells, hours, prefix = 10, 1.0, "smoke"
    else:
        grid = [(k, m) for k in KAPPA for m in MINUTES]
        cells, hours, prefix = 200, 8.0, "grid"
    runs_db = HERE / "runs.db"
    summaries = []
    for kappa_name, minutes in grid:
        name = f"{prefix}-{kappa_name}-{minutes}min"
        started = time.time()
        summary = run_point(name, kappa_name, minutes, cells, hours, runs_db)
        summaries.append(summary)
        print(f"{name}: survival {summary['Survival_fraction']:.3f}  apoptosis {summary['Apoptosis_fraction']:.3f}  "
              f"nonacd {summary['NonACD_fraction']:.3f}  undecided {summary['undecided_fraction']:.3f}  "
              f"({time.time() - started:.0f} s)", flush=True)
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / f"{prefix}-summary.json").write_text(json.dumps(summaries, indent=1) + "\n")
    _sync_workbench()


if __name__ == "__main__":
    main()
