"""Write checks/boolean/absorbing-death/: the composite's death nodes stay on once on (decision 28), analytic oracle.

The two death nodes, Apoptosis (logic CASP3) and NonACD (logic NOT ATP), are taken VERBATIM from
workspace/datasets/calzone2010_cellfate/processed/cellfate_coupled.bnd. Each one's cause is a node that is present at
t = 0 and goes away once, for good, at rate r: CASP3 starts on and switches off at r; ATP starts off and switches on
at r. While its cause is present, a death node switches on at rate k (k_time times Calzone's rate 1). After that its
switch-on rate is 0, and its switch-off rate is k when absorb_death = 0 and 0 when it is nonzero.

With absorb_death = 1 a death node that has switched on stays on, so it is on at t exactly when it switched on before
its cause went away. That happens at rate k while the cause is still present, which has probability exp(-r s) at time s:

    P(on at t) = integral_0^t k exp(-k s) exp(-r s) ds = k / (k + r) (1 - exp(-(k + r) t)).

MaBoSS reports the average over its last window [a, b], k / (k + r) (1 - (exp(-(k + r) a) - exp(-(k + r) b)) /
((k + r) (b - a))). The oracle is that formula, not package output. Here k = r = 1 and [a, b] = [7, 8], so both
nodes must read 0.5.

With absorb_death = 0 (Calzone's own nodes) each node also switches off again at rate k once its cause is gone, and
the same chain gives P(on at t) = t exp(-t) at k = r = 1, whose average over [7, 8] is 8 exp(-7) - 9 exp(-8) = 0.0043.
The negative reads 0.0048 (Apoptosis) and 0.0042 (NonACD) (2026-11-06). `--negative` writes that variant as absorbing-death-negative with the same
expectations. It must FAIL; it is not kept in the repository.

    uv run --project compose python -I checks/boolean/make_absorbing_death.py [--negative]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import NoReturn

import yaml

ROOT = Path(__file__).resolve().parents[2]
COUPLED = ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "cellfate_coupled.bnd"
HERE = Path(__file__).resolve().parent
K_TIME, R_CAUSE, UNITS, WINDOWS, SAMPLES = 1.0, 1.0, 8.0, 8, 50_000
ABS_TOL = 0.01  # the standard error of P near 0.5 at 50000 samples is 0.0022
DEATH = {"Apoptosis": "logic = CASP3;", "NonACD": "logic = NOT ATP;"}


def _fail(message: str) -> NoReturn:
    sys.exit(f"make_absorbing_death.py: {message}")


def _fragment() -> str:
    """The coupled network's two death nodes verbatim, each with a cause that goes away once at rate R_CAUSE."""
    network = COUPLED.read_text()
    blocks = []
    for node, logic in DEATH.items():
        match = re.search(rf"^node {node} \{{.*?^\}}", network, re.MULTILINE | re.DOTALL)
        if match is None or logic not in match.group(0) or "$absorb_death" not in match.group(0):
            _fail(f"the coupled network's {node} node is not `{logic}` with an $absorb_death switch-off")
        blocks.append(match.group(0))
    causes = (f"node CASP3 {{\n  rate_up = 0;\n  rate_down = {R_CAUSE};\n}}\n\n"
              f"node ATP {{\n  rate_up = {R_CAUSE};\n  rate_down = 0;\n}}\n")
    return causes + "\n" + "\n\n".join(blocks) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", action="store_true", help="absorb_death = 0, same expectations; must fail")
    args = parser.parse_args()
    absorb = 0.0 if args.negative else 1.0
    name = "absorbing-death-negative" if args.negative else "absorbing-death"
    s = K_TIME + R_CAUSE
    a, b = UNITS * (WINDOWS - 1) / WINDOWS, UNITS
    expected = K_TIME / s * (1.0 - (math.exp(-s * a) - math.exp(-s * b)) / (s * (b - a)))
    initial = {"ATP": 0.0, "Apoptosis": 0.0, "CASP3": 1.0, "NonACD": 0.0}
    document = {
        "global_time_precision": 6,
        "state": {
            "node_state": initial,
            "node_probabilities": dict(initial),
            "parameters": {},
            "steps": 0,
            "cellfate": {
                "_type": "process",
                "address": "local:viva_maboss.processes.MaBoSSProcess",
                "config": {
                    "network": _fragment(),
                    "parameters": {"k_time": K_TIME, "absorb_death": absorb},
                    "initial_state": {"CASP3": 1.0},
                    "sample_count": SAMPLES,
                    "windows_per_interval": WINDOWS,
                    "seed": 17,
                },
                "interval": UNITS,
                "inputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                           "parameters": ["parameters"], "steps": ["steps"]},
                "outputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                            "steps": ["steps"]},
            },
            "emitter": {
                "_type": "step",
                "address": "local:RAMEmitter",
                "config": {"emit": {"node_probabilities": "map[float]", "steps": "integer"}},
                "inputs": {"node_probabilities": ["node_probabilities"], "steps": ["steps"]},
            },
        },
    }
    case = {
        "description": (
            f"Absorbing death (decision 28). The coupled network's Apoptosis and NonACD nodes (verbatim), absorb_death = "
            f"{absorb:g}, k_time = 1; each one's cause (CASP3 on, ATP off at t = 0) goes away once at rate 1. A death "
            f"node that switched on while its cause was present stays on, so P(on) = k/(k+r) (1 - exp(-(k+r) t)); "
            f"analytic oracle over the last window [7, 8]: {expected:.7f}. With absorb_death = 0, P(on) = t exp(-t) "
            f"(0.0043 over the window; measured 0.0048 and 0.0042) and the case fails. Generated by checks/boolean/make_absorbing_death.py."),
        "document": "document.pbg",
        "interval": UNITS,
        "scale_level": "molecule",
        "expect": [
            {"kind": "rows", "emitter": "emitter", "min": 2},
            {"kind": "scalar", "emitter": "emitter", "field": "steps", "expected": 1},
            *({"kind": "scalar", "emitter": "emitter", "field": f"node_probabilities.{n}",
               "expected": round(expected, 6), "abs": ABS_TOL} for n in DEATH),
        ],
    }
    out = HERE / name
    out.mkdir(exist_ok=True)
    (out / "document.pbg").write_text(json.dumps(document, indent=2) + "\n")
    (out / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote checks/boolean/{name}: absorb_death {absorb:g}, expected P(on) {expected:.6f}")


if __name__ == "__main__":
    main()
