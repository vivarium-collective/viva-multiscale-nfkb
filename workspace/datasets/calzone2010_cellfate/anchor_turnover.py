"""Compute the Boolean layer's protein-turnover rate r_deg (per second) from Lipniacki 2004's own A20 degradation.

Why (Alex, 2026-11-06: "Anchor protein decay", Study 0b). Study 0 found NF-kB's protection transient: the protective
products (cFLIP, BCL2, mXIAP, mcIAP) switched OFF at Calzone's unit rate x k_time whenever NF-kB dipped between its
waves, so cells that turned on survival first nearly all died later. Real proteins do not vanish in minutes; they are
removed by turnover. Lipniacki models turnover for its own NF-kB-induced protein, A20 (reaction A20_degradation,
rate c5 * A20, constitutive), so that constant sets the decay clock of Calzone's NF-kB-induced products. A20 is the
natural anchor: it is NF-kB-induced, like cFLIP, BCL2 and XIAP, and its decay is constitutive. IkB's constitutive decay
(c5a) is not used, because IkB's fate is dominated by IKK-induced degradation, not turnover.

The value is read from the SBML (the document is held while its model is used), not transcribed.

    uv run --project compose python -I workspace/datasets/calzone2010_cellfate/anchor_turnover.py
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import NoReturn

import libsbml

HERE = Path(__file__).resolve().parent
MODEL = HERE.parent / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
OUT = HERE / "processed" / "turnover_anchor.json"


def _fail(message: str) -> NoReturn:
    sys.exit(f"anchor_turnover.py: {message}")


def main() -> None:
    document = libsbml.readSBMLFromFile(str(MODEL))
    model = document.getModel()
    reaction = model.getReaction("A20_degradation")
    if reaction is None:
        _fail("no A20_degradation reaction")
    law = libsbml.formulaToL3String(reaction.getKineticLaw().getMath())
    if law != "Cytosol * c5 * A20":
        _fail(f"A20_degradation's law is {law!r}, not first-order 'Cytosol * c5 * A20'")
    c5 = model.getParameter("c5").getValue()
    if not c5 > 0:
        _fail(f"c5 read as {c5}")
    OUT.write_text(json.dumps({
        "model": MODEL.name,
        "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        "reaction": "A20_degradation",
        "kinetic_law": law,
        "r_deg_per_s": c5,
        "half_life_s": math.log(2) / c5,
        "definition": "r_deg = Lipniacki's A20 protein degradation constant c5 (first-order, constitutive)",
    }, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(HERE)}: r_deg = {c5:g}/s (half-life {math.log(2) / c5 / 60:.1f} min)")


if __name__ == "__main__":
    main()
