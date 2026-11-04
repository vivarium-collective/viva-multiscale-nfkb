# Task plan: v2 spatial layer, nuclear-envelope membrane flux (scoping only)

Written 2026-11-04. This is a plan only: nothing is built, branched, committed or submitted. An independent adversarial
review of the draft found 1 blocker, 6 defects and 5 nits. I checked each against its source, and this version
corrects them (the review notes are marked R1-R12).

## Context

v1 (`~/.claude/plans/linked-jingling-wirth.md`) couples:
- Lipniacki 2004 (BIOMD0000000786) on `TelluriumProcess`;
- a reduced Calzone 2010 network on `MaBoSSProcess`;
- an extracellular TNF field on viva-pde-particle.

It deferred a spatial layer matched to the kinetic compartments, because viva-pde-particle has no flux between
regions. v2 adds:
- **an upstream membrane-flux feature in viva-pde-particle:** cytosol and nucleus regions, with a nuclear envelope
  between them;
- **an operator split:** Tellurium owns every reaction, and the spatial layer owns all four Lipniacki transport fluxes,
  at a nucleus:cytosol volume ratio of 1:Kv.

The design must not repeat v1's review defect, in which two engines evolve the same species, giving two sources of
truth and losing mass.

## Verified facts

Each fact below was read or run on 2026-11-04.
- A **probe** is something I ran myself, with `uv run --no-project`, installing nothing into any repo.
- **R-probe** marks a probe the reviewer ran.

### Lipniacki transport (libSBML on the BioModels file)
Each of the four transport parameters drives a **pair** of reactions, a sink and a source, so there are 8 reactions:

| Parameter | k (1/s) | Sink | Source |
|---|---|---|---|
| `i1` (NF-κB in) | 0.0025 | `NFKB_export` = `Cytosol·i1·NFKB` | `NFKBc_induced_NFKBn_production` = `i1·Kv·NFKB` |
| `i1a` (IκB in) | 0.001 | `IkB_export` = `Cytosol·i1a·IkB` | `IkBc_induced_IkBn_production` = `i1a·Kv·IkB` |
| `e1a` (IκB out) | 0.0005 | `IkBnuc_export` = `Nucleus·e1a·Kv·IkB_nuc` | `IkBn_induced_IkBc_production` = `e1a·IkB_nuc` |
| `e2a` (complex out) | 0.01 | `IkB_NFKB_n_export` = `Nucleus·e2a·Kv·IkB_NFKB_nuc` | `IkB_NFKB_n_induced_IkB_NFKBc_production` = `e2a·IkB_NFKB_nuc` |

- **Each k is per cytosolic volume.** The cytosol side changes at `k·c`, and the nucleus side at `Kv·k·c`.
- **The four parameters appear in no other reaction.** `Kv` appears only in these transport kinetics.
- **Free nuclear NF-κB has no export reaction.**
- **Volumes:** `Kv` = 5, and `Cytosol` = `Nucleus` = 1.
- **The `NFKB_total` rule divides by `ModelValue_1`, not by `Kv`.** `ModelValue_1` ("Initial for Kv") is set from
  `Kv` by an initial assignment at load. So overriding `Kv` alone leaves it at 5 (R-probe).
- **Size:** 16 species, 32 reactions and 1 event.
- **Units and stimulus:** time is in seconds. `TNF := TNF_R`, and the event sets `TNF_R = 1` at t > 363600 s.

### Kinetic side today (viva-tellurium @ 967d5dd, `viva_tellurium/processes.py`)
- **`coupled_species: true`** (lines 454-510) is an operator-split mode. Each update:
  1. re-syncs from the shared store;
  2. integrates the process's own reactions;
  3. emits `after − baseline` as an **additive** delta.

  With `bulk_species: false`, the port is `map[float]`. The docstring gives the contract as
  `x_{n+1} = x_n + Σ_i (x_i − x_n)`.
- **`parameter_overrides`** is applied at build (lines 300-304) and again after `reset_on_init` (lines 335-341).
- **`tests/test_coupled_bulk.py` switches reaction subsets off with it.** Arm A sets `k2 = k3 = 0`, and arm B sets
  `k1 = 0`.
