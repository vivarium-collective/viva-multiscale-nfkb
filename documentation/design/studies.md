# The headline studies

Alex asked for all three (2026-11-04). They are named, not numbered, so they are not confused with the numbered studies of this
project's investigation ({doc}`../reference/glossary`) (Study 0, {doc}`calibration`; Study 1, {doc}`validation`). They nest, so they cost one composite document and one parameter sweep.

| Name | Study | Spatial setup | Swept | Readouts |
|---|---|---|---|---|
| Dose | **Fate vs uniform TNF dose.** The control | Uniform bath at concentration $c_0$, held or decaying at rate $\lambda$ ({doc}`../math/diffusion`) | $c_0$, $\lambda$, `k_time`, NF-κB intact or knocked out | the fraction of cells alive at 24 h (no death node ever on; decision 41), with the survival curve and the death mode (apoptosis, necrosis) ({doc}`calibration`); NF-κB's first nuclear peak (height, time) and period |
| Distance | **Fate vs distance from a TNF bolus.** The headline: what space adds | A point bolus at the centre of a 6 mm box with an absorbing band at its edges (an open medium); cells at r = 100, 300 and 1000 µm (decision 39) | r, bolus size, `k_time`, NF-κB intact or knocked out | as the dose study, plus TNF at the cell over time (`RegionMean`) |
| Wave timing | **NF-κB wave timing under a moving TNF front.** The mechanism | the distance study's runs (no new runs) | r | TNF front arrival vs the times of NF-κB's nuclear peaks |

## The scientific test

A cell in the distance study sees a pulse of TNF: it rises as the bolus arrives, peaks, and falls away. Its peak and
its total dose are far apart. At the chosen bolus sizes a cell's peak receptor occupancy runs from 0.006 to 0.98, but
its occupancy averaged over the day only from 0.001 to 0.12, so no single number places it on the held-dose curve.
Instead, each configuration (distance, bolus size, clock and NF-κB arm) is paired with a uniform bath that decays
exponentially, with the same peak TNF and the same sensed dose: the receptor occupancy the cell accumulates over 24 h
(decisions 50 and 56). Both models read TNF only through occupancy, so that is the dose the cell responds to. The
bath has everything the pulse has except what space adds: the delay before TNF arrives and the pulse's shape.
- **If fate in the pulse matches fate in its bath,** space acts only through dose.
- **If it doesn't,** when TNF arrives matters.

What counts as a match was fixed before the distance study runs, so that the answer cannot be tuned to the result:
- each comparison is an equivalence test with a margin of ±0.05 in the fraction alive at 24 h and about 1,700 cells on
  each side, which gives an 80% chance of showing equivalence when it holds (decisions 40 and 40b). It passes when the
  90% interval for the difference lies inside the margin, which is the two one-sided tests at 5% each. The interval is
  Newcombe's hybrid score interval, which keeps its coverage when survival is near 0 or 1, as it often is here;
- each configuration comes out equivalent, different or inconclusive, and the study's answer is the map of these
  outcomes (decision 53). "Different" means Fisher's exact test rejects no difference at 5% after Holm's correction
  across all 54 configurations. A configuration can pass both tests: with about 1,700 cells a side, a difference
  smaller than the margin can still be significant. It is then equivalent, because decision 40's margin is the
  smallest difference that matters, and both tests are reported (decision 55);
- the distance study runs its own seeds, 1891 to 3780, so its cells are independent of the dose study's, as both
  tests assume (decision 57);
- each configuration also reports its death ratio, and is flagged near the ceiling when both sides are within 0.05
  of everyone alive or everyone dead, where equivalence says little about timing (decision 58);
- both NF-κB arms run, each giving its own map (decision 52). Set side by side, the two maps suggest whether a
  timing effect needs NF-κB; no test of the difference between the arms is fixed in advance, so that reading is not
  a verdict.

