# Roadmap and status

The plan's phases (each atomic and independently checked), as of 2026-11-04:

| Phase | What | Status |
|---|---|---|
| U1 | viva-tellurium `parameters_in` | **released** v0.2.3 (#37, 846f87c, on PyPI) |
| U2 | viva-pde-particle `RegionMean` / `RegionTotal` | open as #70, awaiting review |
| 3 | Standalone baselines: kinetic, Boolean and spatial each against an oracle | **done**, except the d1 dose–response (in progress) |
| 4 | Pairwise couplings: kinetic → Boolean **done**; spatial → kinetic next (needs U1 in the pinned environment) | partial |
| 5 | The full composite: all-finest run first, then at d7 intervals; accepted only on d7 step 5's criteria | not started |
| 6 | A live run on compose-api as an inferred mash-up | after Alex's go |
| compose-api | Pin bumps (viva-tellurium 0.2.3, then viva-pde-particle) with a `TelluriumProcess` compliance case | one compose-api release at a time |

## Later

- **v2 spatial:** the nuclear envelope as a membrane flux between regions sized 1 : $K_v$ ({doc}`spatial`).
- **Particles:** `SmoldynHybrid` near the cell surface, judged against the PDE-only result.
- **Many cells:** one TNF field feeding N cells, each with its own kinetic and Boolean stack. Schliemann 2011 studies
  this kind of heterogeneity.
- **Fate feedback:** the candidate Boolean → kinetic edge, once it has a cited biological basis.
- **A runtime receptor layer:** NFSim, after its upstream fixes ({doc}`rule-based`).
