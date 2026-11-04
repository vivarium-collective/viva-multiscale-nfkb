"""Tutorial 4: sweep the death clock k_time with gene expression anchored to Lipniacki, and watch who wins.

NF-kB's input is held at Lipniacki's post-stimulus nuclear fraction (f = 0.5627); TNF is on. Gene expression runs at
r_tx (per second) from the anchor; k_time sets how fast everything else, including the death machinery, runs.

Run from the repository root:  uv run --project compose python -I documentation/tutorials/code/death_clock_sweep.py
"""

import json
from pathlib import Path

from process_bigraph import allocate_core
from viva_maboss.processes import MaBoSSProcess

DATA = Path("workspace/datasets/calzone2010_cellfate/processed")
NETWORK = (DATA / "cellfate_coupled.bnd").read_text()
R_TX = json.loads((DATA / "transcription_anchor.json").read_text())["r_tx_per_s"]
F = 0.5626781  # Lipniacki's nuclear NF-kB fraction at its post-stimulus peak (see the coupling page)
SECONDS = 8 * 3600.0  # eight hours of composite time


def fates(k_time: float) -> dict[str, float]:
    process = MaBoSSProcess(
        config={
            "network": NETWORK,
            "parameters": {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
                           "u_NFkB": F, "d_NFkB": 1.0 - F, "k_time": k_time, "r_tx": R_TX},
            "initial_state": {"FADD": 1, "ATP": 1, "cIAP": 1, "TNF": 1},
            "sample_count": 20000,
            "windows_per_interval": 20,
            "seed": 2,
        },
        core=allocate_core(),
    )
    start = process.initial_state()
    deltas = process.update(start, SECONDS)["node_probabilities"]
    return {n: start["node_probabilities"][n] + deltas[n] for n in ("Survival", "Apoptosis", "NonACD")}


if __name__ == "__main__":
    print(f"r_tx = {R_TX:.3g} /s (gene expression, fixed); 8 h of composite time")
    for minutes_per_unit in (0.5, 2, 10, 30, 120):
        k_time = 1.0 / (60.0 * minutes_per_unit)
        p = fates(k_time)
        print(f"1 Calzone unit = {minutes_per_unit:5.1f} min:  Survival {p['Survival']:.3f}  "
              f"Apoptosis {p['Apoptosis']:.3f}  NonACD {p['NonACD']:.3f}")
