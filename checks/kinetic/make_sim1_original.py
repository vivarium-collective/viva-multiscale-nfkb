"""Generate checks/kinetic/sim1-original/: BioModels' unmodified Lipniacki 2004 (BIOMD0000000786) in
viva-tellurium's TelluriumProcess must reproduce SED-ML ``sim1`` (0 to 385200 s, 1000 steps of 385.2 s; the
TNF_stimulation event fires at t > 363600 s, raw/curation_notes.txt).

The oracle is another engine: COPASI's ``sim1`` trajectory from viva-biomodels' corpus
(datasets/corpus_comparison/corpus_timecourse.parquet, COPASI rows of BIOMD0000000786 / sim1, downsampled to 100
of sim1's 1001 time points). The expected values are copied by this script, never by hand. Checked rows: the last
pre-stimulus corpus point and every post-stimulus one, for every floating species. Tolerance rel 1e-3 (the
solver-to-solver tolerance of compose-api's tellurium-phase-cycle case) and abs 1e-7 (the corpus stores float32).

    uv run --project compose --with pyarrow --with pandas python -I checks/kinetic/make_sim1_original.py \
        --corpus ~/viva/viva-biomodels/datasets/corpus_comparison/corpus_timecourse.parquet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "workspace/datasets/lipniacki2004/raw/Lipniacki2004.xml"
CASE = Path(__file__).resolve().parent / "sim1-original"
STEP = 385.2  # sim1: outputEndTime 385200 / numberOfSteps 1000
END = 385200.0
STIMULUS = 363600.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    corpus = parser.parse_args().corpus.expanduser()

    frame = pd.read_parquet(corpus, filters=[("biomodel_id", "==", "BIOMD0000000786")])
    copasi = frame[(frame.engine == "copasi") & (frame.job == "sim1")]
    floating = [
        "A20", "A20_mRNA", "IKK_active", "IKK_inact", "IKK_neutral", "IKKactive_IkB", "IKKactive_IkB_NFKB",
        "IkB", "IkB_NFKB", "IkB_NFKB_nuc", "IkB_mRNA", "IkB_nuc", "NFKB", "NFKB_nuc", "cgen_mRNA",
    ]
    times = sorted(float(t) for t in copasi.time.unique())
    before = max(t for t in times if t < STIMULUS)
    checked = [before] + [t for t in times if t > STIMULUS]

    expect: list[dict[str, object]] = [{"kind": "rows", "emitter": "emitter", "min": int(END / STEP) + 1}]
    for time in checked:
        row = round(time / STEP)
        if abs(row * STEP - time) > 1e-3:
            raise SystemExit(f"corpus time {time} is not on sim1's grid")
        expect.append({"kind": "scalar", "emitter": "emitter", "field": "global_time", "row": row,
                       "expected": round(row * STEP, 6), "rel": 1e-9, "abs": 1e-6})
        at = copasi[copasi.time == time].set_index("variable").value
        for species in floating:
            expect.append({"kind": "scalar", "emitter": "emitter", "field": f"species.{species}", "row": row,
                           "expected": float(at[species]), "rel": 1e-3, "abs": 1e-7})

    CASE.mkdir(exist_ok=True)
    shutil.copyfile(RAW, CASE / RAW.name)
    document = {"state": {
        "kinetic": {
            "_type": "process",
            "address": "local:viva_tellurium.processes.TelluriumProcess",
            "config": {"model_file": RAW.name, "bulk_species": False},
            "interval": STEP,
            "inputs": {},
            "outputs": {"species": ["species"], "time": ["kinetic_time"]},
        },
        "emitter": {
            "_type": "step",
            "address": "local:RAMEmitter",
            "config": {"emit": {"species": "map[float]", "global_time": "float"}},
            "inputs": {"species": ["species"], "global_time": ["global_time"]},
        },
    },
        # Due times are rounded to 6 decimals: without it 385.2 added 1000 times drifts past 385200 in floating
        # point and the last tick is skipped (1000 rows instead of 1001, seen 2026-11-04).
        "global_time_precision": 6,
    }
    (CASE / "document.pbg").write_text(json.dumps(document, indent=2) + "\n")
    corpus_sha = hashlib.sha256(corpus.read_bytes()).hexdigest()
    case = {
        "description": (
            "BioModels' unmodified Lipniacki 2004 NF-kB model (BIOMD0000000786) in viva-tellurium's TelluriumProcess, "
            f"stepped every {STEP} s to {END:.0f} s as SED-ML sim1 samples it, with its own TNF_stimulation event at "
            f"t > {STIMULUS:.0f} s. Every floating species at the last pre-stimulus point and at every post-stimulus "
            "point matches COPASI's sim1 trajectory, another engine's output, taken from viva-biomodels' corpus "
            f"(corpus_timecourse.parquet, sha256 {corpus_sha}) by checks/kinetic/make_sim1_original.py."
        ),
        "scale_level": "molecule",
        "document": "document.pbg",
        "files": [RAW.name],
        "interval": END,
        "expect": expect,
    }
    (CASE / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote {CASE.relative_to(ROOT)}: {len(expect)} expectations at rows {[round(t / STEP) for t in checked]}")


if __name__ == "__main__":
    main()
