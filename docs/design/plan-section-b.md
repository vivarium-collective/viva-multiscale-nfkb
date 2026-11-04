# Plan: section B, the multiscale process-bigraph composite

## Context

Section B of `agenda-onboarding.md` (lines 113–191) asks for the design of one modular, multiscale composite built
from the simulators onboarded in A. Its layers are Boolean → ODE kinetic core → optional rule-based → spatial particle +
PDE. d7 (eDMD/VAC) is already scoped there. This plan does not redo d7; its timing step is d7's "use 1".

**Status (2026-11-04): in progress (GO received).** This document sits beside [`eDMD.md`](eDMD.md) (d7's source).
v2's membrane-flux plan is [`task-plan-membrane-flux.md`](task-plan-membrane-flux.md) (scoped and reviewed; decisions
D1–D6 await Alex).

**Progress:**
- **U1 is done on a local branch, and nothing is pushed.** viva-tellurium `feat/parameter-inputs` (`05731d8`,
  `e962e93`), version 0.2.3.
  - The port is named **`parameters_in`**, matching the repo's own `model_in`/`model_out`.
  - It validates the whole map before setting anything, so an unknown id, a rule-defined id, or a non-finite value
    raises.
  - 22 tests on real roadrunner. Re-run in this session: all pass, and on 0.2.2's `processes.py` 18 fail. A
    `constant="true"` parameter can be set at runtime on roadrunner 2.11.0.
- **U2 is done on a local branch, and nothing is pushed.** viva-pde-particle `feat/region-mean` (`6064b57`,
  `1e1f9d3`).
  - It adds **`RegionMean`** (outputs `mean_conc: map[overwrite[float]]`, µM) and **`RegionTotal`** (outputs
    `molecules`). Both are weighted by each node's control volume, as the FV engine conserves it.
  - `region` takes the same `{mask, volume_fraction}` as `FVReactionDiffusion`'s `domain`.
  - 9 tests, including a real composite that conserves mass to rel 1e-12. Re-run in this session: all pass.
  - The package has no version (it is pinned by commit), so nothing was bumped.
- **Workspace:** https://github.com/vivarium-collective/viva-multiscale-nfkb (public, Alex, 2026-11-04).
  - The compose-api check harness is in `compose/`. Kinetic checks `sim1-original` and `preequilibrated-steady`
    pass.
  - The Boolean layer and the d1 dose-response are with the compose-api-targeted-onboarding session, in worktree
    `feat/boolean-layer`.
- **Foreground: everything that doesn't need U1 or U2.**
  - the workspace scaffold;
  - the SBML event-removal transform and the pre-equilibration run;
  - the `sim1` baseline;
  - the `.bnd` transform and the MaBoSS check;
  - the kinetic → Boolean pair;
  - the spatial baselines;
  - the d1 dose-response.
- **compose-api pin bumps run one at a time.**

Section A was proven live on production 0.7.78: all seven compliance cases passed, each in its own inferred mash-up
(runs 9825, 9827, 9828, 9831, 9832, 9834 and 9836, as reported by the A session). Everything below was read on 2026-11-04 from primary sources:
- each wrapper at its manifest-pinned commit, via `gh api`;
- the BioModels REST API and BIOMD0000000786's SBML, parsed with libSBML;
- process-bigraph 1.9.1 in `.venv`;
- this repo.

An independent adversarial review of the first draft found 4 blockers and 9 further defects. I re-checked each blocker
against its source before changing the plan. This version is the corrected one.

Nothing here is built or submitted yet, and `agenda-onboarding.md` is frozen. When it reopens, section B gets one line
linking here.

## What the sources say (each one changes an assumption in B)

