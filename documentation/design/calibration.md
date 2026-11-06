# Study 0: calibrating the coupling

The composite joins two models that keep time differently. Lipniacki's NF-κB model runs in seconds. Calzone's
cell-fate network runs in abstract units. Two speeds can't be read from either model alone, so Study 0 measures their
effect before the headline studies ({doc}`studies`) run on the composite:

- **κ, how fast the Boolean NFkB node follows Lipniacki's NF-κB** ({doc}`coupling`, {doc}`../math/switch`).
- **`k_time`, how fast the death machinery runs** ({doc}`time`): one Calzone unit per 2, 10, 30 or 120 minutes.

The study lives in the workspace as
`workspace/investigations/tnf-fate-in-space/studies/s0-coupling-calibration/`. Its `study.yaml` holds the design,
every run and the findings. `run_grid.py` and `population.py` build and run it, and `analysis.py` makes the tables
quoted here.

## Design

| Choice | What | Why |
|---|---|---|
| Population | 1 deterministic kinetic layer, 200 independent stochastic fate networks (one MaBoSS trajectory each, own seed) | Lipniacki is deterministic, so every cell sees the same NF-κB. The cells differ only in their fate network's random draws, so fractions are fractions of cells. |
| Stimulus | TNF switched on at t = 0 and held at saturation | The simplest stimulus. It is the case Calzone's own network was built for. |
| Duration | 24 h of model time at every clock (Alex: "24 hours everywhere") | At 8 h, 77–85% of cells were still undecided at the slowest clock. |
| Readout | Each cell's fate code every 30 s: Survival + 2·Apoptosis + 4·NonACD | Calzone's fate nodes are not mutually exclusive: a cell can show caspase-3 and ATP loss together. A first 8 h grid summed them as if they were exclusive, double-counted, and was discarded. |
| Classification | **End state** at 24 h, with **first fate** alongside | Survival follows NF-κB, so it is not final: a cell can show Survival first and die later. **Durable survival** means Survival on and no death node at 24 h. |
| Seeds | Every variant reuses the grid's 200 seeds | Differences between runs then come from the change, not from new random draws. Variants are compared with the grid **cell by cell** (exact McNemar test), which an adversarial review showed is needed. Comparing two fractions as if independent hid a consistent shift. |
| Environment | The workspace's pinned `compose/` environment, through compose-api's own runner; the workbench only records the runs (Alex: "Pinned env; workbench records") | The results are what compose-api would produce in production. |

## What it found

End state at 24 h, κ = Lipniacki's NF-κB speed, against Calzone's own network on the MaBoSS engine. Apoptosis and
necrosis can overlap, so the columns don't sum to "dead".

| Clock (min per Calzone unit) | Dead | Apoptosis | Necrosis | Durable survival | No fate yet | Median first fate |
|---|---|---|---|---|---|---|
| 2 | 1.000 | 0.935 | 0.065 | 0 | 0 | 18 min |
| 10 | 1.000 | 0.790 | 0.210 | 0 | 0 | 76 min |
| 30 | 1.000 | 0.690 | 0.310 | 0 | 0 | 205 min |
| 120 | 0.765 | 0.455 | 0.355 | 0.060 | 0.175 | 658 min |
| Calzone alone, t = 40 units, TransRate 1/24 | | 0.953 | 0.029 | 0.014 | | |

1. **Held, saturating TNF kills nearly every cell.** This holds at every κ and every clock: durable survival is 0–6%.
2. **Calzone alone also kills nearly every cell, but the split differs.**
   - At 2 min per unit, the composite's genes switch on at about Calzone's own TransRate (1/25 against 1/24).
   - There it gives no survivors in 600 cells, where Calzone's 1.4% predicts about 8. It also gives more necrosis
     (5–8.5% against 2.9%).
   - The difference is the coupling. Calzone's NFkB switches on fast and stays on while its gate is open. The coupled
     node flips on and off around Lipniacki's fraction $f$ ({doc}`coupling`).
3. **The clock decides how cells die, not whether.** Slowing the death machinery moves death from apoptosis to
   necrosis. The first fate arrives after about 5–9 Calzone units at every clock.
