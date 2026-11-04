"""Tutorial 2: run the coupled cell-fate network on its own and read the three fates.

Run from the repository root:  uv run --project compose python -I documentation/tutorials/code/boolean_fates.py
"""

from pathlib import Path

from process_bigraph import allocate_core
from viva_maboss.processes import MaBoSSProcess

NETWORK = Path("workspace/datasets/calzone2010_cellfate/processed/cellfate_coupled.bnd").read_text()
BASE = {
    "High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0,  # Calzone's mutant switches, all off (wild type)
    "u_TNF": 0.0, "d_TNF": 0.0,                           # TNF held where it starts (on, below)
    "k_time": 1.0, "r_tx": 1 / 24,                         # Calzone's own units and MaBoSS's example TransRate
}


def fates(nfkb_on: float, interval: float = 40.0) -> dict[str, float]:
    """Fate probabilities with TNF on and the NF-kB input held at P(on) = nfkb_on (u = f, d = 1 - f)."""
    process = MaBoSSProcess(
        config={
            "network": NETWORK,
            "parameters": {**BASE, "u_NFkB": nfkb_on, "d_NFkB": 1.0 - nfkb_on},
            "initial_state": {"FADD": 1, "ATP": 1, "cIAP": 1, "TNF": 1},
            "sample_count": 20000,
            "windows_per_interval": 20,
            "seed": 1,
        },
        core=allocate_core(),
    )
    start = process.initial_state()
    deltas = process.update(start, interval)["node_probabilities"]
    return {n: start["node_probabilities"][n] + deltas[n] for n in ("Survival", "Apoptosis", "NonACD")}


if __name__ == "__main__":
    for f in (0.0, 0.25, 0.5, 0.75, 1.0):
        p = fates(f)
        print(f"NF-kB input f = {f:4.2f}:  Survival {p['Survival']:.3f}  Apoptosis {p['Apoptosis']:.3f}  "
              f"NonACD {p['NonACD']:.3f}")
