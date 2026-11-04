"""Write checks/boolean/pair-nfkb-{analytic,seconds}/: the kinetic -> Boolean coupling, with an analytic oracle.

The coupling, exactly as the composite wires it. Lipniacki's five NF-kB-carrying species (uM) feed a MathExpressionStep.
The Step evaluates the driven SBML's own `NFKB_total` assignment rule, READ FROM THE SBML by this script (not
transcribed), then f = (NFKB_nuc / Kv) / NFKB_total, the free nuclear fraction of all NF-kB (no fitted constant). It
writes `u_NFkB = f` and `d_NFkB = 1 - f` into MaBoSSProcess's `parameters` map.

The Boolean side is the coupled network's NFkB node, taken VERBATIM from
workspace/datasets/calzone2010_cellfate/processed/cellfate_coupled.bnd, with its route held open. Its own logic is
`IKK AND (NOT CASP3)` (Calzone gates); here IKK is a node held on and CASP3 a node held off (rates 0, initial states 1
and 0). The question this check isolates is whether the node follows Lipniacki's f once Calzone's gate is open. The
rest of the gate is checked against the full network in coupled-equals-full.

The kinetic layer is held at Lipniacki's post-stimulus NFKB_nuc peak (BIOMD0000000786 sim1, t = 364014 s; COPASI and
Tellurium agree; viva-biomodels corpus_timecourse.parquet), where the rule gives NFKB_total = 0.06 (conserved over the
whole run) and f = 0.5626781. With the gate open, NFkB switches on at rate f and off at 1 - f (times k_time). Starting
off, P(t) = f (1 - exp(-k t)), and over MaBoSS's last window [a, b] (Calzone units) the reported average is
f (1 - (exp(-a) - exp(-b)) / (b - a)). The oracle is that formula, not package output.

The `parameters` store and the Process's defaults hold u_NFkB = d_NFkB = 0, so if the Step did not write them first,
NFkB would stay off and the case would fail. The store must hold the keys before the Step writes them: process-bigraph
1.9.1 silently drops a write to a map[float] key the store does not hold yet (probed 2026-11-04).

    uv run --project compose python -I checks/boolean/make_pair_nfkb_analytic.py
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import NoReturn

import libsbml
import sympy
import yaml

ROOT = Path(__file__).resolve().parents[2]
COUPLED = ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "cellfate_coupled.bnd"
SBML = ROOT / "workspace" / "datasets" / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
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
WINDOWS, SAMPLES = 20, 50_000
ABS_TOL = 0.01  # the standard error of P near 0.5 at 50000 samples is 0.0022


def _fail(message: str) -> NoReturn:
    sys.exit(f"make_pair_nfkb_analytic.py: {message}")


def _rule_from_sbml() -> tuple[str, float]:
    """The driven SBML's NFKB_total rule as an expression in species names and Kv, and Kv's value."""
    # Keep the document referenced while its model is used: libsbml frees a temporary document's model with it, and a
    # value read through a freed model is garbage (it read Kv as 0.0 in the composite generator, 2026-11-04).
    document = libsbml.readSBMLFromFile(str(SBML))
    model = document.getModel()
    rule = model.getRule("NFKB_total")
    if rule is None or not rule.isAssignment():
        _fail("the SBML has no NFKB_total assignment rule")
    kv_alias = model.getInitialAssignmentBySymbol("ModelValue_1")
    if kv_alias is None or libsbml.formulaToL3String(kv_alias.getMath()) != "Kv":
        _fail("ModelValue_1 is not initialised to Kv")
    expression = libsbml.formulaToL3String(rule.getMath()).replace("ModelValue_1", "Kv")
    if {str(s) for s in sympy.sympify(expression).free_symbols} != {*PEAK, "Kv"}:
        _fail(f"the NFKB_total rule's symbols are not the five NF-kB species and Kv: {expression}")
    kv = model.getParameter("Kv").getValue()
    if not kv > 0:
        _fail(f"Kv read as {kv}; expected Lipniacki's V_cyt/V_nuc = 5")
    return expression, kv


def _fragment() -> str:
    """The coupled network's NFkB node verbatim, with its gate (IKK, CASP3) as nodes held at open (1, 0)."""
    network = COUPLED.read_text()
    match = re.search(r"^node NFkB \{.*?^\}", network, re.MULTILINE | re.DOTALL)
    if match is None or "logic = IKK AND (NOT CASP3);" not in match.group(0):
        _fail("the coupled network's NFkB node is not gated by IKK AND (NOT CASP3)")
    held = "node IKK {\n  rate_up = 0;\n  rate_down = 0;\n}\n\nnode CASP3 {\n  rate_up = 0;\n  rate_down = 0;\n}\n"
    return held + "\n" + match.group(0) + "\n"