4. **κ hardly matters.** No κ gives durable survival at 2–30 min per unit, and κ moves the apoptosis/necrosis split by
   at most 0.135.
5. **NF-κB's protection is brief.** NF-κB peaks at $f = 0.933$ at 24 min, drops to 0.020 at 80 min, and settles at 0.28
   after about 6 h. Of the cells that show Survival first, 57–100% die later. The death arms never pause under TNF.
   - At fast clocks, cells die before the protective products can be made: those switch on with a 35-min half-rise.
   - At slow clocks, the protective products' logic keeps failing, because the coupled node is off about 72% of the
     time once $f$ settles.

   Both readings are hypotheses that Study 0c tests.
6. **Calzone's gates are not the main barrier.** Removing them is the gate knockout: no caspase-8 cleavage of RIP1, and
   no SMAC sequestration of cIAP.
   - It keeps 22–27% of cells alive at 24 h (45 and 54 of 200), but durable survival reaches only 2.5–5%.
   - Removing only the RIP1 cleavage turns every death into necrosis.

## Decision: κ

**κ = ln 2 / 337 s, Lipniacki's own NF-κB speed** (Alex, 2026-11-06).
- **Where it comes from:** 337 s is the half-rise of nuclear NF-κB after TNF in Lipniacki's model, so κ is measured,
  not fitted.
- **Why not Calzone's flicker (κ = `k_time`):** it ties NF-κB's speed to the assumed speed of the death machinery,
  which has no biological basis.
- **Why not the slower bracket (ln 2 / 2107 s, the NF-κB → protein delay):** it applies the transcription delay a
  second time, because the genes already carry it.
- **What the data say:** at slow clocks this κ gives the most early survival, and nowhere does it change durable
  survival.

## Study 0b: a confounded test, and what it taught

**The question.** Do NF-κB's protective proteins vanish between NF-κB's waves? Calzone switches a gene product off at
its unit rate once its logic fails, so at fast clocks they vanish within minutes.

**The test.** Alex chose to anchor that decay to Lipniacki's measured protein turnover: A20's degradation constant,
$3\times10^{-4}\ \text{s}^{-1}$, a 38.5 min half-life.

**The result.** As run, the test was **confounded**. Besides the protective products, the edit also slowed:
- **mROS.** mROS is on when NF-κB is *off* (`NOT NFkB`), and it licenses ROS, which drives necrosis.
- **Survival.** This is the readout node, not a protein.

Cell by cell, both artefacts show:
- every fast-clock pair shifts toward necrosis (9 of 9 changed cells at 2 min per unit, p = 0.004);
- at 120 min per unit durable survival *falls*, from 12 cells to 2 (p = 0.006). That is where Lipniacki's turnover
  is faster than Calzone's switch-off, so the Survival node itself decayed faster.

**The lesson for the composite.** "NF-κB target" is not the same as "protective". Each edit to Calzone's network is now
limited to nodes whose biological role is the one the edit is about.

## Study 0c: the persistence bound

Alex chose to bound the question before rerunning the decay test.

**The edit.** NF-κB's four protective products never switch off once made:
- cFLIP, which blocks caspase-8;
- BCL2, which blocks the mitochondrial death steps;
- mXIAP and mcIAP, the transcripts of XIAP and cIAP.

**What it leaves alone:**
- mROS and Survival;
- XIAP and cIAP themselves, which still switch off when SMAC removes them, because that is regulation, not turnover.

This is an upper bound, not a model. It runs at κ = Lipniacki's NF-κB speed, at the four clocks, on the grid's seeds.

**How to read it:**
- **Survival rises.** Persistence is a lever. A corrected decay test, limited to the protective products, then places
  Lipniacki's turnover on that scale.
- **Survival stays near zero.** No amount of persistence lets NF-κB win the race under held TNF. The headline studies
  then rest on exposure instead: whether, when and for how long each cell senses TNF.

**Result:** running.

## What it means for the headline studies

A held, saturating dose cannot show NF-κB protection in this composite. Unless 0c finds a lever, TNF's dose and timing
can change a cell's fate only through exposure: how much TNF reaches it, when, and for how long. In the tissue, that
is exactly what space decides ({doc}`studies`). The receptor dose–response (d1, McMillan 2021) is the next layer it
needs.
