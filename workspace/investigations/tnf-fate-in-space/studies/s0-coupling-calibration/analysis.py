"""Study 0's fate table, from the committed per-cell fate codes (parquet-runs/*/timeseries.parquet).

Calzone's Survival node follows NF-kB and is not a final state: a cell can show Survival first and die later. So each
cell is classified by its END state at 24 h, where:
- **dead** means Apoptosis or NonACD (or both) is on;
- **surviving** means Survival is on and nothing else;
- **none** means no fate node is on.

Death is irreversible, but Calzone's death nodes are not absorbing: Apoptosis follows CASP3 and NonACD follows ATP loss,
and both switch off again if their logic fails (for example when XIAP returns and switches caspase-3 off). So the
end state can show a cell that has died as alive. **ever_dead** counts a cell as dead from the first tick any death node
is on, and **alive** is its complement. These are the primary readouts, and the end-state columns are kept beside them.

The first-fate fractions are reported alongside, with how many first-Survival cells later died.

Every variant (decay-*, persist-*, ko-*) runs on the grid's 200 cell seeds, so each is also compared CELL BY CELL with
the grid run at the same kappa and clock. For each end-state readout (surviving, apoptosis, necrosis, dead) it counts
the cells that gained and lost it, and gives an exact McNemar p (two-sided binomial on those discordant cells).
Comparing the two fractions as if independent ignores this pairing and can hide a consistent shift.

    python3 <this file>      (reads parquet-runs/; writes data/fate-table.json and data/paired.json; prints both)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent


def table(path: Path) -> dict:
    t = pq.read_table(path)
    codes = [t.column(c).to_pylist() for c in t.column_names if c.startswith("code_")]
    n = len(codes)
    row = {"cells": n, "first_survival": 0, "first_survival_then_dead": 0, "end_dead": 0, "end_apoptosis": 0,
           "end_nonacd": 0, "end_apoptosis_and_nonacd": 0, "end_surviving": 0, "end_none": 0, "ever_dead": 0,
           "alive": 0, "alive_survival_on_at_end": 0, "revived": 0}
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
        ever = any(x & 6 for x in series)
        row["ever_dead"] += ever
        row["alive"] += not ever
        row["alive_survival_on_at_end"] += (not ever) and last == 1
        row["revived"] += ever and not last & 6  # a death node was on, and none is at the end
    return {k: (v / n if k != "cells" else v) for k, v in row.items()}


READOUTS = {"ever_dead": lambda s: any(x & 6 for x in s), "end_apoptosis": lambda s: bool(s[-1] & 2),
            "end_necrosis": lambda s: bool(s[-1] & 4), "alive_survival_on": lambda s: s[-1] == 1 and not any(x & 6 for x in s)}


def _series(path: Path) -> list[list[int]]:
    t = pq.read_table(path)
    return [t.column(c).to_pylist() for c in sorted((c for c in t.column_names if c.startswith("code_")),
                                                     key=lambda c: int(c[len("code_c"):]))]


def _mcnemar_exact(gained: int, lost: int) -> float:
    n = gained + lost
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(gained, lost) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def paired(variant: Path, grid: Path) -> dict:
    """Cell-by-cell change from the grid run (same seeds) to the variant, per end-state readout."""
    v, g = _series(variant), _series(grid)
    if len(v) != len(g):
        raise SystemExit(f"{variant.parent.name}: {len(v)} cells against {len(g)} in {grid.parent.name}")
    out = {}
    for name, test in READOUTS.items():
        gained = sum(1 for a, b in zip(g, v, strict=True) if not test(a) and test(b))
        lost = sum(1 for a, b in zip(g, v, strict=True) if test(a) and not test(b))
        out[name] = {"grid": sum(map(test, g)), "variant": sum(map(test, v)), "gained": gained, "lost": lost,
                     "p_mcnemar_exact": _mcnemar_exact(gained, lost)}
    return out


def _grid_partner(name: str) -> str | None:
    for prefix in ("decay-", "decayp-", "persist-"):
        if name.startswith(prefix):
            return "grid-" + name[len(prefix):]
    if name.startswith("ko-"):  # ko-<edit>-<kappa>-<m>min: the kappa and clock are the last two fields
        return "grid-" + "-".join(name.split("-")[-3:])
    return None


def main() -> None:
    rows = {}
    for path in sorted(HERE.glob("parquet-runs/*/timeseries.parquet")):
        name = path.parent.name
        if not name.startswith("smoke"):
            rows[name] = table(path)
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "fate-table.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(f"{'run':38s} {'everD':>5} {'alive':>5} {'aliveS':>6} {'reviv':>5} | end: {'dead':>5} {'apop':>5} {'necr':>5} "
          f"{'surv':>5} {'none':>5}")
    for name, r in rows.items():
        print(f"{name:38s} {r['ever_dead']:5.3f} {r['alive']:5.3f} {r['alive_survival_on_at_end']:6.3f} {r['revived']:5.3f} | "
              f"     {r['end_dead']:5.3f} {r['end_apoptosis']:5.3f} {r['end_nonacd']:5.3f} {r['end_surviving']:5.3f} "
              f"{r['end_none']:5.3f}")
    pairs = {}
    for name in rows:
        partner = _grid_partner(name)
        if partner and partner in rows:
            pairs[name] = {"against": partner, **paired(HERE / "parquet-runs" / name / "timeseries.parquet",
                                                         HERE / "parquet-runs" / partner / "timeseries.parquet")}
    (HERE / "data" / "paired.json").write_text(json.dumps(pairs, indent=1) + "\n")
    print(f"\n{'variant (cell by cell against grid)':38s} " + "  ".join(f"{k:>22s}" for k in READOUTS))
    for name, r in pairs.items():
        print(f"{name:38s} " + "  ".join(
            f"{r[k]['grid']:3d}->{r[k]['variant']:3d} +{r[k]['gained']:<3d}-{r[k]['lost']:<3d}p{r[k]['p_mcnemar_exact']:.3f}"
            for k in READOUTS))


if __name__ == "__main__":
    main()
