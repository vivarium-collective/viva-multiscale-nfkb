# MaBoSS semantics

How the fate network ({doc}`../science/calzone-network`) becomes numbers: the random process MaBoSS simulates, the
equation its probabilities obey, what it reports, and how `MaBoSSProcess` turns that into one cell.

## From a network to a random process

A network with $n$ nodes has $2^n$ **joint states** $s \in \{0,1\}^n$, one on/off value per node. Each node $i$ has two
rate expressions, $\text{rate\_up}_i(s)$ and $\text{rate\_down}_i(s)$. They may use:

- `@logic`, which is the node's own rule evaluated in the current state $s$: 1 if the rule is true, else 0. So
  `rate_up = @logic ? 1 : 0` is 1 when the rule says the node should be on;
- other nodes' names, which read their current values;
- parameters `$name`, numbers fixed for the run (for example `$k_time`, `$r_tx`). A parameter the network uses but the
  configuration does not define is an error, not a default.

From state $s$, node $i$ switches $0 \to 1$ at rate $\text{rate\_up}_i(s)$ if it is off, and $1 \to 0$ at rate
$\text{rate\_down}_i(s)$ if it is on. Only one node switches at a time. Updating one node at a time, at random times, is
called **asynchronous** updating: unlike a synchronous Boolean network, where every node updates at once on a clock tick,
the order in which nodes switch is itself random and set by the rates.

## Waiting times

A rate $\lambda$ means the switch happens after a waiting time $\tau$ with $P(\tau > t) = e^{-\lambda t}$, an
**exponential** waiting time with mean $1/\lambda$. Two facts about exponential waiting times carry every derivation in
this documentation:

1. **No memory.** Having waited $t$ already does not change the remaining wait: $P(\tau > t + u \mid \tau > t) =
   e^{-\lambda u}$. So only the current state matters, which is what makes the process a **Markov chain**.
2. **Competing switches.** If switches with rates $\lambda_1, \dots, \lambda_m$ are all possible, the first happens
   after an exponential wait with the total rate $\Lambda = \sum_j \lambda_j$, and it is switch $j$ with probability
   $\lambda_j / \Lambda$. (The first wait exceeds $t$ only if every one does: $\prod_j e^{-\lambda_j t} = e^{-\Lambda
   t}$.)

## Simulating one trajectory: Gillespie's algorithm

MaBoSS simulates the chain exactly with Gillespie's algorithm (Gillespie 1977; Stoll et al. 2012), which is fact 2 used
repeatedly:

1. In state $s$, compute every node's current switching rate and their total $\Lambda(s)$.
2. Draw the waiting time from an exponential with rate $\Lambda(s)$; advance the clock by it.
3. Pick which node switches, node $i$ with probability $\lambda_i(s)/\Lambda(s)$; switch it.
4. Repeat until the end time. If $\Lambda(s) = 0$, nothing can switch and the state stays.

One such run is a **trajectory**: one possible history of one cell. Many trajectories with different random numbers form
an **ensemble**, whose fractions estimate probabilities.

## The equation the probabilities obey

Let $P(s, t)$ be the probability of joint state $s$ at time $t$, written as a row vector $P(t)$ over all states. Collect
the rates into the **generator** matrix $Q$: $Q_{s s'}$ is the rate of switching from $s$ to $s'$ (nonzero only when
$s'$ differs from $s$ in one node), and $Q_{ss} = -\Lambda(s)$, so each row sums to zero. In a short time $dt$,
probability flows out of $s$ at total rate $\Lambda(s)$ and into $s$ from every $s'$ at rate $Q_{s's}$, which gives the
**forward equation**

$$
\frac{dP}{dt} = P\,Q, \qquad P(t) = P(0)\,e^{tQ}.
$$

**Example: one node on its own.** If a node's rates are constants $u$ (on) and $d$ (off), its two states give
$Q = \begin{pmatrix} -u & u \\ d & -d \end{pmatrix}$, and the probability $p$ of being on obeys
$\dot p = u(1-p) - d\,p$. That is the switch the composite's NF-κB node uses ({doc}`switch`). The equation is never
solved numerically here; it is what the analytic oracles are derived from ({doc}`switch`, {doc}`clock`,
{doc}`../design/boolean`).

## What is reported: window averages

MaBoSS splits $[0, T]$ into windows of length `time_tick` and reports, for each window $[a, b]$, the time-averaged
probability

$$
\bar P_{[a,b]}(s) = \frac{1}{b-a}\int_a^b P(s, t)\,dt .
$$

A node's probability of being on is the sum over the joint states in which it is on. `MaBoSSProcess` sets
`time_tick = interval / windows_per_interval`, where the interval is how much time the process covers per update
({doc}`../design/composite-primer`), and reports the **last window** of each interval, $[T - T/W, T]$, where
$T$ is the interval and $W$ is `windows_per_interval`.

## From an ensemble to one cell: `MaBoSSProcess`

MaBoSS starts every run from fixed per-node initial values; it cannot start from a probability distribution over joint
states. So `MaBoSSProcess` (viva-maboss) runs each interval as a fresh MaBoSS run and carries **one** joint state from
one interval to the next:

1. It runs `sample_count` trajectories over the interval, starting from the carried state.
2. From the last window's joint-state distribution it **samples one joint state**, which becomes the next interval's
   start and is written to `node_state` (0 or 1 per node). The process also writes `node_probabilities`: each node's
   probability of being on over that last window (with one trajectory, the fraction of the window it was on).
3. Both the engine's random seed and the sampler's come from `numpy.random.SeedSequence([seed, step])`, where `step` counts the intervals run so far, so a run is
   reproducible from its seed.

In the studies every cell is one `MaBoSSProcess` with `sample_count = 1`: one trajectory per interval, and the sampled
state is one of the states that trajectory visited in the last window, chosen in proportion to the time it spent there.
So a cell is a single history, and a population is many cells with different seeds. Two consequences:

- The carried state lags the interval's end by about half a window, $T/(2W)$: 1.5 s for a 30 s interval with the studies'
  $W = 10$.
- A node that switches on and off again within one interval, outside its last window, is never recorded
  (absorbing death and this effect: {doc}`../design/boolean`).

## Sampling error

With $N$ trajectories, an estimated probability $p$ is a binomial fraction with standard error $\sqrt{p(1-p)/N}$, at
most $0.5/\sqrt N$. At $N = 50{,}000$ that is at most 0.0022, and at $N = 100{,}000$ at most 0.0016. The checks set
tolerances at about 3.5–4 standard errors, combined over both runs when two ensembles are compared. For one compared
value, a correct model then fails by chance with probability $P(|Z| > 3.5) \approx 5\times10^{-4}$ (at 4: $6\times
10^{-5}$), where $Z$ is a standard normal; over a check that compares all 31 nodes, about 1.4% (0.2%).

## Rates in this workspace's coupled network

Every rate is multiplied by `$k_time` ({doc}`clock`). Calzone's transcription rate `$TransRate` becomes
`$r_tx / $k_time`. The NFkB and TNF nodes take their rates from inputs: `$u_NFkB`, `$d_NFkB`, `$u_TNF` and `$d_TNF`. The
death nodes' switch-off is switched by `$absorb_death` ({doc}`../design/boolean`).
