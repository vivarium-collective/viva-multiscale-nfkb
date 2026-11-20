# Getting started

## Install

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and git, on macOS or on Linux x86-64. (Linux on
arm64 is not supported: libRoadRunner, the engine of the signalling model, publishes no wheel for it.)

```bash
git clone https://github.com/vivarium-collective/viva-multiscale-nfkb
cd viva-multiscale-nfkb
uv sync --frozen --extra simulators
```

`--extra simulators` installs the three simulators the model joins: viva-pde-particle for the TNF field, Tellurium
for the NF-κB signalling and MaBoSS for the cell's fate. Keep it on every `uv run` too, or uv removes them again.

## Run the model

```bash
uv run --frozen --extra simulators \
    multiscale-nfkb run tnf_field_cell.tnf-field-cell --steps 600 \
    --emit nfkb_fraction,node_probabilities/Survival,node_probabilities/Apoptosis,node_probabilities/NonACD
```

This runs `tnf-field-cell`, one cell in a field of TNF, for 600 simulated seconds and prints the values named in
`--emit` at the end:

```text
nfkb_fraction = 0.7001305988285712
node_probabilities/Survival = 0.0
node_probabilities/Apoptosis = 0.0
node_probabilities/NonACD = 0.0
```

- `nfkb_fraction` is the share of the cell's NF-κB in the nucleus: 70% ten minutes after TNF arrives.
- `node_probabilities/...` are the chances of each fate (`NonACD` is necrosis). At ten minutes none has been reached
  yet; the fate network takes longer to decide.

Leave out `--emit` to print the model's whole state. `kinetic_boolean.kinetic-boolean` runs the signalling and fate
models on their own, with TNF held on.

## Open it in the workbench

The workbench is a browser interface for the model: its composites, studies and results.

```bash
bash scripts/serve.sh
```

It prints the address to open, for example `Workspace dashboard: http://127.0.0.1:8765`.

## Run it on a compute cluster

[compose-api](https://compose.cam.uchc.edu) runs process-bigraph models on BioSimulations' cluster. Start the workbench
with it as the backend, and runs go there instead of your machine:

```bash
.venv/bin/vivarium-workbench serve --backend-base-url https://compose.cam.uchc.edu
```

A run there reproduces a run on your machine to within floating-point noise.

## Next

- {doc}`findings`: what the model shows so far.
- {doc}`tutorials/index`: each part of the model on its own, then together.
- {doc}`reference/developer`: running the checks and building this documentation.
