"""Write checks/boolean/pair-nfkb-{analytic,seconds}/: the kinetic -> Boolean coupling, with an analytic oracle.

The composite's coupling, exactly as it will be wired: Lipniacki's five NF-kB-carrying species (uM) feed a
MathExpressionStep that evaluates the driven SBML's own assignment rule
NFKB_total = IKKactive_IkB_NFKB + NFKB + IkB_NFKB + (NFKB_nuc + IkB_NFKB_nuc) / Kv (Kv = 5), then
f = (NFKB_nuc / Kv) / NFKB_total, the free nuclear fraction of all NF-kB (no fitted constant), and writes
`u_NFkB = f` and `d_NFkB = 1 - f` into MaBoSSProcess's `parameters` map. The Boolean layer is the reduced cell-fate
network (workspace/datasets/calzone2010_cellfate/processed/cellfate_reduced.bnd).

The kinetic layer is held at Lipniacki's post-stimulus NFKB_nuc peak (BIOMD0000000786 sim1, t = 364014 s; COPASI and
Tellurium agree; viva-biomodels corpus_timecourse.parquet), where the rule gives NFKB_total = 0.06 (it is conserved over
the whole run) and f = 0.5626781. TNF is off, so no death-receptor
signal reaches CASP8, CASP3 stays off, and NFkB switches on at rate f and off at rate 1 - f from off. Its probability is
then exactly P(t) = f (1 - exp(-t)), and over MaBoSS's last window [a, b] the reported average is
f (1 - (exp(-a) - exp(-b)) / (b - a)). The oracle is that formula, not package output.

The defaults of `$u_NFkB` / `$d_NFkB` in the Process's config, and their seeded values in the `parameters` store, are
0, so if the Step did not write them before the Process's first update, NFkB would stay off and the case would fail.
The store must hold the keys before the Step writes them: process-bigraph 1.9.1 silently drops a write to a
map[float] key the store does not hold yet (probed 2026-11-04; an unseeded store stayed empty and NFkB stayed off).

    uv run --project compose python -I checks/boolean/make_pair_nfkb_analytic.py
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REDUCED = ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "cellfate_reduced.bnd"
HERE = Path(__file__).resolve().parent
# Lipniacki's NF-kB-carrying species (uM) at its post-stimulus NFKB_nuc maximum, t = 364014 s of BIOMD0000000786 sim1
# (COPASI; viva-biomodels corpus_timecourse.parquet). NFKB_total stays 0.0599999987 over the whole run there.
PEAK = {
    "IKKactive_IkB_NFKB": 3.2746876968303695e-05,
    "NFKB": 0.02616054192185402,
    "IkB_NFKB": 4.180367250228301e-05,
    "NFKB_nuc": 0.16880343854427338,
    "IkB_NFKB_nuc": 2.110206514771562e-05,
}
KV = 5.0  # Lipniacki 2004: Kv = V_cyt / V_nuc (driven SBML, ModelValue_1 = Kv)
# the driven SBML's assignment rule, verbatim in its terms
NFKB_TOTAL_RULE = "IKKactive_IkB_NFKB + NFKB + IkB_NFKB + (NFKB_nuc + IkB_NFKB_nuc) / Kv"
WINDOWS, SAMPLES = 20, 50_000
ABS_TOL = 0.01  # the standard error of P near 0.5 at 50000 samples is 0.0022


def write(name: str, k_time: float, interval: float) -> None:
    network = REDUCED.read_text()
    nodes = sorted(re.findall(r"^node\s+(\w+)", network, re.MULTILINE))
    on = {"FADD", "ATP"}  # cellfate.cfg's istates for the kept nodes; TNF off
    total = PEAK["IKKactive_IkB_NFKB"] + PEAK["NFKB"] + PEAK["IkB_NFKB"] + (PEAK["NFKB_nuc"] + PEAK["IkB_NFKB_nuc"]) / KV
    f = (PEAK["NFKB_nuc"] / KV) / total
    # MaBoSS's last window, in Calzone units: the rates are multiplied by k_time (units per composite time unit)
    a, b = k_time * interval * (WINDOWS - 1) / WINDOWS, k_time * interval
    expected = f * (1.0 - (math.exp(-a) - math.exp(-b)) / (b - a))
    initial = {n: float(n in on) for n in nodes}
    document = {
        "global_time_precision": 6,
        "state": {
            "kinetic": dict(PEAK),
            "node_state": initial,
            "node_probabilities": dict(initial),
            # the driven keys must exist before the Step writes them: process-bigraph 1.9.1 drops a write to a
            # map[float] key the store does not hold yet (probed 2026-11-04: empty map stays empty)
            "parameters": {"u_NFkB": 0.0, "d_NFkB": 0.0},
            "steps": 0,
            "nfkb_total": 0.0,
            "nuclear_fraction": {
                "_type": "step",
                "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
                "config": {
                    "expressions": [
                        {"out": "NFKB_total", "expr": NFKB_TOTAL_RULE},
                        {"out": "u_NFkB", "expr": "(NFKB_nuc / Kv) / NFKB_total"},
                        {"out": "d_NFkB", "expr": "1 - u_NFkB"},
                    ],
                    "params": {"Kv": KV},
                },
                "inputs": {name: ["kinetic", name] for name in PEAK},
                "outputs": {"NFKB_total": ["nfkb_total"], "u_NFkB": ["parameters", "u_NFkB"],
                            "d_NFkB": ["parameters", "d_NFkB"]},
            },
            "cellfate": {
                "_type": "process",
                "address": "local:viva_maboss.processes.MaBoSSProcess",
                "config": {
                    "network": network,
                    "parameters": {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "TransRate": 1 / 24,
                                   "u_NFkB": 0.0, "d_NFkB": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
                                   "k_time": k_time},
                    "initial_state": {n: 1.0 for n in on},
                    "sample_count": SAMPLES,
                    "windows_per_interval": WINDOWS,
                    "seed": 11,
                },
                "interval": interval,
                "inputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                           "parameters": ["parameters"], "steps": ["steps"]},
                "outputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                            "steps": ["steps"]},
            },
            "emitter": {
                "_type": "step",
                "address": "local:RAMEmitter",
                "config": {"emit": {"node_probabilities": "map[float]", "parameters": "map[float]",
                                    "nfkb_total": "float", "steps": "integer"}},
                "inputs": {"node_probabilities": ["node_probabilities"], "parameters": ["parameters"],
                           "nfkb_total": ["nfkb_total"], "steps": ["steps"]},
            },
        },
    }
    case = {
        "description": (
            "Kinetic -> Boolean coupling. Lipniacki's five NF-kB species held at its post-stimulus NFKB_nuc peak "
            f"(NFKB_nuc {PEAK['NFKB_nuc']:.7f} uM, sim1 t = 364014 s) -> MathExpressionStep: NFKB_total from the "
            f"driven SBML's own rule ({total:.10f}), f = (NFKB_nuc/Kv)/NFKB_total = {f:.7f} -> MaBoSSProcess "
            "parameters u_NFkB = f, "
            "d_NFkB = 1 - f, on the reduced cell-fate network with TNF off. One interval of "
            f"{interval:g} in 20 windows at k_time = {k_time:.10g} ({k_time * interval:g} Calzone units), 50000 "
            f"trajectories. Analytic oracle: f (1 - (exp(-{a:g}) - exp(-{b:g})) / {b - a:g}) = {expected:.7f} for P(NFkB on) over "
            f"the last window. The death arms stay off (CASP8, CASP3, Apoptosis, NonACD 0). The parameters store must hold "
            "the Step's values. Generated by checks/boolean/make_pair_nfkb_analytic.py."
        ),
        "document": "document.pbg",
        "interval": interval,
        "scale_level": "molecule",
        "expect": [
            {"kind": "rows", "emitter": "emitter", "min": 2},
            {"kind": "scalar", "emitter": "emitter", "field": "steps", "expected": 1},
            {"kind": "scalar", "emitter": "emitter", "field": "nfkb_total", "expected": total, "rel": 1e-12},
            {"kind": "scalar", "emitter": "emitter", "field": "parameters.u_NFkB", "expected": f, "rel": 1e-12},
            {"kind": "scalar", "emitter": "emitter", "field": "parameters.d_NFkB", "expected": 1 - f, "rel": 1e-12},
            {"kind": "scalar", "emitter": "emitter", "field": "node_probabilities.NFkB", "expected": expected,
             "abs": ABS_TOL},
            *({"kind": "scalar", "emitter": "emitter", "field": f"node_probabilities.{n}", "expected": 0.0,
               "abs": 1e-9} for n in ("CASP8", "CASP3", "Apoptosis", "NonACD")),
        ],
    }
    out = HERE / name
    out.mkdir(exist_ok=True)
    (out / "document.pbg").write_text(json.dumps(document, indent=2) + "\n")
    (out / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote checks/boolean/{name}: f = {f:.7f}, k_time {k_time:.6g}, expected P(NFkB on) = {expected:.7f}")


def main() -> None:
    write("pair-nfkb-analytic", k_time=1.0, interval=2.0)
    # the same 2 Calzone units, with the clock converted: one Calzone unit per 600 s, run for 1200 s. The oracle is
    # unchanged, which shows $k_time converts time and nothing else.
    write("pair-nfkb-seconds", k_time=1.0 / 600.0, interval=1200.0)


if __name__ == "__main__":
    main()
