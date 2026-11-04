# The two-state switch, and its window average

Most of the Boolean checks reduce to one node that is a two-state Markov switch whose rates don't depend on the rest of
the network. That has a closed form.

## General switch

A node that turns on at rate $u$ and off at rate $d$, starting off, is on at time $t$ with probability

$$
P(t) = \frac{u}{u+d}\left(1 - e^{-(u+d)t}\right).
$$

It solves $\dot P = u(1-P) - dP$ with $P(0) = 0$, and its stationary value is $u/(u+d)$.

**The kinetic → Boolean coupling** sets $u = f$ and $d = 1 - f$, so $u + d = 1$ and

$$
P(t) = f\,(1 - e^{-t}),
$$

with stationary value exactly $f$, Lipniacki's nuclear fraction. This is why the coupling is model-native: the Boolean
node's long-run probability of being on is the kinetic model's own fraction of active NF-κB, with no new constant.

## Absorbing switch

If $d = 0$ (a node that turns on and stays on, like a target gene while NF-κB is on), then

$$
P(t) = 1 - e^{-ut}.
$$

## Window averages (what MaBoSS reports)

Over the window $[a, b]$, with the general switch averaged by integrating:

$$
\bar P_{[a,b]} = \frac{u}{u+d}\left(1 - \frac{e^{-(u+d)a} - e^{-(u+d)b}}{(u+d)(b-a)}\right),
\qquad
\text{absorbing: } \bar P_{[a,b]} = 1 - \frac{e^{-ua} - e^{-ub}}{u(b-a)} .
$$

## Where the checks use them

| Check | Node | Rates | Window | Value |
|---|---|---|---|---|
| `calzone-reference` | mROS (NF-κB off throughout) | $u = 1/24$, $d = 0$ | [9.9, 10] | 0.339384 |
| `pair-nfkb-analytic` | NFkB | $u = f = 0.5627$, $d = 1 - f$ | [1.9, 2] | 0.482590 |
| `pair-nfkb-seconds` | NFkB | the same, with the clock converted | [1140, 1200] s | 0.482590 |
| `transcription-anchor-*` | BCL2, cFLIP, mXIAP, Survival | $u = r_\text{tx}$, $d = 0$ | the last 1/20 of 2107 s | 0.491235 |

**Why the switch is isolated in each check:**
- **`calzone-reference`:** TNF is off, so NF-κB stays off and mROS's logic, `NOT NFkB`, is constantly true.
- **The pair checks:** TNF is off, so no death signal reaches CASP8, and caspase-3 never blocks NFkB.
- **The anchor checks:** NF-κB is held on by `$High_NFkB = 1`, so each target's logic is constantly true.
