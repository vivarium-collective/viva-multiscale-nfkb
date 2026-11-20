# viva-multiscale-nfkb

**A model of one cell deciding whether to live or die when TNF reaches it.**

TNF is a signalling protein that cells release during inflammation. When it reaches a cell it starts two programmes
at once: one leads to death, the other runs through NF-κB and protects the cell. This model follows that decision
across three scales, from the TNF spreading through the medium to the cell's fate.

```{image} _static/model-overview.svg
:alt: TNF spreads from a source to a cell; receptors bind it; NF-κB responds in damped waves; the cell's fate network settles on survival, apoptosis or necrosis.
:width: 100%
```

## Try it

```bash
git clone https://github.com/vivarium-collective/viva-multiscale-nfkb
cd viva-multiscale-nfkb
uv sync --frozen --extra simulators
uv run --frozen --extra simulators \
    multiscale-nfkb run tnf_field_cell.tnf-field-cell --steps 600 \
    --emit nfkb_fraction,node_probabilities/Survival,node_probabilities/Apoptosis
```

That runs ten minutes of one cell in a TNF field and prints how much of its NF-κB has moved into the nucleus, and
how likely each fate is so far. {doc}`getting-started` explains each step, and how to browse and run the model in the
workbench, on your machine or on a compute cluster.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Getting started
:link: getting-started
:link-type: doc
Install the model, run it from the command line, and open it in the workbench.
:::

:::{grid-item-card} What the model shows
:link: findings
:link-type: doc
What the studies have found so far, and what comes next.
:::

:::{grid-item-card} Tutorials
:link: tutorials/index
:link-type: doc
Run each part of the model on its own, then together.
:::

:::{grid-item-card} The science
:link: science/index
:link-type: doc
TNF, NF-κB, apoptosis and necrosis, and the published models that represent them.
:::
::::

The {doc}`reference section <reference/index>` holds the design, the mathematics and the checks behind every part of
the model.

```{toctree}
:hidden:
:caption: User guide

getting-started
findings
tutorials/index
science/index
```

```{toctree}
:hidden:
:caption: Reference

design/index
math/index
verification/index
reference/index
```
