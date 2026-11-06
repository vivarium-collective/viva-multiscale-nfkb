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
  ({doc}`../math/statistics`). It is the number of cells alive only with NF-κB, minus those alive only without it.
- **The comparator.** In the composite, the protective genes switch on at $r_\text{tx}$ per second and every other rate,
  including NF-κB's whole activation route (TNFR, RIP1, RIP1ub, IKK), runs on the death clock `k_time`. Only the final
  NF-κB node follows Lipniacki directly. So at a death clock of $m$ minutes per Calzone unit, the composite's fate
  network is Calzone's network with TransRate $r_\text{tx} \cdot 60m$ per unit, read after $24 \cdot 60/m$ units.
  Phase A runs Calzone's network alone at exactly those settings, as the like-for-like comparison.

## Phase A: Calzone's network alone

Speeding up the protective genes, read at t = 40 units (20,000 cells):

```{include} _validation_phase_a.md
```

Survival saturates near 25%: even infinitely fast genes cannot save most cells. The reason is upstream. NF-κB's
activation route takes four steps (TNFR → RIP1 → RIP1ub → IKK → NFkB) and caspase-8's takes two (TNFR + FADD → DISC →
CASP8). Active caspase-8 cleaves RIP1, which closes NF-κB's route ({doc}`../science/calzone-network`), so most cells
never switch NF-κB on.

## Phase B: the composite, NF-κB intact against knocked out

The composite runs held TNF from rest for 24 h, with 200 cells on Study 0's seeds. Net protection is in percentage
points; p values are exact McNemar, uncorrected for six comparisons:

```{include} _validation_phase_b.md
```

## Against Calzone alone at the same settings

Phase A also ran Calzone's network alone at each clock's matched TransRate and read time (20,000 cells, so its own
standard error is below 0.004 and is not shown). The composite's values carry ± one standard error over its 200
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
- **No clock meets the standard with real survival.** At 200 min per unit, most intact cells are alive (0.550) and
  most knocked-out cells are dead. But 54 of the 110 alive intact cells have reached no fate at all, and only 18 held
  Survival through the last 2 h. That is delay, not protection. 24 h is only 3 to 12 Calzone units at the clocks from 120 to 480 min per unit.

The limit is the race in Calzone's network between caspase-8 and NF-κB's activation route, which in the composite runs
on the death clock. Lipniacki's model, however, already times that same activation: nuclear NF-κB's half-rise is 337
s. A model-native change would put NF-κB's activation route on Lipniacki's clock, as $r_\text{tx}$ already does for the
genes, so that at slow death clocks NF-κB activates before caspase-8. It is an open question for the project lead
({doc}`roadmap`), to be tested as a Study 1 variant before any change to the model.
