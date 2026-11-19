# The spatial layer <span class="layer spatial">spatial</span>

## Decisions

| Decision | Reason | Evidence |
|---|---|---|
| **viva-pde-particle is the spatial engine** | The candidates were the vivarium-collective wrappers of three spatial simulators. viva-smoldyn (particle simulation) takes no inputs (`inputs()` is `{}`), has no compartments, and reports global counts. viva-fenics (finite elements) meshes only the unit square. viva-pde-particle is `tested` on compose-api and has a finite-volume solver for a partial differential equation (PDE; here the diffusion equation, {doc}`../math/diffusion`), a hybrid that hands regions to Smoldyn's particle simulation, and adapters that transfer values between a field and other layers. | `docs/design/plan-section-b.md` (spatial layer) |
| **v1 is the extracellular TNF field** (Alex) | viva-pde-particle supports one domain with reflecting walls. It has no flux between regions, so it cannot yet model the nuclear envelope. A field around the cell is what it can do today. | viva-pde-particle@7043882 `fv_reaction_diffusion.py` |
| **PDE only first; particles later** | `FVReactionDiffusion` is deterministic and backward-Euler implicit, so diffusion is unconditionally stable and it has closed-form oracles. `SmoldynHybrid` adds sampling noise and a splitting error (the error from advancing the field and the particles in alternating steps rather than together). The headline question needs only the mean field at the cell. Particles matter only if low copy numbers at the membrane change fate, and they will be judged against the PDE-only result. | `checks/spatial/*` |
| **A bolus for the studies; a local source or local uptake can also be expressed** (decision 8b) | A bolus is an initial condition of the `fields` store, it has an exact solution, and it is the moving front whose arrival the exposure studies time (decision 39). A reaction term is mass action over any species, and `external_conc` species are arrays over the grid, so a mask makes a term local: a sustained source, the exposure geometry's absorbing band, or uptake by a cell | viva_pde_particle `kinetics.py`; `checks/spatial/gaussian-diffusion`; `checks/spatial/local-source` |
| **`RegionMean` and `RegionTotal`, new upstream** (merged 2026-11-09 as 25e8a05; compose-api pins it from 0.7.90) | There was no adapter from a field to one concentration at the cell. They are weighted by each grid point's control volume, as the FV engine conserves it. | viva-pde-particle#70; 9 tests, including a composite conserving mass to rel 1e-12; compose-api's `region-mean-closed-form` case |
| **Ownership** | The spatial layer owns TNF transport (diffusion, decay); the kinetic layer only reads TNF at the cell. | {doc}`architecture` |
| **The MVP's field** (decision 33). 2-D, a reflecting box 200 µm wide, $D = 100\ \mu\text{m}^2/\text{s}$. The cell is a disk of radius 9 µm at the centre, and its surface is the ring of grid nodes just outside it ($9 \le r < 11$ µm). A Gaussian bolus (σ₀ 5 µm) starts 40 µm away, scaled so the well-mixed level is 10 $K_d$ | 2-D is the only verified setup. $D$ is the measured value (Wu et al. 2011). The radius is BioNumbers 108905 (NIH/3T3, 18 µm across). The cell samples the field and is not an obstacle, as v1 has one domain. At the cell, TNF peaks at 29 $K_d$ after 4 s and settles at 10 $K_d$. | `checks/spatial/region-mean-bolus` |

## Resolution

`checks/spatial/gaussian-diffusion` measures how the scheme's error in a front's tail converges. At $r = 40\ \mu\text{m}$,
$t = 1\ \text{s}$:

| dx | dt | error |
|---|---|---|
| 2 µm | 0.01 s | +1.15% |
| 1 µm | 0.0025 s | +0.29% |

The studies choose their grid from this table, with the TNF value at the cell in mind, and confirm the choice with one
refinement run.

The MVP's field was chosen this way, on the TNF at the cell against the exact solution (decision 34). Its error is
first order in dt and does not depend on dx: dx 2 µm and dx 1 µm agree to 5%. At dx 2 µm:

| dt | 2 s (front) | 4 s (peak) | 10 s | 30 s (first coupling sample) | 60 s |
|---|---|---|---|---|---|
| 0.1 s | −3.2% | −0.88% | +0.32% | +0.20% | +2.1e-4 |
| 0.05 s (chosen) | −1.7% | −0.45% | +0.17% | +0.10% | +1.1e-4 |
| 0.025 s | −0.90% | −0.24% | +0.09% | +0.06% | +6.3e-5 |

A 990 s run of the field takes 8 s.

## Checks

- **`checks/spatial/gaussian-diffusion`:** a 2D Gaussian TNF field (σ₀ 10 µm, $D = 50\ \mu\text{m}^2/\text{s}$) in a
  reflecting 200 × 200 µm box matches $\sigma^2 = \sigma_0^2 + 2Dt$ at the centre and at 20 and 40 µm. It's checked
  every second to 10 s, rel 1e-2.
- **`checks/spatial/uniform-bath-decay`:** a uniform 0.5 µM bath with decay rate $\lambda = 0.01\ \text{s}^{-1}$ stays uniform
  and follows $0.5\,e^{-\lambda t}$, rel 1e-5.
- **`checks/spatial/region-mean-bolus`:** the full composite's own field and surface, read from
  `tnf_field_cell.composite.json`, against the exact solution in a reflecting box. That solution is the free Gaussian
  plus its mirror images in the walls, averaged over the ring's nodes with numpy rather than RegionMean. The generator
  first asserts the composite's ring, D and bolus. It is checked at 2, 4, 10, 30 and 60 s, with tolerances three
  times the measured error. At 990 s the field is uniform, and the ring reads the box's mean to rel 1e-9, because
  mass is conserved. Two mutated copies fail (`--negative D50`, `--negative ring15`).
- **`checks/spatial/local-source`:** a TNF source confined to a 3 × 3-node patch by an `external_conc` mask, with
  decay, run through a full Composite. The field's total mass from `RegionTotal` equals the scheme's exact
  $(sA/\lambda)(1 - (1 - \lambda\,dt)^n)$ every 10 s to 60 s, rel 1e-9. An ignored mask would give about 1,000 times
  more. Two mutated copies fail: an unseeded mask and an unwired one, both silently zero.
- **`checks/coupled/bolus-occupancy`** (from the same generator): in the full composite with its bolus, the cell's
  occupancy every 15 s is $c/(c+K_d)$ of the exact TNF at the last coupling instant. This guards the rule that the
  dose–response Step re-runs on each kinetic update (`--negative untriggered` fails).

## v2: the nuclear envelope

Matching the spatial layer to the kinetic compartments needs a feature viva-pde-particle lacks: two regions with a
membrane flux. v2 would carry Lipniacki's four transport fluxes ($i_1$, $i_{1a}$, $e_{1a}$, $e_{2a}$) between regions
sized 1 : $K_v$. The two layers would advance in alternating steps (an operator split): at each coupling step the spatial layer
would start from the kinetic model's current concentrations and return only the change that transport caused. VCell (the Virtual
Cell, a modelling and simulation platform for cell biology) already models compartments with membrane fluxes, and viva-pde-particle builds on the VCell software stack (it reads
VCell models through `pyvcell`, VCell's Python library, and its finite-volume scheme mirrors VCell's solver), so v2 extends that rather than
inventing one. Scoped in
[`docs/design/task-plan-membrane-flux.md`](https://github.com/vivarium-collective/viva-multiscale-nfkb/blob/main/docs/design/task-plan-membrane-flux.md).