- **Probe:** with `i1 = i1a = e1a = e2a = 0` set through `rr[pid]`, all 8 transport rates are exactly 0
  (libroadrunner 2.11.0).
- **`_build` resets roadrunner (R1).** Model time therefore starts at 0, and the event fires about 101 h into any run.
- U1 (`parameter_inputs`) is not on viva-tellurium main (66a940d, v0.2.2).

### process-bigraph 1.9.1 (compose-api `.venv`, `composite.py`)
- A process reads its inputs when it becomes due, and its delta is applied at the end of its interval (`run`, line 2659).
- All updates due at one time are applied together, and Steps run after them (`_run_inner`).
- **Probe:** two processes writing additive deltas to one `map[float]` store sum correctly, even when one writes only
  some of the keys.

### Prior art in the VCell stack, which viva-pde-particle mirrors

**vcell-fvsolver v0.11.1** (b28f2db). viva-pde-particle's `pixi.toml` requires `pyvcell-fvsolver >= 0.11.1`; that is a
floor, not a pin.
- **Membranes are first-class.** The solver has `Membrane`, `MembraneVariable` and `JumpCondition`
  (`VCell/include/VCELL/JumpCondition.h`).
- **Input format** (`FVSolver.cpp:568-614`):
  - a jump condition is written as `JUMP_CONDITION_BEGIN <var>`, then one `FLUX <feature> <expr>` line per feature,
    then `JUMP_CONDITION_END`;
  - the worked example is a nucleus/cytosol membrane with equal and opposite fluxes: `FLUX Nucleus (150*(Ca_Cytosol_membrane − Ca_Nucleus_membrane))`, then `FLUX Cytosol −(…)`.
- **Discretization** (`SparseVolumeEqnBuilder.cpp`):
  - membrane neighbours are masked out of the diffusion stencil (about lines 237-244);
  - the flux enters the right-hand side **explicitly**, as `b += flux · me->area · Δt / VOLUME` (lines 692-717);
  - a volume variable has one array over the mesh, with one context per feature.

**pyvcell 0.4.2** (8413fe5). The manifest pins pyvcell **0.5.2**, which also has `class MembraneSubDomain` at
`pyvcell/vcml/models_math.py:223` (re-checked 2026-11-04). Use 0.5.2's line numbers when implementing:
- `models_math.py:143-251` defines `MembraneSubDomain(inside_compartment, outside_compartment,
  jump_conditions=[JumpCondition(name, in_flux, out_flux)])`.
- The writer emits `Membrane` compartments, `FluxStep` reactions and `MembraneMapping` (`vcml_writer.py:119-206`).

**The gap is in viva-pde-particle (@ 7043882), not in VCell:**
- `FVReactionDiffusion` takes one boolean `domain.mask`.
- `CartesianGrid.diffusion_matrix(mask)` keeps a face only if both its nodes are in the mask (`grid.py:152-195`), so
  every region boundary has zero flux.
- `model/sbml.py:from_sbml` raises `NotImplementedError` for species in more than one compartment.
- `geometry/vcell_fv.py` already reads VCell's per-node region map for several subvolumes, but not its smoothed
  membrane areas.
- `pyvcell_fvsolver.solve()` runs to completion (`docs/DESIGN.md` §4), so native VCell can serve as a **reference**,
  not as a composable engine.

**Smoldyn** (the virtualcell/Smoldyn `pyhybrid` submodule @ e86d552):
- A partially permeable surface is one `rate <species> fsoln bsoln <κ>` statement per direction. Molecules that are
  not transmitted reflect (`SmoldynManual.tex`, the surface `action`/`rate` statements).
- The manual gives κ as length/time for adsorption. **Unverified:** the same unit for transmission. Andrews 2009,
  *Phys. Biol.* 6:046015, is cited from memory.
- The fork changes `smolsurface.c` only in how it parses `rate` (an extra index passed to `surfsetrate`).
- viva-pde-particle's writer (`model/smoldyn_config.py`) emits only `action both all reflect` walls.

