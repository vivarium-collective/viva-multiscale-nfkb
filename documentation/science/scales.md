# Scales: what makes this multiscale

"Multiscale" here means two things, and the design has to respect both.

## Scales of organisation

| Scale | Layer | State |
|---|---|---|
| Tissue / extracellular medium (µm) | <span class="layer spatial">spatial</span> | a TNF concentration field on a grid |
| Cell compartments (cytoplasm, nucleus) | <span class="layer kinetic">kinetic</span> | 16 molecular concentrations (µM), continuous and deterministic |
| Cell phenotype | <span class="layer boolean">Boolean</span> | 31 on/off nodes; a probability distribution over fates |

The layers don't share state. Each quantity is written by exactly one layer, and the adapters translate it for the
layer that reads it. {doc}`../design/architecture` gives this rule ("one owner") and its reason.

## Scales of time

Measured unless marked. The NF-κB model's fastest and slowest modes and its oscillation come from its Jacobian
({doc}`../math/timescales`, computed by `analysis/d7/kinetic_timescales.py`); the half-rise and the NF-κB → A20 delay
come from simulating it (`anchor_transcription.py`); the others come from {doc}`../design/time` and {doc}`../design/rule-based`:

| Process | Timescale |
|---|---|
| TNF diffusion across 40 µm ($D \approx 100\ \mu\text{m}^2/\text{s}$, measured for fluorescently labelled TNFα in solution by fluorescence correlation spectroscopy; Wu et al. 2011, a source proposed to the project lead and not yet accepted) | about 4 s ($L^2/4D$, the time for a mean squared displacement of $L^2$ in two dimensions) |
| TNF–receptor binding ($k_\text{off} = 0.01\ \text{s}^{-1}$) | ~100 s |
| Fastest kinetic mode (Jacobian of Lipniacki) | ~6 s |
| NF-κB nuclear half-rise after TNF | 5.6 min |
| NF-κB damped oscillation (least-damped pair, from 2 h after TNF) | period 98–102 min, e-folding 55–90 min |
| NF-κB → target protein (A20) | 35.1 min |
| Slowest kinetic mode | 8000 s (2.2 h): IKK turnover, exactly $1/K_\text{deg}$ |
| Cell death | hours; its clock is the swept axis `k_time` |

These span about four orders of magnitude. That spread is why each layer runs on its own interval, and why the
coupling intervals are set by what crosses each edge rather than by the fastest process anywhere
({doc}`../design/time`).
