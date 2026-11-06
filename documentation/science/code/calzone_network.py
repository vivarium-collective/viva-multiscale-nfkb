"""Write documentation/science/_calzone_nodes.md: Calzone 2010's 31 nodes, read from the pinned network file.

Every rule and rate in the table is parsed from workspace/datasets/calzone2010_cellfate/raw/cellfate.bnd, and the
initial states from raw/cellfate.cfg, so the table cannot drift from the model. "Read by" is computed from the logic
rules. "Changed in the composite" comes from processed/coupling.json, which prep.py writes. Only the biological meaning
of each node is written here by hand, and the script refuses to run unless that list names exactly the network's nodes.

    uv run --project compose python -I documentation/science/code/calzone_network.py           # write the table
    uv run --project compose python -I documentation/science/code/calzone_network.py --check   # fail if it is stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "workspace" / "datasets" / "calzone2010_cellfate"
OUT = ROOT / "documentation" / "science" / "_calzone_nodes.md"

# What each node stands for (Calzone et al. 2010). A node is "on" when the molecule, complex or process is present or
# active at a level that matters for the decision.
MEANING = {
    "TNF": "TNF, the death ligand outside the cell (the input)",
    "TNFR": "TNF receptor 1 with TNF bound",
    "FASL": "Fas ligand, a second death ligand (held off in every run here)",
    "FADD": "FADD, the adaptor that links a death receptor to caspase-8 (on from the start)",
    "DISC_TNF": "the death-inducing signalling complex at the TNF receptor, which activates caspase-8",
    "DISC_FAS": "the same complex at the Fas receptor",
    "CASP8": "caspase-8, the initiator caspase of receptor-driven apoptosis",
    "RIP1": "RIP1, a kinase at the receptor; caspase-8 cleaves and so inactivates it",
    "cIAP": "cIAP1/2, which attach ubiquitin to RIP1; SMAC removes them",
    "RIP1ub": "ubiquitinated RIP1, the scaffold that activates IKK (survival route)",
    "RIP1K": "RIP1's kinase activity, which drives reactive oxygen species (necrosis route)",
    "IKK": "the IκB kinase, which frees NF-κB by marking its inhibitor IκB for destruction",
    "NFkB": "NF-κB active in the nucleus",
    "cFLIP": "cFLIP, an NF-κB target that blocks caspase-8",
    "BCL2": "BCL-2, an NF-κB target that blocks BAX and the permeability transition",
    "BAX": "BAX, which caspase-8 activates and which permeabilises the mitochondrial outer membrane",
    "MOMP": "mitochondrial outer membrane permeabilisation",
    "SMAC": "SMAC, released from mitochondria, which removes XIAP and cIAP",
    "Cyt_c": "cytochrome c, released from mitochondria",
    "mXIAP": "XIAP being made on NF-κB's orders",
    "XIAP": "XIAP, which blocks caspase-3 and the apoptosome",
    "mcIAP": "cIAP being made on NF-κB's orders",
    "apoptosome": "the apoptosome (cytochrome c, Apaf-1, caspase-9), which needs ATP and activates caspase-3",
    "CASP3": "caspase-3, the executioner caspase",
    "mROS": "the absence of NF-κB's antioxidant genes, which lets reactive oxygen species build up",
    "ROS": "reactive oxygen species",
    "MPT": "the mitochondrial permeability transition, which collapses ATP production",
    "ATP": "enough ATP (on from the start)",
    "Apoptosis": "the apoptosis phenotype: caspase-3 is active",
    "NonACD": "the necrosis phenotype (non-apoptotic cell death): ATP is gone",
    "Survival": "the survival phenotype: NF-κB is active",
}
ORDER = list(MEANING)  # receptor -> survival route -> death routes -> phenotypes, the order the page explains them in


def _fail(message: str) -> None:
    sys.exit(f"calzone_network.py: {message}")


def _nodes(network: str) -> dict[str, dict[str, str]]:
    nodes = {}
    for match in re.finditer(r"^node\s+(\w+)\s*\{(.*?)^\}", network, re.MULTILINE | re.DOTALL):
        fields = dict(re.findall(r"(logic|rate_up|rate_down)\s*=\s*([^;]+);", match.group(2)))
        nodes[match.group(1)] = {k: " ".join(v.split()) for k, v in fields.items()}
    return nodes


def _initial_on(cfg: str) -> set[str]:
    return {name for name, value in re.findall(r"^(\w+)\.istate\s*=\s*([01])\s*;", cfg, re.MULTILINE) if value == "1"}


def table() -> str:
    nodes = _nodes((DATA / "raw" / "cellfate.bnd").read_text())
    if set(nodes) != set(MEANING):
        _fail(f"MEANING does not name exactly the network's nodes: {sorted(set(nodes) ^ set(MEANING))}")
    on = _initial_on((DATA / "raw" / "cellfate.cfg").read_text()) | {"TNF"}  # the stimulus is on in every run here
    coupling = json.loads((DATA / "processed" / "coupling.json").read_text())
    changed = {**{n: "rates rewritten" for n in coupling["rewritten"]},
               **{n: "`$TransRate` → `$r_tx / $k_time`" for n in coupling["transrate_nodes"]}}
    readers = {n: sorted((m for m, f in nodes.items() if "logic" in f and re.search(rf"\b{n}\b", f["logic"]) and m != n),
                         key=ORDER.index) for n in nodes}
    rows = ["| Node | Stands for | On when (logic) | Switch-on rate | Switch-off rate | Read by | Start | Composite |",
            "|---|---|---|---|---|---|---|---|"]
    for n in ORDER:
        f = nodes[n]
        logic = f.get("logic", "—")
        rows.append(
            f"| **{n}** | {MEANING[n]} | `{logic}` | `{f['rate_up']}` | `{f['rate_down']}` | "
            f"{', '.join(readers[n]) or '*none (an output)*'} | {'on' if n in on else 'off'} | {changed.get(n, '—')} |")
    return ("<!-- Generated by documentation/science/code/calzone_network.py from the pinned network; do not edit. -->\n"
            + "\n".join(rows) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed table differs")
    args = parser.parse_args()
    text = table()
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            _fail(f"{OUT.relative_to(ROOT)} is stale; rerun without --check")
        print(f"{OUT.relative_to(ROOT)} is current")
        return
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