| # | Finding | Evidence |
|---|---|---|
| F1 | **Boolean library: MaBoSS** (closes B's "BoolNet vs others"; BoolNet has no wrapper). `MaBoSSProcess` applies the `parameters` and `node_state` inputs on every update, carries one sampled joint state between intervals, and outputs `map[float]` deltas. It needs a config default for every `$param`, and it writes its own `.cfg`. | viva-maboss@3fdccd7 `processes.py:9-14,133-160,179-204` |
| F2 | **The kinetic layer steps, but cannot be driven by parameters.** `TelluriumProcess` and `CopasiUTCProcess` take **species** inputs only. Tellurium's `parameters` port is an output (every global parameter, overwritten each update). Its `parameter_overrides` are applied once, at build. A `model_in` reload resets the integrator, so it is rejected. | viva-tellurium@967d5dd `processes.py:255-341`; viva-copasi@937ff13 `processes.py:842-856` |
| F3 | **Tellurium is the core's engine, not COPASI.** `CopasiUTCProcess` passes counts to `setInitialConcentration`, and its `time` does not accumulate. Tellurium is libRoadRunner, which d7 use-1 step 1 (`getFullEigenValues`) already uses. Set `bulk_species: false` (the default `true` makes `species` a 16-element array, not addressable by name). | viva-copasi `processes.py:115,831`; viva-tellurium `processes.py:116` |
| F4 | **The rule-based layer cannot do B's job.** pbg_nfsim only runs network-free simulation (`method=>"nf"`): no `generate_network`, no SBML export. | viva-nfsim@76ff7fc `processes.py:308` |
| F5 | **viva-smoldyn and viva-fenics cannot be the coupled spatial layer.** `SmoldynProcess.inputs()` is `{}`, it has no compartments, and its counts are global. viva-fenics meshes the unit square only. | viva-smoldyn@54c56a1 `processes.py:96-97`; viva-fenics `fem.py:24,31` |
| F6 | **viva-pde-particle is the spatial engine** (`tested`, composed with registry_env in 7c, run 8816): `SmoldynHybrid`, `FVReactionDiffusion`/`FenicsxReactionDiffusion`, `SplittingCoordinator`, and the `steps/transfer.py` adapters. **Limits:** one domain only. The mask is a single subdomain with zero flux at its boundary; the Smoldyn walls only reflect; and `external_conc` is a read-only reactant. **There is no flux between regions**, so no nuclear envelope. There is also no adapter from a field to a well-mixed scalar. | viva-pde-particle@7043882 `fv_reaction_diffusion.py:1-45,79-110`; `model/smoldyn_config.py:28-45,64-67`; `steps/transfer.py` |
| F7 | **Lipniacki's transport and volumes, from libSBML:**<br>• Import and export are one-way first-order fluxes over four parameters: `i1` (NF-κB in), `i1a` (IκB in), `e1a` (IκB out), `e2a` (IκB:NF-κB out). Free NF-κB has no export reaction.<br>• The rule `NFKB_total = … + NFKB_nuc/Kv` gives **Kv = V_cyt/V_nuc = 5**.<br>• `TNF` is a boundary species, set by the rule `TNF := TNF_R`. The event `TNF_stimulation` sets `TNF_R = 1` at t > 363600 s, after a roughly 101 h pre-equilibration. Time is in seconds. | BIOMD0000000786 `Lipniacki2004.xml` (reactions `NFKB_export`, `IkB_export`, `IkBnuc_export`, `IkB_NFKB_n_export`, …) |
| F8 | **Adapters fire on every tick, not on change.** A Step runs whenever an input path is touched, including by a zero delta. "Event-driven" coupling is therefore just scheduling, not change detection. `MathExpressionStep` (`tested`) maps float symbols through expressions. Wiring a float port to a map key (`["node_probabilities","NFkB"]`) is valid. | process-bigraph 1.9.1 `composite.py:2541-2563`; viva-basic-processes@9a1a624 `math_expression.py:164-165` |
| F9 | **Execution in compose-api:**<br>• One `composite.run(interval)`, so process-bigraph's chunking caveat holds when `interval_time` ≥ the largest process interval.<br>• Every address must sit under a `tested` entry, and a new pin restarts at `listed`.<br>• A run that names no environment gets a mash-up.<br>• The viva-tellurium compliance case covers `TelluriumUTCStep`, not `TelluriumProcess`. | `environments/runner.py:155-156`; `docs/plan-environment-composition.md` (safe component, D7.2–D7.4); manifest viva-tellurium evidence |

## The design (v1)

### Kinetic core: **BIOMD0000000786, Lipniacki 2004 NF-κB module**, on `TelluriumProcess` (closes d4/d5; Q1)
- **Model:** two compartments (Cytosol, Nucleus, with Kv = V_cyt/V_nuc = 5); 16 species and 32 reactions; all
  parameters global.
- **Engine agreement:** COPASI and Tellurium agree on its own `sim1` (NRMSE 3.6e-7). That figure comes from
  viva-biomodels' `datasets/corpus_comparison/corpus_metrics.json`, the existing screen for criterion 1.
- **Its natural input is `TNF`, an external boundary species.** That is exactly the port an outer spatial layer
  drives (below).
- **The driven variant is generated, not hand-edited.** A committed libSBML script removes the `TNF_stimulation`
  event; `TNF := TNF_R` is kept, and `TNF_R` becomes the port.
- **Pre-equilibration** (d6): run the kinetic model alone with `TNF_R = 0` to steady state. Then seed the composite
  from that state through `species_overrides`, and record the step and its state.
- **Why not BIOMD0000000027 (d4):** one compartment and no stimulus input.
- **Runners-up (verified):**
  - BIOMD0000000407 (Schliemann 2011, three sized compartments, but 106 local parameters);
  - BIOMD0000000140 (Hoffmann 2002, whose stimulus is a rate rule plus an event).

### Spatial layer: **extracellular TNF field on viva-pde-particle** (Q3)
- **What it is:** one domain, the extracellular medium around the cell, with reflecting walls. This is what
  viva-pde-particle supports today (F6).
- **Ownership:** the spatial layer owns TNF transport (diffusion, plus optional decay and source). The kinetic layer
  only reads the TNF concentration at the cell. Their ownership does not overlap, so no quantity has two sources of
  truth.
- **Phasing:** PDE only (`FVReactionDiffusion`) first. Add `SmoldynHybrid` particles near the cell surface, through
  `SplittingCoordinator`, once the PDE-only coupling passes its oracle.
- **What this means for B:** "spatial layer matched to the kinetic compartments" is **deferred to v2**. It needs a
  feature viva-pde-particle lacks: two regions with a membrane flux (F6, F7). v2 would mean:
  - an upstream membrane-flux interface carrying all four transport fluxes (`i1`, `i1a`, `e1a`, `e2a`);
  - regions sized 1:Kv (nucleus:cytosol);
  - an operator split in which the spatial layer emits only transport deltas and is re-seeded from the kinetic
    store at each coupling step.

  VCell already models multiple compartments with membrane fluxes, and viva-pde-particle already wraps VCell's
  solver. So v2 extends that, rather than inventing one.
- **Multicellular extension:** the same field can later feed N cells, each with its own kinetic and Boolean stack.
  This is the heterogeneity question Schliemann 2011 studies.

### Boolean layer: **the decision half of Calzone 2010 cell fate, on `MaBoSSProcess`** (d1)
- **Source:** `cellfate.bnd` and `.cfg`, shipped in the MaBoSS repo (fetched, HTTP 200). The nodes TNF, NFkB,
  Apoptosis, Survival and NonACD exist.
- **Ownership boundary.** Alex's ruling (2026-11-04): "choose the most biologically accurate and overall
  model-native option". This replaces the original plan to cut TNF/TNFR/RIP1/IKK, because in Calzone TNF→TNFR also
  drives both death arms: DISC_TNF→CASP8 (apoptosis) and RIP1→RIP1K→ROS (necrosis). Lipniacki has neither, so that cut
  left P(Apoptosis) = P(NonACD) = 0 whatever NF-κB does. Probe through `MaBoSSProcess` at t = 40, full network with
  TNF on: Survival 0.015, Apoptosis 0.949, NonACD 0.032.

  **"Remove nothing; Calzone gates" (Alex, 2026-11-04).** This supersedes an earlier cut of RIP1ub, IKK, cIAP and
  mcIAP. That cut was exact only with NF-κB clamped, which the composite never does, because those nodes carry
  Calzone's death → NF-κB feedbacks, which Lipniacki lacks:
  - CASP8 ⊣ RIP1 → RIP1ub → IKK → NFkB (caspase-8 cleaves RIP1);
  - SMAC ⊣ cIAP → RIP1ub;
  - the pro-survival loop NFkB → mcIAP → cIAP.

  Cutting only those loops changes fate. On cmaboss, TNF on, t = 40, 50k samples:

  | Network | Survival | Apoptosis | NonACD |
  |---|---|---|---|
  | Full | 0.0136 | 0.9534 | 0.0291 |
  | Loops cut | 0.1281 | 0.8312 | 0.0001 |

  So the committed, scripted `.bnd` transform keeps all 31 nodes, and **Lipniacki owns how much NF-κB, while Calzone
  owns whether the activation route is still open**: the receptor complex is formed, RIP1 is not cleaved, and cIAP
  is not sequestered.
  - **NFkB** keeps its own logic, `IKK AND NOT CASP3`, as the gate on its rates:
    - `rate_up = @logic ? $u_NFkB : 0`
    - `rate_down = @logic ? $d_NFkB : 1`
    - with u = f and d = 1 − f, from Lipniacki. Study 0 calibrates the switching speed: u + d = κ on Lipniacki's
      clock, because at u + d = 1 the node flickers too fast for survival genes to hold.
  - **Every rate is multiplied by `$k_time`,** and `$TransRate` → `$r_tx/$k_time` in all 7 nodes that use it, cIAP and
    mcIAP included.
  - **Key check:** at u = 1, d = 0 (k_time = 1, r_tx = 1/24), the coupled network equals Calzone's original exactly,
    on all 31 nodes, with TNF on.
  - **Negatives, for coverage gaps the review found:**
    - a mutant where CASP3 doesn't force NFkB off must fail;
    - stripping `$k_time` from a death-arm node must fail.

    The NF-κB rule is read from the SBML, not hand-typed.
  - **f is Lipniacki's own nuclear fraction of NF-κB,** `(NFKB_nuc/Kv) / NFKB_total`, from its `NFKB_total` rule. It is
    dimensionless and has no fitted constant. `NFKB_total` is a rule variable, not a floating species, so the adapter
    computes it from the floating species in that rule: `IKKactive_IkB_NFKB + NFKB + IkB_NFKB + (NFKB_nuc + IkB_NFKB_nuc)/Kv`.
  - **TNF node:** driven by `$u_TNF`/`$d_TNF` from the same receptor-occupancy value that drives Lipniacki's
    `TNF_R` (d1). That value has one writer and two readers.
- **Superseded:** the mutant-equivalence checks of the 4-node cut, kept in git history. They were exact only with
  NF-κB clamped. The kinetic → Boolean pair check stays, re-derived for u + d = κ: TNF off and f held fixed, P(NFkB on)
  matches its analytic window average.
- **Baseline already passing** (worktree `feat/boolean-layer`): `MaBoSSProcess` on the full 31-node network matches
  MaBoSS's own reference output (`refer/res_probtraj.csv`, sysbio-curie/MaBoSS@375ffad) within 0.008 on every node.
- **Config keys,** verified at viva-maboss@3fdccd7: `network`, `parameters`, `initial_state` (0 or 1 per node),
  `sample_count`, `windows_per_interval`, `seed`.
- **Porting the `.cfg`:** its `$` defaults (`High_NFkB`, `Low_CASP8`, `Low_RIP1` and `Low_cIAP` = 0; `TransRate` =
  0.041666…, as a number) and its istates go into `config.parameters` and `config.initial_state`, because
  `MaBoSSProcess` writes its own `.cfg`.
- **Clock (Alex, 2026-11-04): swept, not fixed.** Calzone's rates are in abstract units, and the composite runs in
  Lipniacki's seconds.
  - **No single factor fits.** Measured anchors:
    - Lipniacki: NF-κB half-rise ≈ 6 min; A20 protein half-rise 41 min.
    - Calzone: target-gene induction half-time 16.6 units; apoptosis half-time after TNF 8.5 units.
  - **The `.bnd` transform multiplies every rate by `$k_time`** (Calzone units per composite second; k_time = 1 is the
    original).
  - **Gene expression is anchored to Lipniacki; the sweep moves only the death machinery** ("anchor to Lipniacki,
    sweep death"):
    - Fate is a race between the death arms and NF-κB's protective genes, and `$TransRate` decides it. On the full
      network with TNF on, Survival is 0.02 at MaBoSS's example TransRate 1/24 and 0.20 at 1. Calzone 2010 (PLoS
      Comput Biol, Fig 4) reports about 0.30 / 0.60 / 0.10 survival / apoptosis / necrosis from rate-free asynchronous
      reachability.
    - So `$TransRate` becomes `$r_tx/$k_time`: target genes switch on at r_tx per second whatever k_time is.
    - `anchor_transcription.py` measures r_tx from Lipniacki: from NFKB_nuc's half-rise to A20's half-rise is
      2107 s, so r_tx = ln2/2107 = 3.29e-4 /s (`processed/transcription_anchor.json`).
  - **Checks** (feat/boolean-layer): `transcription-anchor-fast` and `transcription-anchor-slow`. Each document sets
    `parameters.k_time` and `parameters.r_tx`, from the anchor JSON.

### Coupling graph (→ is data flow; each store has one writer)

**Wiring rules found by running composites (2026-11-04), each with a check that fails when the rule is broken:**
- **Seed every map key that a step writes into.** In process-bigraph 1.9.1, a step's write to a `map[float]` key the
  store doesn't hold yet is silently dropped. An overwrite to `["parameters","u"]` on an empty map leaves it empty;
  the same write lands once the key is in the document. So the document seeds every such key: MaBoSS's `parameters`
  (`u_NFkB`, `d_NFkB`, `u_TNF`, `d_TNF`) and Tellurium's `parameters_in` (`TNF_R`, …). The negative check is
  `checks/boolean/pair-nfkb-analytic` with the store left unseeded.
- **A writer to `parameters_in` must declare `overwrite[...]`.** A plain `map[float]` output adds to the store on
  every update (viva-tellurium 0.2.3 README and test).
- **Set `"global_time_precision": 6` at the document's top level.** Without it, floating-point drift skips the last
  tick (`checks/kinetic/sim1-original`).
- **Row 0 of an emitter is t = 0, before any process has written,** so no expectation is placed on it.

| From | Port | Adapter | To | Port |
|---|---|---|---|---|
| PDE `FVReactionDiffusion` | `fields.TNF` | **`RegionMean`** (new, U2: masked mean over the cell-surface voxels) | store `tnf_at_cell` | |
| `tnf_at_cell` | | `MathExpressionStep` (a cited dose-response, fitted offline in BioNetGen, d1) | store `tnf_occupancy` | |
| `tnf_occupancy` | | (direct) | Tellurium | **`parameters_in.TNF_R`** (new, U1; its own store, separate from the `parameters` output; the writer must declare `overwrite[...]`) |
| `tnf_occupancy` | | `MathExpressionStep` (u = occ, d = 1 − occ) | MaBoSS | `parameters.u_TNF`, `parameters.d_TNF` |
| Tellurium | `species` (`bulk_species: false`): `NFKB_nuc`, `IkB_NFKB_nuc`, `NFKB`, `IkB_NFKB`, `IKKactive_IkB_NFKB` | `MathExpressionStep` (f = nuclear fraction; u = f, d = 1 − f) | MaBoSS | `parameters.u_NFkB`, `parameters.d_NFkB` |
| MaBoSS | `node_probabilities.Apoptosis`/`NonACD` | `MathExpressionStep` (gate) | Tellurium | `parameters_in.c1…` (U1). This is a candidate edge; its biological basis must be cited before it ships, otherwise v1 is Boolean read-out only. |

### Headline studies (Alex, 2026-11-04: all three)
One composite and one parameter sweep give all three. Each is a workspace study (`/viva-study`).

| # | Study | Spatial setup | Swept | Readouts |
|---|---|---|---|---|
| 2 | **Fate vs uniform TNF dose.** The control: kinetic + Boolean with a spatially flat input | Uniform bath: the TNF field starts uniform at dose D, with no gradient and optional linear decay | D | MaBoSS Survival/Apoptosis/NonACD probabilities; NF-κB first nuclear peak (height, time) and oscillation period |
| 1 | **Fate vs distance from a point TNF source.** The headline: what space adds, through arrival delay and the dose that reaches the cell | Point source at distance r from the cell's surface region | r, and source strength | Same as 2, plus TNF at the cell over time (the `RegionMean` store) |
| 3 | **NF-κB wave timing under a moving TNF front.** The mechanism | Study 1's runs (no new runs) | r | Timing of the TNF front's arrival vs NF-κB nuclear peaks and oscillation phase, from the kinetic store |

- **The scientific test.** Map each study-1 run onto study 2's dose axis by the TNF dose that reached the cell, at its
  peak and integrated over time. If fate collapses onto study 2's curve, space acts only through dose. If it doesn't,
  arrival timing matters. Study 3 shows the mechanism behind either answer.
- **What the spatial engine supports.**
  - A uniform bath and a **point bolus are both initial conditions** of the `fields` store, which
    `FVReactionDiffusion` supports today. A bolus diffusing in a reflecting box is study 1's moving front, and it has
    an analytic solution: a Gaussian with image terms, which is also Phase 3's spatial oracle.
  - A **sustained point source cannot be expressed today.** `FVReactionDiffusion`'s reaction terms take one scalar
    `k` over the whole domain. A sustained source would need a spatially varying source term upstream, outside v1. v1
    uses the bolus, and that limitation is recorded here.
- **Resolution (measured 2026-11-04, `checks/spatial/gaussian-diffusion`):** the FV scheme's error in a front's tail converges with dx and dt. At r = 40 um, t = 1 s it is +1.15% at dx 2 um / dt 0.01 s and +0.29% at dx 1 um / dt 0.0025 s. Choose study 1's grid with the TNF value at the cell in mind, and confirm the choice with one refinement run.
- **The death-clock axis `k_time` crosses all three studies** (Alex, 2026-11-04). It maps the race itself: how fast
  the death machinery must be for TNF to kill, at each dose (study 2) and distance (study 1). Gene expression stays
  anchored at r_tx = 3.29e-4 /s.
- **Cost:** one composite document, parameterized by D (bath) or by r and bolus size (source), plus k_time, and run per
  sweep point. No runs are added for study 3.

### Time scheme (d2, d3)
- **d7 use 1, step 1: the kinetic layer, measured** (`analysis/d7/kinetic_timescales.py` → `.json`, 2026-11-04).
  Jacobian eigenvalues of the driven Lipniacki model at the pre-equilibrated state and every 60 s for 6 h after
  `TNF_R` = 1 (libRoadRunner; cross-checked against numpy's eigenvalues of the same Jacobian to 2e-16):
  - **Decay timescales from ≈6 s to 8000 s (2.2 h)**, before and after the stimulus: about three orders of magnitude.
    The disparity d7 asked about ("if/when present") is real in this layer.
  - **One zero mode,** the conserved NF-κB total.
  - **A damped oscillation of about 100 min.** The least-damped complex pair has a period of 99–106 min from 1 h on,
    with an e-folding time of 55–105 min. It grows only during the first minute after the stimulus (1 of 360 points).
    NF-κB's nuclear peaks therefore ring for a few cycles and decay: there is no limit cycle.
  - **This settles d7 use 4's open question.** The core does oscillate, but damped, so the clock-related methods would
    apply to this transient ringing, not to a sustained rhythm. Use 4 stays not-now.
  - **Coupling reads:** by d7's rule (interval ≈ 0.1 × the fastest timescale among the inputs a layer reads), the
    kinetic layer's own stiffness (≈6 s) is handled inside CVODE. What constrains the coupling intervals is the
    timescale of what crosses each edge: TNF at the cell (spatial, measured by step 2) and the NF-κB nuclear fraction
    f (minutes; the ~100 min ringing).
- **Intervals:**
  - Every interval is a whole-number multiple of the base step: the spatial layer's interval, or that of the faster
    of the coupled pair.
  - Set `global_time_precision` in the document.
  - The values come from d7 use 1. With a PDE-only spatial layer, backward-Euler diffusion is unconditionally stable,
    so the PDE `dt` is set for accuracy, not stability.
- **Triggers:** fixed ratios. Adapters run every tick their inputs are touched (F8), and the coarse layers hold their
  outputs between updates by default. d3's "early update" of a Process is not available in process-bigraph 1.9.1
  (d7).
- **Run length:** hours of model time in one `composite.run`, after the separate kinetic pre-equilibration.

### Rule-based layer: **not in v1** (Q4, after the researcher's check; key claim re-verified)
- **Why the strongest candidate fails.** The best runtime role was a TNF receptor binding and clustering layer between
  the TNF field and `TNF_R`. It fails in v1 for three reasons:
  - **The wrapper loses bound complexes.** `NFSimProcess` carries state between intervals only for molecule types
    with no binding sites, or with `~` states. Types with binding sites and no states, such as `R(l,l)` and
    `T(1,2,3)`, belong to neither group, so every bound complex is dropped at the end of each interval
    (viva-nfsim@76ff7fc `processes.py:84-96,340-350`, re-read).
  - **Other wrapper limits.** It has no parameter port, and it restarts the same RNG seed every interval
    (`:109-113`).
  - **Timescales.** Receptor binding (about 100 s) is quasi-steady on NF-κB's timescale of hours. Lipniacki's `TNF`
    is an on/off gate (a modifier in `k1*TNF*IKKn` and `k2*TNF*A20*IKKa`), so one scalar carries no extra information
    into the core.
- **(b) IKK or IκB:NF-κB complexes** would duplicate what Lipniacki already owns, breaking the ownership rule.
- **What v1 uses instead (d1).** The `tnf_at_cell → TNF_R` `MathExpressionStep` gets a cited dose-response, fitted
  offline from a published rule-based TNF receptor model run through BioNetGen's own ODE (`generate_network`; no
  viva-nfsim needed):
  - McMillan 2021, on RuleHub `Published/McMillan2021`;
  - or Prada 2020, if its BNGL is available (unverified).

  The step records that mapping a receptor fraction onto Lipniacki's on/off `TNF` is an assumption, with Lipniacki
  2007 as its precedent.
- **v2 and later:** an NFSim receptor layer only alongside a stochastic or multicellular core. It needs these upstream
  viva-nfsim fixes first:
  - carry every species' full state between intervals;
  - add a parameter input port;
  - give TNF its own clamped input;
  - use a new RNG seed each interval.

  Its oracles would be chunked vs. continuous NFsim, and the Goldstein–Perelson equilibrium on TLBR.

### Where it lives
- **A new viva workspace**, made with `/viva-workspace` (default name `viva-multiscale-nfkb`). It holds:
  - the document;
  - the libSBML and `.bnd` transform scripts;
  - the pre-equilibration step;
  - the studies (`/viva-study`);
  - d7's analysis.
- **compose-api** runs it as an inferred mash-up of viva-maboss, viva-tellurium, viva-pde-particle and
  viva-basic-processes. The composite itself needs no new registry entry.

## Phases (each atomic and independently verifiable; each upstream change is one BOJ unit)

1. **U1, viva-tellurium: a `parameters_in: map[float]` input** on `TelluriumProcess`, applied every update with
   the `self._rr[pid] = v` the config overrides already use.
   - The PR carries a real-roadrunner regression test: changing `k1` mid-run changes the rate, and the test fails
     without the port. That also settles whether `constant="true"` parameters can be set at runtime.
   - It adds a new `TelluriumProcess` compliance case (F9).
   - Then:
     - tag and release, checking the PyPI hold first;
     - bump the compose-api pin;
     - rerun compliance, which takes the entry from `listed` back to `tested`.
2. **U2, viva-pde-particle: `RegionMean`** in `steps/transfer.py` (field + mask → mean concentration).
   - Tests: a uniform field returns its value; a masked field ignores what lies outside the mask.
   - Then the same release and pin cycle, with its compliance case rerun in a composed mash-up.
3. **Standalone baselines, each with an oracle:**
   - **Kinetic, original model:** Lipniacki in `TelluriumProcess` reproduces BioModels' `sim1`. The oracle is the
     corpus reference.
   - **Kinetic, transformed model:** after pre-equilibration, stepping `TNF_R` to 1 through U1 reproduces the
     post-event part of `sim1`.
   - **Boolean:** the reduced `.bnd` over **one** interval matches the MaBoSS CLI on the same `.bnd` (F1: across
     several intervals the process carries one sampled state, not the ensemble).
   - **Spatial:** a PDE-only TNF field with no sink conserves mass; a point source matches the analytic diffusion
     solution.
   - **Dose-response (d1):** McMillan 2021's BNGL, run through BioNetGen's ODE, reproduces the paper's binding
     curve. The fitted `TNF_R = f([TNF])` and its source are committed in the workspace.
4. **Pairwise couplings, each with an oracle:**
   - **Spatial → kinetic:** a uniform constant field gives the same trajectory as the kinetic model with the
     equivalent constant `TNF_R`.
   - **Kinetic → Boolean:** with `NFKB_nuc` held fixed, MaBoSS's NFkB on-probability matches its analytic
     switching value.
5. **Full composite.**
   - Run it all-finest first, then at d7 use-1 intervals.
   - Accept it only if the chosen-interval run matches the all-finest one on the reported observables, shows no
     coupling oscillation, and runs faster (d7 step 5).
   - Record the result in the workspace study.
6. **A compose-api live run** as a mash-up, only after Alex's go. Until then nothing is submitted to production.

## Verification
- Every oracle runs through compose-api's `runner.py` and `compliance.evaluate`, never a bespoke harness.
- Upstream tests run the real engines. Nothing in doubt is mocked, and no fixture restates the port under test.
- `/adversarial` review of each upstream diff and of the composite document before either is called done. This plan
  has already had one: 4 blockers and 9 defects, each corrected above.

## Not touched
- `agenda-onboarding.md`, `compose_api/client/`, `assets/compositions/`, `docs/plan/plan-composer-cli.md`,
  `CURRENT.md`.
- Section C is independent; B adds no compliance case to label.
- viva-cobra (FBA) is not in B's hierarchy. It stays an extension point, with Pulse.

## Decisions (Alex, 2026-11-04)
- **Q1, kinetic core:** Lipniacki 2004 (BIOMD0000000786).
- **Q2, U1:** yes, add the viva-tellurium `parameters_in` port.
- **Q3, spatial layer in v1:** the extracellular TNF field. In parallel, a background agent scopes **v2**: an upstream
  membrane-flux feature in viva-pde-particle, and an operator split carrying `i1`, `i1a`, `e1a` and `e2a` at a 1:Kv
  volume ratio. It writes its plan to `docs/ref/multiscale-compositions/task-plan-membrane-flux.md`; Alex authorized
  that one file.
- **Q4, rule-based layer:** the researcher found no robust runtime role for v1, so NFSim is left out of v1, as Alex
  decided for that case. Its offline contribution (d1) is the TNF → `TNF_R` dose-response.
- **The v2 scoping agent is still running.** It writes only
  `docs/ref/multiscale-compositions/task-plan-membrane-flux.md`, then stands by.