The scorer was written and tested before any distance run (`workspace/investigations/tnf-fate-in-space/studies/s2-dose/e4_verdict.py`; its interval reproduces Newcombe's published values). The held baths give the dose curve itself, which the dose study reports ([below](#the-dose-studys-results)). The
wave-timing study shows the mechanism behind either answer.

## The death clock

`k_time` runs across all three studies ({doc}`time`), at 30, 60 and 120 min per unit (decision 38, from a dose
pilot: `analysis/exposure-pilot/`). Gene expression stays anchored at
$r_\text{tx} = 3.29\times10^{-4}\ \text{s}^{-1}$, so each study maps the protection race directly: how fast must the death
machinery be for TNF to kill, at each dose and each distance?

## Settings

- **Bolus sizes** are 1, 10 and 100 µM·µm², chosen from the field before running so that the three cells' peak doses
  span the dose curve at each clock (decisions 42 and 51).
- **The dose study's baths** run from receptor occupancy about 0.005 up to the highest peak any cell reaches (up to 1),
  denser below 0.2, where survival changes fastest. Each distance-study configuration has its own matched decaying
  bath (decisions 43 and 50). Every cell starts with TNF off, as in the field composite (decision 49).
- **The dose study runs locally,** through compose-api's own runner (decision 44). The distance study and the
  many-cells work run on compose-api itself (decision 54). A run there is capped today at 1,000 s of simulated time and
  30 min of computing, and a study runs 24 h, so how they run there is planned before any submission
  (`docs/design/plan-compose-api-dispatch.md`). Each new composite also gets one 990 s live run (decision 44).
- **TNF diffuses at 100 µm²/s,** the measured free-solution value (decision 45).

## The dose study's results

The dose study ran from 19 to 21 November 2026: 102 points (two NF-κB arms, three clocks, 8 held and 9 fading baths),
each with 1,890 cells (seeds 1 to 1,890, in 7 batches of 270) followed for 24 h, every TNF node off at the start
(decision 49). An alive fraction over 1,890 cells has a standard error of at most 0.012. Each table cell gives NF-κB
intact / knocked out. The data are `workspace/investigations/tnf-fate-in-space/studies/s2-dose/data/dose.json`, with
each point's hourly survival curve and median time of first death; the tables are generated from it by
`documentation/design/code/dose_tables.py` (`--check` fails when they are stale).

### Held baths: the dose curve

Alive at 24 h:

```{include} _dose_held.md
```

- **Survival falls with dose at every clock and in both arms.** From occupancy 0.005 to 1 it falls from 0.938 to 0
  at 30 min per unit, from 0.976 to 0.003 at 60, and from 0.990 to 0.241 at 120 (0.138 knocked out). At every dose,
  the slower the death clock, the more cells are alive.
- **NF-κB protects few cells.** At no held dose does the intact arm have fewer cells alive than the knocked-out arm,
  and it has at most 0.047 more at 30 min per unit, 0.069 at 60 and 0.103 at 120 (occupancy 1). Study 1 found a
  similar limit under held, saturating TNF ({doc}`validation`).
- **At low doses most cells reach no fate in 24 h:** at occupancy 0.005, 1,762, 1,834 and 1,864 of the 1,890 intact
  cells at 30, 60 and 120 min per unit. Without NF-κB no cell can reach Survival, so every knocked-out cell alive at
  24 h has reached no fate.
- **Cells are still dying at 24 h.** At 60 and 120 min per unit, up to 0.10 and 0.15 of the cells die in the last
  4 h, so the alive fraction at 24 h is not where the curve would settle.

How cells die. Death is absorbing, so a death node on at 24 h means it ever switched on, and a cell can show both.
The fraction with apoptosis on at 24 h:

```{include} _dose_held_apoptosis.md
```

and with necrosis on:

```{include} _dose_held_necrosis.md
```

With NF-κB intact, apoptosis is the more common mode at every held dose at 30 and 60 min per unit. At 120 min per unit,
and with NF-κB knocked out at every clock, necrosis is the more common at 6 to 8 of the 8 doses.

### Fading baths: the dose study's side of E4

Each fading bath is matched to one distance-study cell and bolus size: the cell's peak TNF and its sensed dose
(decisions 50 and 56). Alive at 24 h (the bolus is in µM·µm², and the half-life is the bath's):

```{include} _dose_baths.md
```

- **These are one side of E4's 54 comparisons.** The other side is the distance study, which has not run yet, so E4
  has no verdicts.
- **20 of the 54 baths are within 0.05 of everyone alive:** every bath at bolus size 1, at every clock and in both
  arms (0.960 to 0.996), and the 1000 µm cell's bath at bolus size 10 at 120 min per unit (0.966 and 0.966). Decision
  58 flags a configuration near the ceiling when its distance-study side is too, where equivalence says little about
  timing. No bath is within 0.05 of everyone dead.
- **NF-κB protects at most 0.061** in a fading bath (the 300 µm cell's bath at bolus size 100, 60 min per unit). At
  bolus size 1 the two arms differ by at most 0.0021, either way.
- **Few cells are still dying at the end of the day:** at most 0.033 of them in the last 4 h (at 120 min per unit),
  against up to 0.15 in the held baths. At 30 min per unit the median time of first death is 3.3 to 6.8 h in the fading
  baths and 4.2 to 13.6 h in the held ones; at 120 it is 11.7 to 16.8 h in the fading baths.

### NF-κB's first nuclear peak

```{include} _dose_nfkb.md
```

NF-κB's trajectory depends only on the bath, because the fate networks don't feed back into it, so its first peak is
the same at every clock and in both arms (knocking NF-κB out removes it from the fate network only). Its first peak
comes no later as the dose rises, from 40.5 min at occupancy 0.005 to 23.5 min at occupancy 1, and higher, from 0.66 of
the NF-κB in the nucleus to 0.94 by occupancy 0.2. The dose study records only this first peak, not the oscillation's
period that the readouts above list.

### How the results were checked

- **Every batch is the bath it names.** NF-κB's trajectory is deterministic, so each point's 7 batches must give the
  same one, and a run of its bath with a single fate network must reproduce it exactly. The study's summary checks
  both and refuses a point otherwise; all 102 points passed (rerun on 23 November 2026, `dose_study.py`). The same
  check refuses a batch run with decision 50's concentration-matched bath.
- **The 234 batches run with the concentration-matched baths** are kept aside in `parquet-runs-concentration-match/`
  and not used (decision 56).

## What Study 0 changes

Study 0 ({doc}`calibration`) found that TNF held on at saturation kills nearly every cell at every death clock it
tested (2 to 120 min per unit). Study 1 ({doc}`validation`) found that NF-κB's net protection is at most about 10 to 13 points (percent of cells)
at any clock from 30 to 480 min per unit as built, a limit set by the activation race in Calzone's own network
({doc}`../science/calzone-network`); with that race anchored (Option A, not adopted), the standard still fails ({doc}`validation`). So the signal these studies look for comes mainly
from exposure: how much TNF reaches a cell, when, and for how long. That is what the dose, distance and wave-timing
studies vary.

## Why a bolus

A bolus is an initial condition of the `fields` store. A bolus diffusing *is* a moving front, and its arrival at each
cell is what the distance and wave-timing studies time. It also has an exact solution: a Gaussian. In the 6 mm box with
its absorbing band, every cell matches the open-medium Gaussian (decision 39). A sustained source could be expressed
too, as a reaction term made local by a mask (decision 8b), and the band is built that way. But a sustained source
holds each cell at a steady dose, which would hide when TNF arrives ({doc}`spatial`).

## Grid

dx 10 µm and dt 0.25 s in the 6 mm box (decision 39). A geometry pilot found they give the same TNF at every cell as dx 5
µm or dt 0.05 s, to three decimals, and that every cell then matches the open-medium solution
(`analysis/exposure-pilot/geometry_pilot.json`).

Over a full day (`analysis/exposure-design/exposure_24h.py`, 3.7 h of computing on a shared machine), the band takes up
all but 1.2% of the bolus. Each cell's TNF follows the open medium for about 3 h, then falls below it as TNF reaching
the walls is removed, to 8–9% of the open-medium value at 24 h. A closed box would instead settle every cell at the
box's mean and give it 1.25 to 1.77 times the dose, most at the far cell.
