"""Derive the composite's Boolean layer from Calzone 2010's cell-fate network (raw/, never edited).

Ownership (Alex, 2026-11-04: "the most biologically accurate and overall model-native option"). Lipniacki 2004 owns NF-kB
activation: its lumped step TNF -> IKK -> IkB degradation -> NF-kB nuclear import stands in for Calzone's
RIP1 -> RIP1ub -> IKK -> NFkB arm. Calzone owns what Lipniacki does not model: the death-receptor arms (DISC_TNF -> CASP8
-> ... -> CASP3 -> Apoptosis; RIP1 -> RIP1K -> ROS -> MPT -> NonACD) and how NF-kB's targets (cFLIP, BCL2, XIAP) hold them
back. So the reduction removes only the nodes whose sole role is that duplicated arm, and turns the two nodes the outer
layers drive into rate-driven inputs:

- removed: RIP1ub (only feeds IKK), IKK (only feeds NFkB), and cIAP and mcIAP, which only fed RIP1ub and so lead
  nowhere once it is gone. `$Low_cIAP`, used only by cIAP, goes with them.
- NFkB: its logic `IKK AND NOT CASP3` becomes `NOT CASP3`, with `$u_NFkB` / `$d_NFkB` in place of IKK's fixed rates 1
  and 0. With CASP3 off, NFkB is on at stationarity with probability u / (u + d); CASP3 still forces it off, and
  Calzone's own `$High_NFkB` mutant switch is kept unchanged.
- TNF: its self-holding logic becomes the rates `$u_TNF` / `$d_TNF`, so the same signal that drives Lipniacki's
  TNF_R drives the receptor here.

- every rate: multiplied by `$k_time` (Calzone time units per composite second), so the time conversion is one
  parameter the studies sweep (Alex, 2026-11-04) and Calzone's internal rate ratios are unchanged. `k_time = 1`
  reproduces the original timing.
- `$TransRate` (NF-kB target-gene induction): replaced by `$r_tx / $k_time`, so after the k_time scaling, target genes
  switch on at `r_tx` per second, Lipniacki's own NF-kB -> target-protein timing (anchor_transcription.py). k_time
  then sweeps only the death machinery's clock (Alex, 2026-11-04). With k_time = 1 and r_tx = 1/24 this is Calzone's
  MaBoSS example exactly.

Everything else is kept byte for byte. The script refuses to write unless the input is the pinned file, each rewritten
node's text is exactly what it expects, and no kept node refers to a removed one.

    uv run --project compose python -I workspace/datasets/calzone2010_cellfate/prep.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import NoReturn

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw" / "cellfate.bnd"
OUT = HERE / "processed" / "cellfate_reduced.bnd"
LOG = HERE / "processed" / "reduction.json"
RAW_SHA256 = "cfef1e7054d77f4736d8e36e712946ad1043c2f967913e400ec449b56a3d26dc"

REMOVED = {
    "RIP1ub": "only input is cIAP AND RIP1, only output is IKK: the ubiquitination step of the NF-kB arm Lipniacki owns",
    "IKK": "only output is NFkB: Lipniacki models IKK activation and its action on IkB:NF-kB",
    "cIAP": "only output was RIP1ub (removed); its effect on the kept network is nil",
    "mcIAP": "only output was cIAP (removed)",
}
REPLACED = {
    "NFkB": (
        "node NFkB {\n"
        "  logic = IKK AND (NOT CASP3);\n"
        "  rate_up = ($High_NFkB ? 1e+100 : (@logic ? 1 : 0));\n"
        "  rate_down = ($High_NFkB ? 0 : (@logic ? 0 : 1));\n"
        "}",
        "node NFkB {\n"
        "  logic = NOT CASP3;\n"
        "  rate_up = ($High_NFkB ? 1e+100 : (@logic ? $u_NFkB : 0));\n"
        "  rate_down = ($High_NFkB ? 0 : (@logic ? $d_NFkB : 1));\n"
        "}",
        "IKK's activation is Lipniacki's; the kinetic layer's nuclear NF-kB drives $u_NFkB/$d_NFkB, CASP3 still blocks",
    ),
    "TNF": (
        "node TNF {\n"
        "  logic = TNF;\n"
        "  rate_up = @logic ? 1 : 0;\n"
        "  rate_down = @logic ? 0 : 1;\n"
        "}",
        "node TNF {\n"
        "  rate_up = $u_TNF;\n"
        "  rate_down = $d_TNF;\n"
        "}",
        "an input: the receptor-occupancy signal that drives Lipniacki's TNF_R drives $u_TNF/$d_TNF",
    ),
}
PARAMETERS_REMOVED = {
    "Low_cIAP": "used only by cIAP (removed)",
    "TransRate": "replaced by $r_tx / $k_time: gene expression on Lipniacki's clock (anchor_transcription.py)",
}
PARAMETERS_ADDED = ("u_NFkB", "d_NFkB", "u_TNF", "d_TNF", "k_time", "r_tx")
_RATE = re.compile(r"(rate_up|rate_down)\s*=\s*([^;]+);")
_BLOCK = re.compile(r"^node\s+(\w+)\s*\{.*?^\}", re.MULTILINE | re.DOTALL)


def _fail(message: str) -> NoReturn:
    sys.exit(f"prep.py: {message}")


def main() -> None:
    data = RAW.read_bytes()
    if hashlib.sha256(data).hexdigest() != RAW_SHA256:
        _fail("raw/cellfate.bnd is not the pinned upstream file")
    blocks = {m.group(1): m.group(0) for m in _BLOCK.finditer(data.decode())}
    if len(blocks) != 31:
        _fail(f"expected 31 nodes, parsed {len(blocks)}")

    kept = []
    for name, block in blocks.items():
        if name in REMOVED:
            continue
        if name in REPLACED:
            expected, replacement, _ = REPLACED[name]
            if block != expected:
                _fail(f"node {name} is not the expected upstream text; refusing to rewrite it")
            block = replacement
        kept.append(block)
    network = "\n\n".join(kept) + "\n"
    # Calzone's rates are per abstract time unit; the composite runs in seconds. Every rate is multiplied by
    # $k_time (Calzone units per second), so Calzone's internal ratios are untouched and the conversion is one study
    # parameter (Alex, 2026-11-04: sweep it as a study axis rather than fix one value). k_time = 1 is the original.
    # Gene expression keeps Lipniacki's clock (Alex, 2026-11-04: "anchor to Lipniacki, sweep death"): $TransRate becomes
    # $r_tx / $k_time, so once every rate is multiplied by $k_time below, target genes switch on at r_tx per second
    # (anchor_transcription.py) whatever k_time the study sweeps.
    network, swapped = re.subn(r"\$TransRate\b", "($r_tx / $k_time)", network)
    if swapped != 5:
        _fail(f"expected $TransRate in 5 kept nodes (cFLIP, BCL2, mROS, mXIAP, Survival), found {swapped}")
    network, scaled = _RATE.subn(lambda m: f"{m.group(1)} = $k_time * ({m.group(2).strip()});", network)
    if scaled != 2 * len(kept):
        _fail(f"expected a rate_up and a rate_down in each of {len(kept)} nodes, scaled {scaled}")

    names = set(blocks)
    for name, block in zip([n for n in blocks if n not in REMOVED], kept, strict=True):
        body = block.split("{", 1)[1]
        stale = {r for r in REMOVED if re.search(rf"\b{r}\b", body)}
        if stale:
            _fail(f"kept node {name} still refers to removed {sorted(stale)}")
    for parameter in PARAMETERS_REMOVED:
        if f"${parameter}" in network:
            _fail(f"${parameter} is still used")
    for parameter in PARAMETERS_ADDED:
        if f"${parameter}" not in network:
            _fail(f"${parameter} is not used")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(network)
    LOG.write_text(json.dumps({
        "source": "raw/cellfate.bnd (sysbio-curie/MaBoSS@375ffad engine/tests/maboss/cellfate/cellfate.bnd)",
        "source_sha256": RAW_SHA256,
        "output_sha256": hashlib.sha256(network.encode()).hexdigest(),
        "nodes_in": len(names),
        "nodes_out": len(names) - len(REMOVED),
        "removed": REMOVED,
        "rewritten": {name: why for name, (_, _, why) in REPLACED.items()},
        "parameters_removed": PARAMETERS_REMOVED,
        "parameters_added": list(PARAMETERS_ADDED),
    }, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(HERE)} ({len(names) - len(REMOVED)} nodes) and {LOG.relative_to(HERE)}")


if __name__ == "__main__":
    main()
