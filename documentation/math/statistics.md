# Statistics

The study results are fractions of simulated cells, and the variants are compared with a baseline cell by cell. This
page derives the quantities quoted with them: standard errors and intervals for a fraction, why variants reuse the
baseline's seeds, the exact McNemar test, and the quasi-steady occupancy estimate used in Study 0.

## A fraction of cells

Each simulated cell is an independent trial: its fate network runs with its own random seed ({doc}`maboss`). If a
fraction $p$ of cells would end alive in an infinite population, the number alive among $N$ cells is binomial, and the
observed fraction $\hat p = k/N$ has standard error

$$
\text{SE} = \sqrt{\frac{p(1-p)}{N}} ,
$$

which is at most $0.5/\sqrt N$: 0.035 for the studies' 200 cells, and 0.0022 for a check's 50,000.

**Intervals.** The studies' 95% intervals use the **Wilson score interval**, which stays inside $[0, 1]$ and is sensible
when $k$ is 0 or close to $N$, where $\hat p \pm 1.96\,\text{SE}$ is not:

$$
\frac{\hat p + \dfrac{z^2}{2N} \pm z\sqrt{\dfrac{\hat p(1-\hat p)}{N} + \dfrac{z^2}{4N^2}}}{1 + \dfrac{z^2}{N}},
\qquad z = 1.96 .
$$

For example, 0 alive of 200 gives $[0, 0.019]$, and 32 of 200 (16%) gives $[0.116, 0.217]$.

## Paired seeds

A variant changes one thing in the model, and the question is what that change does. If the variant ran on new random
seeds, the comparison would mix two effects: the change, and different random draws. So every variant reuses the
baseline's 200 seeds. Cell $i$ in the variant starts with exactly the same random numbers as cell $i$ in the baseline,
and any difference in its outcome follows from the change (directly, or because the change altered which random
numbers are used for what). The two runs are then **paired**, cell by cell.

Pairing makes a comparison much more sensitive. Of 200 cells, most have the same outcome in both runs. The information
is in the cells whose outcome differs, and a test that ignores the pairing dilutes it with the noise of the cells that
did not change.

## The exact McNemar test

For a yes/no outcome (for example "ever dead"), count the cells that changed:

- $b$: no in the baseline, yes in the variant (gained);
- $c$: yes in the baseline, no in the variant (lost).

If the change does nothing, each changed cell is as likely to have gone one way as the other, so $b$ is binomial with
$b + c$ trials and probability ½. The **exact McNemar test** asks how surprising the split is under that hypothesis, on
both sides:

$$
p = \min\Bigl(1,\; 2\,P\bigl(\text{Bin}(b + c, \tfrac12) \le \min(b, c)\bigr)\Bigr)
= \min\Bigl(1,\; \frac{2}{2^{\,b+c}} \sum_{k=0}^{\min(b,c)} \binom{b+c}{k}\Bigr).
$$

Examples from Study 0 ({doc}`../design/calibration`), whose variants 0c (protective proteins never switch off) and 0d
(they switch off at Lipniacki's protein turnover rate) are compared with the unchanged baseline:

| Comparison | Gained | Lost | $p$ |
|---|---|---|---|
| Protein turnover (variant 0d) against baseline, 120 min per unit, dead | 17 | 9 | 0.17 |
| Never-decaying products (0c), 120 min per unit, alive | 39 | 4 | $3\times10^{-8}$ |
| 0d, 120 min per unit, alive with Survival on | 0 | 9 | 0.004 |

The $p$ values are not corrected for the number of comparisons made. The study reports them as they are and says
where that matters.

## Quasi-steady occupancy

Study 0 explains a result with the fraction of time a protective protein is present, its **occupancy**. The protein is
a node with two rates that depend on NF-κB's node ({doc}`../science/calzone-network`):

- it switches on at $r_\text{tx}$, but only while the NF-κB node is on;
- it switches off at $r_\text{off}$, but only while the NF-κB node is off.

The NF-κB node is itself on a fraction $f$ of the time ({doc}`switch`). Suppose it flips much faster than the protein
changes. Then the protein sees an NF-κB node that is on a fraction $f$ of any stretch of time, and its rates average out
to an effective switch-on rate $f\,r_\text{tx}$ and an effective switch-off rate $(1-f)\,r_\text{off}$. For a node with
constant rates $u$ and $d$, the fraction of time on is $u/(u + d)$ ({doc}`switch`). So

$$
\text{occupancy} \approx \frac{f\,r_\text{tx}}{f\,r_\text{tx} + (1-f)\,r_\text{off}} .
$$

With $f = 0.28$ and $r_\text{tx} = 3.29\times10^{-4}$ s⁻¹:

| Switch-off | $r_\text{off}$ (s⁻¹) | Occupancy |
|---|---|---|
| Calzone's, at 30 min per unit | $1/1800$ | 0.19 |
| Calzone's, at 120 min per unit | $1/7200$ | 0.48 |
| Lipniacki's protein turnover | $3\times10^{-4}$ | 0.30 |
| Never (the persistence bound) | 0 | → 1 |

**When it holds.** The averaging needs the NF-κB node's on and off phases to be short compared with the protein's
time constants. At $f = 0.28$ the node stays on for about 11 min and off for about 29 min, against protein time
constants of about 51 min ($1/r_\text{tx}$) and 56 min ($1/r_\text{deg}$). So the estimate is an approximation, and
Study 0 uses it only to order the variants, not to predict their numbers. It also assumes $f$ has settled (from about
6 h after TNF; {doc}`../science/lipniacki-model`).
