# Roadmap and status

The plan's phases (each atomic and independently checked), as of 2026-11-18. Phases 1 and 2 are the two upstream
changes, U1 and U2:

| Phase | What | Status |
|---|---|---|
| U1 | viva-tellurium `parameters_in` | **released** v0.2.3 (#37, 846f87c, on PyPI) |
| U2 | viva-pde-particle `RegionMean` / `RegionTotal` | **merged** (#70, 25e8a05, 2026-11-09); pinned here and in compose-api 0.7.90 (#540) |
| 3 | Standalone baselines: kinetic, Boolean and spatial each against an oracle | **done**; the d1 dose–response in its first form, one-site occupancy (decision 32) |
| 4 | Pairwise couplings: kinetic → Boolean **done**; spatial → cell **done**, inside the full composite (`coupled/field-ablation`, `spatial/region-mean-bolus`) | **done** |
| 5 | The full composite: a run with the finest intervals first, then at intervals chosen by the rule in {doc}`../math/timescales`; accepted only on that page's test | **the MVP is built** (`tnf_field_cell.composite.json`, decisions 31–36) at the checked intervals; the interval rule's test is not yet run |
| 6 | A live run on compose-api as an inferred mash-up, dispatched from the workbench | **done** on compose-api 0.7.90: simulation 12516 from the command line built the mash-up (mash-bb433b1002, version 1), and 12524 from the workbench ran in it. The two are identical on all 991 rows. Against a local run of the same document, the TNF at the cell, the occupancy and NF-κB's nuclear fraction agree within a relative 10⁻⁹ (`compose/live/tnf_field_cell.yaml`, from `compose/live.py`). The fate network's probabilities differ: the live runs used viva-maboss 0.1.1 on Linux and the local run 0.1.2 on macOS, and the two versions draw a cell's sampled state in different orders, so they differ even on one machine (viva-maboss#1). A rerun checks whether 0.1.2 gives the same trajectory on Linux and macOS, once the mash-up has a version with 0.1.2 |
| Study 0 | Calibration of the coupling ({doc}`calibration`): κ decided; under held, saturating TNF nearly every cell dies; protein persistence saves cells only well beyond the measured turnover | **done** |
| Decision 28 | Absorbing death in the network ({doc}`boolean`) | **done** |
| Study 1, validation | Can NF-κB protect cells in the composite? ({doc}`validation`, decision 29) | **done**: no clock meets the standard with held survival; the limit is the activation race in Calzone's network. Option A (decision 30) then removed that race's handicap, and the standard still fails: intact cells that reach Survival lose it, as built and anchored |
| Decision 30 | NF-κB's activation route on Lipniacki's clock ("Option A"; {doc}`boolean`) | **tested**, not adopted: no clock meets the criterion fixed before the run; intact cells reach Survival but many lose it (read from the rules: Survival follows NF-κB's cycling node), and knocked-out cells die more, mostly by necrosis ({doc}`validation`) |
| d1 | TNF's dose–response at the receptor (decision 27) | first form **built**: one-site occupancy, $K_d$ 19 pM (decision 32); McMillan 2021's fit is the refinement |
| compose-api | Pin bumps: viva-tellurium 0.2.3 **done** (compose-api 0.7.79, #502); viva-pde-particle 25e8a05 **done** in 0.7.90 (#540); viva-maboss 0.1.2 **done** in 0.7.91 (#541) | one compose-api release at a time |

## Open questions

These are unresolved, and each is stated where it is used:
- **What stands between the composite and the survival standard?** Under held TNF, no death clock meets it
  ({doc}`validation`). NF-κB's net protection is at most 12.5 points (percent of cells) as built, and at most 35.5 with
  NF-κB's activation route on Lipniacki's clock (decision 30, "Option A"), which the composite did not adopt. Either
  way, intact cells reach Survival and many lose it again. Read from the rules, and not yet tested, Survival follows
  NF-κB's node, which under held TNF is on only about 28% of the time. With the route anchored, knocked-out cells also
  die more, mostly by necrosis, so the standard's knocked-out half is met partly through a death route anchoring
  opened. How Survival should read a cycling NF-κB node, and the necrosis route's timing, are decisions for Alex;
  nothing is tuned without him.
- **Is receptor binding fast enough to use its equilibrium (d1)?** It relaxes within about 100 s, against NF-κB's 337 s
  half-rise: a factor of about 3 ({doc}`rule-based`). The first form assumes it (decision 32); McMillan 2021's fit
  is where to check it.
- **How fast should the fate network's TNF node flip?** Its rates are occ (the receptor-engagement fraction) scaled by `k_time`, so it follows
  the death clock, while the NF-κB node's speed is deliberately independent of it ({doc}`coupling`). No page argues
  this choice yet.
- **How is the cell represented on the spatial grid?** The MVP's answer (decision 33): a disk of radius 9 µm, its
  surface the ring of grid nodes just outside it, sampling the field without excluding volume. The headline studies
  may need it to exclude volume or to sit off-centre.
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
