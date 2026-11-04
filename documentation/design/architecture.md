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
│ TelluriumProcess:       │   │ MaBoSSProcess: reduced Calzone  │
│ Lipniacki 2004          │   │ (27 nodes)                      │
└───────┬─────────────────┘   └───────────────▲─────────────────┘
        │ five NF-κB species                    │ u_NFkB = f, d_NFkB = 1 − f
        └── nuclear fraction f (adapter) ───────┘
```

## Design principles

### 1. One owner per quantity

Every quantity is written by exactly one layer. Other layers read it, and an adapter translates it in between.

- **Why:** two layers that both model the same biology (say, NF-κB activation) give two answers, and the composite
  has no way to say which is right. One owner removes the question.
- **How it shows up:**
  - The spatial layer owns TNF transport, and the kinetic layer only reads TNF at the cell.
  - Lipniacki owns NF-κB activation, so the Boolean network's duplicate of it is removed ({doc}`boolean`).
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
mash-up. A document that passes here runs on the service without a new registry entry, as an inferred mash-up of
viva-maboss, viva-tellurium, viva-pde-particle and viva-basic-processes.

## Why this workspace exists

This workspace is section B of compose-api's multi-framework onboarding. Section A registered seven simulator packages
across five modelling frameworks, and all seven passed live on compose-api 0.7.78. This workspace is the first model
that combines several of them. See {doc}`../reference/history`.
