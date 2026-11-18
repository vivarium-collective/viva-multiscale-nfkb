# Study 1: can NF-κB protect cells in the composite?

Study 0 ({doc}`calibration`) found that under held, saturating TNF the composite kills nearly every cell. In
experiments, cells with working NF-κB mostly survive TNF alone, and they die when NF-κB or protein synthesis is
blocked. That standard comes from two sources the project lead accepted as inputs to the investigation
(Micheau & Tschopp 2003; Lee et al. 2016; {doc}`../reference/bibliography`).

Study 1 ({doc}`decision 29 <decisions>`) asks whether the composite meets that standard using only the published models' own parameters,
and if not, where the limit is. It adds no mechanism. The study lives in
`workspace/investigations/tnf-fate-in-space/studies/s1-survival-validation/`: `phase_a.py`, `phase_b.py` and `data/`.

## How it is measured

- **Knocking NF-κB out.** In the composite, the NF-κB node's switching speed κ is set to 0, so the node never switches
  on ({doc}`coupling`). In Calzone's network alone, $u_\text{NFkB} = 0$ and $d_\text{NFkB} = 1$.
- **Alive.** No death node was ever on. Death is absorbing ({doc}`boolean`).
- **Net protection.** Each intact cell is paired with its knocked-out twin, which has the same seed
  ({doc}`../math/statistics`). It is the number of cells alive only with NF-κB, minus those alive only without it, as a
  percentage of the cells (percentage points).
- **Meeting the standard.** Most NF-κB-competent cells survive and most knocked-out cells die. The design asked for a
  majority surviving. After Phase B showed that at slow clocks many alive cells have reached no fate at all, survival
  was read as *held*: alive, with Survival on through the last 2 h of the run, not merely not dead yet. Held survival
  is stricter than Study 0's *durable survival* (Survival on at the 24 h snapshot; {doc}`calibration`). That reading
  was fixed after the data, and the Phase B table gives both alive and held survival.
- **The comparator.** In the composite, the protective genes switch on at $r_\text{tx}$ per second and every other rate,
  including NF-κB's whole activation route (TNFR, RIP1, RIP1ub, IKK), runs on the death clock `k_time`. Only the final
  NF-κB node follows Lipniacki directly, at $f\kappa$. So at a death clock of $m$ minutes per Calzone unit, the
  composite's fate network is Calzone's network with TransRate $r_\text{tx} \cdot 60m$ per unit, read after
  $24 \cdot 60/m$ units, in every node but NF-κB. Phase A runs Calzone's network alone at exactly those settings, so
  the comparison isolates what the coupled NF-κB node does.

## Phase A: Calzone's network alone

Speeding up the protective genes, read at t = 40 units (20,000 cells):

```{include} _validation_phase_a.md
```

Alive saturates near 25%: even infinitely fast genes cannot save most cells. The reason is upstream. NF-κB's
activation route takes four steps (TNFR → RIP1 → RIP1ub → IKK → NFkB) and caspase-8's takes two (TNFR + FADD → DISC →
CASP8). Active caspase-8 cleaves RIP1, which closes NF-κB's route ({doc}`../science/calzone-network`), so most cells
never switch NF-κB on.

The Survival node is not the readout. It follows NF-κB, and it can be on in a cell whose death node is already on,
because the rest of the network keeps running after death ({doc}`boolean`). So with fast genes more cells show Survival
than are alive (0.201 against 0.156 at TransRate 1, `data/phase_a.json`); *alive* is what counts.

## Phase B: the composite, NF-κB intact against knocked out

The composite runs held TNF from rest for 24 h, with 200 cells on Study 0's seeds. Net protection is in percentage
points; p values are exact McNemar, uncorrected for six comparisons:

```{include} _validation_phase_b.md
```

## Against Calzone alone at the same settings

Phase A also ran Calzone's network alone at each clock's matched TransRate and read time (20,000 cells, so its own
standard error is below 0.004 for an alive fraction and about 0.5 points for net protection, and is not shown). The composite's values carry ± one standard error over its 200
cells: $\sqrt{p(1-p)/n}$ for an alive fraction, and the paired form for net protection ({doc}`../math/statistics`).
By this formula a fraction of 0 has no spread; at 30 min per unit, 0 alive of 200 against Calzone's 0.125 is
decisive on its own ($0.875^{200} \approx 3\times10^{-12}$).

