# MaBoSS semantics

A Boolean network with $n$ nodes has $2^n$ joint states $s \in \{0,1\}^n$. Each node $i$ has two rate expressions,
$\text{rate\_up}_i(s)$ and $\text{rate\_down}_i(s)$, which may depend on the current state (through `@logic` and node
names) and on parameters (`$name`). MaBoSS treats the network as a **continuous-time Markov chain**:

- from state $s$, node $i$ flips $0 \to 1$ at rate $\text{rate\_up}_i(s)$ when it is off, and $1 \to 0$ at rate
  $\text{rate\_down}_i(s)$ when it is on;
- MaBoSS simulates trajectories with the Gillespie algorithm, and the ensemble estimates the probability $P(s, t)$ of
  each joint state.

## What is reported: window averages

MaBoSS splits $[0, T]$ into windows of length `time_tick` and reports, for each window $[a, b]$, the time-averaged
probability

$$
\bar P_{[a,b]}(s) = \frac{1}{b-a}\int_a^b P(s, t)\,dt .
$$

A node's probability of being on is the sum over the joint states in which it is on. `MaBoSSProcess` sets
`time_tick = interval / windows_per_interval` and reports the **last window** of each interval, $[T - T/W, T]$.

## Sampling error

With $N$ trajectories, an estimated probability $p$ has standard error about $\sqrt{p(1-p)/N}$, at most $0.5/\sqrt N$.
At $N = 50{,}000$ that's at most 0.0022, and at $N = 100{,}000$ at most 0.0016. The checks set tolerances at about 3.5–4
standard errors, combined over both runs when two ensembles are compared.

## Rates in this workspace's reduced network

Every rate is multiplied by `$k_time` ({doc}`clock`). Calzone's transcription rate `$TransRate` becomes
`$r_tx / $k_time`. The NFkB and TNF nodes take their rates from inputs: `$u_NFkB`, `$d_NFkB`, `$u_TNF` and `$d_TNF`.
