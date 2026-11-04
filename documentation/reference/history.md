# History: why this workspace exists

This workspace is **section B** of compose-api's multi-framework onboarding (`agenda-onboarding.md`, 2026-11-03).

The agenda has three gated parts:
1. **A:** onboard the viva simulator workspaces, grouped by modelling framework.
2. **B:** design one multiscale composite from what A onboarded. That is this workspace.
3. **C:** classify each compliance case by biological scale.

**Section A.** compose-api#499 (merged 2026-11-04) registered seven packages at level `tested`, across five frameworks:

| Framework | Package |
|---|---|
| ODE/SBML | viva-copasi, viva-tellurium |
| Flux balance | viva-cobra |
| Boolean | viva-maboss, built new for this: no Boolean wrapper existed, and BoolNet is R-only |
| Rule-based | viva-nfsim |
| Spatial | viva-smoldyn, viva-fenics |

viva-biomodels was held at `listed`.

**The releases.**
- 0.7.77 (#500) released #499.
- 0.7.78 (#501) fixed environment inference for documents that use a core short name such as `local:RAMEmitter`. The
  first live run had exposed the bug.

The same day, all seven compliance cases passed on production, each in its own automatically inferred environment
(runs 9825, 9827, 9828, 9831, 9832, 9834, 9836).

**What B adds.** A proved each framework on its own. B builds one model that spans scales and engines (Boolean, ODE and
spatial PDE). It needs no new registry entry: compose-api runs it as an inferred mash-up of viva-maboss,
viva-tellurium, viva-pde-particle and viva-basic-processes.
