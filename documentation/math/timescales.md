# Timescales and coupling intervals

The composite's layers exchange values at fixed intervals. This page derives how fast each part of the NF-κB model
changes, and from that how often the layers must exchange values.

## How fast does an ODE model change? Linearise it

Write the NF-κB model ({doc}`../science/lipniacki-model`) as $\dot x = F(x)$, where $x$ is the vector of 16
concentrations. Near a state $x^*$, a small deviation $\delta x = x - x^*$ evolves as

$$
\dot{\delta x} \approx J\,\delta x, \qquad J_{ij} = \frac{\partial F_i}{\partial x_j}\bigg|_{x^*},
$$

where $J$ is the **Jacobian**. Each eigenvalue $\lambda$ of $J$ is one **mode**: a direction in which deviations change
as $e^{\lambda t}$.

- **Real and negative** ($\lambda = -1/\tau$): the deviation decays by a factor $e$ every $\tau$ seconds. $\tau$ is the
  mode's **relaxation time** (its e-folding time).
- **A complex pair** ($\lambda = -1/\tau \pm i\,\omega$): the deviation oscillates with period $2\pi/\omega$ while its
  amplitude decays with e-folding time $\tau$. That is a **damped oscillation**.
- **Positive real part**: the deviation grows. The state is unstable in that direction.
- **Zero**: a direction in which nothing changes, which is what a **conserved quantity** does.

Because the model is nonlinear, $J$ depends on the state, so the timescales are recomputed along the trajectory.

## What the model's Jacobian gives

`analysis/d7/kinetic_timescales.py` computes the eigenvalues at the rest state, and then every 60 s for 6 h after TNF
is switched on to saturation (361 states; results in `analysis/d7/kinetic_timescales.json`):

| Mode | Timescale | Where it comes from |
|---|---|---|
| Fastest decay | 6.2 s at rest; 6.0–10 s after TNF | |
| Slowest decay | 8000 s (2.2 h) at every state | exactly $1/K_\text{deg}$ = 1/(1.25×10⁻⁴ s⁻¹): IKK's turnover, a linear step that does not depend on the state |
| Zero mode | one, at every state | total NF-κB, which no reaction changes (proved on {doc}`../science/lipniacki-model`) |
| Growing mode | only at 60 s after TNF, the first state sampled after it (growth e-folding 3.6 h) | |
| Oscillating pairs | periods of 67–132 min in 355 of the 360 states after TNF | NF-κB's negative feedbacks ({doc}`../science/lipniacki-model`) |
| Least-damped pair | from 2 h after TNF: period 98–102 min, e-folding 55–90 min (wider swings before 2 h) | the ringing that outlasts the others |

Two things follow:

- **NF-κB's waves ring down; they are not a sustained cycle.** Apart from that one state no mode grows, and the
  slowest-decaying oscillation loses a factor $e$ in 55–90 min, a little less than its ~100 min period. So each wave is
  well under half the size of the one before, which matches the measured waves settling by about 6 h
  ({doc}`../science/lipniacki-model`).
- **The model is stiff:** its timescales span more than three orders of magnitude, from 6 s to 8000 s. An explicit
  integrator would need steps of seconds for hours of time. So the model is solved by an implicit, adaptive integrator
  (CVODE, through libRoadRunner), which handles the fast modes internally.

## How often must layers exchange values?

The layers exchange values every **coupling interval** $\Delta t$. Between exchanges, each layer holds the last value
it received (sample and hold). If the value relaxes on timescale $\tau$, it changes during one interval by a fraction
of about

$$
1 - e^{-\Delta t/\tau} \approx \frac{\Delta t}{\tau} \quad (\Delta t \ll \tau),
$$

and on average the held value is $\Delta t/2$ old. So $\Delta t = 0.1\,\tau$ keeps the held value within about 10% of
the current one at worst, and about 5% on average. That is the rule used here: **each coupling interval is about 0.1 ×
the fastest timescale of the quantity that crosses that edge**, not of the fastest process anywhere. The model's 6 s
modes never cross an edge; they stay inside its integrator. What crosses is TNF at the cell and NF-κB's fraction $f$,
which change over minutes ({doc}`../design/time`).

The rule is a bound to start from, not a proof. A composite's intervals are accepted only if it reproduces a run with
the finest intervals on the reported quantities, shows no oscillation created by the coupling itself, and runs faster
({doc}`../design/time`).
