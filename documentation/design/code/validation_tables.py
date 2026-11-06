"""Study 1's tables for documentation/design/validation.md, generated from the study's committed data.

Reads workspace/investigations/tnf-fate-in-space/studies/s1-survival-validation/data/phase_{a,b}.json and writes
documentation/design/_validation_phase_a.md, _validation_phase_b.md and _validation_matched.md.

Standard errors: an alive fraction p over n cells has SE sqrt(p(1-p)/n). Net protection (b - c)/n, from paired cells
where b were alive only with NF-kB and c only without, has SE sqrt((b + c) - (b - c)^2/n)/n (the variance of a mean of
paired differences in {-1, 0, 1}; math/statistics.md).

    uv run --no-project python -I documentation/design/code/validation_tables.py           # rewrite the tables
    uv run --no-project python -I documentation/design/code/validation_tables.py --check   # fail if one is stale
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "workspace" / "investigations" / "tnf-fate-in-space" / "studies" / "s1-survival-validation" / "data"
OUT = ROOT / "documentation" / "design"


_SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _p(value: float) -> str:
    """An exact McNemar p value as the page prints it: omitted from 0.05 up, one significant figure, and in
    scientific form below 0.001."""
    if value >= 0.05:
        return ""
    if value >= 0.001:
        return f" (p = {value:.1g})"
    mantissa, exponent = f"{value:.0e}".split("e")
    return f" (p = {mantissa}×10{str(int(exponent)).translate(_SUPERSCRIPT)})"


def _points(fraction: float) -> str:
    text = f"{100 * fraction:.1f}"
    return "−" + text[1:] if text.startswith("-") else text


def _alive(fraction: float) -> str:
    return f"{fraction:.3f}".rstrip("0").rstrip(".") if fraction else "0"


def phase_a(a: dict) -> str:
    rows = a["ceiling"]
    head = "| TransRate (per unit) | " + " | ".join(r["transrate"] for r in rows) + " |"
    rule = "|---|" + "---|" * len(rows)
    intact = "| Alive, NF-κB intact | " + " | ".join(f"{r['intact']['alive']:.3f}" for r in rows) + " |"
    knocked = "| Alive, NF-κB knocked out | " + " | ".join(_alive(r["knocked_out"]["alive"]) for r in rows) + " |"
    return "\n".join([head, rule, intact, knocked]) + "\n"


def phase_b(b: dict) -> str:
    lines = ["| Clock (min per unit) | Alive, intact | Alive, knocked out | Held survival, intact "
             "| Net protection (points) | Cells with no fate (intact / knocked out, of 200) |", "|---|---|---|---|---|---|"]
    for r in b["points"]:
        net = _points(r["net_protection"]) + _p(r["p_mcnemar_exact"])
        held = r["survival_on_last_2h_intact"] / r["cells"]
        lines.append(f"| {r['minutes_per_unit']} | {_alive(r['alive_intact'])} | {_alive(r['alive_knocked_out'])} "
                     f"| {_alive(held)} | {net} | {r['no_fate_intact']} / {r['no_fate_knocked_out']} |")
    return "\n".join(lines) + "\n"


def matched(a: dict, b: dict) -> str:
    alone = {m["minutes_per_unit"]: m for m in a["matched"]}
    lines = ["| Clock (min per unit) | Units read | Alive, knocked out: composite / alone "
             "| Alive, intact: composite / alone | Net protection (points): composite / alone |",
             "|---|---|---|---|---|"]
    for r in b["points"]:
        m, n = alone[r["minutes_per_unit"]], r["cells"]
        se = {k: math.sqrt(r[k] * (1 - r[k]) / n) for k in ("alive_knocked_out", "alive_intact")}
        bb, cc = r["rescued_by_nfkb"], r["lost_with_nfkb"]
        se_net = math.sqrt((bb + cc) - (bb - cc) ** 2 / n) / n
        lines.append(
            f"| {r['minutes_per_unit']} | {m['units']:g} "
            f"| {r['alive_knocked_out']:.3f} ± {se['alive_knocked_out']:.3f} / {m['knocked_out']['alive']:.3f} "
            f"| {r['alive_intact']:.3f} ± {se['alive_intact']:.3f} / {m['intact']['alive']:.3f} "
            f"| {_points(r['net_protection'])} ± {100 * se_net:.1f} / {_points(m['gap'])} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if a committed table differs")
    args = parser.parse_args()
    a = json.loads((DATA / "phase_a.json").read_text())
    b = json.loads((DATA / "phase_b.json").read_text())
    tables = {"_validation_phase_a.md": phase_a(a), "_validation_phase_b.md": phase_b(b),
              "_validation_matched.md": matched(a, b)}
    stale = []
    for name, text in tables.items():
        path = OUT / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        sys.exit(f"stale: {', '.join(stale)}; rerun without --check")
    if args.check:
        print("validation tables are current")


if __name__ == "__main__":
    main()
