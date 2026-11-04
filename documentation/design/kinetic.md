# The kinetic layer <span class="layer kinetic">kinetic</span>

## Decisions

| Decision | Reason | Evidence |
|---|---|---|
| **Lipniacki 2004 (BIOMD0000000786)** as the core (Alex, Q1) | Two sized compartments ($K_v = 5$); one external stimulus input (`TNF := TNF_R`); curated; COPASI and Tellurium agree on it | viva-biomodels corpus screen, NRMSE 3.6e-7 |
| **Tellurium (libRoadRunner), not COPASI**, as its engine | `CopasiUTCProcess` passes counts to `setInitialConcentration`, and its `time` does not accumulate. libRoadRunner also exposes the Jacobian that d7 uses. | viva-copasi@937ff13 `processes.py:115,831`; plan F3 |
| **`bulk_species: false`** | The default `true` makes `species` a 16-element array that can't be addressed by name, and the adapters read species by name | viva-tellurium `processes.py:116` |
| **Remove the `TNF_stimulation` event; keep `TNF := TNF_R`** | In the composite the spatial layer owns the stimulus. The original model switches itself on after 101 h. | `workspace/datasets/lipniacki2004/prep.py` (refuses unless the model has exactly that one event) |
| **Pre-equilibrate separately, then seed** | Simulating 101 h of rest inside every composite run wastes time and couples the rest state to coupling intervals. The steady state is computed once (`TNF_R = 0`), checked, and seeded through `species_overrides`. | `checks/kinetic/preequilibrated-steady` |
| **A new input port, `parameters_in`** (viva-tellurium 0.2.3, U1; Alex, Q2) | `TelluriumProcess` took species inputs only. Its `parameters` port is an output, and `parameter_overrides` apply once, at build. So nothing could drive `TNF_R` during a run. | viva-tellurium#37, 22 tests on real roadrunner; 18 of them fail on 0.2.2 |

## The driven model

`prep.py` writes `processed/lipniacki2004_driven.xml` (sha256 `e3d357b9…`), the curated model minus its one event.
Nothing else changes:
- the rule `TNF := TNF_R`;
- `TNF_R`'s initial value of 0;
- every reaction and parameter.

## Checks

- **`checks/kinetic/sim1-original`:** the unmodified model in `TelluriumProcess` matches COPASI's `sim1` trajectory.
  That's every floating species, at the last pre-stimulus point and every post-stimulus point (113 expectations), from
  another engine's output.
- **`checks/kinetic/preequilibrated-steady`:** seeded with the saved steady state and left unstimulated, the driven
  model holds that state for 10 h (rel 1e-6). The state also equals COPASI's `sim1` state just before the original
  stimulus (rel 1e-3).

## What the kinetic layer tells the others

Lipniacki conserves total NF-κB. In the curated SBML,
$\text{NFKB\_total} = \text{IKKactive\_IkB\_NFKB} + \text{NFKB} + \text{IkB\_NFKB} +
(\text{NFKB\_nuc} + \text{IkB\_NFKB\_nuc})/K_v$, and it stays 0.06 µM through the whole stimulated run. Its free
nuclear fraction $f = (\text{NFKB\_nuc}/K_v)/\text{NFKB\_total}$ is what the Boolean layer reads ({doc}`coupling`).
