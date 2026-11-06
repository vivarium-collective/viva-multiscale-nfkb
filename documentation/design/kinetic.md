# The kinetic layer <span class="layer kinetic">kinetic</span>

How the NF-κB model ({doc}`../science/lipniacki-model`) was brought into the composite, and why. Terms such as
process, port and check are defined in {doc}`composite-primer`.

## Decisions

| Decision | Reason | Evidence |
|---|---|---|
| **Lipniacki 2004 (BIOMD0000000786)** as the core (Alex) | Two sized compartments ($K_v = 5$); one external stimulus input (`TNF := TNF_R`); curated; COPASI and Tellurium agree on it | viva-biomodels' screen of BioModels: the two engines' trajectories differ by a normalised root-mean-square error (NRMSE) of 3.6e-7 |
| **Tellurium (libRoadRunner), not COPASI**, as its engine | `CopasiUTCProcess` passes molecule counts where COPASI expects concentrations (`setInitialConcentration`), and its
reported `time` restarts at each update instead of accumulating. libRoadRunner also exposes the Jacobian used for the timescale analysis ({doc}`../math/timescales`). | viva-copasi@937ff13 `processes.py:115,831` |
| **`bulk_species: false`** | The default `true` makes `species` a 16-element array that can't be addressed by name, and the adapters read species by name | viva-tellurium `processes.py:116` |
| **Remove the `TNF_stimulation` event; keep `TNF := TNF_R`** | In the composite the spatial layer owns the stimulus. The original model switches itself on after 101 h. | `workspace/datasets/lipniacki2004/prep.py` (refuses unless the model has exactly that one event) |
| **Pre-equilibrate separately, then seed** | Simulating 101 h of rest inside every composite run wastes time. The steady state is computed once (`TNF_R = 0`), checked, and given to `TelluriumProcess` as its starting concentrations (its `species_overrides` setting). | `checks/kinetic/preequilibrated-steady` |
| **A new input port, `parameters_in`** (viva-tellurium 0.2.3, a change made upstream for this project; Alex) | `TelluriumProcess` took species inputs only. Its `parameters` port is an output, and `parameter_overrides` apply once, at build. So nothing could drive `TNF_R` during a run. | viva-tellurium#37, 22 tests on real roadrunner; 18 of them fail on 0.2.2 |

## The driven model

`prep.py` writes `processed/lipniacki2004_driven.xml` (sha256 `e3d357b9…`), the curated model minus its one event.
Nothing else changes:
- the rule `TNF := TNF_R`;
- `TNF_R`'s initial value of 0;
- every reaction and parameter.

## Checks

- **`checks/kinetic/sim1-original`:** the unmodified model in `TelluriumProcess` matches COPASI's run of `sim1`, the
  simulation BioModels ships with the model (its SED-ML file, the standard format for describing a simulation
  experiment: 0 to 385,200 s, TNF switched on at 101 h).
  That's every floating species, at the last pre-stimulus point and every post-stimulus point (113 expectations), from
  another engine's output.
- **`checks/kinetic/preequilibrated-steady`:** seeded with the saved steady state and left unstimulated, the driven
  model holds that state for 10 h (rel 1e-6). The state also equals COPASI's `sim1` state just before the original
  stimulus (rel 1e-3).

## What the kinetic layer tells the others

Lipniacki conserves total NF-κB (derived and proved on {doc}`../science/lipniacki-model`). In the curated SBML,
$\text{NFKB\_total} = \text{IKKactive\_IkB\_NFKB} + \text{NFKB} + \text{IkB\_NFKB} +
(\text{NFKB\_nuc} + \text{IkB\_NFKB\_nuc})/K_v$, and it stays 0.06 µM through the whole stimulated run. Its free
nuclear fraction $f = (\text{NFKB\_nuc}/K_v)/\text{NFKB\_total}$ is what the Boolean layer reads ({doc}`coupling`).
