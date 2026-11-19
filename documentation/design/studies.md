# The headline studies

Alex asked for all three (2026-11-04). They are named, not numbered, so they are not confused with the numbered studies of this
project's investigation ({doc}`../reference/glossary`) (Study 0, {doc}`calibration`; Study 1, {doc}`validation`). They nest, so they cost one composite document and one parameter sweep.

| Name | Study | Spatial setup | Swept | Readouts |
|---|---|---|---|---|
| Dose | **Fate vs uniform TNF dose.** The control | Uniform bath at concentration $c_0$, optional first-order decay (rate $\lambda$, {doc}`../math/diffusion`) | $c_0$, `k_time` | the fraction of cells alive at 24 h (no death node ever on; decision 41), with the survival curve and the death mode (apoptosis, necrosis) ({doc}`calibration`); NF-κB's first nuclear peak (height, time) and period |
| Distance | **Fate vs distance from a TNF bolus.** The headline: what space adds | A point bolus at the centre of a 6 mm box with an absorbing band at its edges (an open medium); cells at r = 100, 300 and 1000 µm (decision 39) | r, bolus size, `k_time` | as the dose study, plus TNF at the cell over time (`RegionMean`) |
| Wave timing | **NF-κB wave timing under a moving TNF front.** The mechanism | the distance study's runs (no new runs) | r | TNF front arrival vs the times of NF-κB's nuclear peaks |

## The scientific test

Map each distance-study run onto the dose study's dose axis using the TNF dose that reached the cell, both at its peak and
integrated over time.
- **If fate collapses onto the dose study's curve,** space acts only through dose.
- **If it doesn't,** arrival timing matters.

What counts as "collapses" was fixed before the distance study runs, so that the answer cannot be tuned to the result
(decision 40):
- it is an equivalence test, with a margin of ±0.05 in the fraction alive at 24 h and about 270 cells per point;
- it compares each run with a monotone fit of the dose curve, mapped by the TNF dose that reached the cell;
- runs outside the dose study's range are reported, not extrapolated.

The wave-timing study shows the mechanism behind either answer.

## The death clock

`k_time` runs across all three studies ({doc}`time`), at 30, 60 and 120 min per unit (decision 38, from a dose
pilot: `analysis/exposure-pilot/`). Gene expression stays anchored at
$r_\text{tx} = 3.29\times10^{-4}\ \text{s}^{-1}$, so each study maps the protection race directly: how fast must the death
machinery be for TNF to kill, at each dose and each distance?

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
(`analysis/exposure-pilot/geometry_pilot.json`). A 24 h run of that field takes about 2.6 h.