def write(name: str, k_time: float, interval: float, rule: str, kv: float) -> None:
    network = _fragment()
    total = float(sympy.sympify(rule).subs({**PEAK, "Kv": kv}))
    f = (PEAK["NFKB_nuc"] / kv) / total
    # MaBoSS's last window, in Calzone units: the rates are multiplied by k_time (units per composite time unit)
    a, b = k_time * interval * (WINDOWS - 1) / WINDOWS, k_time * interval
    expected = f * (1.0 - (math.exp(-a) - math.exp(-b)) / (b - a))
    initial = {"CASP3": 0.0, "IKK": 1.0, "NFkB": 0.0}
    document = {
        "global_time_precision": 6,
        "state": {
            "kinetic": dict(PEAK),
            "node_state": initial,
            "node_probabilities": dict(initial),
            # the driven keys must exist before the Step writes them (process-bigraph 1.9.1; see the docstring)
            "parameters": {"u_NFkB": 0.0, "d_NFkB": 0.0},
            "steps": 0,
            "nfkb_total": 0.0,
            "nuclear_fraction": {
                "_type": "step",
                "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
                "config": {
                    "expressions": [
                        {"out": "NFKB_total", "expr": rule},
                        {"out": "u_NFkB", "expr": "(NFKB_nuc / Kv) / NFKB_total"},
                        {"out": "d_NFkB", "expr": "1 - u_NFkB"},
                    ],
                    "params": {"Kv": kv},
                },
                "inputs": {species: ["kinetic", species] for species in PEAK},
                "outputs": {"NFKB_total": ["nfkb_total"], "u_NFkB": ["parameters", "u_NFkB"],
                            "d_NFkB": ["parameters", "d_NFkB"]},
            },
            "cellfate": {
                "_type": "process",
                "address": "local:viva_maboss.processes.MaBoSSProcess",
                "config": {
                    "network": network,
                    "parameters": {"High_NFkB": 0.0, "u_NFkB": 0.0, "d_NFkB": 0.0, "k_time": k_time},
                    "initial_state": {"IKK": 1.0},
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
            f"driven SBML's own rule, read from the SBML ({total:.10f}), f = (NFKB_nuc/Kv)/NFKB_total = {f:.7f} -> "
            "MaBoSSProcess parameters u_NFkB = f, d_NFkB = 1 - f, on the coupled network's NFkB node (verbatim) with "
            f"its gate held open (IKK on, CASP3 off). One interval of {interval:g} in {WINDOWS} windows at "
            f"k_time = {k_time:.10g} ({k_time * interval:g} Calzone units), {SAMPLES} trajectories. Analytic oracle: "
            f"f (1 - (exp(-{a:g}) - exp(-{b:g})) / {b - a:g}) = {expected:.7f} for P(NFkB on) over the last window. "
            "Generated by checks/boolean/make_pair_nfkb_analytic.py."
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
        ],
    }
    out = HERE / name
    out.mkdir(exist_ok=True)
    (out / "document.pbg").write_text(json.dumps(document, indent=2) + "\n")
    (out / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote checks/boolean/{name}: f = {f:.7f}, k_time {k_time:.6g}, expected P(NFkB on) = {expected:.7f}")


def main() -> None:
    rule, kv = _rule_from_sbml()
    print(f"NFKB_total rule from the SBML: {rule}  (Kv = {kv:g})")
    write("pair-nfkb-analytic", k_time=1.0, interval=2.0, rule=rule, kv=kv)
    # the same 2 Calzone units with the clock converted: one Calzone unit per 600 s, run for 1200 s
    write("pair-nfkb-seconds", k_time=1.0 / 600.0, interval=1200.0, rule=rule, kv=kv)


if __name__ == "__main__":
    main()
