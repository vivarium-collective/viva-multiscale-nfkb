# 4. Sweep the death clock

Gene expression is anchored to Lipniacki ($r_\text{tx} = 3.29\times10^{-4}\ \text{s}^{-1}$), and `k_time` sets how fast
everything else in the fate network runs ({doc}`../design/time`). This sweep holds NF-κB at one of Lipniacki's stimulated
values ($f = 0.5627$, 414 s after TNF) with TNF on, and runs 8 hours:

```{literalinclude} code/death_clock_sweep.py
:language: python
```

Output (20,000 trajectories):

```text
r_tx = 0.000329 /s (gene expression, fixed); 8 h of composite time
1 Calzone unit =   0.5 min:  Survival 0.000  Apoptosis 0.988  NonACD 0.012
1 Calzone unit =   2.0 min:  Survival 0.000  Apoptosis 0.958  NonACD 0.042
1 Calzone unit =  10.0 min:  Survival 0.000  Apoptosis 0.830  NonACD 0.170
1 Calzone unit =  30.0 min:  Survival 0.023  Apoptosis 0.601  NonACD 0.300
1 Calzone unit = 120.0 min:  Survival 0.122  Apoptosis 0.018  NonACD 0.074
```

## Reading it

The death clock changes both who wins and how the cell dies:
- **Fast death machinery** (half a minute to 10 minutes per unit): apoptosis dominates, before any protective gene is
  made.
- **Slower death machinery:** a growing share dies by necrosis (30% at 30 min per unit), and survival appears.
- **At two hours per unit:** most cells (about 79%) have reached no fate after 8 hours, and survival leads among
  those that have.

So the time axis is not a nuisance. It decides whether TNF's dose and arrival time can matter at all, which is why the
studies sweep it.

```{admonition} Provisional
:class: warning
In this sweep the NF-κB node's switching speed also scales with `k_time`: the open question of tutorial 2. Slower
death clocks also mean slower NF-κB flicker, which helps survival. The calibration study (Study 0) has since
separated the two: the composite now uses κ = Lipniacki's own NF-κB speed, and under held TNF nearly every cell dies at
every clock ({doc}`../design/calibration`).
```
