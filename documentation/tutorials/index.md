# Tutorials

Each tutorial's code is a script in `documentation/tutorials/code/`, shown here as it is in the repository. The outputs
are from running those scripts. Run them from the repository root, in the run environment:

```bash
uv run --project compose python -I documentation/tutorials/code/<script>.py
```

```{admonition} Before you start
:class: tip
The tutorials use the vocabulary of the earlier sections. If a term is new, these pages define it:
- what the fate network is and how a Boolean network runs: {doc}`../science/boolean-networks`,
  {doc}`../science/calzone-network`, {doc}`../math/maboss`;
- the NF-κB model and its nuclear fraction $f$: {doc}`../science/lipniacki-model`;
- composites, processes, wiring and checks: {doc}`../design/composite-primer`;
- the death clock `k_time` and the transcription rate `r_tx`: {doc}`../design/time`.
```

```{toctree}
:maxdepth: 1

01-checks
02-boolean-layer
03-kinetic-to-boolean
04-death-clock
```
