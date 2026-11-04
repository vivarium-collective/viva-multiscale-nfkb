"""d7 use 1, step 1 (docs/design/plan-section-b.md and eDMD.md): the kinetic layer's timescales from its Jacobian.

The kinetic layer has equations, so no eDMD is needed for it: its local timescales are 1 / |Re(lambda)| of the
Jacobian's eigenvalues along a trajectory. This evaluates them on the driven Lipniacki 2004 model (libRoadRunner,
TelluriumProcess's tolerances) at the pre-equilibrated steady state, then every 60 s for 6 h after TNF_R is stepped
to 1, the same 6 h BioModels' curation simulates. Per time point:
- decaying modes (Re < 0): timescale 1 / |Re|, fastest and slowest;
- growing modes (Re > 0): e-folding time 1 / Re. After stimulation a complex pair turns unstable; that is the NF-kB
  oscillation, not an error;
- oscillatory modes (Im != 0): period 2 pi / |Im|;
- zero modes (conserved totals: NF-kB) are excluded from timescales and counted.

Cross-check, independent of roadrunner's eigen solver: every eigenvalue from ``getFullEigenValues`` has a match among
numpy's eigenvalues of roadrunner's full Jacobian, and vice versa, within 1e-9 of the largest eigenvalue (matched by
nearest value; conjugate pairs come out in either order), or the script refuses to write.

Writes analysis/d7/kinetic_timescales.json: the per-time classification and the post-stimulus ranges.

    uv run --project compose python -I analysis/d7/kinetic_timescales.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import tellurium as te

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "workspace/datasets/lipniacki2004/processed"
MODEL = DATA / "lipniacki2004_driven.xml"
STATE = DATA / "lipniacki2004_steady_state.json"
OUT = Path(__file__).resolve().parent / "kinetic_timescales.json"
STEP, DURATION, ZERO = 60.0, 21600.0, 1e-12


def classify(runner: te.roadrunner.ExtendedRoadRunner, after: float | None) -> dict[str, object]:
    eigen = np.array(runner.getFullEigenValues(), dtype=complex)
    check = np.linalg.eigvals(np.array(runner.getFullJacobian()))
    scale = float(np.max(np.abs(eigen)))
    gap = max(max(float(np.min(np.abs(check - v))) for v in eigen), max(float(np.min(np.abs(eigen - v))) for v in check))
    if gap > 1e-9 * scale:
        sys.exit(f"kinetic_timescales.py: eigen solvers disagree by {gap:.3e} at t = {runner.getCurrentTime()}")
    zero = np.abs(eigen) <= ZERO * scale
    live = eigen[~zero]
    decaying = sorted(float(1.0 / -v.real) for v in live if v.real < 0)
    growing = sorted({round(float(1.0 / v.real), 6) for v in live if v.real > 0})
    periods = sorted({round(float(2 * np.pi / abs(v.imag)), 6) for v in live if abs(v.imag) > ZERO * scale})
    return {"t_after_stimulus_s": after, "fastest_decay_s": decaying[0], "slowest_decay_s": decaying[-1],
            "growth_efolding_s": growing, "periods_s": periods, "zero_modes": int(zero.sum())}


def main() -> None:
    seed = json.loads(STATE.read_text())
    if seed["model_sha256"] != hashlib.sha256(MODEL.read_bytes()).hexdigest():
        sys.exit("kinetic_timescales.py: the steady state was made from another model file")
    runner = te.loadSBMLModel(str(MODEL))
    runner.integrator.absolute_tolerance, runner.integrator.relative_tolerance = 1e-10, 1e-8
    for sid, value in seed["species"].items():
        runner[sid] = value

    rows = [classify(runner, None)]
    runner["TNF_R"] = 1.0
    for k in range(1, int(DURATION / STEP) + 1):
        runner.simulate(runner.getCurrentTime(), runner.getCurrentTime() + STEP, 2)
        rows.append(classify(runner, k * STEP))

    post = rows[1:]
    growing = [r for r in post if r["growth_efolding_s"]]
    periods = [p for r in post for p in r["periods_s"]]
    summary = {
        "model": MODEL.name,
        "model_sha256": seed["model_sha256"],
        "pre_stimulus": rows[0],
        "post_fastest_decay_range_s": [min(r["fastest_decay_s"] for r in post), max(r["fastest_decay_s"] for r in post)],
        "post_slowest_decay_range_s": [min(r["slowest_decay_s"] for r in post), max(r["slowest_decay_s"] for r in post)],
        "post_unstable_fraction_of_time": len(growing) / len(post),
        "post_growth_efolding_range_s": [min(min(r["growth_efolding_s"]) for r in growing),
                                         max(max(r["growth_efolding_s"]) for r in growing)] if growing else [],
        "post_period_range_s": [min(periods), max(periods)] if periods else [],
        "zero_modes": sorted({r["zero_modes"] for r in rows}),
        "rows": rows,
    }
    OUT.write_text(json.dumps(summary, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for key in ("post_fastest_decay_range_s", "post_slowest_decay_range_s", "post_unstable_fraction_of_time",
                "post_growth_efolding_range_s", "post_period_range_s", "zero_modes"):
        print(f"  {key}: {summary[key]}")
    print(f"  pre_stimulus: {rows[0]}")


if __name__ == "__main__":
    main()
