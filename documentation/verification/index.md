# Verification

## The rule

A check counts as evidence only if it could fail. Every check here:

1. **Runs the real engines.** It never mocks the thing in doubt: MaBoSS, libRoadRunner and the FV solver all run for
   real.
2. **Has an oracle independent of the code under test:**
   - an analytic solution;
   - another engine's output;
   - the upstream project's own reference output;
   - an exact equivalence against the unreduced model.
3. **Has a proven-failing negative.** A mutated copy (a wrong expected value, a wrong rate, a wrong reduction) was run
   and failed on exactly the expectation it should. The negatives are listed below.

## How a check runs: exactly as compose-api runs it

`compose/check.sh <group> [<case>]`:

1. Reads `checks/<group>/<case>/case.yaml`, which is compose-api's compliance-case format.
2. Runs the case's document through **compose-api's own `runner.py`**, vendored byte for byte at compose-api 0.7.78
   (`compose/RUNNER_SOURCE`). It runs in `compose/`'s environment, pinned to the production mash-up.
3. Scores the results file with **compose-api's own `compliance.evaluate`**, read from a compose-api checkout
   (`COMPOSE_API_DIR`).

**The harness proves itself.** `checks/harness` holds two of compose-api's own compliance cases, copied unchanged. Both
pass here as they pass live (production runs 9825 and 9828). With one expected value changed, the MaBoSS case fails on
exactly that value.

## Catalogue

| Check | What it shows | Oracle | Negative proven to fail |
|---|---|---|---|
| `harness/maboss-oracle` | the harness reproduces compose-api's verdict | analytic switch | expected 0.70: fails on that value |
| `harness/tellurium-phase-cycle` | the same, for Tellurium | COPASI's report | — |
| `kinetic/sim1-original` | Lipniacki in `TelluriumProcess` = COPASI's `sim1` | another engine (corpus) | — |
| `kinetic/preequilibrated-steady` | the saved rest state is a steady state and matches COPASI before the stimulus | corpus | — |
| `spatial/gaussian-diffusion` | FV diffusion of a Gaussian bolus | closed form | — |
| `spatial/uniform-bath-decay` | a uniform bath stays uniform and decays | closed form | — |
| `boolean/calzone-reference` | `MaBoSSProcess` = MaBoSS's own reference run of Calzone, all 31 nodes | upstream reference + analytic mROS | mROS expected 0.30: fails; TransRate 1/12: fails on mROS |
| `boolean/reduction-high-nfkb` | the cut is exact with NF-κB forced on | full network on the MaBoSS engine | dropping cFLIP: CASP8 1.0 vs 0.21 |
| `boolean/reduction-nfkb-knockout` | the cut is exact with NF-κB knocked out; death arms intact | full network on the MaBoSS engine | the first plan's cut: apoptosis 0 vs 0.91 |
| `boolean/pair-nfkb-analytic` | kinetic → Boolean coupling through Lipniacki's own NF-κB rule | analytic switch | $K_v = 4$; an unseeded `parameters` store |
| `boolean/pair-nfkb-seconds` | `$k_time` converts time and nothing else | the same analytic value | clock unconverted: 0.562 vs 0.483 |
| `boolean/transcription-anchor-fast`, `-slow` | target genes keep Lipniacki's clock at any `k_time` | analytic absorbing switch | uniform clock: 0.014 vs 0.491 |

"—" means a negative for that check is not yet recorded in this documentation.

## Generated, not hand-written

Every case is written by a script beside it (`checks/<group>/make_*.py`), which computes its expected values from the
oracle: the reference file, the corpus or the closed form. Re-running the script regenerates the case exactly.
