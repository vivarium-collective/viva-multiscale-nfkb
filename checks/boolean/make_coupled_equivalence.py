"""Write checks/boolean/coupled-{equals-full,equals-full-early,equals-full-seconds,equals-full-early-seconds,nfkb-knockout}/: the coupled cell-fate network
(MaBoSSProcess) must reproduce the FULL, unmodified Calzone network (the MaBoSS engine run directly on raw/cellfate.bnd,
not through the Process) wherever its inputs say what Calzone itself would.

The coupled network (workspace/datasets/calzone2010_cellfate/prep.py) keeps all 31 nodes and every logic rule. It changes
only the rates: NFkB follows `$u_NFkB`/`$d_NFkB` while its own logic (IKK AND NOT CASP3) holds, TNF is driven by
`$u_TNF`/`$d_TNF`, every rate is multiplied by `$k_time`, and `$TransRate` becomes `$r_tx / $k_time`. So:

- `equals-full`: with u_NFkB = 1, d_NFkB = 0 (NF-kB switches like Calzone's own node), k_time = 1, r_tx = 1/24 and TNF
  held on, the coupled network IS Calzone's network. Every one of the 31 nodes must match, under TNF, where the death arms
  are active and caspase-3 does shut NF-kB down. That also covers the rule "caspase-3 still forces NF-kB off".
- `equals-full-seconds` and `equals-full-early-seconds`: the same comparisons with the clock converted, k_time = 1/60
  (one Calzone unit per minute) and r_tx = k_time / 24, which leaves `$r_tx / $k_time` at 1/24, so every rate scales by
  the same factor. A continuous-time Markov chain with every rate scaled by k satisfies P_k(t) = P_1(k t), so the
  expected values are those of `equals-full` (2400 s) and `equals-full-early` ([420, 480] s). What these prove, and what
  they don't:
  - they catch an unclocked rate whose speed decides the race. CASP8 fails both; BAX and MOMP fail the early one;
  - a downstream relay (MPT, ROS, ATP, Cyt_c, CASP3) left unclocked changes when things happen, not how the fates
    split, and can pass both (adversarial re-review, 2026-11-04).

  That every rate is on the clock is guaranteed by construction: prep.py refuses to write unless each of the 62 rates is
  exactly `$k_time * (original rate)`.
- `equals-full-early`: the same comparison over the window [7, 8], while caspase-3 is switching on. The gate's
  `NOT CASP3` term is visible only there (P(NFkB) 0.215 with it, 0.244 without). Later, caspase-8 has cleaved RIP1
  and closed the route anyway. It is invisible even under Calzone's `$Low_CASP8` mutant, where caspase-3 hardly ever
  activates (0.0004), because the apoptosome needs caspase-8's BAX route.
- `nfkb-knockout`: u_NFkB = 0, d_NFkB = 1 (no nuclear NF-kB) against the full network with NF-kB loss of function
  (NFkB rate_up 0). The death arms must be intact.

The full network runs 200000 trajectories with its own seed, the Process 50000 with another. Every node is compared over
the case's last window (Calzone units: [38, 40] at t = 40, or [7, 8] for the early cases) at abs 0.01, about 4
combined standard errors at p = 0.5.

    uv run --project compose python -I checks/boolean/make_coupled_equivalence.py
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

import cmaboss
import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "workspace" / "datasets" / "calzone2010_cellfate"
HERE = Path(__file__).resolve().parent
UNITS, WINDOWS = 40.0, 20
FULL_SAMPLES, PROCESS_SAMPLES, ABS_TOL = 200_000, 50_000, 0.01
TRANSRATE = 1 / 24
FULL_PARAMETERS = {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0, "TransRate": TRANSRATE}
ISTATE_ON = {"FADD", "ATP", "cIAP", "TNF"}  # cellfate.cfg's istates, with TNF on
FULL_NFKB = "  rate_up = ($High_NFkB ? 1e+100 : (@logic ? 1 : 0));\n"


def _fail(message: str) -> NoReturn:
    sys.exit(f"make_coupled_equivalence.py: {message}")


def _nodes(network: str) -> list[str]:
    return sorted(re.findall(r"^node\s+(\w+)", network, re.MULTILINE | re.IGNORECASE))


def _full_marginals(network: str, units: float = UNITS, windows: int = WINDOWS, **mutant: float) -> dict[str, float]:
    """The full network's last-window node probabilities, from the MaBoSS engine itself (Calzone units)."""
    nodes = _nodes(network)
    lines = [f"${k} = {v!r};" for k, v in {**FULL_PARAMETERS, **mutant}.items()]
    lines += [f"max_time = {units!r};", f"time_tick = {units / windows!r};",
              f"sample_count = {FULL_SAMPLES};", "seed_pseudorandom = 20101;"]
    lines += [f"{n}.istate = {int(n in ISTATE_ON)};" for n in nodes]
    with tempfile.TemporaryDirectory() as tmp:
        bnd, cfg = Path(tmp, "full.bnd"), Path(tmp, "full.cfg")
        bnd.write_text(network)
        cfg.write_text("\n".join(lines) + "\n")
        probs, _, labels, _ = cmaboss.MaBoSSSim(str(bnd), str(cfg)).run().get_last_nodes_probtraj()
    marginals = dict.fromkeys(nodes, 0.0)
    marginals.update({str(n): float(p) for n, p in zip(labels, probs[0], strict=True)})
    return marginals