### viva-pde-particle internals the design relies on (@ 7043882)
- **Component contract** (`docs/DESIGN.md` §13):
  - units are µm, s and µM;
  - processes read at the start of their interval and publish at the end;
  - engines know nothing of each other;
  - schedulers resolve their children by address.
- **The FV matrix** is `diag(s) + D·dt·K`, factorized once per species with SuperLU (`fv_reaction_diffusion.py:76`),
  so a nonsymmetric matrix is supported.
- **Steps per update:** the engine takes `max(1, round(interval/dt))` steps (`fv_reaction_diffusion.py:109`).
- **`SplittingCoordinator`** (`processes/splitting.py`):
  - hard-codes the `pde` and `particles` roles;
  - its `jacobi` is VCell's lagged scheme;
  - it merges every child output as an **overwrite** (line 124).
- **Releases:** the repo has **no tags or releases**, and its version is `0.0.0`.
- **compose-api** pins it by commit: level `tested`, image `viva-pde-particle@3`, compliance case
  `fokker-planck-ensemble`.

### compose-api constraints
- **Production minimum level:** `HPC_MINIMUM_LEVEL = TESTED` (`registry/manifest.py:43`).
- **Merging to main deploys** (Flux).
- **viva-tellurium is not in `registry_env`** (`environments.yaml:37-45`). The split runs as a
  {viva-pde-particle, viva-tellurium} mash-up.

### Probes that size the design

**Discretization** (numpy, nodes assigned by centre). The geometry is a sphere of radius 3 µm inside one of radius
6^(1/3)·3 µm:

| dx (µm) | Kv_h = V_cyt,h / V_nuc,h | staircase area / sphere area |
|---|---|---|
| 0.5 | 5.014 | 1.499 |
| 0.25 | 5.013 | 1.502 |
| 0.125 | 4.999 | 1.500 |

A permeability calibrated on the analytic area would make transport 50% too fast.

**Splitting error on Lipniacki itself.**
- The kinetic arm is roadrunner with transport switched off. The transport arm is the exact well-mixed `expm`, which is
  the large-D limit of the spatial arm.
- Both start from t = 360000 s and run for 3 h past the event.
- The metric is the maximum `NFKB_nuc` error, relative to its peak, against the monolithic model:

| τ (s) | Jacobi (additive) | Lie | Strang |
|---|---|---|---|
| 1 | 9.8e-4 | | |
| 10 | 9.8e-3 | 1.0e-2 | 4.9e-4 |
| 60 | 7.4e-2 | 6.2e-2 | 1.1e-2 |
| 300 | 4.6e-1, **goes negative (−1.4e-4)** | 5.4e-1 | 3.1e-1 |

**Kinetic timescales.** The fastest Jacobian eigenvalue of the transport-free model is −0.10/s in my probe and −0.16/s
in the R-probe, depending on the state. So d7's 0.1× rule gives τ ≈ 0.6-1 s. That bound binds before transport does
(R8).

**Conservation (R-probe).** With CVODE re-synced every 1 s over 4 h, both NF-κB pools are conserved to 1.3e-10.

## Design

### 1. Upstream: regions and membranes in `FVReactionDiffusion`

**What it mirrors.** It mirrors VCell's model: one array per species over the whole grid, membrane faces removed from
the diffusion stencil, and a jump-condition flux across each membrane face. It differs in one way: the flux is put
into the matrix, so it is treated **implicitly** (D3).

**Config.** Absent keys mean today's behaviour.

```yaml
domain:
  mask: ...            # unchanged; still allowed alone
  regions:             # new: grid-shaped int labels, -1 = outside (frozen, as outside the mask today)
    labels: <array>
    names: [cytosol, nucleus]
membranes:             # new; between two named regions
  - name: nuclear_envelope
    inside: nucleus
    outside: cytosol
    permeability:      # µm/s; flux into `inside` per area J = P_in·c_out − P_out·c_in  (µM·µm/s)
      NFKB:     {in: <P>, out: 0}
      IkB:      {in: <P>, out: <P>}
      IkB_NFKB: {in: 0,   out: <P>}
```

