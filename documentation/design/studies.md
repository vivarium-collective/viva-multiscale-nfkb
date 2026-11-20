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
exponentially, with the same peak TNF and the same 24 h dose (decision 50). The bath has everything the pulse has except
what space adds: the delay before TNF arrives and the pulse's shape.
- **If fate in the pulse matches fate in its bath,** space acts only through dose.
- **If it doesn't,** when TNF arrives matters.

What counts as a match was fixed before the distance study runs, so that the answer cannot be tuned to the result:
- each comparison is an equivalence test with a margin of ±0.05 in the fraction alive at 24 h and about 1,700 cells on
  each side, which gives an 80% chance of showing equivalence when it holds (decisions 40 and 40b);
- each configuration comes out equivalent, different (a test of the difference rejects, corrected for the number of
  tests) or inconclusive, and the study's answer is the map of these outcomes (decision 53);
- both NF-κB arms run, so that a timing effect can be traced to NF-κB or ruled out (decision 52).

The held baths give the dose curve itself, which the dose study reports. The wave-timing study shows the mechanism
behind either answer.

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

Over a full day (`analysis/exposure-design/exposure_24h.py`, 3.6 h of computing on a shared machine), the band takes up
all but 1.2% of the bolus. Each cell's TNF follows the open medium for about 3 h, then falls below it as TNF reaching
the walls is removed, to 8–9% of the open-medium value at 24 h. A closed box would instead settle every cell at the
box's mean and give it 1.25 to 1.77 times the dose, most at the far cell.
