"""Derive the driven Lipniacki 2004 model from BioModels' curated SBML (raw/, never edited).

BIOMD0000000786 stimulates itself: the event ``TNF_stimulation`` sets the parameter ``TNF_R`` from 0 to 1 once
``time > 363600`` s, after 101 h of pre-equilibration (raw/curation_notes.txt), and the boundary species ``TNF``
follows it through the assignment rule ``TNF := TNF_R``. In the composite the spatial layer owns the stimulus and
drives ``TNF_R`` through TelluriumProcess's parameter input, so the event is removed. Nothing else changes: the rule,
``TNF_R``'s initial value (0) and every reaction and parameter are kept, and the script refuses to write if the input
is not the expected file or the model does not have exactly that one event.

    uv run --project compose python -I workspace/datasets/lipniacki2004/prep.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import libsbml

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw" / "Lipniacki2004.xml"
OUT = HERE / "processed" / "lipniacki2004_driven.xml"
RAW_SHA256 = "78ff021b45d4ca35dd6f3a4de371196625a3a6a908531ff028b3ed946142d39c"  # BioModels download, 2026-11-04
EVENT = "TNF_stimulation"


def _fail(message: str) -> None:
    sys.exit(f"prep.py: {message}")


def main() -> None:
    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
    if digest != RAW_SHA256:
        _fail(f"{RAW.name} sha256 is {digest}, expected {RAW_SHA256}")

    document = libsbml.readSBMLFromFile(str(RAW))
    if document.getNumErrors(libsbml.LIBSBML_SEV_ERROR):
        _fail(f"{RAW.name} does not read cleanly:\n{document.getErrorLog().toString()}")
    model = document.getModel()

    events = [model.getEvent(i).getId() for i in range(model.getNumEvents())]
    if events != [EVENT]:
        _fail(f"expected exactly the event {EVENT!r}, found {events}")
    rule = model.getRuleByVariable("TNF")
    if rule is None or libsbml.formulaToL3String(rule.getMath()) != "TNF_R":
        _fail("expected the assignment rule TNF := TNF_R")
    stimulus = model.getParameter("TNF_R")
    if stimulus is None or stimulus.getConstant() or stimulus.getValue() != 0.0:
        _fail("expected a non-constant parameter TNF_R with initial value 0")

    model.removeEvent(EVENT)
    model.setId(f"{model.getId()}_driven")
    model.setName(f"{model.getName()} (TNF_stimulation event removed; TNF_R driven externally)")

    if document.checkInternalConsistency():
        errors = document.getErrorLog()
        severe = [errors.getError(i) for i in range(errors.getNumErrors()) if errors.getError(i).isError()]
        if severe:
            _fail("derived model is inconsistent:\n" + "\n".join(e.getMessage() for e in severe))

    OUT.parent.mkdir(exist_ok=True)
    libsbml.writeSBMLToFile(document, str(OUT))
    print(f"wrote {OUT.relative_to(HERE)} sha256 {hashlib.sha256(OUT.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
