"""Write checks/boolean/activation-anchor-{fast,slow}/: NF-kB's activation route keeps Lipniacki's clock at any k_time.

Decision 30 (Option A). The coupled network's RIP1, RIP1ub and IKK nodes are taken VERBATIM from
workspace/datasets/calzone2010_cellfate/processed/cellfate_coupled.bnd. Their inputs are held: TNFR on, caspase-8 and
DISC_FAS off (so RIP1's logic `(DISC_FAS OR TNFR) AND NOT CASP8` holds), cIAP on (so RIP1ub's `cIAP AND RIP1` holds
once RIP1 is on). With `anchor_activation` = 1 each of the three switches on at r_act per second, whatever k_time is,
and none can switch off while its logic holds. So IKK is on at time t exactly when three independent exponential
waits at rate r have all ended, an Erlang(3, r) time:

    P(IKK on at t) = F(t) = 1 - exp(-r t) (1 + r t + (r t)^2 / 2).

MaBoSS reports the average over its last window [a, b]. With G(t) = -exp(-r t) (3 + 2 r t + (r t)^2 / 2) / r, an
antiderivative of F's complement, the window average is 1 - (G(b) - G(a)) / (b - a). The oracle is that formula, not
package output. r = r_act from processed/activation_anchor.json; the run ends at T = Lipniacki's IKK_active half-rise,
where F = 1/2 by construction, so the window average is just under 1/2. It is the same at k_time = 1/60 (-fast) and
1/6000 (-slow).

`--negative` sets anchor_activation = 0 (Calzone's clock) with the same expectations: the route then switches at
k_time per second, so the same window average with r = k_time is 0.2561 (fast) and 9e-7 (slow). The negatives read
0.2562 and 0.0 and fail (2026-11-06). They are not kept in the repository.

    uv run --project compose --frozen python -I checks/boolean/make_activation_anchor.py [--negative]
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
DATA = ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed"
COUPLED, ANCHOR = DATA / "cellfate_coupled.bnd", DATA / "activation_anchor.json"
HERE = Path(__file__).resolve().parent
ROUTE = {"RIP1": "logic = (DISC_FAS OR TNFR) AND (NOT CASP8);", "RIP1ub": "logic = cIAP AND RIP1;",
         "IKK": "logic = RIP1ub;"}
HELD = {"TNFR": 1.0, "CASP8": 0.0, "DISC_FAS": 0.0, "cIAP": 1.0}
CASES = {"fast": 1.0 / 60.0, "slow": 1.0 / 6000.0}
WINDOWS, SAMPLES = 8, 50_000
ABS_TOL = 0.01  # the standard error of P near 0.5 at 50000 samples is 0.0022


def _fail(message: str) -> NoReturn:
    sys.exit(f"make_activation_anchor.py: {message}")


def _fragment() -> str:
    """The coupled network's activation route verbatim, with its inputs held at constant values."""
    network = COUPLED.read_text()
    held = "\n\n".join(f"node {n} {{\n  rate_up = 0;\n  rate_down = 0;\n}}" for n in HELD)
    blocks = []
    for node, logic in ROUTE.items():
        match = re.search(rf"^node {node} \{{.*?^\}}", network, re.MULTILINE | re.DOTALL)
        if match is None or logic not in match.group(0) or "$anchor_activation" not in match.group(0):
            _fail(f"the coupled network's {node} node is not `{logic}` with an $anchor_activation switch-on")
        blocks.append(match.group(0))
    return held + "\n\n" + "\n\n".join(blocks) + "\n"


def window_average(r: float, a: float, b: float) -> float:
    """The average over [a, b] of the Erlang(3, r) CDF."""
    def g(t: float) -> float:
        return -math.exp(-r * t) * (3 + 2 * r * t + (r * t) ** 2 / 2) / r
    return 1.0 - (g(b) - g(a)) / (b - a)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", action="store_true", help="anchor_activation = 0, same expectations; must fail")
    args = parser.parse_args()
    anchor = json.loads(ANCHOR.read_text())
    r_act, t_end = anchor["r_act_per_s_for_ikk_half_rise"], anchor["ikk_active_half_rise_s"]
    expected = window_average(r_act, t_end * (WINDOWS - 1) / WINDOWS, t_end)
    switch = 0.0 if args.negative else 1.0
    initial = {**HELD, "RIP1": 0.0, "RIP1ub": 0.0, "IKK": 0.0}
    for label, k_time in CASES.items():
        name = f"activation-anchor-{label}" + ("-negative" if args.negative else "")
        document = {
            "global_time_precision": 6,
            "state": {
                "node_state": dict(initial),
                "node_probabilities": dict(initial),
                "parameters": {},
                "steps": 0,
                "cellfate": {
                    "_type": "process",
                    "address": "local:viva_maboss.processes.MaBoSSProcess",
                    "config": {
                        "network": _fragment(),
                        "parameters": {"k_time": k_time, "Low_RIP1": 0.0, "anchor_activation": switch,
                                       "r_act": r_act},
                        "initial_state": {n: v for n, v in initial.items() if v},
                        "sample_count": SAMPLES,
                        "windows_per_interval": WINDOWS,
                        "seed": 23,
                    },
                    "interval": t_end,
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
                f"Activation anchor (decision 30). The coupled network's RIP1, RIP1ub and IKK nodes (verbatim), with "
                f"TNFR and cIAP held on and CASP8 and DISC_FAS held off; anchor_activation = {switch:g}, k_time = "
                f"{k_time:.6g} per second, r_act = {r_act:.6g} per second. Each step switches on at r_act whatever "
                f"k_time is, so IKK is on at an Erlang(3, r_act) time; analytic oracle over the last window ending at "
                f"{t_end:g} s (Lipniacki's IKK_active half-rise): {expected:.7f}. With anchor_activation = 0 the route "
                f"runs on k_time and the case fails. Generated by checks/boolean/make_activation_anchor.py."),
            "document": "document.pbg",
            "interval": t_end,
            "scale_level": "molecule",
            "expect": [
                {"kind": "rows", "emitter": "emitter", "min": 2},
                {"kind": "scalar", "emitter": "emitter", "field": "steps", "expected": 1},
                {"kind": "scalar", "emitter": "emitter", "field": "node_probabilities.IKK",
                 "expected": round(expected, 6), "abs": ABS_TOL},
            ],
        }
        out = HERE / name
        out.mkdir(exist_ok=True)
        (out / "document.pbg").write_text(json.dumps(document, indent=2) + "\n")
        (out / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
        print(f"wrote checks/boolean/{name}: k_time {k_time:.6g}, anchor_activation {switch:g}, expected P(IKK on) "
              f"{expected:.6f}")


if __name__ == "__main__":
    main()
