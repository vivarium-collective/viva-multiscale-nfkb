# The rule-based layer, and the dose–response (d1)

## No rule-based layer at runtime in v1 (Alex, Q4)

The strongest runtime role for viva-nfsim was a receptor-binding layer: TNF trimers binding and clustering receptors,
between the TNF field and Lipniacki's `TNF_R`. It fails in v1 for three reasons, each checked at the source:

1. **The wrapper drops bound complexes between intervals.** `NFSimProcess` carries state between intervals only for
   molecule types with no binding sites, or with `~` states. Types like `R(l,l)` and `T(1,2,3)` belong to neither
   group, so every bound complex vanishes at the end of each interval (viva-nfsim@76ff7fc `processes.py:84-96,340-350`).
2. **No parameter port, and the same RNG seed every interval** (`:109-113`).
3. **The timescales make it unnecessary.** Binding equilibrates in about 100 s ($k_\text{off} = 0.01\ \text{s}^{-1}$),
   which is quasi-steady on NF-κB's timescale of hours. Lipniacki's `TNF` is also an on/off gate, so one scalar carries
   all the information the core can use.

Using NFSim for IKK or IκB:NF-κB complexes instead would duplicate what Lipniacki already owns.

## What v1 uses instead: an offline dose–response (d1, in progress)

Because binding is fast, its **equilibrium** is all the composite needs. That's a function from the TNF concentration
at the cell to receptor engagement, $\text{occ} = g([\text{TNF}])$. It is computed offline from McMillan 2021's
published rule-based model, using BioNetGen's own ODE network generation (no viva-nfsim). It is then fitted and
committed, and applied by a `MathExpressionStep`.

- **Source:** RuleWorld/RuleHub `Published/McMillan2021/McMillan_2021.bngl` at b84f0a7, kept unedited in
  `workspace/datasets/mcmillan2021_tnfr/raw/` with its sha256.
- **Model:** the TNF trimer `T(1,2,3)` binds receptors `R(p,a)` in three steps, with $K_1 = 10$, $K_2 = 100$ and
  $K_3 = 1000$ nM and $k_\text{off} = 0.01\ \text{s}^{-1}$. McMillan et al. fitted these constants to native
  mass-spectrometry fractions of TNF with 0–3 receptors bound, solving the equilibria with BioNetGen (Methods).
- **The oracle:** the equilibrium of stepwise binding is the solution of the mass-action equations. Solving them
  independently gives a check on BioNetGen's ODE steady state.
- **Open choices, to be documented when d1 lands:**
  - which observable counts as "engaged" (any bound receptor, or ≥ 2 receptors per trimer, which clustering needs);
  - the receptor density on a cell surface, as against the paper's soluble ectodomain.

```{admonition} Assumption, recorded wherever the curve is used
:class: warning
The curve maps a receptor-engagement fraction onto Lipniacki's 0/1 `TNF_R`. The plan records Lipniacki 2007 as the
precedent for that mapping; d1 will quote the relevant passage when it lands. The binding constants come from soluble
receptor in vitro, not from a cell membrane.
```

## v2 and later

A runtime NFSim receptor layer becomes worth having alongside a stochastic or multicellular core. It needs these
upstream viva-nfsim fixes first:
- carry every species' full state between intervals;
- add a parameter input port;
- give TNF its own clamped input;
- use a new RNG seed each interval.

Its oracles would be chunked against continuous NFsim runs, and the Goldstein–Perelson equilibrium for trivalent
ligands.
