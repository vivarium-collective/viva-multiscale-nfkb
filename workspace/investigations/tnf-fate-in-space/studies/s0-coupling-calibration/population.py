"""Build and run one population document for Study 0: one kinetic layer, N independent cell-fate networks.

Lipniacki's kinetics are deterministic, so every cell sees the same NF-kB trajectory; each cell's fate network
(MaBoSSProcess, sample_count 1, its own seed) is one stochastic cell. A summing MathExpressionStep counts the cells in
each fate at every tick, so the results file holds the population counts and NF-kB's f, not N x 31 nodes per tick.

The document is built from the registered composite spec (viva_multiscale_nfkb/composites/kinetic_boolean.composite.json)
and run through compose-api's own runner (compose/runner.py, vendored at 0.7.78) in the pinned environment compose/,
exactly as the workspace's checks run, so results are what compose-api would produce.

    uv run --project compose python -I <this file> --kappa K --k-time T --cells N --hours H --out DIR [--seed S]
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SPEC = ROOT / "viva_multiscale_nfkb" / "composites" / "kinetic_boolean.composite.json"
SBML = ROOT / "workspace" / "datasets" / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
FATES = ("Survival", "Apoptosis", "NonACD")


def _substitute(node, values):
    if isinstance(node, dict):
        return {k: _substitute(v, values) for k, v in node.items()}
    if isinstance(node, list):
        return [_substitute(v, values) for v in node]
    if isinstance(node, str):
        full = re.fullmatch(r"\$\{(\w+)\}", node)
        if full:
            return values[full.group(1)]
    return node


def build(kappa: float, k_time: float, cells: int, seed: int, interval: float) -> dict:
    spec = json.loads(SPEC.read_text())
    values = {name: p["default"] for name, p in spec["parameters"].items()}
    values.update({"kappa": kappa, "k_time": k_time, "interval": interval, "sample_count": 1})
    state = _substitute(spec["state"], {**values, "seed": seed})
    one = state.pop("cellfate")
    template = {k: state.pop(k) for k in ("node_state", "node_probabilities", "steps")}
    state.pop("emitter")
    state["cells"] = {}
    for i in range(cells):
        name = f"c{i}"
        cell = copy.deepcopy(one)
        cell["config"]["seed"] = seed + i
        cell["inputs"] = {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                          "parameters": ["..", "..", "parameters"], "steps": ["steps"]}
        cell["outputs"] = {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                           "steps": ["steps"]}
        state["cells"][name] = {**copy.deepcopy(template), "fate": cell}
    sums = [{"out": f"n_{fate}", "expr": " + ".join(f"{fate}_{i}" for i in range(cells))} for fate in FATES]
    # the time of the count; reading global_time is also what triggers this Step every tick, because each cell's
    # MaBoSSProcess writes its whole node_state map, a parent of the per-node inputs (see the composite spec)
    sums.append({"out": "counted_at", "expr": "global_time"})
    state["counts"] = {f"n_{fate}": 0.0 for fate in FATES}
    state["counted_at"] = 0.0
    state["count_fates"] = {
        "_type": "step",
        "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
        "config": {"expressions": sums},
        "inputs": {**{f"{fate}_{i}": ["cells", f"c{i}", "node_state", fate] for fate in FATES for i in range(cells)},
                   "global_time": ["global_time"]},
        "outputs": {**{f"n_{fate}": ["counts", f"n_{fate}"] for fate in FATES}, "counted_at": ["counted_at"]},
    }
    state["emitter"] = {
        "_type": "step",
        "address": "local:RAMEmitter",
        "config": {"emit": {"counts": "map[float]", "counted_at": "float", "nfkb_fraction": "float",
                            "nfkb_fraction_time": "float", "global_time": "float"}},
        "inputs": {"counts": ["counts"], "counted_at": ["counted_at"], "nfkb_fraction": ["nfkb_fraction"],
                   "nfkb_fraction_time": ["nfkb_fraction_time"], "global_time": ["global_time"]},
    }
    return {"global_time_precision": 6, "state": state}


def run(document: dict, hours: float, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    (out / "document.pbg").write_text(json.dumps(document))
    omex = out / "input.omex"
    with zipfile.ZipFile(omex, "w") as z:
        z.write(out / "document.pbg", "document.pbg")
        z.write(SBML, SBML.name)
    log = out / "runner.log"
    with log.open("w") as f:
        subprocess.run(["uv", "run", "--project", str(ROOT / "compose"), "--frozen", "python", "-I",
                        str(ROOT / "compose" / "runner.py"), "run", str(omex), "-o", str(out / "output"),
                        "-n", str(hours * 3600.0)], check=True, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    return next((out / "output").glob("results_*.pber"))


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--kappa", type=float, required=True)
    a.add_argument("--k-time", type=float, required=True)
    a.add_argument("--cells", type=int, required=True)
    a.add_argument("--hours", type=float, required=True)
    a.add_argument("--interval", type=float, default=30.0)
    a.add_argument("--seed", type=int, default=1)
    a.add_argument("--out", type=Path, required=True)
    args = a.parse_args()
    pber = run(build(args.kappa, args.k_time, args.cells, args.seed, args.interval), args.hours, args.out)
    rows = json.loads(pber.read_text())["emitter"]
    last = rows[-1]
    print(json.dumps({"pber": str(pber), "rows": len(rows), "t_end_s": last["global_time"],
                      "f_end": last["nfkb_fraction"], **{k: v / args.cells for k, v in last["counts"].items()}}))


if __name__ == "__main__":
    sys.exit(main())
