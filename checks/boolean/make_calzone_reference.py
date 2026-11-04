"""Write checks/boolean/calzone-reference/: MaBoSSProcess on Calzone 2010's full cell-fate network against MaBoSS's own
reference run of it.

The oracle is upstream, not ours. sysbio-curie/MaBoSS ships the network, its configuration and the engine's reference
output for that configuration (``engine/tests/maboss/cellfate/{cellfate.bnd, cellfate.cfg, refer/res_probtraj.csv}``,
fetched at a pinned commit into workspace/datasets/calzone2010_cellfate/raw/). The reference is 100000 trajectories over
max_time 10 with time_tick 0.1. Its last row is the window [9.9, 10.0], which is exactly the window MaBoSSProcess
reports after one interval of 10 split into 100 windows. Each node's expected probability is the sum of the reference's
joint-state probabilities over the states in which that node is on, so every node of the network is checked, on or off.

What it proves: that the Process passes the network, every ``$`` parameter (including ``TransRate = 1/24``) and the
initial states to the engine as the reference configuration does, and reads back node probabilities over the right
window. Under the reference condition (TNF off) only mROS moves: it switches on at TransRate because NFkB stays off, so
its window average is also known analytically, ``1 - (exp(-9.9/24) - exp(-10/24)) / (0.1/24)``, and the script checks
the reference against that formula before writing anything.

    uv run --project compose python -I checks/boolean/make_calzone_reference.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import NoReturn

import yaml

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "raw"
OUT = Path(__file__).resolve().parent / "calzone-reference"
SHA256 = {  # sysbio-curie/MaBoSS@375ffadb346adf4173536705fc7efad6c4602714, engine/tests/maboss/cellfate/
    "cellfate.bnd": "cfef1e7054d77f4736d8e36e712946ad1043c2f967913e400ec449b56a3d26dc",
    "cellfate.cfg": "3734729982e66a71c5f491171a2ae37086fb7f81c0f705a58dc9ec514f20ab21",
    "res_probtraj.csv": "cb88e0760d6487d8942727900192588d2282ea6594ba3bb4b18fc1a228ce32ae",
}
INTERVAL = 10.0
WINDOWS = 100
SAMPLES = 100_000
# MaBoSS reports each probability with a standard error; at 100000 samples it is at most 0.0016 for any node here,
# for the reference and for this run alike, so 0.008 is about 3.5 combined standard errors.
ABS_TOL = 0.008


def _fail(message: str) -> NoReturn:
    sys.exit(f"make_calzone_reference.py: {message}")


def _read(name: str) -> str:
    data = (RAW / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256[name]:
        _fail(f"raw/{name} is not the pinned upstream file")
    return data.decode()


def _config(cfg: str) -> tuple[dict[str, float], dict[str, float], float, float]:
    """The reference configuration's $parameters, initial states, max_time and time_tick."""
    parameters = {}
    for name, expression in re.findall(r"^\$(\w+)\s*=\s*([^;]+);", cfg, re.MULTILINE):
        numerator, _, denominator = expression.partition("/")
        parameters[name] = float(numerator) / float(denominator) if denominator else float(numerator)
    istates = {node: float(value) for node, value in re.findall(r"^(\w+)\.istate\s*=\s*([01]);", cfg, re.MULTILINE)}
    return parameters, istates, _setting(cfg, "max_time"), _setting(cfg, "time_tick")


def _setting(cfg: str, key: str) -> float:
    match = re.search(rf"^{key}\s*=\s*([^;]+);", cfg, re.MULTILINE)
    if match is None:
        _fail(f"the reference configuration has no {key}")
    return float(match.group(1))


def _last_window_marginals(probtraj: str, nodes: list[str]) -> tuple[float, dict[str, float]]:
    rows = list(csv.reader(probtraj.splitlines(), delimiter="\t"))
    header, last = rows[0], rows[-1]
    first_state = header.index("State")
    marginals = dict.fromkeys(nodes, 0.0)
    for i in range(first_state, len(last) - 2, 3):
        on = set() if last[i] == "<nil>" else set(last[i].split(" -- "))
        for node in on:
            marginals[node] += float(last[i + 1])
    return float(last[0]), marginals


