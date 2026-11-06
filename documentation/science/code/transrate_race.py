"""The race on Calzone's network: fate fractions at t = 40 Calzone units for two transcription rates, TNF on.

Quoted in documentation/science/boolean-networks.md. The coupled network with u_NFkB = 1, d_NFkB = 0, k_time = 1 and
absorb_death = 0 is Calzone's network exactly (checks/boolean/coupled-equals-full), so r_tx plays TransRate here.

    uv run --project compose python -I documentation/science/code/transrate_race.py
"""

from pathlib import Path

from process_bigraph import allocate_core
from viva_maboss.processes import MaBoSSProcess

ROOT = Path(__file__).resolve().parents[3]
NETWORK = (ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "cellfate_coupled.bnd").read_text()
AS_CALZONE = {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
              "u_NFkB": 1.0, "d_NFkB": 0.0, "k_time": 1.0, "absorb_death": 0.0}


def fates(transrate: float, units: float = 40.0, cells: int = 50_000) -> dict[str, float]:
    process = MaBoSSProcess(
        config={"network": NETWORK, "parameters": {**AS_CALZONE, "r_tx": transrate},
                "initial_state": {"FADD": 1, "ATP": 1, "cIAP": 1, "TNF": 1}, "sample_count": cells,
                "windows_per_interval": 20, "seed": 3},
        core=allocate_core())
    start = process.initial_state()
    deltas = process.update(start, units)["node_probabilities"]
    return {n: start["node_probabilities"][n] + deltas[n] for n in ("Survival", "Apoptosis", "NonACD")}


if __name__ == "__main__":
    for transrate in (1 / 24, 1.0):
        p = fates(transrate)
        print(f"TransRate {transrate:.4f}: " + "  ".join(f"{n} {v:.3f}" for n, v in p.items()))
