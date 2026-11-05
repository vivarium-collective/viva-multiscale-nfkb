"""Study 0's fate table, from the committed per-cell fate codes (parquet-runs/*/timeseries.parquet).

Calzone's Survival node follows NF-kB and is not a final state: a cell can show Survival first and die later. So each
cell is classified by its END state at 24 h, where:
- **dead** means Apoptosis or NonACD (or both) is on;
- **surviving** means Survival is on and nothing else;
- **none** means no fate node is on.

The first-fate fractions are reported alongside, with how many first-Survival cells later died.

    python3 <this file>      (reads the study's parquet-runs/, writes data/fate-table.json and prints the table)
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent


def table(path: Path) -> dict:
    t = pq.read_table(path)
    codes = [t.column(c).to_pylist() for c in t.column_names if c.startswith("code_")]
    n = len(codes)
    row = {"cells": n, "first_survival": 0, "first_survival_then_dead": 0, "end_dead": 0, "end_apoptosis": 0,
           "end_nonacd": 0, "end_apoptosis_and_nonacd": 0, "end_surviving": 0, "end_none": 0}
    for series in codes:
        hit = next((i for i, x in enumerate(series) if x), None)
        last = series[-1]
        if hit is not None and series[hit] == 1:
            row["first_survival"] += 1
            row["first_survival_then_dead"] += bool(last & 6)
        row["end_dead"] += bool(last & 6)
        row["end_apoptosis"] += bool(last & 2)
        row["end_nonacd"] += bool(last & 4)
        row["end_apoptosis_and_nonacd"] += bool(last & 2 and last & 4)
        row["end_surviving"] += last == 1
        row["end_none"] += last == 0
    return {k: (v / n if k != "cells" else v) for k, v in row.items()}


def main() -> None:
    rows = {}
    for path in sorted(HERE.glob("parquet-runs/*/timeseries.parquet")):
        name = path.parent.name
        if not name.startswith("smoke"):
            rows[name] = table(path)
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "fate-table.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(f"{'run':38s} {'dead':>5} {'apop':>5} {'necr':>5} {'surv':>5} {'none':>5} | {'1stS':>5} {'1stS->dead':>10}")
    for name, r in rows.items():
        print(f"{name:38s} {r['end_dead']:5.3f} {r['end_apoptosis']:5.3f} {r['end_nonacd']:5.3f} "
              f"{r['end_surviving']:5.3f} {r['end_none']:5.3f} | {r['first_survival']:5.3f} {r['first_survival_then_dead']:10.3f}")


if __name__ == "__main__":
    main()
