# Architecture

## The composite

```text
   ┌──────────────── spatial ────────────────┐
   │ FVReactionDiffusion: TNF field (µM)     │
   └───────────────┬─────────────────────────┘
                   │ fields.TNF
            RegionMean (cell-surface voxels)           adapter
                   │ tnf_at_cell (µM)
        dose–response (McMillan 2021, d1)              adapter
                   │ tnf_occupancy (0–1)
        ┌──────────┴────────────┐
        │                       │ u_TNF = occ, d_TNF = 1 − occ
        │ parameters_in.TNF_R   ▼
┌───────▼──── kinetic ────┐   ┌──────────── Boolean ────────────┐
│ TelluriumProcess:       │   │ MaBoSSProcess: Calzone, gated   │
│ Lipniacki 2004          │   │ (all 31 nodes)                  │
└───────┬─────────────────┘   └───────────────▲─────────────────┘
        │ five NF-κB species                    │ u_NFkB = fκ/k_time, d_NFkB = (1 − f)κ/k_time
        └── nuclear fraction f (adapter) ───────┘
```

Reading the diagram (terms such as process, store, port and adapter: {doc}`composite-primer`):
- **`fields.TNF`**: the TNF concentration on the spatial grid, in µM ({doc}`spatial`).
- **`RegionMean`**: an adapter that averages the field over the grid cells at the cell's surface, giving one
  concentration, `tnf_at_cell`.
- **d1**: the dose–response, which turns that concentration into **occ**, the fraction of TNF receptors occupied
  ({doc}`rule-based`).
- **`parameters_in.TNF_R`**: the NF-κB model's TNF input ({doc}`../science/lipniacki-model`), set to occ.
- **`u_TNF`, `d_TNF`**: the fate network's TNF node rates, so the node is on a fraction occ of the time.
- **$f$**: NF-κB's nuclear fraction. **`u_NFkB`, `d_NFkB`** are the fate network's NF-κB node rates, with κ its
  flipping speed and `k_time` the death clock ({doc}`coupling`, {doc}`time`).

## Design principles

### 1. One owner per quantity

Every quantity is written by exactly one layer. Other layers read it, and an adapter translates it in between.

- **Why:** two layers that both model the same biology (say, NF-κB activation) give two answers, and the composite
  has no way to say which is right. One owner removes the question.
- **How it shows up:**
  - The spatial layer owns TNF transport, and the kinetic layer only reads TNF at the cell.
  - Lipniacki owns *how much* NF-κB is active; Calzone owns *whether its route is open*, so nothing is removed and
    Calzone's own logic gates the NF-κB input ({doc}`boolean`).
  - One `tnf_occupancy` store is read by two layers.

### 2. Reuse published models, and change them only by script

Each model comes from its published source, pinned with a sha256 in `workspace/datasets/<name>/raw/`, which is never
edited. Every change is a committed, deterministic script (`prep.py`) that writes `processed/`. Each script refuses to
run if its input is not the expected file, and it logs each change with its reason.

- **Why:** the composite's credibility is the credibility of its parts, so a reader must be able to see exactly what
  changed in each part.

### 3. Fix gaps upstream, not here

When an engine could not do what the design needed, the fix went into that engine's own repository, with tests, as a
release. The workspace does not carry a local copy or a wrapper around it.

- **viva-tellurium 0.2.3** adds `parameters_in`, so another layer can set a parameter such as `TNF_R` during a run.
- **viva-pde-particle** adds `RegionMean` and `RegionTotal`, which reduce a field to one concentration at the cell
  (open as viva-pde-particle#70, awaiting review).

### 4. Every claim has a check that can fail

Each layer and each coupling has a check: a compose-api compliance case with an oracle independent of the code under
test, and a mutated copy proven to fail. See {doc}`../verification/index`.

### 5. Run as compose-api runs it

The checks run through compose-api's own runner and scorer, in an environment pinned to compose-api's production
mash-up: every simulator package is at the commit compose-api's registry pins. So a document that passes here runs on
the service without a new registry entry, as a mash-up compose-api infers from the document's processes (viva-maboss,
viva-tellurium, viva-pde-particle and viva-basic-processes). The one exception ahead: the spatial → kinetic coupling needs
`RegionMean`, still in review (viva-pde-particle#70), so viva-pde-particle's pin must move once it is merged.

## Why this workspace exists

The compose-api project is onboarding simulators from several modelling frameworks, in sections. Section A
registered seven simulator packages across five modelling frameworks, and all seven passed live on compose-api 0.7.78.
Section B, this workspace, is the first model that combines several of them. See {doc}`../reference/history`.
