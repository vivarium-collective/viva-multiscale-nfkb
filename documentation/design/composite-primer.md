# Composites and checks: a primer

The composite is a [process-bigraph](https://github.com/vivarium-collective/process-bigraph) document, and every
claim about it is checked by running documents through compose-api. This page defines the vocabulary the design pages
use. The semantics described are those of the pinned engine (process-bigraph 1.9.1, bigraph-schema 1.8.1).

## A composite is a document

A composite is one nested document (JSON) holding two kinds of things:

- **Stores** hold state: a number, a map of numbers, a nested group. Each has a **type** (`float`, `map[float]`, ...)
  that says how it is updated.
- **Processes** and **steps** compute. Each is an entry with:
  - `address`: the class that does the work, for example `local:viva_maboss.processes.MaBoSSProcess`;
  - `config`: its fixed settings, such as the network file and the seed;
  - `inputs` and `outputs`: its **ports**, each **wired** to a store by a path such as `["parameters", "u_NFkB"]`.

So a process never knows where its data lives. It reads its input ports and returns values for its output ports, and the
document's wiring decides which stores those are. The same process can be wired into different composites unchanged.

## Processes and steps

- A **process** advances in time. It has an `interval` in seconds. Every interval it reads its inputs and returns an
  **update** covering that span. `TelluriumProcess` (the NF-κB model) and `MaBoSSProcess` (the fate network) are
  processes.
- A **step** has no interval. It runs whenever one of the stores it reads is written to (even if the value does not
  change; a write to a whole map does not trigger a step that reads one of its keys, {doc}`coupling`), and turns inputs into outputs at
  once. The **adapters** that translate one layer's quantity into another's are steps. For example, a
  `MathExpressionStep` computes NF-κB's nuclear fraction $f$ from the kinetic layer's species and writes the fate
  network's switching rates ({doc}`coupling`).

## Updates and types

A process does not set a store; it returns an update, and the store's type says how the update is applied:

- for a `float`, the update is a **delta**, added to the current value. That suits quantities that change by amounts;
- for `overwrite[float]`, the update **replaces** the value. That suits quantities that are *set*, such as the TNF
  signal written into the kinetic model's `TNF_R`.

A writer that sets a value must declare `overwrite`. Otherwise its value is added to the store again on every update.
The pinned engine also drops a write to a map key the store does not hold yet. Both rules are spelled out where they
apply ({doc}`coupling`).

## Time and results

- The composite runs to an end time. Each process advances on its own interval. The composite's coupling interval, 30 s
  in the studies, is the interval its processes share, so they exchange values every 30 s. It satisfies the rule in
  {doc}`../math/timescales`: $f$ changes fastest during its 337 s half-rise, and $0.1 \times 337 \approx 34$ s.
- An **emitter** is a step that records chosen stores each time the composite advances. Its records, one row per time point, are
  the run's results file. Row 0 is the state at t = 0, before any process has run.

## compose-api, and how a check is run

**compose-api** is the BioSimulations service that runs process-bigraph documents (`compose.cam.uchc.edu`):

- **It runs a document** with its own `runner.py`, in a container on an HPC cluster.
- **The environment** is a **mash-up**: one environment that compose-api builds by installing the packages that
  provide the document's processes, for example viva-tellurium and viva-maboss.
- **The registry** decides which packages it may install: a manifest of entries, each pinned to a commit and given a
  curation level. A process can run only if its entry is at level `tested` or higher.

A **check** (a compliance case) is a folder holding three things:
- a document;
- an interval;
- `case.yaml`, which lists **expectations**: a value in the results, the expected value, and a tolerance.

compose-api's `compliance.evaluate` scores the results file against the expectations.

Every check in this project has two more properties:
- **An independent oracle.** The expected values come from a different engine, an upstream reference run, or an
  analytic formula ({doc}`../math/index`), never from the code under test.
- **A proven-failing negative, where recorded.** The check was run once with a deliberate defect and shown to fail
  ({doc}`../verification/index`).

**Running checks locally.** `compose/check.sh <group> [<case>]` runs a case exactly as compose-api does:
- it uses compose-api's own runner, copied into this repository;
- it runs in `compose/`, an environment pinned to the same packages as the production mash-up;
- it scores with `compliance.evaluate` from a compose-api checkout.

Two of compose-api's own cases, copied unchanged into `checks/harness`, show that the local result matches the live
one ({doc}`../getting-started`).
