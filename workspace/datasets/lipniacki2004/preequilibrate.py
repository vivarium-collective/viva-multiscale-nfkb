"""Pre-equilibrate the driven Lipniacki 2004 model, as BioModels' curation does before stimulating it.

raw/curation_notes.txt: "Model is pre-simulated for 101 hours (363600 seconds) before triggering the system with
TNF." The composite starts from that state instead of spending 101 h of model time on it. This runs
processed/lipniacki2004_driven.xml with TNF_R = 0 for 363600 s on libRoadRunner with TelluriumProcess's default
tolerances (abs 1e-10, rel 1e-8), refuses to write unless the result is a steady state (max |dx/dt| / |x| below
1e-8), and writes processed/lipniacki2004_steady_state.json: the floating species' concentrations, to be given to
TelluriumProcess as ``species_overrides``, with their provenance.

    uv run --project compose python -I workspace/datasets/lipniacki2004/preequilibrate.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import tellurium as te

HERE = Path(__file__).resolve().parent
MODEL = HERE / "processed" / "lipniacki2004_driven.xml"
OUT = HERE / "processed" / "lipniacki2004_steady_state.json"
DURATION = 363600.0
ABSOLUTE, RELATIVE = 1e-10, 1e-8  # TelluriumProcess defaults (viva-tellurium 967d5dd processes.py)
STEADY = 1e-8


def main() -> None:
    runner = te.loadSBMLModel(str(MODEL))
    runner.integrator.absolute_tolerance = ABSOLUTE
    runner.integrator.relative_tolerance = RELATIVE
    if runner["TNF_R"] != 0.0:
        sys.exit("preequilibrate.py: TNF_R must start at 0")
    runner.simulate(0.0, DURATION, 2)

    ids = list(runner.getFloatingSpeciesIds())
    values = np.array(runner.getFloatingSpeciesConcentrations())
    rates = np.array(runner.getRatesOfChange())
    worst = float(np.max(np.abs(rates) / np.maximum(np.abs(values), 1e-12)))
    if worst > STEADY:
        sys.exit(f"preequilibrate.py: not at steady state after {DURATION} s (max relative rate {worst:.3e})")

    OUT.write_text(json.dumps({
        "model": MODEL.name,
        "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        "TNF_R": 0.0,
        "duration_s": DURATION,
        "tolerances": {"absolute": ABSOLUTE, "relative": RELATIVE},
        "max_relative_rate": worst,
        "species": {sid: float(v) for sid, v in zip(ids, values, strict=True)},
    }, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(HERE)}: {len(ids)} species, max relative rate {worst:.3e}")


if __name__ == "__main__":
    main()
