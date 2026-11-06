# Roadmap and status

The plan's phases (each atomic and independently checked), as of 2026-11-06. Phases 1 and 2 are the two upstream
changes, U1 and U2:

| Phase | What | Status |
|---|---|---|
| U1 | viva-tellurium `parameters_in` | **released** v0.2.3 (#37, 846f87c, on PyPI) |
| U2 | viva-pde-particle `RegionMean` / `RegionTotal` | open as #70, awaiting review |
| 3 | Standalone baselines: kinetic, Boolean and spatial each against an oracle | **done**, except the d1 dose–response (not started) |
| 4 | Pairwise couplings: kinetic → Boolean **done**; spatial → kinetic next (U1 is in the pinned environment; it also needs U2's `RegionMean`) | partial |
| 5 | The full composite: a run with the finest intervals first, then at intervals chosen by the rule in {doc}`../math/timescales`; accepted only on that page's test | not started |
| 6 | A live run on compose-api as an inferred mash-up | after Alex's go |
| Study 0 | Calibration of the coupling ({doc}`calibration`): κ decided; under held, saturating TNF nearly every cell dies; protein persistence saves cells only well beyond the measured turnover | **done** |
| Decision 28 | Absorbing death in the network ({doc}`boolean`) | **done** |
| Study 1, validation | Can NF-κB protect cells in the composite? ({doc}`validation`, decision 29) | **done**: no clock meets the standard with held survival; the limit is the activation race in Calzone's network |
| d1 | TNF's dose–response at the receptor (McMillan 2021; decision 27) | not started; after the decision on NF-κB's activation route (below) |
| compose-api | Pin bumps: viva-tellurium 0.2.3 **done** (compose-api 0.7.79, #502); viva-pde-particle after U2 merges | one compose-api release at a time |

## Open questions

These are unresolved, and each is stated where it is used:
- **Should NF-κB's activation route run on Lipniacki's clock?** Under held TNF, NF-κB's net protection in the composite is at most about 10 to 13
  points (percent of cells), and no death clock meets the standard with held survival ({doc}`validation`). The
  limit is the activation race in Calzone's network, between caspase-8 and NF-κB's activation route (TNFR, RIP1, RIP1ub, IKK), which runs on
  the death clock even though Lipniacki already times that activation (337 s). Anchoring it to Lipniacki, as
  $r_\text{tx}$ does for the genes, is the model-native option, to be tested as a Study 1 variant first. A decision for
  Alex before d1.
- **Is receptor binding fast enough to use its equilibrium (d1)?** It relaxes within about 100 s, against NF-κB's 337 s
  half-rise: a factor of about 3 ({doc}`rule-based`). To be checked when d1 is built.
- **How fast should the fate network's TNF node flip?** Its rates are occ (the receptor-engagement fraction) scaled by `k_time`, so it follows
  the death clock, while the NF-κB node's speed is deliberately independent of it ({doc}`coupling`). No page argues
  this choice yet.
- **How is the cell represented on the spatial grid?** Its size, its position, and which grid cells count as its
  surface ({doc}`coupling`, `RegionMean`) are not yet specified.
- **Why a 2D grid?** The tool supports 3D, so this is a choice. It sets how the peak dose falls with distance ($1/r^2$
  against $1/r^3$), and in either dimension the integrated dose needs decay or a finite window
  ({doc}`../math/diffusion`).
- **What counts as "collapses onto the dose curve"** in the headline studies' test: the statistic and threshold are to
  be fixed before the distance study runs ({doc}`studies`).
- **What value of TNF's diffusion coefficient do the spatial studies use?** The measured free-solution value is
  about 100 µm²/s ({doc}`../science/scales`); the checks use 50 as a test value. Not decided.

## Later

- **The full composite's slow modes from simulated trajectories,** where no equations are available (Noé & Nüske
  2013): the analysis of {doc}`../math/timescales`, estimated from trajectories instead of from a Jacobian.

- **v2 spatial:** the nuclear envelope as a membrane flux between regions sized 1 : $K_v$ ({doc}`spatial`).
- **Particles:** `SmoldynHybrid` near the cell surface, judged against the PDE-only result.
- **Many cells:** one TNF field feeding N cells, each with its own kinetic and Boolean stack. Schliemann 2011 studies
  this kind of heterogeneity.
- **Fate feedback:** the candidate Boolean → kinetic edge, once it has a cited biological basis.
- **A runtime receptor layer:** NFSim, after its upstream fixes ({doc}`rule-based`).
