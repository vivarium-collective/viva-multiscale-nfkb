# 4. Sweep the death clock

Gene expression is anchored to Lipniacki ($r_\text{tx} = 3.29\times10^{-4}\ \text{s}^{-1}$), and `k_time` sets how fast
everything else in the fate network runs ({doc}`../design/time`). This sweep holds NF-κB at Lipniacki's post-stimulus
fraction ($f = 0.5627$) with TNF on, and runs 8 hours:

```{literalinclude} code/death_clock_sweep.py
:language: python
```

Output (20,000 trajectories):

```text
r_tx = 0.000329 /s (gene expression, fixed); 8 h of composite time
1 Calzone unit =   0.5 min:  Survival 0.000  Apoptosis 1.000  NonACD 0.000
1 Calzone unit =   2.0 min:  Survival 0.000  Apoptosis 1.000  NonACD 0.000
1 Calzone unit =  10.0 min:  Survival 0.014  Apoptosis 0.958  NonACD 0.009
1 Calzone unit =  30.0 min:  Survival 0.323  Apoptosis 0.353  NonACD 0.165
1 Calzone unit = 120.0 min:  Survival 0.611  Apoptosis 0.008  NonACD 0.035
```

## Reading it

The race has a winner that depends on the death clock:
- **Fast death machinery** (a unit of half a minute to two minutes): death wins before any protective gene is made.
- **Slow death machinery** (two hours a unit): the genes arrive first, and most cells survive.
- **Around half an hour a unit:** all three fates occur. That is the regime in which TNF dose and arrival time can
  tip the balance, and so where the headline studies have something to find.

```{admonition} Provisional
:class: warning
In this sweep the NF-κB node's switching speed also scales with `k_time`: the open question of tutorial 2. Slower
death clocks also mean slower NF-κB flicker, which helps survival. The calibration study (Study 0) separates the two
effects before these numbers are used.
```
