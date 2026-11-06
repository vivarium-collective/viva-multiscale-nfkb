# The cell-fate network (Calzone 2010)

The composite's fate layer is the cell-fate network of Calzone et al. (2010), kept whole: 31 nodes, every rule
({doc}`../design/boolean`). This page shows the network itself, built up from what a node is, so that every later
argument about it can be checked here.

## Nodes, rules and rates

**A node** stands for one molecule, complex or process, and is either **on** (present or active at a level that matters
for the decision) or **off**. A cell's state is the list of all 31 on/off values.

**A rule** (`logic`) says when a node *should* be on, as a function of other nodes. `BAX = CASP8 AND (NOT BCL2)` reads:
BAX should be on when caspase-8 is on and BCL-2 is off.

**Rates** say how fast a node moves to what its rule says. Each node has a switch-on rate, used while it is off, and a
switch-off rate, used while it is on. A rate $\lambda$ means the switch happens after a random waiting time with mean
$1/\lambda$ (an exponential waiting time). In the rate expressions below:

- `@logic ? 1 : 0` means "1 if the rule is true, otherwise 0". So `rate_up = @logic ? 1 : 0` with
  `rate_down = @logic ? 0 : 1` is a node that follows its rule at rate 1 in each direction. That is Calzone's default.
- Rates are per **Calzone unit**, an abstract time unit: the network has no seconds of its own. Most steps have rate 1,
  so one step takes one unit on average. How long a unit is in real time is set by the death clock, `k_time`, the number of
  Calzone units per second: one unit lasts $1/k_\text{time}$ seconds ({doc}`../design/time`).
- `$TransRate` marks the slow steps that need new protein to be made: NF-κB's target genes, and cIAP. In Calzone's
  MaBoSS example it is 1/24, so they take 24 units on average.
- `$Low_CASP8`, `$Low_RIP1`, `$Low_cIAP` and `$High_NFkB` are Calzone's mutant switches: set to 1, they hold a node off
  (switch-on rate 0, switch-off rate effectively infinite) or on. They are 0 in the composite and the studies; the
  `transcription-anchor` checks ({doc}`../verification/index`) set `$High_NFkB = 1` to hold NF-κB on.

Which node switches next, and when, is random. The engine, MaBoSS, simulates that random sequence
({doc}`../math/maboss`). Running many cells (many random sequences) gives the fraction that ends in each fate.

## The three routes

TNF binding its receptor starts all three at once.

**Survival.** TNFR → RIP1 → RIP1ub (needs cIAP) → IKK → NFkB. Active NF-κB orders new protein: cFLIP, BCL2, mXIAP
(→ XIAP), mcIAP (→ cIAP), and the Survival phenotype node. Each of these is a `$TransRate` step, so the survival route
is slow at its end.

**Apoptosis.** TNFR with FADD forms DISC_TNF → CASP8 → BAX → MOMP → Cyt_c (and SMAC) → apoptosome (needs ATP) → CASP3
→ the Apoptosis phenotype. Every step has rate 1, so this route is fast.

**Necrosis.** RIP1 → RIP1K → ROS, which builds up only while mROS is on, that is while NF-κB's antioxidant genes are
*not* expressed (`mROS = NOT NFkB`). ROS → MPT (unless BCL2 is on) → ATP is lost → the NonACD phenotype.

**Where they cross.** The routes block one another, which is what makes the decision:

| Interaction | Effect |
|---|---|
| CASP8 cleaves RIP1 (`RIP1 = … AND NOT CASP8`) | apoptosis shuts the survival and necrosis routes at their start |
| CASP3 blocks NF-κB (`NFkB = IKK AND NOT CASP3`) | the executioner caspase stops NF-κB |
| SMAC removes XIAP and cIAP | mitochondria releasing SMAC lift two brakes on death and cut RIP1ub |
| cFLIP blocks CASP8; BCL2 blocks BAX and MPT; XIAP blocks CASP3 and the apoptosome | NF-κB's products are the brakes on death |
| NF-κB keeps cIAP made (NFkB → mcIAP → cIAP) | NF-κB sustains its own route |
| MPT collapses ATP; the apoptosome needs ATP | necrosis pre-empts apoptosis |

## Why held TNF mostly kills

The survival route ends in steps that take 24 units on average (`$TransRate` = 1/24). The apoptosis route is seven
steps of one unit each from the bound receptor to caspase-3 (DISC_TNF, CASP8, BAX, MOMP, Cyt_c, apoptosome, CASP3). So in most cells caspase-8 is active long before cFLIP has been made to block it, and
caspase-8 then cleaves RIP1, which closes the survival route. With TNF held on and Calzone's own rates, the network gives
apoptosis 0.953, necrosis 0.029 and survival 0.014 at t = 40 units (the unmodified network on the MaBoSS engine,
200,000 cells: the oracle of the `coupled-equals-full` check, {doc}`../verification/index`). That race between a fast death route and slow protection is the question every
study in this project varies ({doc}`../design/time`, {doc}`../design/calibration`).

## Every node

Generated from the pinned network file (`raw/cellfate.bnd`, MaBoSS's copy of Calzone's model) and its initial states
(`raw/cellfate.cfg`, which sets TNF off; the table shows it on, because every run here switches TNF on). *Read by* lists the nodes whose rule uses this node. *Composite* says how
the composite changes the node ({doc}`../design/boolean`); in addition, every rate is multiplied by `$k_time`.

```{include} _calzone_nodes.md
```

Three things to notice in the table:
- **Apoptosis, NonACD and Survival are read by no node.** They are outputs: the network's decision, not part of it. So
  changing how they switch off (absorbing death, {doc}`../design/boolean`) cannot change any other node.
- **cIAP switches off only when SMAC is on** (`rate_down = ($Low_cIAP ? 1e+100 : ((SMAC) ? 1 : 0))`), not when its
  rule fails: cIAP is removed by SMAC, not lost when mcIAP stops.
- **TNF's rule is itself** (`logic = TNF`), so in Calzone's network TNF stays as it starts. The composite replaces it
  with an input driven by the receptor signal.

```{note}
Regenerate the table after any change to the network or to `workspace/datasets/calzone2010_cellfate/prep.py` (the script that writes the
composite's version of the network; {doc}`../design/architecture`):
`uv run --project compose python -I documentation/science/code/calzone_network.py`. Its `--check` mode fails when the
committed table is stale.
```
