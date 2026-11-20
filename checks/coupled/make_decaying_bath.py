"""Generate `coupled/decaying-bath`: the dose study's decaying bath (decision 50) reaches both layers on time.

The document is the dose study's own (s2-dose `dose_study.document`): Study 1's population of 270 fate networks and one
Lipniacki model, intact, 30 min per unit, in the bath matched to the near cell at bolus size 10 (`bath-near-M10`,
half-life 5.5 min). Only the emitter is changed, to record what the two layers read, and the SBML is inlined so the
document stands alone.

The oracle is the closed form. At each coupling instant t = 30 k s, the bath's TNF is c0 exp(-lambda t) and the
occupancy c / (c + Kd), written to Lipniacki's TNF_R (the `stimulus` store) and to the TNF node's rates u_TNF = occ and
d_TNF = 1 - occ in the shared `parameters` store the fate networks read. Row k of the emitter is t = 30 k; row 0 is the
seeded value, so the bath acts from t = 0. Row 0 also holds the first and last cells' TNF node, in both stores
MaBoSSProcess starts from: off, so TNF reaches a cell only through the bath (decision 49).

`--negative {decay2,unseeded,tnf-on}` writes `decaying-bath-negative`, which must fail:
- decay2 doubles the decay rate in the document;
- unseeded leaves u_TNF and d_TNF out of the `parameters` store, so process-bigraph drops the Step's writes;
- tnf-on seeds every cell's TNF node on, as Study 1's builder does.

    uv run --frozen --extra simulators python -I checks/coupled/make_decaying_bath.py [--negative NAME]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOSE_STUDY = ROOT / "workspace" / "investigations" / "tnf-fate-in-space" / "studies" / "s2-dose" / "dose_study.py"
SBML = ROOT / "workspace" / "datasets" / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
ARM, MINUTES, BATH = "intact", 30, "bath-near-M10"
END, STEP = 1200.0, 30.0
ROWS = (0, 1, 2, 10, 20, 40)
NEGATIVES = ("decay2", "unseeded", "tnf-on")
WATCHED = ("c0", "c269")  # the first and last cells


def _dose_study():
    spec = importlib.util.spec_from_file_location("dose_study", DOSE_STUDY)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {DOSE_STUDY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def document(ds, negative: str | None) -> dict:
    doc = ds.document(ARM, MINUTES, BATH, 1)
    state = doc["state"]
    kinetic = state["kinetic"]
    if kinetic["config"]["model_file"] != SBML.name:
        raise SystemExit(f"the population runs {kinetic['config']['model_file']}, not {SBML.name}")
    config = {k: v for k, v in kinetic["config"].items() if k != "model_file"}
    kinetic["config"] = {"model": SBML.read_text(), "model_format": "sbml", **config}
    if negative == "decay2":
        state["decaying_bath"]["config"]["params"]["decay"] *= 2
    if negative == "unseeded":
        del state["parameters"]["u_TNF"], state["parameters"]["d_TNF"]
    if negative == "tnf-on":
        for cell in state["cells"].values():
            cell["node_state"]["TNF"] = cell["node_probabilities"]["TNF"] = 1.0
    tnf = {f"{store}_{cid}": ["cells", cid, store, "TNF"] for cid in WATCHED
           for store in ("node_state", "node_probabilities")}
    state["emitter"] = {
        "_type": "step",
        "address": "local:RAMEmitter",
        "config": {"emit": {"stimulus": "map[float]", "parameters": "map[float]", "global_time": "float",
                            **dict.fromkeys(tnf, "float")}},
        "inputs": {"stimulus": ["stimulus"], "parameters": ["parameters"], "global_time": ["global_time"], **tnf},
    }
    return doc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", choices=NEGATIVES, help="write a mutated copy that must fail")
    args = parser.parse_args()
    ds = _dose_study()
    bath = ds.exposures()[BATH]
    c0, decay = bath["c0_uM"], bath["decay_per_s"]

    def occ(t: float) -> float:
        c = c0 * math.exp(-decay * t)
        return c / (c + ds.KD)

    expect: list[dict] = [{"kind": "rows", "emitter": "emitter", "min": int(END / STEP) + 1}]
    expect += [{"kind": "scalar", "emitter": "emitter", "field": f"{store}_{cid}", "row": 0, "expected": 0.0,
                "abs": 1e-12} for cid in WATCHED for store in ("node_state", "node_probabilities")]
    for row in ROWS:
        t = row * STEP
        expect.append({"kind": "scalar", "emitter": "emitter", "field": "global_time", "row": row, "expected": t,
                       "abs": 1e-6})
        for field, value in (("stimulus.TNF_R", occ(t)), ("parameters.u_TNF", occ(t)),
                             ("parameters.d_TNF", 1.0 - occ(t))):
            expect.append({"kind": "scalar", "emitter": "emitter", "field": field, "row": row, "expected": value,
                           "rel": 1e-9, "abs": 1e-12})
    case_name = "decaying-bath" + ("-negative" if args.negative else "")
    description = (
        f"NEGATIVE ({args.negative}): must fail. Delete after running." if args.negative else
        f"The dose study's decaying bath (decision 50) in its own document (s2-dose dose_study.document, {ARM}, "
        f"{MINUTES} min per unit, {BATH}: c0 {c0:.6g} uM, lambda {decay:.6g} /s, 270 fate networks). Every cell's "
        f"TNF node starts off (decision 49; the first and last cells are checked). At each coupling instant t = 30 k "
        f"s, Lipniacki's TNF_R and the TNF rates in the shared parameters store (u = occ, d = 1 - occ) equal the "
        f"closed form occ = c0 exp(-lambda t) / (c0 exp(-lambda t) + Kd), Kd {ds.KD:g} uM, from the seeded value at "
        f"t = 0 to t = {END:.0f} s (occupancy {occ(0):.3f} to {occ(END):.3f}). Generated by "
        f"checks/coupled/make_decaying_bath.py.")
    case_dir = HERE / case_name
    case_dir.mkdir(exist_ok=True)
    (case_dir / "document.pbg").write_text(json.dumps(document(ds, args.negative), separators=(",", ":")) + "\n")
    case = {"description": description, "scale_level": "cell", "document": "document.pbg", "interval": END,
            "expect": expect}
    (case_dir / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    size = (case_dir / "document.pbg").stat().st_size / 1e6
    print(f"wrote {case_name}: {len(expect)} expectations, document {size:.1f} MB; occupancy {occ(0):.4f} -> "
          f"{occ(END):.4f}")


if __name__ == "__main__":
    main()
