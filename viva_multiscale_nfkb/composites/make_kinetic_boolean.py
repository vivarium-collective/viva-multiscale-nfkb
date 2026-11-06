"""Write kinetic_boolean.composite.json: Lipniacki's NF-kB (TelluriumProcess) coupled to Calzone's cell fate (MaBoSSProcess).

One cell, as a composite spec (docs: viva-superpowers conventions/composites.md). Every piece is the checked one:
- **kinetic:** the driven Lipniacki model (`lipniacki2004_driven.xml`, shipped beside the document), started from the
  pre-equilibrated steady state and stimulated through viva-tellurium 0.2.3's `parameters_in` (checks/kinetic/
  stimulus-through-port).
- **adapter:** a MathExpressionStep that evaluates the SBML's own NFKB_total rule, read from the SBML here, then
  f = (NFKB_nuc / Kv) / NFKB_total (checks/boolean/pair-nfkb-*). It writes u_NFkB = f * kappa / k_time and
  d_NFkB = (1 - f) * kappa / k_time. The network multiplies every rate by k_time, so NF-kB's Boolean node switches at
  kappa per second, the calibration parameter of Study 0, whatever k_time is. kappa = k_time is Calzone's own flicker
  (u = f, d = 1 - f in Calzone units).
- **cell fate:** the coupled Calzone network (`cellfate_coupled.bnd`, all 31 nodes; checks/boolean/coupled-*), with
  TNF held on, as the stimulus is on.

Parameters: kappa (1/s), k_time (Calzone units per s), r_tx (1/s), seed, interval (s, the coupling step for both
layers), sample_count (MaBoSS trajectories per interval; 1 makes the process one cell).

    uv run --project compose python -I viva_multiscale_nfkb/composites/make_kinetic_boolean.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import libsbml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "workspace" / "datasets"
SBML = DATA / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
STEADY = DATA / "lipniacki2004" / "processed" / "lipniacki2004_steady_state.json"
NETWORK = DATA / "calzone2010_cellfate" / "processed" / "cellfate_coupled.bnd"
ANCHOR = DATA / "calzone2010_cellfate" / "processed" / "transcription_anchor.json"
OUT = Path(__file__).resolve().parent / "kinetic_boolean.composite.json"
NFKB_SPECIES = ("IKKactive_IkB_NFKB", "NFKB", "IkB_NFKB", "NFKB_nuc", "IkB_NFKB_nuc")
ON_AT_START = ("FADD", "ATP", "cIAP", "TNF")  # cellfate.cfg's istates, with TNF on (the stimulus is on)


def nfkb_rule_and_kv() -> tuple[str, float]:
    """The SBML's NFKB_total rule (in species names and Kv) and Kv. The document is kept referenced while its model is
    read: libsbml frees a temporary document's model with it, and a value read afterwards is garbage (Kv read as 0.0)."""
    document = libsbml.readSBMLFromFile(str(SBML))
    model = document.getModel()
    rule = libsbml.formulaToL3String(model.getRule("NFKB_total").getMath())
    if libsbml.formulaToL3String(model.getInitialAssignmentBySymbol("ModelValue_1").getMath()) != "Kv":
        raise SystemExit("ModelValue_1 is not initialised to Kv")
    kv = model.getParameter("Kv").getValue()
    if not kv > 0:
        raise SystemExit(f"Kv read as {kv}; expected Lipniacki's V_cyt/V_nuc = 5")
    return rule.replace("ModelValue_1", "Kv"), kv


