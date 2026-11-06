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
1 Calzone unit =   0.5 min:  Survival 0.000  Apoptosis 0.991  NonACD 0.018
1 Calzone unit =   2.0 min:  Survival 0.000  Apoptosis 0.968  NonACD 0.066
1 Calzone unit =  10.0 min:  Survival 0.000  Apoptosis 0.874  NonACD 0.243
1 Calzone unit =  30.0 min:  Survival 0.024  Apoptosis 0.683  NonACD 0.394
1 Calzone unit = 120.0 min:  Survival 0.122  Apoptosis 0.019  NonACD 0.075
```

The sweep runs the composite's network with absorbing death (`absorb_death = 1`, {doc}`../design/boolean`): once
Apoptosis or NonACD switches on, it stays on. So each death column is the probability that the cell has shown that
fate by 8 h. A cell can show both, because caspase-3 and ATP loss can occur together, so the columns are never
summed.

## Reading it

Here the death clock changes both who wins and how the cell dies. It can change who wins because gene expression stays
on Lipniacki's clock while `k_time` moves only the death machinery; a uniform sweep of every rate would not
({doc}`../design/time`):
- **Fast death machinery** (half a minute to 10 minutes per unit): apoptosis dominates, before any protective gene is
  made.
- **Slower death machinery:** a growing share shows necrosis (39% at 30 min per unit), and survival appears.
- **At two hours per unit:** within 8 hours only 2% of cells have shown apoptosis and 7.5% necrosis, while 12% show
  survival. Eight hours is only four Calzone units at this clock, so most cells have not yet reached a fate.

So the time axis is not a nuisance. It decides whether TNF's dose and arrival time can matter at all, which is why the
studies sweep it.

```{admonition} Provisional
:class: warning
In this sweep the NF-κB node's switching speed also scales with `k_time`: the question tutorial 2 discusses, which Study 0 has since settled. Slower
death clocks also mean slower NF-κB flicker, which helps survival. The calibration study (Study 0) has since
separated the two: the composite now uses κ = Lipniacki's own NF-κB speed, and under held TNF nearly every cell dies at
every clock ({doc}`../design/calibration`).
```
