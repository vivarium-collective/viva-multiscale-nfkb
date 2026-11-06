# The spatial layer <span class="layer spatial">spatial</span>

## Decisions

| Decision | Reason | Evidence |
|---|---|---|
| **viva-pde-particle is the spatial engine** | The candidates were the vivarium-collective wrappers of three spatial simulators. viva-smoldyn (particle simulation) takes no inputs (`inputs()` is `{}`), has no compartments, and reports global counts. viva-fenics (finite elements) meshes only the unit square. viva-pde-particle is `tested` on compose-api and has a finite-volume solver for a partial differential equation (PDE; here the diffusion equation,
{doc}`../math/diffusion`), a hybrid that hands regions to Smoldyn's particle simulation, and adapters that transfer values between a field and other layers. | `docs/design/plan-section-b.md` (spatial layer) |
| **v1 is the extracellular TNF field** (Alex) | viva-pde-particle supports one domain with reflecting walls. It has no flux between regions, so it cannot yet model the nuclear envelope. A field around the cell is what it can do today. | viva-pde-particle@7043882 `fv_reaction_diffusion.py` |
| **PDE only first; particles later** | `FVReactionDiffusion` is deterministic and backward-Euler implicit, so diffusion is unconditionally stable and it has closed-form oracles. `SmoldynHybrid` adds sampling noise and a splitting error (the error from advancing the field and the particles in
alternating steps rather than together). The headline question needs only the mean field at the cell. Particles matter only if low copy numbers at the membrane change fate, and they will be judged against the PDE-only result. | `checks/spatial/*` |
| **A bolus, not a sustained source** | `FVReactionDiffusion`'s reaction terms take one scalar rate over the whole domain, so a localised source can't be expressed. An initial bolus is an initial condition of the `fields` store, and it has an exact solution. | viva_pde_particle `kinetics.py`; `checks/spatial/gaussian-diffusion` |
| **`RegionMean` and `RegionTotal`, new upstream** (in review) | There was no adapter from a field to one concentration at the cell. They are weighted by each node's control volume, as the FV engine conserves it. | viva-pde-particle#70; 9 tests, including a composite conserving mass to rel 1e-12 |
| **Ownership** | The spatial layer owns TNF transport (diffusion, decay); the kinetic layer only reads TNF at the cell. | {doc}`architecture` |

## Resolution

`checks/spatial/gaussian-diffusion` measures how the scheme's error in a front's tail converges. At $r = 40\ \mu\text{m}$,
$t = 1\ \text{s}$:

| dx | dt | error |
|---|---|---|
| 2 µm | 0.01 s | +1.15% |
| 1 µm | 0.0025 s | +0.29% |

The studies choose their grid from this table, with the TNF value at the cell in mind, and confirm the choice with one
refinement run.

## Checks

- **`checks/spatial/gaussian-diffusion`:** a 2D Gaussian TNF field (σ₀ 10 µm, $D = 50\ \mu\text{m}^2/\text{s}$) in a
  reflecting 200 × 200 µm box matches $\sigma^2 = \sigma_0^2 + 2Dt$ at the centre and at 20 and 40 µm. It's checked
  every second to 10 s, rel 1e-2.
- **`checks/spatial/uniform-bath-decay`:** a uniform 0.5 µM bath with decay rate $\lambda = 0.01\ \text{s}^{-1}$ stays uniform
  and follows $0.5\,e^{-\lambda t}$, rel 1e-5.

## v2: the nuclear envelope

Matching the spatial layer to the kinetic compartments needs a feature viva-pde-particle lacks: two regions with a
membrane flux. v2 would carry Lipniacki's four transport fluxes ($i_1$, $i_{1a}$, $e_{1a}$, $e_{2a}$) between regions
sized 1 : $K_v$. The two layers would advance in alternating steps (an operator split): at each coupling step the spatial layer
would start from the kinetic model's current concentrations and return only the change that transport caused. VCell (the Virtual
Cell, a modelling and simulation platform for cell biology) already models compartments with membrane fluxes, and viva-pde-particle builds on the VCell software stack (it reads
VCell models through `pyvcell`, VCell's Python library, and its finite-volume scheme mirrors VCell's solver), so v2 extends that rather than
inventing one. Scoped in
[`docs/design/task-plan-membrane-flux.md`](https://github.com/vivarium-collective/viva-multiscale-nfkb/blob/main/docs/design/task-plan-membrane-flux.md).