def main() -> None:
    network = _read("cellfate.bnd")
    parameters, istates, max_time, time_tick = _config(_read("cellfate.cfg"))
    nodes = sorted(re.findall(r"^node\s+(\w+)", network, re.MULTILINE | re.IGNORECASE))
    if (max_time, time_tick) != (INTERVAL, INTERVAL / WINDOWS):
        _fail(f"the reference ran max_time {max_time}, time_tick {time_tick}; this case assumes 10 and 0.1")
    if set(istates) != set(nodes) or any(v not in (0.0, 1.0) for v in istates.values()):
        _fail("the reference configuration does not give every node a 0 or 1 initial state")
    window_start, expected = _last_window_marginals(_read("res_probtraj.csv"), nodes)
    if not math.isclose(window_start, INTERVAL - time_tick):
        _fail(f"the reference's last row starts at {window_start}, not {INTERVAL - time_tick}")

    rate = parameters["TransRate"]
    analytic = 1.0 - (math.exp(-rate * 9.9) - math.exp(-rate * 10.0)) / (rate * 0.1)
    if abs(expected["mROS"] - analytic) > 0.005:
        _fail(f"the reference's mROS ({expected['mROS']}) disagrees with its analytic value ({analytic})")

    document = {
        "global_time_precision": 6,
        "state": {
            "node_state": {n: istates[n] for n in nodes},
            "node_probabilities": {n: istates[n] for n in nodes},
            "parameters": {},
            "steps": 0,
            "cellfate": {
                "_type": "process",
                "address": "local:viva_maboss.processes.MaBoSSProcess",
                "config": {
                    "network": network,
                    "parameters": parameters,
                    "initial_state": {n: v for n, v in istates.items() if v},
                    "sample_count": SAMPLES,
                    "windows_per_interval": WINDOWS,
                    "seed": 233814379,
                },
                "interval": INTERVAL,
                "inputs": {
                    "node_state": ["node_state"],
                    "node_probabilities": ["node_probabilities"],
                    "parameters": ["parameters"],
                    "steps": ["steps"],
                },
                "outputs": {
                    "node_state": ["node_state"],
                    "node_probabilities": ["node_probabilities"],
                    "steps": ["steps"],
                },
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
            "MaBoSSProcess on Calzone 2010's full cell-fate network (31 nodes, the reference configuration: TNF off, "
            "TransRate 1/24), one interval of 10 in 100 windows, 100000 trajectories. Every node's probability over "
            "the last window [9.9, 10] is compared with MaBoSS's own reference output for that configuration "
            "(sysbio-curie/MaBoSS@375ffad engine/tests/maboss/cellfate/refer/res_probtraj.csv, summed over joint "
            f"states). The only node that moves is mROS, whose reference value {expected['mROS']:.6f} also matches "
            f"its analytic window average {analytic:.6f}. Tolerance {ABS_TOL}, about 3.5 combined standard errors. "
            "Generated by checks/boolean/make_calzone_reference.py."
        ),
        "document": "document.pbg",
        "interval": INTERVAL,
        "scale_level": "molecule",
        "expect": [
            {"kind": "rows", "emitter": "emitter", "min": 2},
            {"kind": "scalar", "emitter": "emitter", "field": "steps", "expected": 1},
            *(
                {"kind": "scalar", "emitter": "emitter", "field": f"node_probabilities.{n}",
                 "expected": round(expected[n], 6), "abs": ABS_TOL}
                for n in nodes
            ),
        ],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "document.pbg").write_text(json.dumps(document, indent=2) + "\n")
    (OUT / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(nodes)} nodes; mROS reference {expected['mROS']:.6f}, "
          f"analytic {analytic:.6f}")


if __name__ == "__main__":
    main()
