"""E4's scorer (s2-dose/e4_verdict.py) against oracles that don't come from it.

- The interval: Newcombe's own published values (Stat Med 1998;17:873, Table II, method 10 "Score, no CC"; 95%), and,
  at the 90% the test uses, his method 10 written out here from the paper's definition (two Wilson score intervals
  combined).
- Holm: the step-down adjustment written out here, applied to the scorer's own Fisher p-values in a shuffled family.
- The verdicts: counts whose outcome follows from the margin and the family size.
"""

from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

import pytest

SCORER = (Path(__file__).resolve().parents[1] / "workspace" / "investigations" / "tnf-fate-in-space" / "studies"
          / "s2-dose" / "e4_verdict.py")


@pytest.fixture(scope="module")
def e4():
    spec = importlib.util.spec_from_file_location("e4_verdict", SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Newcombe 1998, Table II, method 10: (a, m, b, n) -> 95% limits for a/m - b/n, to four decimals
NEWCOMBE_TABLE_II = {
    (56, 70, 48, 80): (0.0524, 0.3339),
    (9, 10, 3, 10): (0.1705, 0.8090),
    (6, 7, 2, 7): (0.0582, 0.8062),
    (5, 56, 0, 29): (-0.0381, 0.1926),
    (0, 10, 0, 20): (-0.1611, 0.2775),
    (0, 10, 0, 10): (-0.2775, 0.2775),
    (10, 10, 0, 20): (0.6791, 1.0000),
    (10, 10, 0, 10): (0.6075, 1.0000),
}


@pytest.mark.parametrize(("counts", "limits"), NEWCOMBE_TABLE_II.items())
def test_interval_reproduces_newcombe_table_ii(e4, counts, limits):
    low, high = e4.interval(*counts, alpha=0.05)
    assert (round(low, 4), round(high, 4)) == limits


def _wilson(x: int, n: int, z: float) -> tuple[float, float]:
    p = x / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z / (1 + z * z / n) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return centre - half, centre + half


def _newcombe_method_10(a: int, m: int, b: int, n: int, z: float) -> tuple[float, float]:
    p1, p2 = a / m, b / n
    l1, u1 = _wilson(a, m, z)
    l2, u2 = _wilson(b, n, z)
    return (p1 - p2 - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            p1 - p2 + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


@pytest.mark.parametrize("counts", [(945, 1890, 945, 1890), (1700, 1890, 1650, 1890), (12, 1890, 3, 1890),
                                    (1890, 1890, 1881, 1890)])
def test_the_test_interval_is_newcombes_at_90_percent(e4, counts):
    z90 = 1.6448536269514722  # the standard normal's 95th percentile
    assert e4.interval(*counts) == pytest.approx(_newcombe_method_10(*counts, z90), abs=1e-9)


def _holm(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted, running = [0.0] * len(p_values), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted


def test_holm_follows_the_step_down_rule_in_any_order(e4):
    pairs = [(945, 1890, 945 - k, 1890) for k in (0, 20, 40, 55, 70, 90, 120)]
    random.Random(7).shuffle(pairs)
    results = e4.verdicts(pairs)
    assert [r["holm_p"] for r in results] == pytest.approx(_holm([r["fisher_p"] for r in results]), rel=1e-12)


NULL = (945, 1890, 945, 1890)  # identical sides


def test_identical_sides_are_equivalent(e4):
    (result,) = e4.verdicts([NULL])
    assert result["verdict"] == "equivalent"
    assert result["difference"] == 0


def test_a_large_difference_is_different(e4):
    (result,) = e4.verdicts([(1400, 1890, 900, 1890)])
    assert result["verdict"] == "different"


def test_the_correction_spans_the_family(e4):
    # 0.04 apart: the interval crosses +0.05, and Fisher's p (~0.015) rejects alone but not after Holm over 54
    edge = (945, 1890, 870, 1890)
    (alone,) = e4.verdicts([edge])
    assert alone["interval_90"][1] > e4.MARGIN
    assert alone["verdict"] == "different"
    family = e4.verdicts([edge] + [NULL] * 53)
    assert family[0]["verdict"] == "inconclusive"
    assert family[0]["holm_p"] == pytest.approx(min(1.0, 54 * alone["fisher_p"]))


def test_equivalence_is_decided_before_a_significant_difference(e4):
    # 0.03 apart with 20,000 cells a side: Fisher rejects (p ~ 2e-9), but the whole interval is inside the margin.
    # Equivalent, as decision 55 says: the margin is the smallest difference that matters.
    (result,) = e4.verdicts([(10600, 20000, 10000, 20000)])
    assert result["holm_p"] < e4.ALPHA
    assert -e4.MARGIN < result["interval_90"][0] and result["interval_90"][1] < e4.MARGIN
    assert result["verdict"] == "equivalent"


def _dose_points():
    points = [{"arm": arm, "minutes_per_unit": clock, "exposure": f"occ{occ:g}", "cells": 1890, "alive_cells": 1000}
              for arm in ("intact", "knocked_out") for clock in (30, 60) for occ in (0.1, 1.0)]
    points += [{"arm": arm, "minutes_per_unit": clock, "exposure": f"bath-{ring}-M{bolus:g}", "cells": 1890,
                "alive_cells": 900 + 10 * clock + (5 if arm == "intact" else 0)}
               for arm in ("intact", "knocked_out") for clock in (30, 60) for ring in ("near", "far")
               for bolus in (1.0, 10.0)]
    return points


def _distance_points():
    return [{"arm": arm, "minutes_per_unit": clock, "ring": ring, "bolus": bolus, "cells": 1890, "alive_cells": 1200}
            for arm in ("intact", "knocked_out") for clock in (30, 60) for ring in ("near", "far") for bolus in (1, 10)]


def test_each_configuration_meets_its_own_bath(e4):
    rows = e4.score(_distance_points(), _dose_points())
    assert len(rows) == 16  # held baths take no part
    for row in rows:
        assert row["bath"]["exposure"] == f"bath-{row['ring']}-M{row['bolus']:g}"
        expected = 900 + 10 * row["minutes_per_unit"] + (5 if row["arm"] == "intact" else 0)
        assert row["bath"]["alive_cells"] == expected


@pytest.mark.parametrize("mutate", ["missing", "duplicate", "unpaired_bath", "no_count"])
def test_the_pairing_must_be_one_to_one(e4, mutate):
    distance, dose = _distance_points(), _dose_points()
    if mutate == "missing":
        distance[0]["bolus"] = 100  # no bath-near-M100 in the dose study
    elif mutate == "duplicate":
        distance.append(dict(distance[0]))
    elif mutate == "unpaired_bath":
        distance.pop()
    elif mutate == "no_count":
        del next(p for p in dose if p["exposure"].startswith("bath-"))["alive_cells"]
    with pytest.raises(ValueError):
        e4.score(distance, dose)


def test_impossible_counts_are_refused(e4):
    with pytest.raises(ValueError):
        e4.verdicts([(1891, 1890, 945, 1890)])
