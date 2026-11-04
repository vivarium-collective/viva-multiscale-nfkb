"""Derive the composite's Boolean layer from Calzone 2010's cell-fate network (raw/, never edited).

Ownership (Alex, 2026-11-04: "Remove nothing; Calzone gates"). Calzone's network is kept whole: all 31 nodes, every
logic rule. Lipniacki 2004 and Calzone describe different things about NF-kB activation, so neither is cut:

- **Lipniacki owns HOW MUCH.** Its fitted kinetics give how much NF-kB is free in the nucleus over time once TNF acts:
  the nuclear fraction f, supplied as `$u_NFkB = f`, `$d_NFkB = 1 - f`.
- **Calzone owns WHETHER THE ROUTE IS OPEN.** Its chain TNFR -> RIP1 -> RIP1ub (needs cIAP) -> IKK -> NFkB is also how
  the death machinery shuts NF-kB down. Caspase-8 cleaves RIP1 (CASP8 -| RIP1), SMAC sequesters cIAP (SMAC -| cIAP),
  caspase-3 blocks NF-kB (CASP3 -| NFkB), and NF-kB keeps cIAP topped up (NFkB -> mcIAP -> cIAP). Lipniacki has none of
  these. Cutting them, as a first version of this script did, dropped Calzone's necrosis from 0.029 to 0.0001 and raised
  survival about tenfold (adversarial review, 2026-11-04; reproduced on cmaboss).

So the NFkB node keeps its own logic, `IKK AND (NOT CASP3)`, and only its rates change: while the route is open it
switches on at `$u_NFkB` and off at `$d_NFkB` (stationary P(on) = f); when the route closes it switches off at rate 1, as
in Calzone. At u = 1, d = 0 it is Calzone's node exactly (checks/boolean/coupled-equals-full).

The other changes:
- **TNF:** its self-holding logic becomes the rates `$u_TNF` / `$d_TNF`. The same receptor-occupancy signal that drives
  Lipniacki's TNF_R drives the receptor here.
- **Every rate is multiplied by `$k_time`** (Calzone time units per composite second). This is the death-machinery
  clock that the studies sweep (Alex, 2026-11-04). k_time = 1 is the original timing; k_time must be > 0.
- **`$TransRate` becomes `$r_tx / $k_time` in the 7 nodes that use it.** These are Calzone's slow,
  transcription-scale steps:
  - NF-kB-induced production of cFLIP, BCL2, mXIAP and mcIAP;
  - cIAP's production from mcIAP;
  - mROS, which is induced when NF-kB is OFF (`logic = NOT NFkB`);
  - the Survival phenotype node.

  After the k_time scaling, each of these switches ON at `r_tx` per second at any k_time, so they keep Lipniacki's
  own NF-kB -> target-protein timing (anchor_transcription.py; Alex: "anchor to Lipniacki, sweep death"). Their
  switch-OFF rates are unchanged in form (cFLIP, BCL2, mXIAP, mcIAP, mROS and Survival when their logic fails, cIAP
  when SMAC is on) and stay on the k_time clock; the calibration study decides whether they should move.
- With u_NFkB = 1, d_NFkB = 0, TNF held (u_TNF = d_TNF = 0), k_time = 1 and r_tx = 1/24, the network is Calzone's
  MaBoSS example exactly (checks/boolean/coupled-equals-full).

Everything else is kept byte for byte. The script refuses to write unless the input is the pinned file and each
rewritten node's text is exactly what it expects.

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
OUT = HERE / "processed" / "cellfate_coupled.bnd"
LOG = HERE / "processed" / "coupling.json"
RAW_SHA256 = "cfef1e7054d77f4736d8e36e712946ad1043c2f967913e400ec449b56a3d26dc"
TRANSRATE_NODES = ("cIAP", "cFLIP", "BCL2", "mROS", "mcIAP", "mXIAP", "Survival")

REPLACED = {
    "NFkB": (
        "node NFkB {\n"
        "  logic = IKK AND (NOT CASP3);\n"
        "  rate_up = ($High_NFkB ? 1e+100 : (@logic ? 1 : 0));\n"
        "  rate_down = ($High_NFkB ? 0 : (@logic ? 0 : 1));\n"
        "}",
        "node NFkB {\n"
        "  logic = IKK AND (NOT CASP3);\n"
        "  rate_up = ($High_NFkB ? 1e+100 : (@logic ? $u_NFkB : 0));\n"
        "  rate_down = ($High_NFkB ? 0 : (@logic ? $d_NFkB : 1));\n"
        "}",
        "logic kept (Calzone gates: the activation route is open and caspase-3 is off); while it holds, NF-kB follows "
        "Lipniacki's nuclear fraction f through $u_NFkB = f and $d_NFkB = 1 - f",
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
    "TransRate": "replaced by $r_tx / $k_time: target-gene induction on Lipniacki's clock (anchor_transcription.py)",
}
PARAMETERS_ADDED = ("u_NFkB", "d_NFkB", "u_TNF", "d_TNF", "k_time", "r_tx")
_RATE = re.compile(r"(rate_up|rate_down)\s*=\s*([^;]+);")
_BLOCK = re.compile(r"^node\s+(\w+)\s*\{.*?^\}", re.MULTILINE | re.DOTALL)


def _fail(message: str) -> NoReturn:
    sys.exit(f"prep.py: {message}")


def _encloses_all(text: str) -> bool:
    """True when `text` is balanced, so the parentheses that wrap it enclose the whole expression."""
    depth = 0
    for ch in text:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if depth < 0:
            return False
    return depth == 0


def main() -> None:
    data = RAW.read_bytes()
    if hashlib.sha256(data).hexdigest() != RAW_SHA256:
        _fail("raw/cellfate.bnd is not the pinned upstream file")
    blocks = {m.group(1): m.group(0) for m in _BLOCK.finditer(data.decode())}
    if len(blocks) != 31:
        _fail(f"expected 31 nodes, parsed {len(blocks)}")

    nodes = []
    for name, block in blocks.items():
        if name in REPLACED:
            expected, replacement, _ = REPLACED[name]
            if block != expected:
                _fail(f"node {name} is not the expected upstream text; refusing to rewrite it")
            block = replacement
        nodes.append(block)
    network = "\n\n".join(nodes) + "\n"

    users = sorted(n for n, b in blocks.items() if "$TransRate" in b)
    if tuple(sorted(TRANSRATE_NODES)) != tuple(users):
        _fail(f"expected $TransRate in {sorted(TRANSRATE_NODES)}, found it in {users}")
    network, swapped = re.subn(r"\$TransRate\b", "($r_tx / $k_time)", network)
    network, scaled = _RATE.subn(lambda m: f"{m.group(1)} = $k_time * ({m.group(2).strip()});", network)
    if scaled != 2 * len(nodes):
        _fail(f"expected a rate_up and a rate_down in each of {len(nodes)} nodes, scaled {scaled}")
    # Every rate must be EXACTLY $k_time times its original expression: the whole right-hand side is
    # "$k_time * (<expr>)", where the outer parentheses enclose all of <expr> (balanced), and nothing follows them.
    for kind, rhs in re.findall(r"(?i)(rate_up|rate_down)\s*=\s*([^;]+);", network):
        inner = re.fullmatch(r"\$k_time \* \((.*)\)", rhs.strip(), re.DOTALL)
        if inner is None or not _encloses_all(inner.group(1)):
            _fail(f"{kind} = {rhs.strip()} is not exactly $k_time * (original rate)")
    for name, block in zip(blocks, nodes, strict=True):
        if len(re.findall(r"(?i)rate_(up|down)\s*=", block)) != 2:
            _fail(f"node {name} does not have exactly one rate_up and one rate_down")
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
        "nodes": len(nodes),
        "removed": {},
        "ownership": "Lipniacki owns how much NF-kB (f); Calzone owns whether the activation route is open (logic kept)",
        "rewritten": {name: why for name, (_, _, why) in REPLACED.items()},
        "transrate_nodes": list(TRANSRATE_NODES),
        "transrate_uses_replaced": swapped,
        "rates_scaled_by_k_time": scaled,
        "parameters_removed": PARAMETERS_REMOVED,
        "parameters_added": list(PARAMETERS_ADDED),
    }, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(HERE)} ({len(nodes)} nodes, {swapped} TransRate uses, {scaled} rates scaled) "
          f"and {LOG.relative_to(HERE)}")


if __name__ == "__main__":
    main()
