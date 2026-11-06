# Clock conversion, and why gene expression is invariant to it

## Scaling every rate converts time

Let the coupled network's rates be $\rho_i(s)$ in Calzone units. Multiplying every rate by $k$ (`$k_time`, Calzone
units per second) gives a chain whose law at time $t$ seconds equals the original chain's law at time $kt$ Calzone
units:

$$
P_k(s, t) = P_1(s, kt).
$$

This holds because the generator scales by $k$: $Q_k = kQ_1$, so $e^{tQ_k} = e^{(kt)Q_1}$. Every probability, window
average and fate fraction is the same function of $kt$. Only the time axis changes. That's what `pair-nfkb-seconds`
checks: $k = 1/600$ over 1200 s gives the same value as $k = 1$ over 2 units.

## The transcription term is invariant to $k$

`prep.py` writes Calzone's transcription rate as `$r_tx / $k_time` *inside* a rate that is then multiplied by
`$k_time`:

$$
\text{rate}_\text{target} = k \cdot \frac{r_\text{tx}}{k} = r_\text{tx}\quad\text{(per second)},
$$

whatever $k$ is. The death machinery's rates scale with $k$. NF-κB's own switching does not: the composite writes
$u = f\kappa/k$ and $d = (1-f)\kappa/k$, so the network's rates $k\,u = f\kappa$ and $k\,d = (1-f)\kappa$ are also
independent of $k$ ({doc}`switch`; {doc}`../design/decisions`, row 25). Only in the checks that set $\kappa = k$ does
NF-κB's switching scale with $k$. So:

- **gene expression runs on Lipniacki's measured clock,** $r_\text{tx} = \ln 2 / 2107\ \text{s}$;
- **`k_time` moves only the death machinery's speed** relative to it.

`transcription-anchor-fast` and `transcription-anchor-slow` check exactly this. At $k = 1/60$ and $k = 1/6000$, each
target gene's probability over Lipniacki's delay is the same, 0.491235.

## The anchor

$r_\text{tx}$ is the rate at which a target gene, an absorbing switch with $d = 0$, reaches half probability after the
delay Lipniacki itself produces between nuclear NF-κB and its target protein:

$$
1 - e^{-r_\text{tx}\,\Delta} = \tfrac12 \;\Rightarrow\; r_\text{tx} = \frac{\ln 2}{\Delta},
\qquad \Delta = t_{1/2}(\text{A20}) - t_{1/2}(\text{NFKB\_nuc}) = 2444 - 337 = 2107\ \text{s}.
$$

Each half-rise $t_{1/2}$ is the first time the species is half-way from its pre-stimulus value to its first peak.
`anchor_transcription.py` computes it on libRoadRunner from the pre-equilibrated state with `TNF_R` stepped to 1, at
one-second resolution.