def main() -> None:
    steady = json.loads(STEADY.read_text())
    network = NETWORK.read_text()
    nodes = sorted(line.split()[1] for line in network.splitlines() if line.startswith("node "))
    initial = {n: float(n in ON_AT_START) for n in nodes}
    anchor = json.loads(ANCHOR.read_text())
    r_tx = anchor["r_tx_per_s"]
    # decision 25 (Alex, 2026-11-06; Study 0): the NF-kB node flips at Lipniacki's own nuclear half-rise, ln 2 / 337 s
    kappa = math.log(2) / anchor["nfkb_nuc_half_rise_s"]
    rule, kv = nfkb_rule_and_kv()
    spec = {
        "name": "kinetic-boolean",
        "description": (
            "One cell: Lipniacki 2004 NF-kB (TelluriumProcess, pre-equilibrated, TNF_R stepped to 1 through "
            "parameters_in) -> NF-kB nuclear fraction f (the SBML's own rule) -> Calzone 2010 cell fate "
            "(MaBoSSProcess, all 31 nodes, NF-kB gated by Calzone's own logic). The Boolean NF-kB node switches at "
            "kappa per second; the death machinery runs on k_time."),
        "tags": ["kinetics", "sbml", "ode", "systems-biology"],
        "requires": {"processes": ["TelluriumProcess", "MathExpressionStep", "MaBoSSProcess", "RAMEmitter"]},
        "parameters": {
            "kappa": {"type": "float", "default": kappa,
                      "description": "NF-kB node switching rate (1/s): ln 2 / NF-kB's nuclear half-rise (decision 25)"},
            "k_time": {"type": "float", "default": 1.0 / 600.0,
                       "description": "death-machinery clock (Calzone units per s), > 0"},
            "r_tx": {"type": "float", "default": r_tx,
                     "description": "transcription-scale steps' ON rate (1/s), from Lipniacki"},
            "absorb_death": {"type": "float", "default": 1.0,
                             "description": "1: Apoptosis and NonACD stay on once on (death is irreversible; decision 28); "
                                            "0: Calzone's reversible death nodes. A switch: any nonzero value "
                                            "is absorbing"},
            "seed": {"type": "int", "default": 1, "description": "MaBoSS seed for this cell"},
            "interval": {"type": "float", "default": 30.0, "description": "coupling step (s) for both layers"},
            "sample_count": {"type": "int", "default": 1, "description": "MaBoSS trajectories per interval"},
        },
        "state": {
            "stimulus": {"TNF_R": 1.0},
            "species": dict(steady["species"]),
            "kinetic": {
                "_type": "process",
                "address": "local:viva_tellurium.processes.TelluriumProcess",
                "config": {"model_file": SBML.name, "bulk_species": False, "species_overrides": steady["species"]},
                "interval": "${interval}",
                "inputs": {"parameters_in": ["stimulus"]},
                "outputs": {"species": ["species"], "time": ["kinetic_time"]},
            },
            "nfkb_total": 0.0,
            "nfkb_fraction": 0.0,
            "nfkb_fraction_time": 0.0,
            "kinetic_time": 0.0,
            "parameters": {"u_NFkB": 0.0, "d_NFkB": 0.0},
            "nuclear_fraction": {
                "_type": "step",
                "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
                "config": {
                    "expressions": [
                        {"out": "NFKB_total", "expr": rule},
                        {"out": "f", "expr": "(NFKB_nuc / Kv) / NFKB_total"},
                        {"out": "u_NFkB", "expr": "f * kappa / k_time"},
                        {"out": "d_NFkB", "expr": "(1 - f) * kappa / k_time"},
                        # the kinetic layer's time when f was computed; reading it is also what triggers this Step on
                        # every kinetic update: process-bigraph 1.9.1 triggers a Step only when an updated path or one
                        # of its prefixes is an input path, and TelluriumProcess writes the whole `species` map, a
                        # PARENT of the per-species inputs, so those alone never re-trigger it (composite.py:2541-2569)
                        {"out": "f_time", "expr": "kinetic_time"},
                    ],
                    "params": {"Kv": kv, "kappa": "${kappa}", "k_time": "${k_time}"},
                },
                "inputs": {**{s: ["species", s] for s in NFKB_SPECIES}, "kinetic_time": ["kinetic_time"]},
                "outputs": {"NFKB_total": ["nfkb_total"], "f": ["nfkb_fraction"], "f_time": ["nfkb_fraction_time"],
                            "u_NFkB": ["parameters", "u_NFkB"], "d_NFkB": ["parameters", "d_NFkB"]},
            },
            "node_state": initial,
            "node_probabilities": dict(initial),
            "steps": 0,
            "cellfate": {
                "_type": "process",
                "address": "local:viva_maboss.processes.MaBoSSProcess",
                "config": {
                    "network": network,
                    "parameters": {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0,
                                   "u_NFkB": 0.0, "d_NFkB": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
                                   "k_time": "${k_time}", "r_tx": "${r_tx}",
                                   "absorb_death": "${absorb_death}"},
                    "initial_state": {n: 1.0 for n in ON_AT_START},
                    "sample_count": "${sample_count}",
                    "windows_per_interval": 10,
                    "seed": "${seed}",
                },
                "interval": "${interval}",
                "inputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                           "parameters": ["parameters"], "steps": ["steps"]},
                "outputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                            "steps": ["steps"]},
            },
            "emitter": {
                "_type": "step",
                "address": "local:RAMEmitter",
                "config": {"emit": {"node_state": "map[float]", "nfkb_fraction": "float",
                                    "nfkb_fraction_time": "float", "global_time": "float"}},
                "inputs": {"node_state": ["node_state"], "nfkb_fraction": ["nfkb_fraction"],
                           "nfkb_fraction_time": ["nfkb_fraction_time"], "global_time": ["global_time"]},
            },
        },
    }
    OUT.write_text(json.dumps(spec, indent=1) + "\n")
    print(f"wrote {OUT.name}: {len(nodes)} Boolean nodes, r_tx default {r_tx:.4g}/s")


if __name__ == "__main__":
    main()
