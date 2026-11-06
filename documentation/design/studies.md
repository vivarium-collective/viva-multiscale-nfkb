# The headline studies

Alex asked for all three (2026-11-04). They nest, so they cost one composite document and one parameter sweep.

| # | Study | Spatial setup | Swept | Readouts |
|---|---|---|---|---|
| 2 | **Fate vs uniform TNF dose.** The control | Uniform bath at concentration $c_0$, optional linear decay | $c_0$, `k_time` | fraction of cells alive (no death node ever on) and with durable survival; the death mode (apoptosis, necrosis) ({doc}`calibration`); NF-κB's first nuclear peak (height, time) and period |
| 1 | **Fate vs distance from a TNF bolus.** The headline: what space adds | Point bolus at distance r from the cell's surface region | r, bolus size, `k_time` | as 2, plus TNF at the cell over time (`RegionMean`) |
| 3 | **NF-κB wave timing under a moving TNF front.** The mechanism | study 1's runs (no new runs) | r | TNF front arrival vs the times of NF-κB's nuclear peaks |

## The scientific test

Map each study-1 run onto study 2's dose axis using the TNF dose that reached the cell, both at its peak and
integrated over time.
- **If fate collapses onto study 2's curve,** space acts only through dose.
- **If it doesn't,** arrival timing matters.

What counts as "collapses" (the statistic that compares the mapped study-1 results with study 2's curve, and the
threshold) is not chosen yet. It will be fixed and recorded here before study 1 runs, so that the answer cannot be
tuned to the result.

Study 3 shows the mechanism behind either answer.

## The death clock

`k_time` runs across all three studies ({doc}`time`). Gene expression stays anchored at
$r_\text{tx} = 3.29\times10^{-4}\ \text{s}^{-1}$, so each study maps the race directly: how fast must the death
machinery be for TNF to kill, at each dose (study 2) and each distance (study 1)?

## What Study 0 changes

Study 0 ({doc}`calibration`) found that TNF held on at saturation kills nearly every cell at every death clock. So the
signal these studies look for has to come from exposure: how much TNF reaches a cell, when, and for how long. That
is what dose (study 2), distance (study 1) and front arrival (study 3) vary. NF-κB's protective products save cells
only if they persist far beyond their measured turnover (Studies 0c and 0d), so protection is not expected to add a
signal of its own here.

## Why a bolus

A bolus is an initial condition of the `fields` store, which `FVReactionDiffusion` supports today. A sustained point
source isn't expressible, because the reaction rate is one scalar over the whole domain ({doc}`spatial`). A bolus
diffusing in a reflecting box *is* a moving front, and it has an exact solution (a Gaussian, with image terms at the
walls).

## Grid

The grid is chosen from the convergence table in {doc}`spatial`, with the TNF value at the cell in mind, and confirmed
by one refinement run.
