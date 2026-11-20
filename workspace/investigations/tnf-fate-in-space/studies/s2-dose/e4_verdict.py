"""E4, the collapse test: does a cell near a TNF bolus fare as it would in a uniform bath of the same dose?

Fixed before any distance run (decisions 40, 40b and 50 to 53). Each distance-study configuration (NF-kB arm, clock,
bolus size, ring) is compared with this study's decaying bath matched to its ring and bolus size, `bath-<ring>-M<bolus>`
at the same arm and clock: the same peak TNF and the same 24 h TNF dose, without the arrival delay or the pulse's shape
(decision 50). The readout is the fraction of cells alive at 24 h (decision 41), about 1,700 cells on each side (40b).

Each configuration gets one of three verdicts (decision 53):
- **equivalent**: the two one-sided tests, each at the 5% level, both reject a difference of 0.05 or more. That is the
  90% interval for the difference (distance minus bath) lying inside (-0.05, 0.05). The interval is Newcombe's hybrid
  score interval (his method 10, Stat Med 1998;17:873), which keeps close to its nominal coverage near 0 and 1, where
  the Wald interval does not: survival near 0 or 1 is common here;
- **different**: Fisher's exact test of no difference rejects at 5% after Holm's correction across every configuration
  of the study (54: 2 arms x 3 clocks x 3 bolus sizes x 3 rings);
- **inconclusive**: neither.
A configuration can pass both tests, since with this many cells a difference smaller than the margin can be
significant. It is then equivalent (decision 55), because decision 40's margin is the smallest difference that
matters; both tests' results are in the output.

Inputs:
- the dose study's `data/dose.json` (`dose_study.py`): per point `arm`, `minutes_per_unit`, `exposure`, `cells` and
  `alive_cells`;
- the distance study's results, a JSON object whose `points` each give `arm`, `minutes_per_unit`, `ring` (near, middle
  or far: ring_exposure.json's `cell`), `bolus` (uM um^2), `cells` and `alive_cells`.
The two must pair one to one: every distance configuration has its bath, and every bath its configuration, so the Holm
family is the whole study.

    uv run --frozen python -I workspace/investigations/tnf-fate-in-space/studies/s2-dose/e4_verdict.py \\
        --distance <distance results.json> --out <e4.json>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import confint_proportions_2indep

HERE = Path(__file__).resolve().parent
MARGIN = 0.05  # in the fraction alive at 24 h (decision 40)
ALPHA = 0.05  # each one-sided test (so a 90% interval), and the Holm-corrected test of a difference


def bath_name(ring: str, bolus: float) -> str:
    """The dose study's matched bath for a ring and bolus size, as dose_study.exposures names it."""
    return f"bath-{ring}-M{bolus:g}"


def interval(alive_a: int, cells_a: int, alive_b: int, cells_b: int, alpha: float = 2 * ALPHA) -> tuple[float, float]:
    """Newcombe's hybrid score interval for alive_a / cells_a - alive_b / cells_b, at confidence 1 - alpha."""
    low, high = confint_proportions_2indep(alive_a, cells_a, alive_b, cells_b, method="newcomb", compare="diff",
                                           alpha=alpha)
    return float(low), float(high)


def verdicts(pairs: list[tuple[int, int, int, int]]) -> list[dict]:
    """Score a whole family of comparisons, each (alive, cells) for the distance side then the bath side."""
    if not pairs:
        raise ValueError("no comparisons to score")
    for alive_a, cells_a, alive_b, cells_b in pairs:
        if not (0 <= alive_a <= cells_a and 0 <= alive_b <= cells_b and cells_a > 0 and cells_b > 0):
            raise ValueError(f"impossible counts {alive_a}/{cells_a}, {alive_b}/{cells_b}")
    p_values = [float(fisher_exact([[a, n - a], [b, m - b]], alternative="two-sided").pvalue)
                for a, n, b, m in pairs]
    reject, holm, _, _ = multipletests(p_values, alpha=ALPHA, method="holm")
    out = []
    for (a, n, b, m), p, p_holm, rejected in zip(pairs, p_values, holm, reject, strict=True):
        low, high = interval(a, n, b, m)
        if -MARGIN < low and high < MARGIN:
            verdict = "equivalent"
        elif rejected:
            verdict = "different"
        else:
            verdict = "inconclusive"
        out.append({"difference": a / n - b / m, "interval_90": [low, high], "fisher_p": p, "holm_p": float(p_holm),
                    "verdict": verdict})
    return out


def score(distance_points: list[dict], dose_points: list[dict]) -> list[dict]:
    """Pair every distance configuration with its matched bath and score the family."""
    baths = {}
    for p in dose_points:
        if not p["exposure"].startswith("bath-"):
            continue  # a held bath: the dose curve, reported by the dose study, not tested here
        key = (p["arm"], p["minutes_per_unit"], p["exposure"])
        if key in baths:
            raise ValueError(f"the dose study has {key} twice")
        if "alive_cells" not in p:
            raise ValueError(f"dose point {key} has no alive_cells: rerun dose_study.py, which reads its batches back")
        baths[key] = p
    pairs, rows, seen = [], [], set()
    for d in distance_points:
        key = (d["arm"], d["minutes_per_unit"], bath_name(d["ring"], d["bolus"]))
        if key in seen:
            raise ValueError(f"the distance study has {key} twice")
        seen.add(key)
        if key not in baths:
            raise ValueError(f"no matched bath for the distance configuration {key}")
        bath = baths[key]
        pairs.append((d["alive_cells"], d["cells"], bath["alive_cells"], bath["cells"]))
        rows.append({"arm": d["arm"], "minutes_per_unit": d["minutes_per_unit"], "ring": d["ring"], "bolus": d["bolus"],
                     "distance": {"cells": d["cells"], "alive_cells": d["alive_cells"]},
                     "bath": {"exposure": key[2], "cells": bath["cells"], "alive_cells": bath["alive_cells"]}})
    if unpaired := sorted(set(baths) - seen):
        raise ValueError(f"matched baths with no distance configuration: {unpaired}")
    return [row | result for row, result in zip(rows, verdicts(pairs), strict=True)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--distance", type=Path, required=True, help="the distance study's results (see the docstring)")
    parser.add_argument("--dose", type=Path, default=HERE / "data" / "dose.json", help="the dose study's dose.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = score(json.loads(args.distance.read_text())["points"], json.loads(args.dose.read_text())["points"])
    counts = Counter((r["arm"], r["verdict"]) for r in rows)
    args.out.write_text(json.dumps({"margin": MARGIN, "alpha": ALPHA, "interval": "Newcombe hybrid score, 90%",
                                    "difference_test": "Fisher exact, two-sided, Holm across the family",
                                    "family": len(rows), "configurations": rows}, indent=1) + "\n")
    for (arm, verdict), n in sorted(counts.items()):
        print(f"{arm:12} {verdict:13} {n}")


if __name__ == "__main__":
    main()
