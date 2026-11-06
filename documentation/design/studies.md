# The headline studies

Alex asked for all three (2026-11-04). They are named, not numbered, so they are not confused with the
investigation's numbered studies (Study 0, {doc}`calibration`; Study 1, {doc}`validation`). They nest, so they cost one composite document and one parameter sweep.

| Name | Study | Spatial setup | Swept | Readouts |
|---|---|---|---|---|
| Dose | **Fate vs uniform TNF dose.** The control | Uniform bath at concentration $c_0$, optional first-order decay (rate $\lambda$, {doc}`../math/diffusion`) | $c_0$, `k_time` | fraction of cells alive (no death node ever on) and with durable survival; the death mode (apoptosis, necrosis) ({doc}`calibration`); NF-κB's first nuclear peak (height, time) and period |
| Distance | **Fate vs distance from a TNF bolus.** The headline: what space adds | Point bolus at distance r from the cell's surface region | r, bolus size, `k_time` | as the dose study, plus TNF at the cell over time (`RegionMean`) |
| Wave timing | **NF-κB wave timing under a moving TNF front.** The mechanism | the distance study's runs (no new runs) | r | TNF front arrival vs the times of NF-κB's nuclear peaks |

## The scientific test

Map each distance-study run onto the dose study's dose axis using the TNF dose that reached the cell, both at its peak and
integrated over time.
- **If fate collapses onto the dose study's curve,** space acts only through dose.
- **If it doesn't,** arrival timing matters.

What counts as "collapses" (the statistic that compares the mapped distance-study results with the dose study's curve, and the
threshold) is not chosen yet. It will be fixed and recorded here before the distance study runs, so that the answer cannot be
tuned to the result.

The wave-timing study shows the mechanism behind either answer.

## The death clock

`k_time` runs across all three studies ({doc}`time`). Gene expression stays anchored at
$r_\text{tx} = 3.29\times10^{-4}\ \text{s}^{-1}$, so each study maps the race directly: how fast must the death
machinery be for TNF to kill, at each dose and each distance?

## What Study 0 changes

Study 0 ({doc}`calibration`) found that TNF held on at saturation kills nearly every cell at every death clock it
tested (2 to 120 min per unit). Study 1 ({doc}`validation`) found that NF-κB's net protection is at most about 10 to 13 points (percent of cells)
at any clock from 30 to 480 min per unit, a limit set by the activation race in Calzone's own network
({doc}`../science/calzone-network`). So the signal these studies look for comes mainly
from exposure: how much TNF reaches a cell, when, and for how long. That is what the dose, distance and wave-timing
studies vary.

## Why a bolus

A bolus is an initial condition of the `fields` store, which `FVReactionDiffusion` supports today. A sustained point
source isn't expressible, because the reaction rate is one scalar over the whole domain ({doc}`spatial`). A bolus
diffusing in a reflecting box *is* a moving front, and it has an exact solution (a Gaussian, with image terms at the
walls).

## Grid

The grid is chosen from the convergence table in {doc}`spatial`, with the TNF value at the cell in mind, and confirmed
by one refinement run.
