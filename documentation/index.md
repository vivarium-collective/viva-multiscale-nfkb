# viva-multiscale-nfkb

**How does a cell decide whether to live or die when a TNF signal reaches it, and what does space add to that
decision?**

This workspace builds one multiscale model to answer that question. It is a
[process-bigraph](https://github.com/vivarium-collective/process-bigraph) composite of three published models, each
running in its own engine and each responsible for one part of the biology:

| Layer | What it models | Model | Engine |
|---|---|---|---|
| <span class="layer spatial">spatial</span> | TNF diffusing through the medium around the cell | finite-volume reaction–diffusion | viva-pde-particle `FVReactionDiffusion` |
| <span class="layer kinetic">kinetic</span> | TNF → IKK → NF-κB activation; NF-κB's nuclear oscillations and target genes | Lipniacki 2004 (BioModels BIOMD0000000786) | viva-tellurium `TelluriumProcess` (libRoadRunner) |
| <span class="layer boolean">Boolean</span> | The cell-fate decision: survival, apoptosis or necrosis | Calzone 2010 cell-fate network, all 31 nodes, gating Lipniacki's NF-κB | viva-maboss `MaBoSSProcess` (MaBoSS) |
| <span class="layer adapter">adapters</span> | Unit and meaning conversions between layers | — | `MathExpressionStep`, `RegionMean` |

TNF spreads through the medium. The receptors at the cell surface turn the TNF that reaches them into a
receptor-activation signal. NF-κB then enters the nucleus in damped waves. The cell's fate network weighs NF-κB's
protective genes against the death signals TNF itself starts. Each arrow in that chain is a coupling between two engines,
and each coupling is checked against an independent oracle.

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
How a check is scored, and the catalogue of checks, each with its oracle and a proven-failing negative.
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

```{admonition} Status (2026-11-04)
:class: important
Each layer and each pairwise coupling has been built and checked on its own. The integrated composite and the three
headline studies are next; see {doc}`design/roadmap`. The plan of record is
[`docs/design/plan-section-b.md`](https://github.com/vivarium-collective/viva-multiscale-nfkb/blob/main/docs/design/plan-section-b.md).
This documentation explains and justifies that plan, and does not replace it.
```
