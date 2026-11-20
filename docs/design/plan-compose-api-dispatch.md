# Plan: running the distance study on compose-api

Status: draft 2, 2026-11-20. Alex decided that NF-κB's next studies, the distance study and then the many-cells work,
run on compose-api instead of locally (decision 54); the dose study finishes locally as it is. Alex chose route A, long
runs, and to build it without waiting on Jim ("just do this option without having to ask Jim first"); Jim has had a
heads-up. The compose-api change is planned as its release 0.7.97. Nothing is submitted beyond the one 990 s live run
per new composite until that release is live and Alex approves the first submission.

## What the study needs

- **Configurations:** 3 bolus sizes × 3 clocks × 2 arms (decisions 51 and 52), each with cells at 100, 300 and
  1000 µm: 54 ring configurations.
- **Cells:** 1,890 per ring configuration (7 batches of 270 seeds; decision 40b), so 102,060 fate networks over 24 h.
- **Simulated time:** 24 h (86,400 s) per run, the readout's horizon (decision 41).
- **What a document can share:** cells only sample the field, so every ring, clock, arm and batch for one bolus size
  can share one field. Lipniacki's model doesn't depend on the clock or the arm: both enter only in the Step that
  turns NF-κB's nuclear fraction into the fate network's NF-κB rates ($u = f\kappa/k_\text{time}$). So each ring needs
  one Lipniacki model and, for each clock and arm, its own coupling Step and the parameter store its cells share.

## What compose-api allows (0.7.96, read from its source)

| Limit | Value | Where |
|---|---|---|
| Simulated time per run | 1,000 s | `compose_api/api/routers/simulation.py:241`, hard-coded |
| Wall time per job | 30 min | `compose_api/simulation/job_script.py:34` |
| Resources per job | 2 CPUs, 8 GB (a batch submission: 1 CPU, 1 GB) | `job_script.py:189-190` |
| Resuming a run | no; the runner saves the final state as `state_<stamp>.pbg` "as a convenience" | `compose_api/environments/runner.py:168-169` |
| Ownership | a signed-in submitter owns the run, private unless `visibility=public`; the owner can change it later | `compose_api/authorization.py:152` |

A 24 h run is 86 times the simulated-time cap, and on this machine a 24 h run of the 6 mm field alone took 3.6 h, seven
times the wall-time cap. So the study can't run as one job per document under today's limits.

## Measured cost (local, single-threaded)

- The 6 mm field, 601 × 601 nodes, dt 0.25 s: 3.6 h per simulated day (`analysis/exposure-design/exposure_24h.py`).
- A population of 270 fate networks and one Lipniacki model: 8.1 min per simulated day (the dose study, 380 runs).
- **The whole study:** 102,060 cells come to about 51 CPU-hours. The field adds 3.6 CPU-hours per document that
  carries one: 11 for three documents (one per bolus size, 34,020 cells each), 75 for 21 (one per bolus size and
  batch, 4,860 cells each). Document size grows about 7 kB per cell, so 34,020 cells make about 240 MB and 4,860 make
  about 35 MB. So 21 documents is the practical packing, about 126 CPU-hours in all.

## Two routes

**A. Long runs on compose-api (chosen).** compose-api accepts runs longer than 1,000 s and 30 min: a signed-in
submitter may ask for up to a configured maximum of simulated time (anonymous runs keep 1,000 s), and only such a run
gets a longer job time, scaled to what it asks for and capped within the partition's limit.
- The study is then 21 documents, one per bolus size and batch. Each holds the field, 3 rings, a Lipniacki model per
  ring, and 4,860 fate networks (3 clocks × 2 arms × 270 × 3 rings).
- Each takes about 6 h of wall time (3.6 h of field and 2.4 h of cells), and all 21 can run at once.
- No change to the composite, and each run is one record on compose-api.

**B. Chained 990 s segments, no compose-api change.** Each document runs as 88 consecutive jobs, each starting from the
saved state of the one before.
- **The composite has to change first.** Lipniacki's state lives inside roadrunner, and TelluriumProcess's `species`
  input is unwired, so a restarted run would reset NF-κB to rest. Wiring it makes the store the state of record, but
  then roadrunner re-initialises at every interval. That adds an error at integrator tolerance, which needs its own
  check: a run chained in two halves against a straight run, everything within a stated tolerance.
- **Time restarts at 0 in each segment.** Anything that reads absolute time needs an offset. The decaying bath does,
  but it runs locally; the distance composite doesn't, which a check must confirm.
- **About 1,850 jobs:** 21 chains of 88, each segment about 4 min of computing plus queue time. Each segment's state
  has to be downloaded and resubmitted, and a failed segment stops its chain.

## In both routes

- **Environment.** The distance composite uses only the field composite's classes: FVReactionDiffusion, RegionMean,
  MathExpressionStep, TelluriumProcess, MaBoSSProcess and RAMEmitter. So compose-api infers the existing mash-up
  (`mash-bb433b1002`, version 2, viva-maboss 0.1.2) and needs no new environment. The first document's live run
  confirms it.
- **Runs are signed-in and private** while the study runs, and made public when its results are published. A public
  anonymous run has no owner, so its visibility can't be changed later.
- **One full document is measured first, locally** (plan step 5): its wall time, memory and size. The measurement
  decides how many fate networks a document can hold within 8 GB.
- **The matched decaying baths run locally** in the dose study (decision 50), so E4's two sides run in different
  places. The decaying-bath check and the far-bolus check cover each side. A compose-api run and a local run of the
  same document must agree, as the MVP's live record does (`compose/live.py`).

## Decided

- **Route A** (Alex, 2026-11-20: "long runs: please just do this option without having to ask Jim first... approved").
- **Jim gets a heads-up, not a request** (Alex: "Give him a heads up yourself in slack"). The one number left for him
  is the longest job the cluster's partition allows, which caps the long-run time limit.