def _write(name: str, coupled: str, inputs: dict[str, float], interval: float, expected: dict[str, float],
           description: str, windows: int = WINDOWS) -> None:
    nodes = _nodes(coupled)
    initial = {n: float(n in ISTATE_ON) for n in nodes}
    parameters = {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
                  **inputs}
    document = {
        "global_time_precision": 6,
        "state": {
            "node_state": initial,
            "node_probabilities": dict(initial),
            "parameters": {},
            "steps": 0,
            "cellfate": {
                "_type": "process",
                "address": "local:viva_maboss.processes.MaBoSSProcess",
                "config": {
                    "network": coupled,
                    "parameters": parameters,
                    "initial_state": {n: 1.0 for n in nodes if n in ISTATE_ON},
                    "sample_count": PROCESS_SAMPLES,
                    "windows_per_interval": windows,
                    "seed": 7,
                },
                "interval": interval,
                "inputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                           "parameters": ["parameters"], "steps": ["steps"]},
                "outputs": {"node_state": ["node_state"], "node_probabilities": ["node_probabilities"],
                            "steps": ["steps"]},
            },
            "emitter": {
                "_type": "step",
                "address": "local:RAMEmitter",
                "config": {"emit": {"node_probabilities": "map[float]", "steps": "integer"}},
                "inputs": {"node_probabilities": ["node_probabilities"], "steps": ["steps"]},
            },
        },
    }
    case = {
        "description": description + " Generated by checks/boolean/make_coupled_equivalence.py.",
        "document": "document.pbg",
        "interval": interval,
        "scale_level": "molecule",
        "expect": [
            {"kind": "rows", "emitter": "emitter", "min": 2},
            {"kind": "scalar", "emitter": "emitter", "field": "steps", "expected": 1},
            *({"kind": "scalar", "emitter": "emitter", "field": f"node_probabilities.{n}",
               "expected": round(expected[n], 6), "abs": ABS_TOL} for n in nodes),
        ],
    }
    out = HERE / name
    out.mkdir(exist_ok=True)
    (out / "document.pbg").write_text(json.dumps(document, indent=2) + "\n")
    (out / "case.yaml").write_text(yaml.safe_dump(case, sort_keys=False, width=120))
    fates = {k: round(expected[k], 4) for k in ("Survival", "Apoptosis", "NonACD", "NFkB", "CASP3")}
    print(f"wrote checks/boolean/{name}: full network {fates}")


def main() -> None:
    full = (DATA / "raw" / "cellfate.bnd").read_text()
    coupled = (DATA / "processed" / "cellfate_coupled.bnd").read_text()
    if FULL_NFKB not in full:
        _fail("the full network's NFkB node is not the expected upstream text")
    if _nodes(full) != _nodes(coupled):
        _fail("the coupled network does not have exactly the full network's nodes")
    as_calzone = {"u_NFkB": 1.0, "d_NFkB": 0.0}
    wild_type = _full_marginals(full)
    early = _full_marginals(full, units=8.0, windows=8)

    _write("coupled-equals-full", coupled, {**as_calzone, "k_time": 1.0, "r_tx": TRANSRATE}, UNITS, wild_type,
           "The coupled network with NF-kB switching as Calzone's own node (u_NFkB = 1, d_NFkB = 0), k_time = 1, "
           "r_tx = 1/24, TNF on, t = 40, against the unmodified Calzone network on the MaBoSS engine. All 31 nodes "
           "agree, under TNF, where the death arms are active and caspase-3 shuts NF-kB down.")
    k = 1.0 / 60.0
    _write("coupled-equals-full-seconds", coupled, {**as_calzone, "k_time": k, "r_tx": k * TRANSRATE}, UNITS / k,
           wild_type,
           "As coupled-equals-full, with the clock converted: k_time = 1/60 (one Calzone unit per 60 s) over 2400 s, "
           "and r_tx = k_time/24, so every rate scales by k_time and the chain at 2400 s equals the original at 40 "
           "units. The expected values are the same as coupled-equals-full. It catches an unclocked rate that decides "
           "the race (CASP8 fails it); downstream relays may not show at t = 40, and prep.py guarantees by construction "
           "that every rate is on the clock.")
    _write("coupled-equals-full-early-seconds", coupled, {**as_calzone, "k_time": k, "r_tx": k * TRANSRATE}, 8.0 / k,
           early,
           "As coupled-equals-full-early ([7, 8] Calzone units), with the clock converted: k_time = 1/60, last window "
           "[420, 480] s, r_tx = k_time/24. While the death cascade is still moving, an unclocked relay shows (BAX and "
           "MOMP fail it).", windows=8)
    _write("coupled-equals-full-early", coupled, {**as_calzone, "k_time": 1.0, "r_tx": TRANSRATE}, 8.0,
           early,
           "As coupled-equals-full, over the window [7, 8] while caspase-3 is switching on. Calzone's NOT CASP3 term in "
           "NF-kB's gate is visible only here: later, caspase-8 has cleaved RIP1 and closed NF-kB's route anyway. Without "
           "the term, P(NFkB) in this window is 0.244 rather than 0.215 (probed on the engine, 200000 trajectories).",
           windows=8)
    knockout = full.replace(FULL_NFKB, FULL_NFKB.replace("(@logic ? 1 : 0)", "0"))
    _write("coupled-nfkb-knockout", coupled, {"u_NFkB": 0.0, "d_NFkB": 1.0, "k_time": 1.0, "r_tx": TRANSRATE}, UNITS,
           _full_marginals(knockout),
           "The coupled network with no nuclear NF-kB (u_NFkB = 0) against the full Calzone network with NF-kB loss of "
           "function (NFkB rate_up 0), TNF on, t = 40. All 31 nodes agree: TNF still reaches apoptosis and necrosis.")


if __name__ == "__main__":
    main()
