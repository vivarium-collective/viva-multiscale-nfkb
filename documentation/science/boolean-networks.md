# Boolean networks

The fate layer is a Boolean network. This page explains what that is and how such a network is run, which is what the
rest of the documentation assumes when it speaks of nodes, rules, updating, attractors and rates.

## Why on/off

A cell-fate decision involves dozens of molecules whose concentrations and rate constants are mostly unmeasured. A
Boolean network keeps what is known with more confidence, namely **who activates or inhibits whom**, and gives up the
rest: each molecule, complex or process is reduced to **on** (present or active enough to act) or **off**. The price is
that quantities and times are gone. The rest of this project puts some of them back, from the NF-κB model
({doc}`lipniacki-model`) and as calibrated rates ({doc}`../design/time`).

## Nodes, states and rules

- A **node** is one on/off variable. With $n$ nodes there are $2^n$ **states** of the whole network; Calzone's network
  ({doc}`calzone-network`) has 31 nodes, so about two billion states.
- Each node has a **rule**, a logical formula over other nodes that says what the node's value *should* be. For example
  `CASP3 = apoptosome AND (NOT XIAP)`: caspase-3 should be active when the apoptosome is and XIAP is not.
- A node whose current value differs from what its rule says is **enabled**: it is due to change.

## Updating: which enabled node changes, and when

A rule says what a node should become, not when. The **updating scheme** decides that, and it changes the answers:

| Scheme | What happens | What it gives |
|---|---|---|
| Synchronous | every enabled node changes at once, on each tick | one deterministic sequence of states; can show cycles that need many changes to coincide exactly |
| Asynchronous | one enabled node changes at a time; any of them may be the one | a branching graph of possible sequences: the states **reachable** from the start |
| Continuous-time with rates (MaBoSS) | one node changes at a time, after a random wait; faster nodes are more likely to go first | a probability for every sequence, so a probability for every outcome ({doc}`../math/maboss`) |

Biology is asynchronous: two processes almost never complete at the same instant. That is why both Calzone's analysis
and this project use asynchronous schemes.

## Attractors: where the network settles

Follow the updates long enough and the network ends up in an **attractor**: a **stable state**, where no node is enabled
(every node already agrees with its rule), or a **cycle** of states it keeps returning to. The states from which it
ends in a given attractor are that attractor's **basin**.

A cell fate is an attractor, or a set of them, read through output nodes: in Calzone's network the **Survival**,
**Apoptosis** and **NonACD** nodes ({doc}`calzone-network`). Under TNF a cell can end in more than one of these, and
which one depends on the order in which the competing routes advance.

## Reachability is not probability

An asynchronous analysis without rates answers *which* fates can be reached from the start. To say *how often* each is
reached, every branch in the graph needs a probability: some rule for which enabled node goes first. Any such rule is a
choice of relative rates. Rates turn out to decide the fractions. On Calzone's network, with TNF on and everything else
fixed, changing only the rate of the transcription steps (`$TransRate`) moves the outcome a long way. Fractions of
cells at t = 40 Calzone units (the network's own time unit, {doc}`calzone-network`; the reading time this project's
checks use, well after the fates settle: with NF-κB knocked out, P(Apoptosis) is 0.909 at t = 20 and 0.910 from 30 to
40, `documentation/design/code/death_halftime.py`), 50,000 simulated cells each (each
one a separate random run of the network, {doc}`../math/maboss`), every other rate 1 (`documentation/science/code/transrate_race.py`):

| Transcription rate | Survival | Apoptosis | Necrosis |
|---|---|---|---|
| 1/24 (MaBoSS's example) | 0.014 | 0.952 | 0.030 |
| 1 | 0.201 | 0.540 | 0.259 |

The wiring is identical in both rows. What differs is which route tends to win the race to its attractor: with slow
transcription, caspase-8 is usually active before NF-κB's protective proteins exist. The fractions are therefore a
property of the rates as much as of the wiring. The Calzone 2010 paper gets its figures by such a rule: from each state, every possible
next transition gets equal probability, and a fate's probability is the fraction of paths that reach it. The authors
call this a strong assumption and say the values cannot be compared directly with experiment. They computed it on a
**reduced model**, one with some variables hidden but the same stable states. That is why the paper's figures (about 30%
survival, 60% apoptosis and 10% necrosis; {doc}`models`) are not a target for the
rated network, and why this project measures or calibrates the rates it uses ({doc}`../design/time`,
{doc}`../design/calibration`).

## Where to go next

- The network itself, node by node: {doc}`calzone-network`.
- How MaBoSS turns rates into probabilities, and the equations the checks use: {doc}`../math/maboss`.
