"""Generate `coupled/distance-replay`: the distance study's population reads its ring's recorded TNF at every instant.

The document is the study's own (s3-distance `distance_study.document`: the near ring, bolus 10 uM um^2, 30 min per
unit, NF-kB intact, batch 1; Study 1's population of 270 fate networks and one Lipniacki model, driven by a
TimeSeriesStep). Only the emitter is changed, to record what the two layers read, and the SBML is inlined so the
document stands alone.

The oracle is the 24 h field run (analysis/exposure-design/exposure_24h_band1.json), read here directly: at each
coupling instant t = 30 k s the TNF at the cell is ten times the field run's per-unit value at t (0 at t = 0), and the
occupancy c / (c + Kd) goes to Lipniacki's TNF_R and to the TNF node's rates u = occ and d = 1 - occ in the shared
`parameters` store. At t = 0 the first and last cells' TNF node is off in both MaBoSS stores (decision 49).

`--negative {late,tnf-on}` writes `distance-replay-negative`, which must fail:
- late replays the series one interval late (each sample at t + 30 s);
- tnf-on seeds every cell's TNF node on, as Study 1's builder does.

    uv run --project compose --frozen python -I checks/coupled/make_distance_replay.py [--negative NAME]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = ROOT / "workspace" / "investigations" / "tnf-fate-in-space" / "studies" / "s3-distance" / "distance_study.py"
SBML = ROOT / "workspace" / "datasets" / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
FIELD = ROOT / "analysis" / "exposure-design" / "exposure_24h_band1.json"
POINT = ("intact", 30, "near", 10.0, 1)  # arm, min per unit, ring, bolus, batch
END, STEP = 1200.0, 30.0
ROWS = (0, 1, 2, 4, 10, 20, 40)  # the near cell's TNF peaks at about 25 s
WATCHED = ("c0", "c269")
NEGATIVES = ("late", "tnf-on")


def _study():
    spec = importlib.util.spec_from_file_location("distance_study", STUDY)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {STUDY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def document(ds, negative: str | None) -> dict:
    doc = ds.document(*POINT)
    state = doc["state"]
    kinetic = state["kinetic"]
    if kinetic["config"]["model_file"] != SBML.name:
        raise SystemExit(f"the population runs {kinetic['config']['model_file']}, not {SBML.name}")
    config = {k: v for k, v in kinetic["config"].items() if k != "model_file"}
    kinetic["config"] = {"model": SBML.read_text(), "model_format": "sbml", **config}
    if negative == "late":  # each sample one interval late: the value at t = 30 k s is the one recorded at 30 (k - 1)
        values = state["replay"]["config"]["values"]
        state["replay"]["config"]["values"] = {name: [series[0], *series[:-1]] for name, series in values.items()}
    if negative == "tnf-on":
        for cell in state["cells"].values():
            cell["node_state"]["TNF"] = cell["node_probabilities"]["TNF"] = 1.0
    tnf = {f"{store}_{cid}": ["cells", cid, store, "TNF"] for cid in WATCHED for store in ("node_state",
                                                                                          "node_probabilities")}
    state["emitter"] = {
        "_type": "step",
        "address": "local:RAMEmitter",
        "config": {"emit": {"tnf_at_cell": "map[float]", "stimulus": "map[float]", "parameters": "map[float]",
                            "global_time": "float", **dict.fromkeys(tnf, "float")}},
        "inputs": {"tnf_at_cell": ["tnf_at_cell"], "stimulus": ["stimulus"], "parameters": ["parameters"],
                   "global_time": ["global_time"], **tnf},
    }
    return doc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", choices=NEGATIVES, help="write a mutated copy that must fail")
    args = parser.parse_args()
    ds = _study()
    field = json.loads(FIELD.read_text())
    _, _, ring, bolus, _ = POINT

    def tnf(row: int) -> float:  # independent of distance_study.replayed: the field run's file, read here
        return 0.0 if row == 0 else bolus * field["tnf_at_cell"][ring][row - 1]

    def occ(row: int) -> float:
        return tnf(row) / (tnf(row) + ds.KD)

    def scalar(name: str, row: int, expected: float) -> dict:
        return {"kind": "scalar", "emitter": "emitter", "field": name, "row": row, "expected": expected,
                "rel": 1e-12, "abs": 1e-15}

    expect: list[dict] = [{"kind": "rows", "emitter": "emitter", "min": int(END / STEP) + 1}]
    for row in ROWS:
        expect += [scalar("global_time", row, row * STEP), scalar("tnf_at_cell.TNF", row, tnf(row)),
                   scalar("stimulus.TNF_R", row, occ(row)), scalar("parameters.u_TNF", row, occ(row)),
                   scalar("parameters.d_TNF", row, 1.0 - occ(row))]
    expect += [scalar(f"{store}_{cid}", 0, 0.0) for cid in WATCHED for store in ("node_state", "node_probabilities")]
    case_name = "distance-replay" + ("-negative" if args.negative else "")
    description = (
        f"NEGATIVE ({args.negative}): must fail. Delete after running." if args.negative else
        "The distance study's population reads its ring's recorded TNF at every coupling instant (s3-distance "
        "distance_study.document: near ring, bolus 10 uM um^2, 30 min per unit, intact, batch 1, 270 fate networks, a "
        "TimeSeriesStep). At t = 30 k s the TNF at the cell is ten times the 24 h field run's per-unit value "
        "(exposure_24h_band1.json), and Lipniacki's TNF_R and the TNF rates in the shared parameters store are its "
        "occupancy c / (c + Kd), Kd 19 pM; every cell's TNF node starts off (decision 49; the first and last cells "
        "are checked). Generated by checks/coupled/make_distance_replay.py.")
    case_dir = HERE / case_name
    case_dir.mkdir(exist_ok=True)
    (case_dir / "document.pbg").write_text(json.dumps(document(ds, args.negative), separators=(",", ":")) + "\n")
    case = {"description": description, "scale_level": "cell", "document": "document.pbg", "interval": END,
            "expect": expect}
    (case_dir / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    size = (case_dir / "document.pbg").stat().st_size / 1e6
    print(f"wrote {case_name}: {len(expect)} expectations, document {size:.1f} MB")


if __name__ == "__main__":
    main()