- A species that is not listed does not cross the membrane.
- D is one value per species.
- Reaction `terms` keep their current meaning. The v2 spatial arm has none.

**Class changes.**
- **`CartesianGrid`** (`grid.py`):
  - `diffusion_matrix` accepts labels and keeps a face only when both of its nodes share a label.
  - New `membrane_faces(labels, a, b)` returns the face weight `w = a_ij/dx_d`, the face fraction already used at
    lines 172-183.
  - New `region_volumes` and `membrane_area` give V_h and A_h.
- **`FVReactionDiffusion`:**
  - When membranes are configured, the per-species matrix is `diag(s) + dt·(D·K + M)`.
  - For a face of weight w between inside node i and outside node j:
    - row i gets `+w·P_out` at (i, i) and `−w·P_in` at (i, j);
    - row j gets `+w·P_in` at (j, j) and `−w·P_out` at (j, i).
  - Every column of M sums to zero, so `Σ s·V·u` is conserved (up to the LU residual).
  - The matrix is an M-matrix by strict column diagonal dominance. That gives positivity and unconditional stability.
  - **M is built only when membranes are configured**, so a document without membranes runs exactly today's code (R5).
- **A helper:** `permeability_for_rate(k, volume, area)` = `k·V/A`.

**Lipniacki mapping.**
- For all four fluxes, **P = k·V_cyt,h / A_h**. The cytosol side then changes at `k·c`, and the nucleus side at
  `k·Kv_h·c`.
- The generator reports Kv_h and refuses a geometry with |Kv_h/5 − 1| > 1%.

**The particle side (Smoldyn) is deferred** (D4). When it is taken up, it needs:
- a second surface, with one `rate s fsoln bsoln κ` per direction (the reverse rate is left unset for a one-way flux);
- region-aware binning. Today's compartment-aware binning handles one domain, and §10-11 of `docs/DESIGN.md` records
  a bias near the membrane;
- the closed-form oracle below, checked as an ensemble mean.

**Tests.** They use the real solver and no mocks, in `tests/test_membranes.py`.
1. **Closed form, one node per region** (exact; R4).
   - `dc_i/dt = (A/V_i)(P_in·c_o − P_out·c_i)`, with λ = A·(P_in/V_o + P_out/V_i).
   - Backward Euler gives `(1+λ·dt)^(−n)` to 1e-12, and the result converges at first order to `exp(−λt)` as dt
     halves.
   - At large D the same law holds only approximately; assert it to the measured spatial error, not to 1e-12.
2. **Mass conservation.** Random fields, random P (including one-way) and several D give `Σ s·V·u` constant to 1e-10
   relative (R12).
3. **P = 0 reduces to v1.** The result equals each region run as its own `domain.mask`, to 1e-13 relative. The orderings
   differ, so it is not bit-identical (R5). The existing suite and `scripts/component_regression.py` stay bit-identical,
   because M is absent there.
4. **Lipniacki at large D, on a 1D slab.** The region means match `expm` of the 2×2 transport matrix with the Lipniacki
   k and Kv_h, to the FV dt error.
5. **Staircase area guard, on a 3D sphere-in-sphere.** With A_h, the result matches the well-mixed rate at large D.
   Using the analytic area would be about 1.5× off.
6. **Optional native cross-check (gated on P3).** A planar membrane in a box, compared against VCell with the same
   flux as a `FluxStep`, both converging as dt → 0.

### 2. Operator split with Tellurium

**Model file.** Use **v1's driven variant**: the committed libSBML transform with `TNF_stimulation` removed and
`TNF := TNF_R` kept (R1).
- The stimulus is a `TNF_R` set by `parameter_overrides`.
- Pre-equilibrate with `TNF_R = 0` on **the split composite itself**, because its fixed point differs from the
  monolithic one: Kv_h, finite D, and Jacobi's O(τ) bias.
- Then restart with `TNF_R = 1` and `species_overrides` set to the recorded state.
- This needs no U1 and avoids simulating 101 h. U1 is needed only when v1's TNF field drives `TNF_R` (Phase 7).

