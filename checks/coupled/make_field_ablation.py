"""Generate checks/coupled/field-ablation: the full composite's field -> cell edge adds nothing when the field is flat.

Two documents, both rendered from tnf_field_cell.composite.json by process-bigraph's own CompositeSpec with the same
parameters, and both under a uniform, constant TNF field at c = 10 Kd (no terms, so it stays uniform). They differ
in one edge only:
- **full:** the field -> RegionMean -> `tnf_at_cell` -> dose-response -> Lipniacki's `TNF_R` and MaBoSS's TNF rates.
  This is the case's document.
- **ablated:** the RegionMean step is removed and `tnf_at_cell` is seeded with c. The field process still runs, on a
  field nothing reads, so both documents have the same processes, schedule and emitter rows.

The ablated document runs through compose-api's runner (vendored, compose/runner.py) here, and its rows become the
expectations:
- the nuclear fraction f (kinetic);
- the on-probabilities of TNF, TNFR, IKK, NFkB, Apoptosis and Survival (Boolean, same seed);
- every 15 s from 15 to 990 s, coupling instants included. The dose-response Step's `priority` makes the schedule
  the same for every hash seed (decision 35): all rows were identical over six seeds.

The oracle is independent of the edge under test. The occupancy is also held to its closed form, c / (c + Kd), so a
wrong Kd, a wrong formula or a broken TNF_R wire fails here too. A RegionMean mean of a uniform field equals c to
rounding, so the tolerances are tight: rel 1e-9 on f and on occupancy, abs 1e-9 on the probabilities. Whether the field
reaches the cell correctly in space is checks/spatial/region-mean-bolus's job, and when it is sampled is
checks/coupled/bolus-occupancy's.

`--negative {kd2,swap,unwired}` writes field-ablation-negative with the mutated full document and the same
expectations. It must fail; run it, then delete it.
- kd2 doubles Kd.
- swap swaps MaBoSS's u_TNF and d_TNF.
- unwired gives Tellurium's `parameters_in` a store nothing writes.

    uv run --project compose python -I checks/coupled/make_field_ablation.py [--negative NAME]
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from process_bigraph.composite_spec import CompositeSpec

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COMPOSITE = ROOT / "viva_multiscale_nfkb" / "composites" / "tnf_field_cell.composite.json"
RUNNER = ROOT / "compose" / "runner.py"
NAME = "field-ablation"
END = 990
NODES = ("TNF", "TNFR", "IKK", "NFkB", "Apoptosis", "Survival")
ROWS = list(range(15, END + 1, 15))


def documents() -> tuple[dict, dict, float, float]:
    """The full and ablated documents, c and Kd."""
    spec = CompositeSpec.from_file(str(COMPOSITE))
    kd = json.loads(COMPOSITE.read_text())["parameters"]["Kd"]["default"]
    full = spec.to_document()
    state = full["state"]
    c = 10 * kd
    grid = state["field"]["config"]["grid"]
    state["fields"] = {"TNF": [[c] * grid["num"][0] for _ in range(grid["num"][1])]}
    ablated = copy.deepcopy(full)
    del ablated["state"]["surface"]
    ablated["state"]["tnf_at_cell"] = {"TNF": c}
    return full, ablated, c, kd


def run(document: dict) -> list[dict]:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "ablated.pbg"
        path.write_text(json.dumps(document))
        subprocess.run([sys.executable, "-I", str(RUNNER), "run", str(path), "-o", f"{td}/out", "-n", str(END)],
                       check=True, capture_output=True)
        [pber] = Path(td, "out").glob("results_*.pber")
        return json.loads(pber.read_text())["emitter"]


def mutate(document: dict, negative: str) -> dict:
    doc = copy.deepcopy(document)
    s = doc["state"]
    if negative == "kd2":
        s["dose_response"]["config"]["params"]["Kd"] *= 2
    elif negative == "swap":
        for e in s["dose_response"]["config"]["expressions"]:
            e["expr"] = {"u_TNF": "1 - occ", "d_TNF": "occ"}.get(e["out"], e["expr"])
    else:
        s["kinetic"]["inputs"] = {"parameters_in": ["unwired"]}
        s["unwired"] = {"TNF_R": 0.0}
    return doc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative", choices=["kd2", "swap", "unwired"], help="write a mutated copy that must fail")
    args = parser.parse_args()
    full, ablated, c, kd = documents()
    rows = run(ablated)
    if len(rows) != END + 1:
        raise SystemExit(f"the ablated run emitted {len(rows)} rows, not {END + 1}")
    occ = c / (c + kd)
    expect = []
    for t in ROWS:
        row = rows[t]
        expect.append({"kind": "scalar", "emitter": "emitter", "field": "tnf_occupancy.TNF_R", "row": t,
                       "expected": occ, "rel": 1e-9, "abs": 0.0})
        expect.append({"kind": "scalar", "emitter": "emitter", "field": "nfkb_fraction", "row": t,
                       "expected": row["nfkb_fraction"], "rel": 1e-9, "abs": 0.0})
        expect += [{"kind": "scalar", "emitter": "emitter", "field": f"node_probabilities.{n}", "row": t,
                    "expected": row["node_probabilities"][n], "rel": 0.0, "abs": 1e-9} for n in NODES]
    last = rows[ROWS[-1]]
    if not (last["nfkb_fraction"] > 10 * rows[0]["nfkb_fraction"] and last["node_probabilities"]["TNFR"] > 0.5):
        raise SystemExit("the ablated run did not respond to TNF; the check would test nothing")
    name = f"{NAME}-negative" if args.negative else NAME
    case_dir = HERE / name
    case_dir.mkdir(exist_ok=True)
    (case_dir / "document.pbg").write_text(json.dumps(mutate(full, args.negative) if args.negative else full) + "\n")
    case = {
        "description": (
            "The full composite (tnf_field_cell.composite.json, its defaults: k_time 1/120 per s, sample_count 100, "
            "seed 1) under a uniform, constant TNF field at 10 Kd, against the same document with the field -> cell "
            "edge removed (no RegionMean; tnf_at_cell seeded with 10 Kd; the field process still runs). The ablated "
            "run's NF-kB nuclear fraction and fate-node on-probabilities, every 15 s from 15 to 990 s, are "
            "the expectations, with occupancy held to its closed form c / (c + Kd). Generated by "
            "checks/coupled/make_field_ablation.py."),
        "scale_level": "cell",
        "document": "document.pbg",
        "interval": float(END),
        "expect": [{"kind": "rows", "emitter": "emitter", "min": END + 1}, *expect],
    }
    (case_dir / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    print(f"wrote {name}: {len(expect)} expectations; at {ROWS[-1]} s f = {last['nfkb_fraction']:.4f}, "
          f"P[TNFR] = {last['node_probabilities']['TNFR']:.2f}, P[Apoptosis] = {last['node_probabilities']['Apoptosis']:.2f}")


if __name__ == "__main__":
    main()
