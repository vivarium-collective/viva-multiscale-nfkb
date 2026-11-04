"""Compute the Boolean layer's transcription rate r_tx (per second) from Lipniacki 2004's own NF-kB target-gene timing.

Why (Alex, 2026-11-04: "anchor to Lipniacki, sweep death"). In Calzone's network, cell fate is a race between the death
arms and NF-kB's protective target genes (cFLIP, BCL2, mXIAP, and Survival), which switch on at `$TransRate` once NF-kB
is on. Calzone gives no time unit, and its MaBoSS example sets TransRate = 1/24 of the signalling rate without a source.
Lipniacki models NF-kB-driven gene expression in seconds, fitted to data: IkBa and A20 transcription, translation and
nuclear transport. So Lipniacki sets the transcription clock, and the composite's `$k_time` sweep covers only the clock
nobody can ground, the death machinery's.

The anchor is measured, not chosen. From the pre-equilibrated steady state (lipniacki2004/processed/
lipniacki2004_steady_state.json), TNF_R is stepped to 1 and the driven model is run on libRoadRunner. The delay is
the time from NF-kB's nuclear half-rise to its target protein A20's half-rise, each relative to its first peak. A
Calzone target node switching on at rate r while NF-kB is on reaches half probability at ln 2 / r, so
r_tx = ln 2 / delay.

    uv run --project compose python -I workspace/datasets/calzone2010_cellfate/anchor_transcription.py
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
OUT = HERE / "processed" / "transcription_anchor.json"
DURATION_S, POINTS = 6 * 3600, 21601  # one-second resolution over six hours, past A20's first peak


def _fail(message: str) -> NoReturn:
    sys.exit(f"anchor_transcription.py: {message}")


def _half_rise(t: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """The first peak's time, and the time y first reaches half-way from its start to that peak."""
    peaks = np.flatnonzero((y[1:-1] >= y[:-2]) & (y[1:-1] > y[2:])) + 1
    if peaks.size == 0:
        _fail("no peak in the trajectory")
    peak = int(peaks[0])
    half = int(np.flatnonzero(y >= y[0] + 0.5 * (y[peak] - y[0]))[0])
    return float(t[peak]), float(t[half])


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
    result = rr.simulate(0, DURATION_S, POINTS, selections=["time", "[NFKB_nuc]", "[A20]"])
    t = np.asarray(result[:, 0])
    nfkb_peak, nfkb_half = _half_rise(t, np.asarray(result[:, 1]))
    a20_peak, a20_half = _half_rise(t, np.asarray(result[:, 2]))
    delay = a20_half - nfkb_half
    r_tx = math.log(2) / delay
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "model": MODEL.name,
        "model_sha256": model_sha,
        "stimulus": "TNF_R stepped 0 -> 1 from the pre-equilibrated steady state",
        "nfkb_nuc_half_rise_s": nfkb_half,
        "nfkb_nuc_first_peak_s": nfkb_peak,
        "a20_half_rise_s": a20_half,
        "a20_first_peak_s": a20_peak,
        "target_delay_s": delay,
        "r_tx_per_s": r_tx,
        "definition": "r_tx = ln 2 / (A20 half-rise - NFKB_nuc half-rise); each half-rise is relative to its first peak",
    }, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(HERE)}: delay {delay:.0f} s ({delay / 60:.1f} min), r_tx = {r_tx:.6g} /s")


if __name__ == "__main__":
    main()
