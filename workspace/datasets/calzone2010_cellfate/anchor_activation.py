"""Measure Lipniacki 2004's own NF-kB activation timing, for anchoring Calzone's activation route (Option A).

Why. In Calzone's network NF-kB's activation route (RIP1 -> RIP1ub -> IKK) races caspase-8's (DISC_TNF -> CASP8). In
the composite both routes switch at `$k_time`, so the death clock cannot change the race (Study 1). Lipniacki times the
same activation in seconds: TNF activates IKK (`k1 * TNF * IKKn`), IKK frees NF-kB, NF-kB enters the nucleus. So, as
`anchor_transcription.py` does for the target genes, the activation route can take Lipniacki's measured time.

What is measured. From the pre-equilibrated steady state (lipniacki2004/processed/lipniacki2004_steady_state.json),
TNF_R is stepped to 1 and the driven model is run on libRoadRunner at one-second resolution. Each half-rise is the time
a species first reaches half-way from its start to its first peak (as in anchor_transcription.py):
- `IKK_active`: TNF -> active IKK;
- `NFKB_nuc`: TNF -> nuclear NF-kB (the composite's kappa = ln 2 / this, decision 25).

The Boolean route RIP1 -> RIP1ub -> IKK is three steps in series. If each switches on at rate r, the time to IKK on is
Erlang(3, r), whose median is q / r with 1 - e^{-q} (1 + q + q^2 / 2) = 1/2, q = 2.6741. So the route's median equals
a measured time T when r = q / T. This script reports r for T = IKK_active's half-rise; which T the composite uses is a
modelling decision recorded in documentation/design/decisions.md, not made here.

    uv run --project compose --frozen python -I workspace/datasets/calzone2010_cellfate/anchor_activation.py
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import NoReturn

import numpy as np
import roadrunner

HERE = Path(__file__).resolve().parent
LIPNIACKI = HERE.parent / "lipniacki2004" / "processed"
MODEL, STEADY = LIPNIACKI / "lipniacki2004_driven.xml", LIPNIACKI / "lipniacki2004_steady_state.json"
OUT = HERE / "processed" / "activation_anchor.json"
DURATION_S, POINTS = 2 * 3600, 7201  # one-second resolution over two hours, past both first peaks
STEPS = 3  # RIP1, RIP1ub, IKK


def _fail(message: str) -> NoReturn:
    sys.exit(f"anchor_activation.py: {message}")


def _half_rise(t: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """The first peak's time, and the time y first reaches half-way from its start to that peak."""
    peaks = np.flatnonzero((y[1:-1] >= y[:-2]) & (y[1:-1] > y[2:])) + 1
    if peaks.size == 0:
        _fail("no peak in the trajectory")
    peak = int(peaks[0])
    half = int(np.flatnonzero(y >= y[0] + 0.5 * (y[peak] - y[0]))[0])
    return float(t[peak]), float(t[half])


def erlang_median_factor(steps: int) -> float:
    """q such that Erlang(steps, rate 1) has median q, by bisection on its closed-form CDF."""
    def cdf(x: float) -> float:
        return 1.0 - math.exp(-x) * sum(x**k / math.factorial(k) for k in range(steps))
    lo, hi = 0.0, 10.0 * steps
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if cdf(mid) < 0.5 else (lo, mid)
    return 0.5 * (lo + hi)


def main() -> None:
    steady = json.loads(STEADY.read_text())
    model_sha = hashlib.sha256(MODEL.read_bytes()).hexdigest()
    if steady["model_sha256"] != model_sha:
        _fail("the steady state was not computed for this model file")
    rr = roadrunner.RoadRunner(str(MODEL))
    rr.integrator.absolute_tolerance, rr.integrator.relative_tolerance = 1e-12, 1e-10
    for species, value in steady["species"].items():
        rr[f"[{species}]"] = value
    rr["TNF_R"] = 1.0
    result = rr.simulate(0, DURATION_S, POINTS, selections=["time", "[IKK_active]", "[NFKB_nuc]"])
    t = np.asarray(result[:, 0])
    ikk_peak, ikk_half = _half_rise(t, np.asarray(result[:, 1]))
    nfkb_peak, nfkb_half = _half_rise(t, np.asarray(result[:, 2]))
    q = erlang_median_factor(STEPS)
    OUT.write_text(json.dumps({
        "model": MODEL.name,
        "model_sha256": model_sha,
        "stimulus": "TNF_R stepped 0 -> 1 from the pre-equilibrated steady state",
        "ikk_active_half_rise_s": ikk_half,
        "ikk_active_first_peak_s": ikk_peak,
        "nfkb_nuc_half_rise_s": nfkb_half,
        "nfkb_nuc_first_peak_s": nfkb_peak,
        "route_steps": STEPS,
        "erlang_median_factor": q,
        "r_act_per_s_for_ikk_half_rise": q / ikk_half,
        "definition": "r_act = q / T: three steps at rate r_act reach IKK on with median T; T = IKK_active half-rise",
    }, indent=2) + "\n")
    print(f"IKK_active half-rise {ikk_half:.0f} s (peak {ikk_peak:.0f} s); NFKB_nuc half-rise {nfkb_half:.0f} s "
          f"(peak {nfkb_peak:.0f} s); q = {q:.4f}; r_act = {q / ikk_half:.4g} /s")


if __name__ == "__main__":
    main()
