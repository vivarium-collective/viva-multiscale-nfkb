# Study 1: can NF-κB protect cells in the composite?

Study 0 ({doc}`calibration`) found that under held, saturating TNF the composite kills nearly every cell. Cells in
experiments behave differently: with working NF-κB, most survive TNF alone, and they die when NF-κB or protein
synthesis is blocked. Two sources support this, recorded on the investigation as proposed inputs pending the project
lead's acceptance (Micheau & Tschopp 2003; Lee et al. 2016; {doc}`../reference/bibliography`). Study 1 (decision 29)
asks whether the composite can reproduce that pattern using only the published models' own parameters, and if not,
where the limit lies. It adds no mechanism.

The study is `workspace/investigations/tnf-fate-in-space/studies/s1-survival-validation/`. Its scripts are `phase_a.py`
and `phase_b.py`, and its results are in `data/`.

## The standard

- **NF-κB intact:** most cells survive held TNF.
- **NF-κB knocked out:** most cells die (the negative control).

NF-κB is knocked out by setting the NF-κB node's switching speed κ to 0, so the node never switches on
({doc}`coupling`). In Calzone's network alone the equivalent is $u_\text{NFkB} = 0$, $d_\text{NFkB} = 1$.

## Phase A: Calzone's network alone

The question: can Calzone's wiring ever let most cells survive held TNF? The protective genes' induction speed
(TransRate) is swept far past MaBoSS's example. Fates are read at t = 40 Calzone units, 50,000 cells per point.

| TransRate (per unit) | 1/24 | 1/4 | 1 | 4 | 16 | 64 |
|---|---|---|---|---|---|---|
| Survival, NF-κB intact | 0.014 | 0.087 | 0.201 | 0.286 | 0.313 | 0.320 |
| Survival, NF-κB knocked out | 0 | 0 | 0 | 0 | 0 | 0 |

Survival rises with induction speed but saturates near 32%, close to the Calzone paper's own ~30%. The reason is
upstream of the genes. With every step on one clock, caspase-8 activates in two steps (TNFR + FADD → DISC → CASP8)
while NF-κB needs four (TNFR → RIP1 → RIP1ub → IKK → NFkB), and active caspase-8 cleaves RIP1, which closes NF-κB's route
({doc}`../science/calzone-network`). Fast induction cannot help a cell whose NF-κB never switches on.

That ceiling is for Calzone's network alone. In the composite, NF-κB's activation follows Lipniacki's model in seconds,
and only the death route runs on the death clock, so the composite is not bound by it.

## Phase B: the composite

The composite is the NF-κB model plus 200 fate networks, with TNF held on from rest, 24 h, absorbing death and Study 0's
seeds. It runs at four death clocks with NF-κB intact ($\kappa = \ln 2/337$ s⁻¹) and knocked out. Pairing each cell
with its knocked-out twin (same seed, {doc}`../math/statistics`) measures how many cells NF-κB itself saves:

| Clock (min per unit) | Alive, intact | Alive, knocked out | Rescued by NF-κB | Lost | Net protection | Durable survival, intact |
|---|---|---|---|---|---|---|
| 30 | 0 | 0 | 0 | 0 | 0% | 0% |
| 120 | 0.160 | 0.055 | 22 | 1 | 10.5% (p = 6×10⁻⁶) | 4.5% |
| 240 | 0.740 | 0.650 | 26 | 8 | 9% (p = 0.003) | 20% |
| 480 | 0.980 | 0.985 | 1 | 2 | −0.5% | 13.5% |

At 240 and 480 min per unit, most "alive" cells have not reached any fate within 24 h (at 480: 163 of 200 intact and
197 of 200 knocked out), so there "alive" measures delay, not survival.

## What it shows

**No death clock meets the standard.**
- At fast clocks every cell dies, with or without NF-κB.
- At slow clocks most cells, with or without NF-κB, have not decided within 24 h.
- In between, NF-κB saves at most about 10% of cells.

In Calzone's network alone, NF-κB's effect reaches 32 percentage points (Phase A). So the coupling weakens NF-κB's
protection; it does not itself cause the death.

Study 0 measured two features of the coupling that can do this:
- The NF-κB node is on only about 28% of the time once NF-κB settles, so the protective products are absent most of
  the time ({doc}`../math/statistics`, occupancy).
- The protective genes switch on at Lipniacki's $r_\text{tx}$ (35 min half-rise), while caspase-8 needs only a few
  Calzone units.

Which of these limits protection is not tested here. It is an open question ({doc}`roadmap`), and a decision for the
project lead before the dose–response (d1) and the headline studies, whose signal needs NF-κB to be able to protect.
