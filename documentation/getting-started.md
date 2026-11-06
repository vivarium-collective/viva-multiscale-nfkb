# Getting started

This page installs the environments and runs every check. What compose-api, a check, a mash-up and the registry are is
explained in {doc}`design/composite-primer`; COPASI and libRoadRunner are two independent ODE solvers, which the kinetic
checks compare.

## What you need

- [uv](https://docs.astral.sh/uv/). Every Python command here runs through it.
- A checkout of [compose-api](https://github.com/biosimulations/compose-api). The checks are scored by compose-api's
  own `compliance.evaluate` (see {doc}`verification/index`). Point `COMPOSE_API_DIR` at it; it defaults to
  `~/uchc/biosimulations/compose-api` and is only read.
- macOS (arm64 or x86-64) or Linux x86-64. libRoadRunner publishes no Linux aarch64 wheel, so Linux on arm64 cannot
  install the run environment (this is also why the workspace's linux/arm64 image build fails).

```bash
git clone https://github.com/vivarium-collective/viva-multiscale-nfkb
cd viva-multiscale-nfkb
export COMPOSE_API_DIR=/path/to/compose-api
```

## Two environments, on purpose

| Environment | Where | What it is for |
|---|---|---|
| **The run environment** | `compose/` (its own `pyproject.toml` and `uv.lock`) | Pinned to exactly what compose-api's production mash-up installs: process-bigraph 1.9.1, bigraph-schema 1.8.1, Python 3.12, and each simulator package at the commit compose-api's registry pins. Every check runs here. |
| **The workspace environment** | the repository root | The workspace package, its dashboard, and the `docs` group that builds this documentation. |

They are separate because a check that passes here must pass the same way on compose-api. The run environment
installs the same packages at the same versions the service's composed image does.

## Run every check

```bash
bash compose/check.sh harness    # compose-api's own maboss and tellurium cases: proves the harness
bash compose/check.sh kinetic    # Lipniacki vs COPASI; the pre-equilibrated steady state
bash compose/check.sh spatial    # diffusion and decay against closed-form solutions
bash compose/check.sh boolean    # MaBoSS reference, equivalence with the full network, the couplings, the clock
```

Each check prints `PASS` or one `FAIL` line per expectation it missed. The runs write to `.checks-out/<group>/<case>/`
(the runner log and the results file), which git ignores.

## Build this documentation

```bash
uv run --group docs sphinx-build -W -b html documentation documentation/_build/html
open documentation/_build/html/index.html
```

`-W` turns every warning into an error, so a broken cross-reference fails the build.
