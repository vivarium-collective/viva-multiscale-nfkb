"""Build and run one population document for Study 0: one kinetic layer, N independent cell-fate networks.

Lipniacki's kinetics are deterministic, so every cell sees the same NF-kB trajectory; each cell's fate network
(MaBoSSProcess, sample_count 1, its own seed) is one stochastic cell. A MathExpressionStep records, at every tick,
each cell's fate code (Survival + 2*Apoptosis + 4*NonACD), so the results file holds one number per cell
per tick and NF-kB's f, not N x 31 nodes per tick.

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
# Named network edits for knockout variants. Each is an exact (old, new) replacement in the coupled network; build()
# refuses an edit whose old text is not present exactly once, so a variant can never silently be the baseline.
TURNOVER = ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "turnover_anchor.json"
# Each replacement is (node, old, new): `old` must occur exactly once inside that node's block (node None: in the whole
# network), so an edit can never silently miss, or hit, the wrong node. `parameters` are added to the MaBoSS config.
EDITS = {
    # caspase-8 no longer cleaves RIP1
    "casp8-rip1-ko": {"replacements": [("RIP1", "logic = (DISC_FAS OR TNFR) AND (NOT CASP8);",
                                        "logic = (DISC_FAS OR TNFR);")]},
    # SMAC no longer sequesters cIAP: it acts twice in Calzone, in cIAP's logic and in its decay rate
    "smac-ciap-ko": {"replacements": [("cIAP", "logic = (mcIAP AND (NOT SMAC));", "logic = (mcIAP);"),
                                      ("cIAP", "(($Low_cIAP ? 1e+100 : ((SMAC) ? 1 : 0)))",
                                       "(($Low_cIAP ? 1e+100 : 0))")]},
    # Study 0b (Alex, 2026-11-06: "Anchor protein decay"): the transcription-scale products switch OFF at Lipniacki's
    # protein turnover, r_deg per second (A20's c5; anchor_turnover.py), whatever k_time is, instead of Calzone's unit
    # rate x k_time. cIAP is left alone: it switches off only when SMAC sequesters it, which is not turnover.
    "decay-lipniacki": {
        "replacements": [
            ("cFLIP", "rate_down = $k_time * ((@logic ? 0 : 1));", "rate_down = $k_time * ((@logic ? 0 : ($r_deg / $k_time)));"),
            *[(node, "rate_down = $k_time * (@logic ? 0 : 1);", "rate_down = $k_time * (@logic ? 0 : ($r_deg / $k_time));")
              for node in ("BCL2", "mROS", "mcIAP", "mXIAP", "Survival")],
        ],
        "parameters": {"r_deg": "turnover_anchor"},
    },
    # Study 0c (Alex, 2026-11-06: "Run 0c bound first"): an upper bound, not a model. NF-kB's PROTECTIVE products never
    # switch off once made. cFLIP blocks caspase-8, BCL2 blocks MOMP and MPT, and mXIAP and mcIAP are the transcripts of
    # XIAP and cIAP. Unlike decay-lipniacki, this leaves alone:
    # - mROS, which is on when NF-kB is OFF and licenses ROS, a necrosis driver;
    # - Survival, the phenotype readout, not a protein.
    # XIAP and cIAP still switch off when SMAC removes them, which is not turnover.
    "persist-protective": {
        "replacements": [
            ("cFLIP", "rate_down = $k_time * ((@logic ? 0 : 1));", "rate_down = 0;"),
            *[(node, "rate_down = $k_time * (@logic ? 0 : 1);", "rate_down = 0;") for node in ("BCL2", "mcIAP", "mXIAP")],
        ],
    },
}


def _apply(network: str, edit: str) -> tuple[str, dict]:
    spec = EDITS[edit]
    for node, old, new in spec["replacements"]:
        if node is None:
            if network.count(old) != 1:
                raise SystemExit(f"edit {edit}: {old!r} is not in the network exactly once")
            network = network.replace(old, new)
            continue
        match = re.search(rf"^node {node} \{{.*?^\}}", network, re.MULTILINE | re.DOTALL)
        if match is None or match.group(0).count(old) != 1:
            raise SystemExit(f"edit {edit}: {old!r} is not in node {node} exactly once")
        network = network.replace(match.group(0), match.group(0).replace(old, new))
    parameters = {}
    for name, source in spec.get("parameters", {}).items():
        if source == "turnover_anchor":
            parameters[name] = json.loads(TURNOVER.read_text())["r_deg_per_s"]
    return network, parameters


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


def build(kappa: float, k_time: float, cells: int, seed: int, interval: float, edits: tuple[str, ...] = ()) -> dict:
    spec = json.loads(SPEC.read_text())
    values = {name: p["default"] for name, p in spec["parameters"].items()}
    values.update({"kappa": kappa, "k_time": k_time, "interval": interval, "sample_count": 1})
    state: dict = _substitute(spec["state"], {**values, "seed": seed})
    one = state.pop("cellfate")
    for edit in edits:
        one["config"]["network"], added = _apply(one["config"]["network"], edit)
        one["config"]["parameters"].update(added)
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
    # Each cell's fate CODE every tick: Survival + 2*Apoptosis + 4*NonACD. Calzone's fate nodes are not mutually
    # exclusive (a cell can show caspase-3 and ATP loss together), so fates are never summed across nodes; run_grid.py
    # classifies each cell by the first fate it reaches and reports overlaps separately.
    codes = [{"out": f"code_{i}", "expr": f"Survival_{i} + 2*Apoptosis_{i} + 4*NonACD_{i}"} for i in range(cells)]
    # the time of the coding; reading global_time is also what triggers this Step every tick, because each cell's
    # MaBoSSProcess writes its whole node_state map, a parent of the per-node inputs (see the composite spec)
    codes.append({"out": "coded_at", "expr": "global_time"})
    # every key the Step writes is seeded: process-bigraph 1.9.1 drops a write to a map key the store lacks
    state["fate_codes"] = {f"c{i}": 0.0 for i in range(cells)}
    state["coded_at"] = 0.0
    state["code_fates"] = {
        "_type": "step",
        "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
        "config": {"expressions": codes},
        "inputs": {**{f"{fate}_{i}": ["cells", f"c{i}", "node_state", fate] for fate in FATES for i in range(cells)},
                   "global_time": ["global_time"]},
        "outputs": {**{f"code_{i}": ["fate_codes", f"c{i}"] for i in range(cells)}, "coded_at": ["coded_at"]},
    }
    state["emitter"] = {
        "_type": "step",
        "address": "local:RAMEmitter",
        "config": {"emit": {"fate_codes": "map[float]", "coded_at": "float", "nfkb_fraction": "float",
                            "nfkb_fraction_time": "float", "global_time": "float"}},
        "inputs": {"fate_codes": ["fate_codes"], "coded_at": ["coded_at"], "nfkb_fraction": ["nfkb_fraction"],
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
    a.add_argument("--edit", action="append", default=[], choices=sorted(EDITS), help="named network edit (repeatable)")
    args = a.parse_args()
    pber = run(build(args.kappa, args.k_time, args.cells, args.seed, args.interval, tuple(args.edit)), args.hours,
               args.out)
    rows = json.loads(pber.read_text())["emitter"]
    last = rows[-1]
    print(json.dumps({"pber": str(pber), "rows": len(rows), "t_end_s": last["global_time"],
                      "f_end": last["nfkb_fraction"], "coded_at_end": last["coded_at"]}))


if __name__ == "__main__":
    sys.exit(main())
