"""How fast Calzone's network kills when NF-kB is blocked: P(Apoptosis) against time, TNF on, Calzone's own units.

Quoted in documentation/design/time.md. The coupled network with u_NFkB = 0, d_NFkB = 1 (no nuclear NF-kB),
k_time = 1, r_tx = 1/24 and absorb_death = 0 is Calzone's network with NF-kB's switch-on rate 0
(checks/boolean/coupled-nfkb-knockout). Each time point is a separate run from t = 0 with the same seed, 50,000 cells,
read over a last window of 1/200 of the run.

    uv run --project compose python -I documentation/design/code/death_halftime.py
"""

import itertools
from pathlib import Path

from process_bigraph import allocate_core
from viva_maboss.processes import MaBoSSProcess

ROOT = Path(__file__).resolve().parents[3]
NETWORK = (ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "cellfate_coupled.bnd").read_text()
NO_NFKB = {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
           "u_NFkB": 0.0, "d_NFkB": 1.0, "k_time": 1.0, "r_tx": 1 / 24, "absorb_death": 0.0}


def apoptosis_at(units: float) -> float:
    process = MaBoSSProcess(
        config={"network": NETWORK, "parameters": NO_NFKB, "initial_state": {"FADD": 1, "ATP": 1, "cIAP": 1, "TNF": 1},
                "sample_count": 50_000, "windows_per_interval": 200, "seed": 5},
        core=allocate_core())
    start = process.initial_state()
    return start["node_probabilities"]["Apoptosis"] + process.update(start, units)["node_probabilities"]["Apoptosis"]


def crossing(series: list[tuple[float, float]], level: float) -> float:
    """The first time P reaches `level`, by linear interpolation between the sampled times."""
    for (t0, p0), (t1, p1) in itertools.pairwise(series):
        if p0 < level <= p1:
            return t0 + (level - p0) * (t1 - t0) / (p1 - p0)
    raise ValueError(f"P(Apoptosis) never reaches {level}")


if __name__ == "__main__":
    times = [t / 2 for t in range(2, 81)]  # 1 to 40 units, every half unit
    series = [(t, apoptosis_at(t)) for t in times]
    plateau = series[-1][1]
    print(f"P(Apoptosis) at t = 40 units: {plateau:.3f}")
    print(f"P reaches 0.5 at t = {crossing(series, 0.5):.1f} units")
    print(f"P reaches half its t = 40 value ({plateau / 2:.3f}) at t = {crossing(series, plateau / 2):.1f} units")
