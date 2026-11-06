"""Study 1, Phase A: the survival ceiling of Calzone's network under held TNF.

Sweeps the protective genes' induction speed (TransRate) far past MaBoSS's example, with NF-kB intact and knocked out,
and reads the three fates at t = 40 Calzone units. The coupled network with u_NFkB = 1, d_NFkB = 0, k_time = 1 and
absorb_death = 0 is Calzone's network exactly (checks/boolean/coupled-equals-full), so r_tx plays TransRate; NF-kB knocked
out is u_NFkB = 0, d_NFkB = 1 (checks/boolean/coupled-nfkb-knockout). Writes data/phase_a.json.

    uv run --project compose python -I workspace/investigations/tnf-fate-in-space/studies/s1-survival-validation/phase_a.py
"""

import json
from fractions import Fraction
from pathlib import Path

from process_bigraph import allocate_core
from viva_maboss.processes import MaBoSSProcess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
NETWORK = (ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "cellfate_coupled.bnd").read_text()
BASE = {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
        "k_time": 1.0, "absorb_death": 0.0}
NFKB = {"intact": {"u_NFkB": 1.0, "d_NFkB": 0.0}, "knocked_out": {"u_NFkB": 0.0, "d_NFkB": 1.0}}
TRANSRATES = (Fraction(1, 24), Fraction(1, 4), Fraction(1), Fraction(4), Fraction(16), Fraction(64))
UNITS, CELLS, WINDOWS, SEED = 40.0, 50_000, 40, 3
FATES = ("Survival", "Apoptosis", "NonACD")


def fates(nfkb: str, transrate: float) -> dict[str, float]:
    process = MaBoSSProcess(
        config={"network": NETWORK, "parameters": {**BASE, **NFKB[nfkb], "r_tx": transrate},
                "initial_state": {"FADD": 1, "ATP": 1, "cIAP": 1, "TNF": 1}, "sample_count": CELLS,
                "windows_per_interval": WINDOWS, "seed": SEED},
        core=allocate_core())
    start = process.initial_state()
    deltas = process.update(start, UNITS)["node_probabilities"]
    return {n: round(start["node_probabilities"][n] + deltas[n], 4) for n in FATES}


def main() -> None:
    rows = []
    for nfkb in NFKB:
        for rate in TRANSRATES:
            p = fates(nfkb, float(rate))
            rows.append({"nfkb": nfkb, "transrate": str(rate), **p})
            print(f"NF-kB {nfkb:11s} TransRate {rate!s:>5s}: " + "  ".join(f"{n} {p[n]:.3f}" for n in FATES), flush=True)
    out = HERE / "data" / "phase_a.json"
    out.write_text(json.dumps({"units": UNITS, "cells": CELLS, "windows": WINDOWS, "seed": SEED, "rows": rows}, indent=1)
                   + "\n")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
