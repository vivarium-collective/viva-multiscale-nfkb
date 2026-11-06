"""Study 1, Phase A: Calzone's network alone under held TNF, the comparator for the composite.

Calzone's network is the coupled network with u_NFkB = 1, d_NFkB = 0 and k_time = 1 (checks/boolean/coupled-equals-full),
so r_tx plays TransRate. NF-kB knocked out is u_NFkB = 0, d_NFkB = 1. Death is absorbing, as in Phase B. Each point runs
20,000 trajectories through MaBoSS's own engine API and reads the joint state distribution at the end. "Alive" means
neither Apoptosis nor NonACD is on (with absorbing death, never on).

Two sweeps, both written to data/phase_a.json:
- ceiling: TransRate from MaBoSS's example 1/24 up to 64 per unit, read at t = 40 Calzone units;
- matched: the composite's own settings at each death clock of m minutes per unit, that is TransRate r_tx * 60 m (the
  genes run at r_tx per second, everything else on k_time) read after 24 h = 24 * 60 / m units.

    uv run --project compose python -I workspace/investigations/tnf-fate-in-space/studies/s1-survival-validation/phase_a.py
"""

import json
import tempfile
from fractions import Fraction
from pathlib import Path

import cmaboss

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
NETWORK = ROOT / "workspace" / "datasets" / "calzone2010_cellfate" / "processed" / "cellfate_coupled.bnd"
R_TX = json.loads((NETWORK.parent / "transcription_anchor.json").read_text())["r_tx_per_s"]
BASE = {"High_NFkB": 0.0, "Low_CASP8": 0.0, "Low_RIP1": 0.0, "Low_cIAP": 0.0, "u_TNF": 0.0, "d_TNF": 0.0,
        "k_time": 1.0, "absorb_death": 1.0}
NFKB = {"intact": {"u_NFkB": 1.0, "d_NFkB": 0.0}, "knocked_out": {"u_NFkB": 0.0, "d_NFkB": 1.0}}
ON_AT_START = ("FADD", "ATP", "cIAP", "TNF")
CEILING_TRANSRATES = (Fraction(1, 24), Fraction(1, 4), Fraction(1), Fraction(4), Fraction(16), Fraction(64))
MATCHED_MINUTES = (30, 120, 180, 200, 240, 480)
CELLS, WINDOWS, SEED = 20_000, 40, 11
DEATH = {"Apoptosis", "NonACD"}


def _on(label: str) -> set[str]:
    return set() if label == "<nil>" else set(label.split(" -- "))


def run(nfkb: str, transrate: float, units: float, workdir: Path) -> dict[str, float]:
    nodes = [line.split()[1] for line in NETWORK.read_text().splitlines() if line.startswith("node ")]
    lines = [f"${k} = {v!r};" for k, v in {**BASE, **NFKB[nfkb], "r_tx": transrate}.items()]
    lines += [f"max_time = {units!r};", f"time_tick = {units / WINDOWS!r};", f"sample_count = {CELLS};",
              f"seed_pseudorandom = {SEED};"]
    lines += [f"{n}.istate = {int(n in ON_AT_START)};" for n in nodes]
    cfg = workdir / f"{nfkb}.cfg"
    cfg.write_text("\n".join([*lines, ""]))
    probs, _, labels, _ = cmaboss.MaBoSSSim(str(NETWORK), str(cfg)).run().get_last_probtraj()
    states = [(w, _on(str(label))) for w, label in zip(list(probs[0]), labels, strict=True)]
    return {"alive": round(sum(w for w, on in states if not DEATH & on), 4),
            "survival_on": round(sum(w for w, on in states if "Survival" in on), 4)}


def _pair(transrate: float, units: float, workdir: Path) -> dict:
    intact, knocked_out = run("intact", transrate, units, workdir), run("knocked_out", transrate, units, workdir)
    return {"transrate_per_unit": round(transrate, 4), "units": round(units, 4), "intact": intact,
            "knocked_out": knocked_out, "gap": round(intact["alive"] - knocked_out["alive"], 4)}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ceiling = [{"transrate": str(r), **_pair(float(r), 40.0, Path(tmp))} for r in CEILING_TRANSRATES]
        matched = [{"minutes_per_unit": m, **_pair(R_TX * 60 * m, 24 * 60 / m, Path(tmp))} for m in MATCHED_MINUTES]
    for row in ceiling + matched:
        label = f"TransRate {row['transrate']:>5s} at t = 40" if "transrate" in row else f"{row['minutes_per_unit']:4d} min/unit"
        print(f"{label}: alive intact {row['intact']['alive']:.3f}, knocked out {row['knocked_out']['alive']:.3f}, "
              f"gap {row['gap']:+.3f}; Survival on, intact {row['intact']['survival_on']:.3f}")
    (HERE / "data" / "phase_a.json").write_text(json.dumps(
        {"cells": CELLS, "windows": WINDOWS, "seed": SEED, "absorb_death": 1.0, "ceiling": ceiling, "matched": matched},
        indent=1) + "\n")
    print("wrote data/phase_a.json")


if __name__ == "__main__":
    main()
