# viva-multiscale-nfkb

**How does a cell decide whether to live or die when a TNF signal reaches it, and what does space add to that
decision?**

This workspace builds one multiscale model to answer that question. It is a
[process-bigraph](https://github.com/vivarium-collective/process-bigraph) composite of two published models, Lipniacki's
NF-κB model and Calzone's cell-fate network, and a TNF diffusion field. Each runs in its own engine and is responsible
for one part of the biology. The engines are wrapped as processes by the `viva-*` packages (the vivarium-collective
family of simulator wrappers); the adapters are small translation steps ({doc}`design/composite-primer`):

| Layer | What it models | Model | Engine |
|---|---|---|---|
| <span class="layer spatial">spatial</span> | TNF diffusing through the medium around the cell | finite-volume reaction–diffusion | viva-pde-particle `FVReactionDiffusion` |
| <span class="layer kinetic">kinetic</span> | TNF → IKK → NF-κB activation; NF-κB's nuclear oscillations and target genes | Lipniacki 2004 (BioModels BIOMD0000000786) | viva-tellurium `TelluriumProcess` (libRoadRunner) |
| <span class="layer boolean">Boolean</span> | The cell-fate decision: survival, apoptosis or necrosis | Calzone 2010 cell-fate network, all 31 nodes, gating Lipniacki's NF-κB | viva-maboss `MaBoSSProcess` (MaBoSS) |
| <span class="layer adapter">adapters</span> | Unit and meaning conversions between layers | — | `MathExpressionStep`, `RegionMean` |

TNF spreads through the medium. The receptors at the cell surface turn the TNF that reaches them into a
receptor-activation signal. NF-κB then enters the nucleus in damped waves. The cell's fate network weighs NF-κB's
protective genes against the death signals TNF itself starts. Each arrow in that chain is a coupling between two engines,
and each coupling built so far is checked against an independent oracle.

**New here?** A *composite* is one document that wires several models together; each model runs as a *process* that
reads and writes shared values. A *check* runs a small document and compares its results with an *oracle*, an expected
value that does not come from the code under test, such as a formula or another engine's output. The pages build these
up in order: the biology and the models ({doc}`science/index`), the mathematics the checks rely on
({doc}`math/index`), and the design decisions ({doc}`design/index`), starting from {doc}`design/composite-primer`. Decisions marked "Alex" were made by Alex Patrie,
who leads the project ({doc}`design/decisions`).

::::{grid} 2
:gutter: 2

:::{grid-item-card} 🚀 Getting started
:link: getting-started
:link-type: doc
Install the pinned environment and run every check in one command.
:::

:::{grid-item-card} 🧪 Tutorials
:link: tutorials/index
:link-type: doc
Run each layer, then the couplings, then sweep the clock.
:::

:::{grid-item-card} 🧬 The science
:link: science/index
:link-type: doc
TNF, NF-κB, apoptosis and necrosis, and the three models chosen to represent them.
:::

:::{grid-item-card} 🏗️ Design
:link: design/index
:link-type: doc
Each layer, each coupling and each clock, with the reason for every decision.
:::

:::{grid-item-card} ∑ Mathematics
:link: math/index
:link-type: doc
The switch, window-average, nuclear-fraction, clock-invariance and diffusion results the checks rely on.
:::

:::{grid-item-card} ✅ Verification
:link: verification/index
:link-type: doc
How a check is scored, and the catalogue of checks, each with its oracle and, where one is recorded, a proven-failing negative.
:::
::::

```{toctree}
:hidden:
:maxdepth: 2

getting-started
science/index
math/index
design/index
tutorials/index
verification/index
reference/index
```

```{admonition} Status (2026-11-06)
:class: important
Each layer has been built and checked on its own, and so has the kinetic → Boolean coupling. Study 0 has calibrated
that coupling ({doc}`design/calibration`), and Study 1 found that NF-κB's net protection is at most about 10 to 13 points (percent of cells) in
the composite, a limit set by the activation race in Calzone's network ({doc}`design/validation`). Whether to put NF-κB's activation route
on Lipniacki's clock is open. Then come TNF's dose–response at the receptor, the spatial → kinetic coupling,
then the integrated composite and the three
headline studies; see {doc}`design/roadmap`. The plan of record (this workspace's design
plan; the workspace is "section B" of compose-api's onboarding, {doc}`reference/history`) is
[`docs/design/plan-section-b.md`](https://github.com/vivarium-collective/viva-multiscale-nfkb/blob/main/docs/design/plan-section-b.md).
This documentation explains and justifies that plan, and does not replace it.
```