**Ownership: one writer of record per quantity.**
- **The kinetic store.** It is a `map[float]` of compartment concentrations: Tellurium's `species`, with
  `bulk_species: false`. It is the only source of truth for those concentrations.
- **The Tellurium arm.** `coupled_species: true`, with `parameter_overrides: {i1: 0, i1a: 0, e1a: 0, e2a: 0,
  TNF_R: <0 or 1>, Kv: Kv_h, ModelValue_1: Kv_h}`.
  - It owns every reaction and emits additive reaction deltas.
  - `Kv` and `ModelValue_1` are set to Kv_h so that the `NFKB_total` diagnostic and the reference run agree (R2).
  - Do not wire `model_in`: `_reload_from_sbml` skips the overrides.
- **The spatial arm: `CompartmentCoupler`,** a new viva-pde-particle Process. It holds the FV engine as a child,
  resolved by address, as `Stepper` and `SplittingCoordinator` do.
  - It owns transport only and emits additive transport deltas on the same `species` store.
  - Its `fields` store holds each species' **shape**; the region means of that store are not authoritative.
  - **Config:**
    - `pde` (a node);
    - `compartments`: `NFKB: {cytosol: NFKB, nucleus: NFKB_nuc}`, `IkB: {cytosol: IkB, nucleus: IkB_nuc}`,
      `IkB_NFKB: {cytosol: IkB_NFKB, nucleus: IkB_NFKB_nuc}`;
    - `reseed: scale`.
  - **Ports:** inputs `species: map[float]` and `fields`; outputs `species: map[float]` (additive) and `fields`
    (overwrite).

**Re-seeding contract (each update of the spatial arm).**
1. Read the kinetic concentration c_r for each mapped species and region, and the current field u.
2. In each region, scale u so that its volume-weighted mean is c_r. If the region's mean is 0, set the region uniform.
3. Advance the engine over the interval (transport only, implicit). The coupler raises an error unless τ is a whole
   multiple of the engine's dt (R9).
4. Emit `Δ_r = mean_r(u_after) − c_r` on `species`, and `u_after` on `fields`.

**What this guarantees.**
- **Mass conservation.**
  - FV conservation gives `V_cyt,h·Δ_cyt + V_nuc,h·Δ_nuc = 0`.
  - Tellurium's deltas conserve each compartment's NF-κB pool.
  - So the coupled system conserves `c + n/Kv_h`, and `NFKB_total` (with `ModelValue_1 = Kv_h`) is constant.
- **One source of truth.** The field is re-normalized to the store every interval and never writes absolute values to
  it, so the two cannot drift apart.

**Stated approximation (R6).** Reactions are well-mixed per compartment. Scaling each species separately puts
reaction products where the existing field of that species is, not where they form. For example, NF-κB freed from
`IkB_NFKB` by IκB degradation should appear where `IkB_NFKB` is.
- So the layer resolves **diffusion-limited transport only**.
- Whether that is close enough to a fully spatial model is P3's second question (a VCell reference with the reactions
  included). Do not call the layer "matched" until that answer is in.

**Why `parameter_overrides` switches transport off (D1).**
- It exists at the pinned commit.
- It is the switch-off pattern viva-tellurium's own coupled test uses.
- One parameter per pair zeroes both halves of the pair.
- The probe verified it.

The alternatives are `parameter_inputs`, which needs U1 and could be left unwired, or extending v1's libSBML transform
to delete 8 reactions. Either works. Overrides keep one model file for the split run and the reference run.

**Scheme: Jacobi, process-bigraph's native order.**
- Both arms run at one interval τ, read the same state, and their deltas sum. That is the `coupled_species` contract,
  and it needs no new scheduler.
- Equal intervals make the read-at-start rule exact.
- Set `global_time_precision`, and call `run` with an interval of at least τ.
- Lie or Strang ordering needs U6. U6 is **not small** (R11): `SplittingCoordinator`'s roles would have to be
  generalized and additive ports merged.

**Stability and accuracy at long intervals.**
- Jacobi is first order, with about 1% error at τ = 10 s.
- It goes negative at τ = 300 s, because both arms subtract from the same start value. A negative store value then
  corrupts the next CVODE re-sync.