```{include} _validation_matched.md
```

The tables are generated from the study's data by `documentation/design/code/validation_tables.py` (`--check` fails
when they are stale).

## What it shows

- **The death is Calzone's own.** With NF-κB knocked out, the composite and Calzone alone agree within one standard
  error at every clock but 480 min per unit, where they differ by 2.0. The intact composite never protects
  significantly more than Calzone alone.
- **The coupling lowers protection only at fast and middle clocks:** 0 against 12.5 points at 30 min per unit (no cell
  alive, against Calzone's 0.125), and 10.5 against 21.5 at 120 (4.8 standard errors). At 180 and 200 the composite is lower by about 1.5
  standard errors, which is not significant; at 240 and 480 the two agree within noise.
- **No clock meets the standard with held survival.** At 200 min per unit, most intact cells are alive (0.550) and
  most knocked-out cells are dead. But 54 of the 110 alive intact cells have reached no fate at all, and only 18 held
  Survival through the last 2 h; of the other 56, which reached Survival, 38 did not hold it. That is delay and
  lapse, not protection. 24 h is only 3 to 12 Calzone units at the clocks from 120 to 480 min per unit.

The limit is the activation race in Calzone's network, between caspase-8 and NF-κB's activation route
({doc}`../science/calzone-network`), which in the composite runs
on the death clock. Lipniacki's model, however, already times that same activation: nuclear NF-κB's half-rise is 337
s. A model-native change would put NF-κB's activation route on Lipniacki's clock, as $r_\text{tx}$ already does for the
genes, so that NF-κB activates before caspase-8. That change is {doc}`decision 30 <decisions>`, which the project
calls "Option A", tested next.

## Option A: NF-κB's activation route on Lipniacki's clock

**What changes.** With the switch `anchor_activation` on ({doc}`decision 30 <decisions>`, {doc}`boolean`), RIP1, RIP1ub
and IKK each switch on at $r_\text{act}$ = 0.0239 per second instead of at the death clock's `k_time`. That rate makes
the three steps in series reach IKK in a median of 112 s, the time IKK's activity takes to reach half its peak in
Lipniacki's model ({doc}`boolean` derives it). TNFR and every switch-off stay on `k_time`, and NF-κB's own node keeps
its switching rate κ = ln 2 / 337 s (decision 25), so the route's 112 s add to NF-κB's own timing rather than
replacing it. Everything else is Phase B: the
same six clocks, the same 200 seeds, NF-κB intact and knocked out, and 24 h.

**The standard, fixed before the run** by the project lead (Alex, 2026-11-06): at one or more clocks, at least half
the intact cells hold survival, and at most half the knocked-out cells are alive.

Each entry is unanchored → anchored. In the last two columns, each cell is paired with its unanchored twin, the cell
with the same seed in the same arm. "Saved" counts the cells alive only with anchoring, and "lost" those alive only
without it. The p value is the exact McNemar test on those two counts, shown where it is below 0.05. The 12 p values
are not corrected for the 12 comparisons; at a Bonferroni threshold of 0.05/12 ≈ 0.004, the intact change at 180 and
the knocked-out change at 480 would not count. Net protection, the alive fraction intact minus the alive fraction
knocked out, is the same number as the paired count defined above.

```{include} _validation_anchored.md
```

**No clock meets the standard.** Each half is met at some clock, never both at one:
- At 240 min per unit, 0.495 of the knocked-out cells are alive, just under the bar, but only 0.36 of the intact cells
  hold survival.
- At 480, 0.56 of the intact cells hold survival, but 0.94 of the knocked-out cells are alive too. At that clock almost
  no cell dies within 24 h, with or without NF-κB.

**Why intact cells do not hold survival.** Anchoring lets nearly every surviving intact cell reach Survival, but many
lose it again. The table counts intact cells alive at 24 h; an alive cell that reached any fate reached Survival, the
only fate that is not death:

```{include} _validation_anchored_survival.md
```

At 240 min per unit, 155 of the 159 alive intact cells reached Survival, but only 91 had it on at 24 h, and 72 held it
through the last 2 h. Survival's rule is NFkB: it switches on, at the gene rate, while NF-κB's node is on, and off, on
the death clock, while it is off. Under held TNF the node is not held on. It is a duty cycle, on about 28% of the time
for about 11 min at a stretch ({doc}`coupling`), so a cell's Survival can lapse in the off spells. This account is read
from the rules and these counts; it was not tested by changing how Survival reads NF-κB.

**Net protection rises, partly because knocked-out cells die more.** Net protection rises when intact cells survive
more, and also when knocked-out cells die more. Anchoring does both:
- At 120 min per unit, most of the rise comes from intact cells: 12.5 of its 15 points.
- At 180, intact cells gain 9.5 points and knocked-out cells lose 13.5.
- At 200 and 240, knocked-out cells lose 15.5 points at each, against intact gains of 9.5 and 5.5.

The standard asks knocked-out cells to die, so this helps its second half: at 240 it brings knocked-out alive from 0.65
to 0.495. But it is not NF-κB protecting more. It is anchoring killing cells that have no NF-κB, and most of them die
by necrosis: 27 of the 35 knocked-out cells it killed at 180 min per unit, and 37 of 45 at 240 (the death-mode table
below).

**How cells die.** Anchoring speeds RIP1, and RIP1 starts necrosis as well as NF-κB's activation route
({doc}`../science/calzone-network`):
1. RIP1 switches on RIP1K.
2. RIP1K, with mROS, switches on ROS. In Calzone's network mROS stands for the absence of NF-κB's antioxidant genes,
   not a measured level of oxygen radicals. Its rule is NOT NFkB: it switches on, at the gene rate, while NF-κB is off,
   and off, on the death clock, once NF-κB is on.
3. ROS, without BCL2 (whose rule is NFkB), switches on MPT, the mitochondrial permeability transition.
4. MPT switches ATP off.
5. With ATP off, NonACD (non-apoptotic cell death, the network's necrosis node) switches on.

A knocked-out cell never switches NF-κB on, so mROS switches on and stays on and BCL2 never switches on: nothing holds
the route back once RIP1 is on. RIP1's rule needs caspase-8 off, and anchoring lets RIP1 switch on before caspase-8 can
close it. The five steps after RIP1 still run on the death clock. Its apoptosis falls too: the apoptosome, which apoptosis needs, needs ATP, and MPT switches ATP off.

Each entry is the fraction of cells with Apoptosis, or NonACD, on at 24 h, unanchored → anchored. Death is absorbing, so
this counts every cell in which it ever switched on, and a cell can show both. The last column follows the cells
anchoring killed, dead with anchoring and alive without it, paired by seed, and counts those with NonACD on:

```{include} _validation_anchored_modes.md
```

From 30 to 200 min per unit, apoptosis falls and necrosis rises in both arms. At 240 the intact arm's necrosis barely
moves, and at 480 almost no cell dies. Cell by cell, most of the cells anchoring killed had NonACD on, in both arms.
Anchoring killed intact cells too, mostly by necrosis (23 of 28 at 180), and those cells can no longer hold survival.
The account of why is read from the network's rules; it was not tested by changing the necrosis route.

**What follows.**
- By the standard fixed before the run, the composite does not adopt Option A: `anchor_activation` stays 0.
- One thing stands between the composite and the standard: intact cells reach Survival, but many lose it. Phase B
  shows the same lapse as built (at 200 min per unit, 38 of the 56 alive intact cells that reached Survival did not
  hold it); anchoring lets more cells reach Survival, and many of them lapse too.
- Necrosis bears on what the result means, not on whether it meets the standard. It meets the knocked-out half partly
  through a death route that anchoring opened, and it kills intact cells too.
- How Survival should read an NF-κB node that cycles, and whether the necrosis route should be timed differently, are
  modelling decisions for the project lead ({doc}`roadmap`).

**Engine.** These runs, like Phase B's, used viva-maboss 0.1.1, the version pinned then, so each pair compares like with
like. Each cell carries one sampled state of the fate network from one interval to the next ({doc}`../math/maboss`).
viva-maboss 0.1.2 lists the network's states in a fixed order before that draw, where 0.1.1 used the order MaBoSS
reported them in, which differs between platforms. The same random number can then pick a different state, so a rerun
today gives an equally likely sample, not the same trajectories. The data are `data/phase_b_anchored.json` and
`parquet-runs/anchored-*`, from `phase_b.py --variant activation-anchored`.
