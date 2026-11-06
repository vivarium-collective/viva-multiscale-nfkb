# Study 0: calibrating the coupling

The composite joins two models that keep time differently. Lipniacki's NF-κB model runs in seconds. Calzone's
cell-fate network runs in abstract units. Two speeds are not given by either model: which of Lipniacki's timescales the
Boolean NF-κB node should follow, and how long a Calzone unit is. Study 0 measures their effect before the headline
studies ({doc}`studies`) run on the composite:

- **κ, how fast the Boolean NFkB node follows Lipniacki's NF-κB** ({doc}`coupling`, {doc}`../math/switch`).
- **`k_time`, how fast the death machinery runs** ({doc}`time`): one Calzone unit per 2, 10, 30 or 120 minutes.

It then asks whether NF-κB's protective proteins could save cells if they lasted longer, in three follow-ups (the
variants table below; they are Study 0's variants, also called Studies 0b–0d):
- **0b** anchors their decay to Lipniacki's measured protein turnover, but its edit also touched two other nodes, so
  it is confounded;
- **0c** is an upper bound: they never decay;
- **0d** is 0b corrected: the measured turnover on the four protective products only.

The study lives in the workspace as
`workspace/investigations/tnf-fate-in-space/studies/s0-coupling-calibration/`. Its `study.yaml` holds the design,
every run and its findings. `run_grid.py` and `population.py` build and run it, and `analysis.py` makes the
tables quoted here.

## Design

