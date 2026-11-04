# multiscale-nfkb

<!-- BEGIN:badges -->
<!-- `vivarium-workbench gen-readme` fills this with CI / read-only workbench / license
     badges once the repo is on GitHub (URLs derived from the git remote). Run
     `vivarium-workbench gen-readme --workspace .` to refresh. -->
<!-- END:badges -->

A multiscale process-bigraph composite of how a cell decides its fate after TNF stimulation. It couples a Boolean
cell-fate network (MaBoSS), an NF-κB signalling model (Lipniacki 2004, BioModels BIOMD0000000786, on Tellurium) and
the TNF concentration field around the cell (viva-pde-particle). NF-κB is *nuclear factor kappa-light-chain-enhancer
of activated B cells*, the transcription factor TNF switches into the nucleus. Scaffolded from
[viva-template](https://github.com/vivarium-collective/viva-template).

## Why this workspace exists

This workspace exists in large part because of a specific step in
[compose-api](https://github.com/biosimulations/compose-api), the BioSimulations service that runs process-bigraph
documents on HPC: the onboarding of the **multi-framework viva workspace simulator packages**.

- **The onboarding.** On 2026-11-04 compose-api added seven viva simulator packages to its registry at level
  `tested` ([compose-api#499](https://github.com/biosimulations/compose-api/pull/499)). They span five modelling
  frameworks:

  | Framework | Package |
  |---|---|
  | ODE/SBML | viva-copasi, viva-tellurium |
  | flux balance (FBA) | viva-cobra |
  | Boolean | viva-maboss |
  | rule-based | viva-nfsim |
  | spatial | viva-smoldyn, viva-fenics |

  Each one passed its compliance case in a real composed environment.
- **Combining frameworks in one run.** compose-api already infers a combined environment, a "mash-up", from a
  document's process addresses (its environment-composition plan, D7). Since
  [compose-api#501](https://github.com/biosimulations/compose-api/pull/501) (release 0.7.78), that works for these
  packages too, so a single document can mix frameworks and run as one job. The same day, all seven compliance cases
  passed on production (compose.cam.uchc.edu, 0.7.78), each in its own inferred mash-up.
- **What this workspace adds.** Onboarding proved each framework on its own. This workspace builds one model that
  spans scales from several of the newly onboarded frameworks: Boolean, ODE, and the spatial PDE layer. It needs no
  new registry entry, because it runs in a mash-up of viva-maboss, viva-tellurium, viva-pde-particle and
  viva-basic-processes.
- **Gaps it exposed,** each fixed upstream rather than worked around here:
  - **Kinetic layer:** Tellurium could not take parameter values from another layer during a run. The fix is a
    `parameters_in` port on viva-tellurium.
  - **Spatial layer:** the spatial package had no way to turn a field into one concentration at the cell. The fix is
    `RegionMean`/`RegionTotal` in viva-pde-particle.
  - **Not used, by finding:**
    - viva-smoldyn takes no inputs.
    - viva-fenics meshes only the unit square.
    - viva-nfsim drops bound complexes between intervals.

The design record, including what was ruled out and why, is in [`docs/design/`](docs/design/). The plan is
[`plan-section-b.md`](docs/design/plan-section-b.md).

## Layers

| Layer | Engine (registry entry) | What it owns |
|---|---|---|
| Boolean cell fate | MaBoSS (`viva-maboss`): Calzone 2010 network, minus the arm the kinetic layer models | Survival / apoptosis / necrosis decision |
| NF-κB kinetics | libRoadRunner (`viva-tellurium`): Lipniacki 2004, BIOMD0000000786 | TNF → IKK → NF-κB activation and nuclear transport |
| Extracellular TNF field | finite-volume PDE (`viva-pde-particle`) | TNF diffusion around the cell |
| Adapters | `viva-basic-processes` `MathExpressionStep`; `viva-pde-particle` `RegionMean` | Unit and rate mappings between layers |

## Checks: the same verdict compose-api would give

- **The environment.** `compose/` is a uv project pinned to the production mash-up: process-bigraph 1.9.1,
  bigraph-schema 1.8.1, Python 3.12, and each entry at the commit compose-api's registry pins.
- **The runner.** `compose/check.sh <group> [<case>]` runs a check's document through compose-api's own `runner.py`,
  vendored byte-for-byte at 0.7.78 (see `compose/RUNNER_SOURCE`). It scores the results with compose-api's own
  `compliance.evaluate`.
- **The checks.** They live in `checks/<group>/<case>/case.yaml`, compose-api's compliance-case format. Every check
  has an oracle independent of the code under test, and a mutated copy that fails.
- **Scoring needs compose-api.** It uses a compose-api checkout, set with `COMPOSE_API_DIR` (it defaults to
  `~/uchc/biosimulations/compose-api`) and only read.

```bash
compose/check.sh harness   # compose-api's own maboss and tellurium cases: the harness gives their verdicts
compose/check.sh kinetic   # Lipniacki vs COPASI's sim1; the pre-equilibrated steady state
```

<!-- BEGIN:dashboard -->
<!-- `vivarium-workbench gen-readme` fills this with a one-line link to the published
     read-only workbench (<pages>/workbench/, derived from the git remote). Before the
     repo is pushed it shows a local-serve note; after the publish workflow runs
     (enable once: Settings → Pages → Source = `gh-pages`) it links the live copy. -->
<!-- END:dashboard -->

## What's inside

<!-- A short, plain description of what this workspace contains — the families of
     studies, the key composites, what a reader should look at first. The two tables
     below are generated from the workspace; this prose is yours. -->

### Composites

<!-- BEGIN:composites -->
<!-- generated by `vivarium-workbench gen-readme` — edit the source, not this table -->

| Composite | What it is |
|---|---|
<!-- END:composites -->

### Investigations

<!-- BEGIN:investigations -->
<!-- generated by `vivarium-workbench gen-readme` — edit the source, not this table -->

| Investigation | Research question |
|---|---|
<!-- END:investigations -->

## Run it locally

    bash scripts/serve.sh            # starts the workbench and opens it
    python3 scripts/lint-workspace.py

`NEXT_STEPS.md` is the full tour. The code lives in `viva_multiscale_nfkb/`;
`build_core()` in `core.py` registers the processes and composites. Working with an
AI coding assistant? `docs/first-run-agent-guide.md` takes it from a clean clone to a
running workbench.

## Building on it

[viva-superpowers](https://github.com/vivarium-collective/viva-superpowers) is the
Claude Code plugin whose skills build and extend this kind of workspace:

- `/viva-study <slug>` — start a study (Design → Build → Simulate → Evaluate → Decide).
- `/viva-investigation <slug>` — group studies under one research question.
- `/viva-expert <tool>` — wrap a simulator as a process-bigraph process or step (`--lightweight` writes in-workspace).
- `/viva-viz` — generate a visualization from a description.
- `/viva-report` — rebuild the reports.

Decide-phase studies can record `followup_proposals[]`; seed a child study from one
with `/viva-study seed-from-followup <parent>/<proposal_id>`.

## Layout

Project code lives at the repo root; research state is grouped under `workspace/`
(the `.pbg/` machine state stays at the root like `.git/`). Directory locations come
from the `layout:` map in `workspace.yaml` — edit it to move things.

- `workspace.yaml` — canonical state (validated against `.pbg/schemas/workspace.schema.json`).
- `viva_multiscale_nfkb/` — your Python package (`core.py` exposes `build_core()`).
- `scripts/` — `lint-workspace.py`, `serve.sh`, helpers.
- `workspace/studies/`, `workspace/composites/`, `workspace/references/`, `workspace/datasets/` — research artifacts.
- `workspace/notes/` — friction logs, walkthroughs, agent transcripts, ADRs. See `workspace/notes/README.md` for the
  cleanup rule: **files under `notes/` survive cleanup sweeps by default**, because they're the
  input to the next round of infrastructure improvements.
- `.pbg/schemas/` — JSON schemas the lint + dashboard validate against.

## Cleanup conventions

Cleanup PRs (`chore(cleanup): …`, `chore(repo): trim …`) routinely remove generated files,
one-shot scripts, and stale planning docs. Two locations are off-limits to bulk cleanup:

- `workspace/notes/**` — see the rule in `workspace/notes/README.md`.
- `workspace/references/notes/**` — per-paper literature notes, used by the findings protocol.

If a specific file in either location is genuinely obsolete, delete it in its own commit
with a one-line justification per file. Don't bundle with unrelated cleanup.
