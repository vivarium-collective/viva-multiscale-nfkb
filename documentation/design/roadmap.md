# Roadmap and status

The plan's phases (each atomic and independently checked), as of 2026-11-06. Phases 1 and 2 are the two upstream
changes, U1 and U2:

| Phase | What | Status |
|---|---|---|
| U1 | viva-tellurium `parameters_in` | **released** v0.2.3 (#37, 846f87c, on PyPI) |
| U2 | viva-pde-particle `RegionMean` / `RegionTotal` | open as #70, awaiting review |
| 3 | Standalone baselines: kinetic, Boolean and spatial each against an oracle | **done**, except the d1 dose–response (in progress) |
| 4 | Pairwise couplings: kinetic → Boolean **done**; spatial → kinetic next (U1 is in the pinned environment; it also needs U2's `RegionMean`) | partial |
| 5 | The full composite: a run with the finest intervals first, then at intervals chosen by the rule in {doc}`../math/timescales`; accepted only on that page's test | not started |
| 6 | A live run on compose-api as an inferred mash-up | after Alex's go |
| Study 0 | Calibration of the coupling ({doc}`calibration`): κ decided; under held, saturating TNF nearly every cell dies; protein persistence saves cells only well beyond the measured turnover | **done** |
| Decision 28 | Absorbing death in the network ({doc}`boolean`) | **done** |
| Validation study | Why the coupled model kills nearly every cell under held TNF when cells with working NF-κB survive it (decision 29) | **next** |
| d1 | TNF's dose–response at the receptor (McMillan 2021; decision 27) | after the validation study |
| compose-api | Pin bumps: viva-tellurium 0.2.3 **done** (compose-api 0.7.79, #502); viva-pde-particle after U2 merges | one compose-api release at a time |

## Open questions

These are unresolved, and each is stated where it is used:
- **Is receptor binding fast enough to use its equilibrium (d1)?** It relaxes within about 100 s, against NF-κB's 337 s
  half-rise: a factor of about 3 ({doc}`rule-based`). To be checked when d1 is built.
- **How fast should the fate network's TNF node flip?** Its rates are the occupancy scaled by `k_time`, so it follows
  the death clock, while the NF-κB node's speed is deliberately independent of it ({doc}`coupling`). No page argues
  this choice yet.
- **How is the cell represented on the spatial grid?** Its size, its position, and which grid cells count as its
  surface ({doc}`coupling`, `RegionMean`) are not yet specified.
- **Why a 2D grid?** Not yet argued ({doc}`../math/diffusion`).
- **What counts as "collapses onto the dose curve"** in the headline studies' test: the statistic and threshold are to
  be fixed before study 1 runs ({doc}`studies`).
- **Measured values still to be cited:** TNF's diffusion coefficient ({doc}`../science/scales`), and how fast and how
  often TNF kills cells in experiments ({doc}`time`).

## Later

- **The full composite's slow modes from simulated trajectories,** where no equations are available (Noé & Nüske
  2013; the timescale analysis's planned second use).

- **v2 spatial:** the nuclear envelope as a membrane flux between regions sized 1 : $K_v$ ({doc}`spatial`).
- **Particles:** `SmoldynHybrid` near the cell surface, judged against the PDE-only result.
- **Many cells:** one TNF field feeding N cells, each with its own kinetic and Boolean stack. Schliemann 2011 studies
  this kind of heterogeneity.
- **Fate feedback:** the candidate Boolean → kinetic edge, once it has a cited biological basis.
- **A runtime receptor layer:** NFSim, after its upstream fixes ({doc}`rule-based`).
