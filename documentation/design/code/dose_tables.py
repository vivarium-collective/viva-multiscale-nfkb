"""The dose study's tables for documentation/design/studies.md, generated from the study's committed data.

Reads workspace/investigations/tnf-fate-in-space/studies/s2-dose/data/dose.json and
analysis/exposure-design/ring_exposure.json, and writes documentation/design/_dose_held.md, _dose_held_apoptosis.md,
_dose_held_necrosis.md, _dose_baths.md and _dose_nfkb.md.

    uv run --no-project python -I documentation/design/code/dose_tables.py           # rewrite the tables
    uv run --no-project python -I documentation/design/code/dose_tables.py --check   # fail if one is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOSE = ROOT / "workspace" / "investigations" / "tnf-fate-in-space" / "studies" / "s2-dose" / "data" / "dose.json"
RINGS = ROOT / "analysis" / "exposure-design" / "ring_exposure.json"
OUT = ROOT / "documentation" / "design"
ARMS = ("intact", "knocked_out")
PAIR = "\u00a0/\u00a0"  # intact / knocked out, with no-break spaces so a table cell never wraps inside a pair
RING_LABEL = {"near": "100 µm", "middle": "300 µm", "far": "1000 µm"}


def _fraction(value: float) -> str:
    return f"{value:.3f}"


def _exact(point: dict, key: str) -> float:
    """A point's fraction from its cell count, so the table rounds once: dose.json's fractions are already rounded to
    4 decimals (0.5725 for 1,082 of 1,890 alive, which is 0.572). Alive comes from alive_cells; a death mode's count is
    recovered from its 4-decimal fraction, which is exact because one cell (1/1,890) is more than 0.0001."""
    cells = point["cells"]
    count = point["alive_cells"] if key == "alive_24h" else round(point[key] * cells)
    if round(count / cells, 4) != point[key]:
        raise SystemExit(f"{DOSE}: {point['exposure']} {key} {point[key]} is not a count of {cells} cells")
    return count / cells


def _points(dose: dict) -> dict[tuple[str, int, str], dict]:
    points = {(p["arm"], p["minutes_per_unit"], p["exposure"]): p for p in dose["points"]}
    if len(points) != len(dose["points"]):
        raise SystemExit(f"{DOSE} names a point twice")
    return points


def _clocks(dose: dict) -> list[int]:
    return sorted({p["minutes_per_unit"] for p in dose["points"]})


def _held(dose: dict) -> list[str]:
    """Held exposures in order of occupancy."""
    held = {p["exposure"]: p["occupancy"] for p in dose["points"] if "occupancy" in p}
    return sorted(held, key=held.__getitem__)


def held(dose: dict, key: str = "alive_24h") -> str:
    """A fraction in each held bath, at each clock, NF-kB intact / knocked out: alive at 24 h, or how cells die, the
    fraction with Apoptosis (apoptosis_24h) or NonACD (necrosis_24h) on at 24 h."""
    points, clocks = _points(dose), _clocks(dose)
    lines = ["| Receptor occupancy | " + " | ".join(f"{m} min per unit" for m in clocks) + " |",
             "|---|" + "---|" * len(clocks)]
    for e in _held(dose):
        cells = [PAIR.join(_fraction(_exact(points[arm, m, e], key)) for arm in ARMS) for m in clocks]
        lines.append(f"| {points[ARMS[0], clocks[0], e]['occupancy']:g} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def baths(dose: dict, rings: dict) -> str:
    """Alive at 24 h in each fading bath, matched to a distance-study cell and bolus size, NF-kB intact / knocked out."""
    points, clocks = _points(dose), _clocks(dose)
    lines = ["| Matched cell, bolus (peak occupancy; half-life) | " + " | ".join(f"{m} min per unit" for m in clocks) + " |",
             "|---|" + "---|" * len(clocks)]
    for r in rings["rows"]:
        e = f"bath-{r['cell']}-M{r['bolus']:g}"
        if (ARMS[0], clocks[0], e) not in points:
            raise SystemExit(f"{DOSE} has no point for the bath {e}")
        cells = [PAIR.join(_fraction(_exact(points[arm, m, e], "alive_24h")) for arm in ARMS) for m in clocks]
        lines.append(f"| {RING_LABEL[r['cell']]}, {r['bolus']:g} ({r['peak_occupancy']:.3f}; "
                     f"{r['bath_half_life_min']:.0f} min) | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def nfkb(dose: dict) -> str:
    """NF-kB's first nuclear peak and its period (decision 60) in each bath. Both depend only on the bath: the fate
    networks don't feed back, and the knocked-out arm removes NF-kB from the fate network only, so they must be the
    same at every clock and in both arms."""
    peaks: dict[str, dict] = {}
    periods: dict[str, float | None] = {}
    for p in dose["points"]:
        peak = p["nfkb_first_peak"]
        if peaks.setdefault(p["exposure"], peak) != peak:
            raise SystemExit(f"{DOSE}: NF-kB's first peak in {p['exposure']} differs between points")
        if periods.setdefault(p["exposure"], p["nfkb_period_min"]) != p["nfkb_period_min"]:
            raise SystemExit(f"{DOSE}: NF-kB's period in {p['exposure']} differs between points")
    held_names = _held(dose)
    occupancy = {p["exposure"]: p["occupancy"] for p in dose["points"] if "occupancy" in p}
    lines = ["| Bath | First peak (min) | Nuclear fraction | Period (min) |", "|---|---|---|---|"]
    for e in held_names + [e for e in peaks if e not in held_names]:
        name = f"held, occupancy {occupancy[e]:g}" if e in occupancy else (
            "fading, matched to the {} cell, bolus {}".format(RING_LABEL[e.split("-")[1]], e.split("-M")[1]))
        period = "none" if periods[e] is None else f"{periods[e]:g}"
        lines.append(f"| {name} | {peaks[e]['time_min']:g} | {peaks[e]['nuclear_fraction']:.2f} | {period} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if a committed table differs")
    args = parser.parse_args()
    dose, rings = json.loads(DOSE.read_text()), json.loads(RINGS.read_text())
    if rings["kd_uM"] != dose["kd_uM"]:
        raise SystemExit(f"{RINGS} and {DOSE} use different Kd")
    tables = {"_dose_held.md": held(dose), "_dose_held_apoptosis.md": held(dose, "apoptosis_24h"),
              "_dose_held_necrosis.md": held(dose, "necrosis_24h"), "_dose_baths.md": baths(dose, rings),
              "_dose_nfkb.md": nfkb(dose)}
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
        print("dose tables are current")


if __name__ == "__main__":
    main()