| Choice | What | Why |
|---|---|---|
| Population | 1 deterministic kinetic layer, 200 independent stochastic fate networks (one MaBoSS trajectory each, own seed) | Lipniacki is deterministic, so every cell sees the same NF-κB. The cells differ only in their fate network's random draws, so fractions are fractions of cells. |
| Composite | The NF-κB model ({doc}`../science/lipniacki-model`) and the fate network ({doc}`../science/calzone-network`), coupled through NF-κB's nuclear fraction $f$ ({doc}`coupling`). No spatial layer and no dose–response | Calibrates the coupling on its own, before space and dose are added |
| Stimulus | TNF at saturation from t = 0 and held: the NF-κB model's `TNF_R` = 1 from its rest state, and the fate network's TNF node on from the start with rates `u_TNF` = `d_TNF` = 0, so it stays on | The simplest stimulus. It is the case Calzone's own network was built for. |
| Grid | κ × clock: κ ∈ {κ = `k_time`, NF-κB flipping at Calzone's unit rate; $\ln 2/337$ s, Lipniacki's NF-κB half-rise; $\ln 2/2107$ s, Lipniacki's NF-κB → protein delay}, and 2, 10, 30 or 120 min per Calzone unit (`k_time` = 1/(60 × minutes) per second). 12 points, 200 cells each, cell seeds 1–200 | Spans κ from NF-κB's own rise in Lipniacki's model (337 s) to its NF-κB → protein delay (2107 s), plus the Calzone-unit rate, and the clock across a factor of 60 |
| Coupling | Every 30 s. Each cell's fate network is one `MaBoSSProcess` with one trajectory per interval, so it records one sampled on/off state per node every 30 s ({doc}`../math/maboss`) | Each cell is a single history, as a real cell is |
| Duration | 24 h of model time at every clock (Alex: "24 hours everywhere") | At 8 h, 77–85% of cells were still undecided (no fate node yet on) at the slowest clock. |
| Recording | Each cell's fate code every 30 s: Survival + 2·Apoptosis + 4·NonACD | Calzone's fate nodes are not mutually exclusive: a cell can show caspase-3 and ATP loss together. A first 8 h grid summed them as if they were exclusive, double-counted, and was discarded. |
| Readout | **Alive**: no death node on at any tick in 24 h. **Durable survival**: alive with Survival on at 24 h. End state and first fate (the first fate node a cell switches on, Survival included; {doc}`../reference/glossary`) alongside | Death is irreversible, but Calzone's death nodes are not absorbing: Apoptosis follows CASP3 and NonACD follows ATP loss, and both switch off when their logic fails. Read by end state, up to 27% of a run's cells (with Calzone's gates removed) looked alive after they had died. |
| Seeds | Every variant reuses the grid's 200 seeds | Differences between runs then come from the change, not from new random draws. Variants are compared with the grid **cell by cell** (exact McNemar test), which an adversarial review showed is needed. Comparing two fractions as if independent hid a consistent shift. |
| Environment | The workspace's pinned `compose/` environment, through compose-api's own runner; vivarium-workbench, the study dashboard, only records the runs (Alex: "Pinned env; workbench records") | The results are what compose-api would produce in production. |

### Variants

Each variant changes the fate network in one named way (`population.py`, `EDITS`), runs at κ = Lipniacki's NF-κB speed
on the grid's seeds, and is compared with the grid cell by cell.

| Variant | Nodes edited | Edit | Question |
|---|---|---|---|
| Gate removal: RIP1 | RIP1 | logic drops `NOT CASP8` | what if caspase-8 could not cleave RIP1 and close the survival route? |
| Gate removal: both | RIP1, cIAP | also: SMAC no longer removes cIAP | what if neither gate existed? |
| 0b (confounded) | cFLIP, BCL2, mXIAP, mcIAP, **mROS, Survival** | switch-off at $r_\text{deg}$ instead of one Calzone unit | do the protective proteins vanish too fast? (mROS and Survival should not have been included) |
| 0c, the bound | cFLIP, BCL2, mXIAP, mcIAP | never switch off once made | can persistence save cells at all? |
| 0d | cFLIP, BCL2, mXIAP, mcIAP | switch-off at $r_\text{deg}$ | what does the measured turnover give? |
| Absorbing death | Apoptosis, NonACD | never switch off once on (`absorb_death` = 1) | does absorbing death change any result? ({doc}`boolean`) |

## What the grid found

κ = Lipniacki's NF-κB speed, 24 h, 200 cells per clock. Apoptosis and necrosis can overlap in the end state, so those
two columns don't sum to "dead".

| Clock (min per Calzone unit) | Alive | Durable survival | Died, then revived | End: apoptosis | End: necrosis | Median first fate |
|---|---|---|---|---|---|---|
| 2 | 0 | 0 | 0 | 0.935 | 0.065 | 18 min |
| 10 | 0 | 0 | 0 | 0.790 | 0.210 | 76 min |
| 30 | 0 | 0 | 0 | 0.690 | 0.310 | 205 min |
| 120 | 0.160 | 0.045 | 0.075 | 0.455 | 0.355 | 658 min |
| Calzone alone, t = 40 units, TransRate 1/24 (a different readout: the fraction of cells with each node on at t = 40, so only roughly comparable) | | 0.014 | | 0.953 | 0.029 | |

1. **Held, saturating TNF kills nearly every cell.** No cell is alive at 2–30 min per unit for any κ. At 120 min per
   unit, 6.5–16% are alive, depending on κ. 24 h is only 12 Calzone units at that clock, short of the 40 at which
   Calzone's own run is read, so some of those cells may still die.
2. **Calzone alone also kills nearly every cell, but the split differs.**
   - At 2 min per unit, the composite's genes switch on at about Calzone's own TransRate: $r_\text{tx}/k_\text{time} =
     3.29\times10^{-4} \times 120 = 0.039$ per unit, about 1/25, against 1/24.
   - There it gives no survivors in 600 cells, where Calzone's 1.4% predicts about 8. It also gives more necrosis
     (5–8.5% against 2.9%).
   - The difference is the coupling. Calzone's NFkB switches on fast and stays on while its gate is open. The coupled
     node flips on and off around Lipniacki's fraction $f$ ({doc}`coupling`).
3. **The clock decides how cells die, not whether.** Slowing the death machinery moves death from apoptosis to
   necrosis. The first fate arrives after about 5–9 Calzone units at every clock.
4. **κ hardly matters.** No κ leaves a cell alive at 2–30 min per unit, and κ moves the apoptosis/necrosis split by at
   most 0.135.
5. **NF-κB's protection is brief.** NF-κB peaks at $f = 0.933$ at 24 min, drops to 0.020 at 80 min, and settles at 0.28
   after about 6 h. Of the cells that show Survival first, 69–100% have a death node on later (all of them at 2–30
   min per unit).
   - At fast clocks, cells die before the protective products can be made: those switch on with a 35-min half-rise.
   - At slow clocks, the protective products' logic keeps failing, because the coupled node is off about 72% of the
     time once $f$ settles. The death arms never pause under TNF.

   Studies 0c and 0d test both readings.
6. **Calzone's gate on NF-κB diverts death but doesn't prevent it.** The death machinery closes NF-κB's gate in three
   ways (*Gate*, {doc}`../reference/glossary`): caspase-8 cleaves RIP1, SMAC removes cIAP, and caspase-3 blocks NF-κB
   directly. The first two can be removed: caspase-8's cleavage of RIP1 and SMAC's sequestration of cIAP.
   - Removing only the RIP1 cleavage turns every death into necrosis.
   - Removing both still kills every cell at some point in 24 h (200 of 200, at 10 and at 30 min per unit). The 22.5–27% that the end state showed as
     alive had died and then lost the death signal. Counting those cells as alive was the error that made *alive* the
     readout.

## Decision: κ

**κ = ln 2 / 337 s, Lipniacki's own NF-κB speed** (Alex, 2026-11-06).
- **Where it comes from:** 337 s is the half-rise of nuclear NF-κB after TNF in Lipniacki's model: the time to get
  half-way from its rest level to its first peak (`anchor_transcription.py`). With $f$ held, the node's probability of being on rises as
  $f(1 - e^{-\kappa t})$ ({doc}`../math/switch`), which reaches half its level at $t = \ln 2/\kappa$. Setting
  $\kappa = \ln 2/337$ s⁻¹ makes the node rise as fast as nuclear NF-κB does, so κ is measured, not fitted.
- **Why not Calzone's flicker (κ = `k_time`):** it ties NF-κB's speed to the assumed speed of the death machinery,
  which has no biological basis.
- **Why not the slower bracket (ln 2 / 2107 s, the NF-κB → protein delay):** it applies the transcription delay a
  second time, because the genes already carry it.
- **What the data say:** at 120 min per unit this κ leaves the most cells alive (16%, against 6.5% and 9.5%). At 2–30
  min per unit no κ leaves any cell alive.

## Do the protective proteins vanish too fast? Studies 0b, 0c and 0d

NF-κB induces four products that block the death arms:
- cFLIP, which blocks caspase-8;
- BCL2, which blocks the mitochondrial death steps;
- mXIAP and mcIAP, the transcripts of XIAP and cIAP.

In the network, each switches on at `r_tx` while NFkB is on. Once NFkB is off, it switches off after one Calzone unit,
on average. At fast clocks that is minutes. The question was whether the cells die because the products vanish
between NF-κB's waves.

### Study 0b: a confounded test, and what it taught

**The test.** Alex chose to anchor the products' decay to Lipniacki's measured protein turnover: A20's degradation
constant $c_5$ (the model's `A20_degradation` reaction), $r_\text{deg} = 3\times10^{-4}\ \text{s}^{-1}$, a 38.5 min
half-life. Lipniacki's model contains no cFLIP, BCL2, XIAP or cIAP, so A20, the one NF-κB-induced protein whose
turnover it does contain, stands in for all four. That is an assumption.

**The result.** As run, the test was **confounded**. Besides the protective products, the edit also slowed:
- **mROS.** mROS is on when NF-κB is *off* (`NOT NFkB`), and it licenses ROS, which drives necrosis.
- **Survival.** This is the readout node, not a protein.

Cell by cell against the grid:
- at no clock does the paired comparison change the alive/dead outcome beyond noise;
- at 2 and 10 min per unit the paired comparison shifts the death mode toward necrosis (9 of 9 changed cells at 2 min per unit,
  p = 0.004), which is the mROS artefact;
- at 120 min per unit, durable survival falls from 9 cells to 0 (p = 0.004). There Lipniacki's turnover is 2.2× faster
  than the grid's switch-off. This was first read as the Survival node decaying faster, but 7 of the 9 cells die.
  Study 0d, which leaves Survival alone, gives the same counts (6 of the 7 dead cells are the same cells). So the
  faster loss of the protective products is enough to cost all 9, though 0d cannot show that Survival's own decay
  added nothing in 0b.


**The lesson for the composite.** "NF-κB target" is not the same as "protective". Each edit to Calzone's network is now
limited to nodes whose biological role is the one the edit is about.

### Study 0c: the persistence bound

Alex chose to bound the question before rerunning the decay test. **The edit:** the four protective products never
switch off once made. mROS and Survival are left alone, and so are XIAP and cIAP themselves, which still switch off
when SMAC removes them, because that is regulation, not turnover. This is an upper bound, not a model.

### Study 0d: the measured turnover

The corrected 0b: the four protective products, and nothing else, switch off at $r_\text{deg}$ at every clock. On
average a product then switches off 56 min after NFkB goes off. That is 1.9–28× later than in the grid at 2–30 min per
unit, and 2.2× sooner at 120 min per unit. The rate is Lipniacki's; acting only while NFkB is off is the network's
form. Lipniacki's own decay is constitutive, which would remove the products faster still.

### Results

Alive at 24 h, κ = Lipniacki's NF-κB speed, on the grid's seeds:

| Clock (min per Calzone unit) | 2 | 10 | 30 | 120 |
|---|---|---|---|---|
| Grid (products off after one unit) | 0 | 0 | 0 | 16% |
| 0d: Lipniacki's turnover | 0 | 0 | 0 | 12% |
| 0c: never off (bound) | 3% | 8.5% | 13% | 33.5% |

- **Persistence is a lever (0c).** Cell by cell, almost every change is from dead to alive: 6, 17 and 26 cells saved,
  none lost, at 2, 10 and 30 min per unit (p = 0.031, < 0.001, < 0.001), and 39 saved against 4 lost at 120 min per
  unit (p < 0.001). Most rescued cells have Survival *off* at 24 h, because Survival follows the flickering NFkB node:
  *alive*, not the Survival node, is the readout of a protected cell.
- **The measured turnover doesn't pull it (0d).** At 2–30 min per unit the products last far longer than in the grid,
  yet every cell still dies, including every cell that 0c saved. At 120 min per unit, 17 cells are newly dead and 9
  newly alive (p = 0.17), no change beyond noise, but durable survival falls from 9 cells to 0 (p = 0.004). Of the
  cells that show Survival first, 79% have a death node on later (grid 69%, 0c 33%).

### Where the turnover can act

It depends on the clock, because the clock decides *when* cells die relative to NF-κB's time course. NF-κB peaks at
$f = 0.933$ at 24 min, falls below 0.1 from 65 to 100 min, oscillates between about 0.2 and 0.38, and settles at
$f = 0.28$ by about 6 h.

**2–30 min per unit: cells die during the transient.** In 0d, 200, 199 and 171 of the 200 cells have died before 6 h.
At 2 min per unit they die (median first fate, which is almost always a death here, 18 min) before the products are made at all, since those switch on with a
35-min half-rise, so decay cannot matter. At 10–30 min per unit the bound saves 8.5–13% and the measured rate saves
none. These runs record no product states, so they cannot say which part of the transient decides that.

**120 min per unit: cells die after NF-κB settles.** Only 2–4 first deaths come before 6 h, so the settled duty cycle is
what matters. Two rates set a product's presence:

- induction, $r_\text{tx} = \ln 2 / 2107\ \text{s} = 3.3\times10^{-4}\ \text{s}^{-1}$, which acts only while the coupled
  NFkB node is on (about 28% of the time: about 11 min on, 29 min off, {doc}`../math/switch`);
- switch-off, $r_\text{off}$, which acts only while the node is off.

Quasi-steady, a product's time-averaged occupancy ({doc}`../reference/glossary`) is

$$
\frac{f\,r_\text{tx}}{f\,r_\text{tx} + (1-f)\,r_\text{off}} .
$$

| Variant | $r_\text{off}$ | Occupancy | Durable survival | Alive |
|---|---|---|---|---|
| Grid | $k_\text{time} = 1/7200 = 1.39\times10^{-4}\ \text{s}^{-1}$ | 0.48 | 9 cells | 16% |
| 0d | $r_\text{deg} = 3\times10^{-4}\ \text{s}^{-1}$ | 0.30 | 0 | 12% |
| 0c | 0 | → 1 | 21 cells | 33.5% |

The order matches. Three caveats:
- **It is an approximation.** The node's on and off phases (11 and 29 min) are not much shorter than the products'
  time constants (51 and 56 min).
- **The duty cycle is not external.** NFkB's logic is `IKK AND NOT CASP3`, so the death arms close the route that the
  estimate assumes is open.
- **Occupancy is not why nearly every cell dies.** The 0c bound keeps products once made, yet still kills 87–97% at
  2–30 min per unit.

Recording the four products' states in a run would test the estimate.

## What it means for the headline studies

At Study 0's clocks (2 to 120 min per unit), a held, saturating dose shows little NF-κB protection in this composite,
and the measured protein turnover doesn't change that. Study 1 later measured it across clocks: at most about 10 to
13 points, limited by the race in Calzone's own network ({doc}`validation`). The remaining levers Study 0 identified:

- **How NF-κB induces the products.** Lipniacki's transcription is proportional to nuclear NF-κB; Calzone's genes see
  only an on/off node. Driving the products' induction by $f$ directly (*graded transcription*) keeps the same
  time-averaged induction, $f\,r_\text{tx}$, so by the estimate above it keeps the same occupancy. It changes the
  products' timing, not their average. Its case is fidelity to Lipniacki, not a rescue these data predict.
- **Exposure.** How much TNF reaches each cell, when, and for how long. In the tissue, that is exactly what space
  decides ({doc}`studies`). The receptor dose–response (d1, McMillan 2021) is the layer it needs.

Alex's two decisions after Study 0 (2026-11-06; {doc}`decisions`, rows 27 and 28):

- **Exposure (d1) is the next lever**, not graded transcription, since nothing in Study 0 predicts a rescue from
  graded transcription.
- **Death becomes absorbing in the network itself**, so that a death flag stays set, which a later edge can use to stop
  a dead cell signalling. Until now only the readout made death irreversible. No node reads Apoptosis or NonACD, and
  rerunning the baseline with absorbing death on the same seeds moved no cell's first death ({doc}`boolean`).
