"""What each distance-study cell is exposed to, per bolus size: the numbers that size the pulses and fix the dose
mapping.

Reads exposure_24h_band1.json (decision 39's field with its absorbing band; exposure_24h.py), whose TNF at each cell is
per unit bolus mass (1 uM um^2). The field is linear in the bolus, so a bolus of mass M gives M times it. Occupancy is
the composite's one-site law, occ = c / (c + Kd), Kd 19 pM (decision 32), sampled every 30 s as the coupling samples it.

For each bolus size and cell it reports:
- the peak: concentration, occupancy and time;
- the 24 h integrals of concentration and of occupancy;
- the held occupancy giving the same occupancy-time over 24 h (the integral / 24 h);
- the share of the occupancy-time delivered after 1 h and after 6 h;
- its matched fading bath, c(t) = c0 exp(-lambda t), for the dose study (decision 56): the cell's peak concentration
  c0, and lambda solved so that the bath gives the cell the same sensed dose, the occupancy-time the coupling delivers
  over 24 h. Both models read TNF only through occupancy, so this is the dose the cell responds to. The coupling
  samples occupancy every 30 s and holds it for the interval, at t = 0, 30, ..., 86370 s, so both sides are summed
  that way: the bath from its t = 0 value, the ring cell from the field's samples (0 at t = 0, before the TNF
  arrives). Reported as lambda, its half-life, and the bath's 24 h concentration integral over the cell's.
It also reports the closed box's 24 h integral (exposure_24h_band0.json) against the band's, the band's effect.

    uv run --frozen --extra simulators python -I analysis/exposure-design/ring_exposure.py   # writes ring_exposure.json
"""

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from viva_multiscale_nfkb.composites.make_tnf_field_cell import KD  # uM, decision 32

HERE = Path(__file__).resolve().parent
SIZES = (1.0, 10.0, 100.0)  # bolus mass, uM um^2


def bath_sensed_dose(c0: float, decay: float, dt: float, samples: int) -> float:
    """The occupancy-time a bath c0 exp(-decay t) delivers through a coupling that samples it at t = 0, dt, ... and
    holds each value for dt."""
    c = c0 * np.exp(-decay * dt * np.arange(samples))
    return float((c / (c + KD)).sum() * dt)


def matched_decay(c0: float, sensed: float, dt: float, samples: int) -> float:
    """The decay rate at which a bath starting at c0 delivers `sensed` occupancy-time. The delivered dose falls
    monotonically from samples * dt * occ(c0) (no decay) towards dt * occ(c0) (instant decay), so it has one root."""
    return brentq(lambda k: bath_sensed_dose(c0, k, dt, samples) - sensed, 1e-12, 10.0, xtol=1e-15, rtol=1e-13)


def main() -> None:
    band = json.loads((HERE / "exposure_24h_band1.json").read_text())
    closed = json.loads((HERE / "exposure_24h_band0.json").read_text())
    t = np.array(band["time_s"])
    dt = float(band["sample_s"])
    if not np.allclose(np.diff(t), dt) or t[0] != dt:
        raise SystemExit("samples are not every sample_s from sample_s")
    span = float(t[-1])
    rows = []
    for name, distance in band["cells_um"].items():
        unit = np.array(band["tnf_at_cell"][name])
        unit_closed = np.array(closed["tnf_at_cell"][name])
        for size in SIZES:
            c = size * unit
            occ = c / (c + KD)
            k = int(c.argmax())
            c_integral = float(c.sum() * dt)
            occ_integral = float(occ.sum() * dt)
            sensed = float(occ[:-1].sum() * dt)  # held at t = 0 (0), 30, ..., 86370 s: the coupling's own sum
            lam = matched_decay(float(c[k]), sensed, dt, len(t))
            bath_c = float(c[k]) * np.exp(-lam * dt * np.arange(len(t)))
            rows.append({
                "cell": name, "distance_um": distance, "bolus": size,
                "peak_uM": float(c[k]), "peak_time_s": float(t[k]), "peak_occupancy": float(occ[k]),
                "c_integral_uM_s": c_integral, "occupancy_integral_s": occ_integral,
                "held_equivalent": occ_integral / span,
                "share_after_1h": float(occ[t > 3600].sum() * dt) / occ_integral,
                "share_after_6h": float(occ[t > 6 * 3600].sum() * dt) / occ_integral,
                "sensed_dose_s": sensed, "bath_decay_per_s": lam, "bath_half_life_min": math.log(2) / lam / 60,
                "bath_over_cell_c_integral": float(bath_c.sum() * dt) / c_integral,
                "closed_over_band_c_integral": float(unit_closed.sum() / unit.sum()),
            })
    (HERE / "ring_exposure.json").write_text(json.dumps({"kd_uM": KD, "span_s": span, "rows": rows}, indent=1) + "\n")
    print(f"{'cell':7}{'M':>6}{'peak occ':>10}{'at (min)':>9}{'occ-time (min)':>15}{'held equiv':>11}"
          f"{'after 1 h':>10}{'after 6 h':>10}{'bath t1/2 (min)':>16}{'bath/cell conc':>15}")
    for r in rows:
        print(f"{r['cell']:7}{r['bolus']:6g}{r['peak_occupancy']:10.3f}{r['peak_time_s'] / 60:9.1f}"
              f"{r['occupancy_integral_s'] / 60:15.2f}{r['held_equivalent']:11.5f}{r['share_after_1h']:10.2f}"
              f"{r['share_after_6h']:10.2f}{r['bath_half_life_min']:16.1f}{r['bath_over_cell_c_integral']:15.2f}")


if __name__ == "__main__":
    main()