- The coupler raises on a negative re-seed target rather than clamping, because clamping breaks conservation. The
  R-probe found transported species ≥ 1e-5 after the stimulus, so rounding alone will not trip it.
- The condition is τ·(sum of the arms' depletion rates) ≪ 1.

**How d7 use 1 sets the intervals.**
- **Transport timescales are exact.** The transport operator is linear, so they come from the generalized eigenproblem
  `(D·K + M)v = −λ·diag(s)·v` (`scipy.sparse.linalg.eigs`). That covers the diffusion time and the envelope rates
  1/k and 1/(Kv·k). Neither arm needs eDMD; it is needed only for a Smoldyn variant.
- **Kinetic timescales** come from `getFullEigenValues` (d7 step 1), at about 0.10-0.16/s.
- **Set τ** to 0.1 × the fastest timescale, which is about 0.6-1 s, snapped to whole multiples of the base step and of
  the FV dt. Per the probe, Jacobi error at τ = 1 s is about 1e-3.
- **Accept a τ** only if it matches the all-finest run within the study tolerance, shows no oscillation, never goes
  negative, and runs faster (d7 step 5).

**Relation to v1.** v1's extracellular TNF field stays a separate FV engine on its own, larger grid, with its oracle
and U2 coupling unchanged. v2 adds the intracellular engine beside it.

## Phases (atomic; each with its verification)

**Release rule for each upstream unit:** one PR containing the fix, its regression test and the version bump; then a
tag; then a release. Check every workflow for PyPI publishing first (the release-hold rule).

| # | Unit | Depends on | Verification |
|---|---|---|---|
| 0 | **Probes P1-P6**, as scripts in the v2 workspace | none | each answers its question, and the answer is recorded |
| 1 | **U3, viva-pde-particle: regions and membranes**, plus 1D-slab and 3D generators and `permeability_for_rate` | none (independent of U1 and U2) | tests 1-5 (and 6 if P3 passes); existing suite and component regression bit-identical |
| 2 | **U4, viva-pde-particle: `CompartmentCoupler`** | U2 (reuses its region-mean helper), U3 | a real Composite with the coupler and a linear-reaction Process:<br>• with reactions off, it matches test 1;<br>• the weighted total is conserved to 1e-10;<br>• scaling keeps the shape and is exact for uniform fields;<br>• a negative target raises;<br>• a τ that is not a multiple of dt raises |
| 3 | **compose-api: one PR pinning viva-pde-particle at U4's merge** | 1, 2 | on the PR branch, before merging:<br>• build image `viva-pde-particle@4`;<br>• lock the {viva-pde-particle, viva-tellurium} mash-up;<br>• run `fokker-planck-ensemble` and the new `viva-pde-particle/nuclear-envelope-exchange` case (test 1's closed form) through `runner.py` + `compliance.evaluate`, alone and in that mash-up;<br>• merge once, still at `tested`, with the new evidence. A merged `listed` would block production (R3) |
| 4 | **compose-api case `viva-tellurium/coupled-split`**: Tellurium with transport off, plus a well-mixed transport arm, against monolithic Lipniacki | none (967d5dd suffices) | first-order convergence over two values of τ (for example, error ratio ≈ 10 from 10 s to 1 s, as in the probe). A one-arm case would be tautological (R7) |
| 5 | **Workspace (v1's `viva-multiscale-nfkb`): the split composite at large D, using the driven variant** | 3, 4 | • pre-equilibrate the split composite itself;<br>• stimulate through the override;<br>• compare against monolithic Lipniacki with `Kv = ModelValue_1 = Kv_h` (R2), within the probe's Jacobi error at the chosen τ (about 1e-3 at 1 s);<br>• `NFKB_total` constant to 1e-9;<br>• never negative |
| 6 | **Physical D and 3D geometry** | 5, P6 | d7 use 1: a timescale table, the chosen τ, and acceptance against the all-finest run; P2 and P3 answered and recorded in the study |
| 7 | **Join v1's composite** (TNF field, U1 drive, MaBoSS) | v1 U1, 6 | v1's full-composite acceptance, now with the matched layer |
| 8 | Optional: **U5**, a Smoldyn permeable envelope; **U6**, Lie or Strang in a generalized `SplittingCoordinator` | D2, D4 | U5: closed form as an ensemble mean within its confidence interval. U6: Strang error at the probe's ratio to Jacobi |
| 9 | **compose-api live run** as a mash-up | Alex's go | nothing is submitted before that |

## Risks and probes

| # | Risk or unknown | Smallest real probe |
|---|---|---|
| P1 | LU fill-in on a 3D grid of about 100k nodes, for 3 species, is too slow or too large | factorize `diag(s)+dt·(D·K+M)` at dx = 0.25 µm on the sphere-in-sphere; record time and peak RSS |
| P2 | The splitting error at **finite** D is unmeasured; the probe used the large-D limit | rerun the probe table with the spatial arm at a cited D, after U3 |
| P3 | (a) Can native VCell be the reference? That is, a pyvcell BioModel with Cytosol, Nucleus and an envelope `FluxStep` → libvcell `.fvinput` with `JUMP_CONDITION` → `pyvcell_fvsolver`. (b) How far is the well-mixed-reactions approximation (R6) from VCell running the whole model spatially? | (a) one box model in the `reference` environment; (b) the same model with Lipniacki's reactions included, comparing per-region means |
| P4 | Does the pyhybrid Smoldyn build honour `rate s fsoln bsoln κ`, and what are κ's units for transmission? | one surface and one species through `SmoldynHybrid`; compare the crossing rate with κ·c·A |
| P5 | Does compose-api's `validate_submission` inspect the coupler's nested child `address`? It resolves only through `core.link_registry`, so only registered classes can load | call `validate_submission` on the Phase 5 document |
| P6 | Diffusion coefficients for NF-κB, IκBα and IκBα:NF-κB in cytoplasm and nucleoplasm are not yet cited | `/viva-cite-bands`; record the values with their sources |
| — | Jacobi goes negative at long τ | measured (τ = 300 s); guarded by the raise and by d7 acceptance |
| — | Kv_h ≠ 5 | measured (≤ 0.3% at dx ≤ 0.5 µm); reported, gated, and `Kv`/`ModelValue_1` overridden |
| — | A pin bump changes the image that other users run | Phase 3 reruns `fokker-planck-ensemble` before merging |

## Open decisions for Alex

**D1. Switching transport off in Tellurium.**
- **Recommendation:** `parameter_overrides`. It exists now, viva-tellurium's own coupled test uses it, the probe
  verified it, and it keeps one model file for both the split and reference runs.
- **Alternatives:** extend v1's libSBML transform to delete the 8 reactions, or use `parameter_inputs`, which needs U1.

**D2. Splitting scheme.**
- **Recommendation:** native Jacobi at τ ≈ 1 s.
- Add U6 (Strang was about 20× more accurate at τ = 10 s in the probe) only if Phase 6 cannot meet its tolerance at a
  τ the run time allows.
- U6 means generalizing `SplittingCoordinator`, which is not a small change.

**D3. Implicit or VCell-explicit envelope flux.**
- **Recommendation:** implicit. It costs nothing extra in a solve that is already factorized, and it is conservative,
  positive and unconditionally stable.
- Explicit would mirror vcell-fvsolver line for line. Test 6 converges either way.

**D4. Particle-side envelope in v2.**
- **Recommendation:** defer it as U5.
- Re-seeding a stochastic arm from a deterministic store needs its own design for adding and removing molecules.

**D5. Release discipline for viva-pde-particle.**
- The repo has never been tagged, and the BOJ rules need a tag for each merged unit.
- **Recommendation:** start semver at `v0.1.0` with U3, after asking its maintainer.

**D6. What "matched compartments" must mean.**
- **Recommendation:** accept the transport-only layer (well-mixed reactions) for v2, with P3(b) quantifying the gap.
- The alternative is to hold the claim until a fully spatial reaction layer exists. That is a larger and different
  project.
