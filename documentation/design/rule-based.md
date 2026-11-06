# The rule-based layer, and the dose–response (d1)

**Rule-based models** describe molecules with binding sites, and rules for which sites bind, instead of listing every
complex as its own species. They are written in the BioNetGen language (BNGL): `T(1,2,3)` is a molecule `T` with three
sites named 1, 2 and 3, `!1` marks a bond (both ends carry the same label), and `!+` means "bound to something". A
simulator such as NFSim follows the molecules one by one; BioNetGen can also expand the rules into ordinary
differential equations. This page explains why the composite uses a rule-based model only offline, to compute TNF's
dose–response at the receptor, the step called **d1**.

## No rule-based layer at runtime in v1 (Alex)

The strongest runtime role for viva-nfsim was a receptor-binding layer: TNF trimers binding and clustering receptors,
between the TNF field and Lipniacki's `TNF_R`. It fails in v1 for three reasons, each checked at the source:

1. **The wrapper drops bound complexes between intervals.** `NFSimProcess` carries state between intervals only for
   molecule types with no binding sites, or with `~` states (sites that carry a modification state, such as
   phosphorylated or not, written `site~state`). Types like `R(l,l)` (a receptor with two binding sites, both named `l`)
   and `T(1,2,3)` belong to neither
   group, so every bound complex vanishes at the end of each interval (viva-nfsim@76ff7fc `processes.py:84-96,340-350`).
2. **No parameter port, and the same random-number generator (RNG) seed every interval** (`:109-113`).
3. **The timescales may make it unnecessary.** Quasi-steady means: when one process relaxes much faster than everything that reads it, it can be treated as always at
   its equilibrium. Binding relaxes toward equilibrium at rate $k_\text{off} + k_\text{on}[R] \ge k_\text{off}$
   ($k_\text{off} = 0.01\ \text{s}^{-1}$), so within about 100 s or less, depending on receptor density. That is only about a third of NF-κB's 337 s half-rise, so
   the separation is a factor of about 3, not orders of magnitude, and the equilibrium is an approximation to be checked
   when d1 is built (an open question; {doc}`roadmap`). Lipniacki's `TNF` is also an on/off gate, so one scalar carries
   all the information the core can use.

Using NFSim for IKK or IκB:NF-κB complexes instead would duplicate what Lipniacki already owns.

## What v1 uses instead: an offline dose–response (d1, not started)

Because binding is fast, its **equilibrium** is all the composite needs. That's a function from the TNF concentration
at the cell to receptor engagement, $\text{occ} = g([\text{TNF}])$. It is computed offline from McMillan 2021's
published rule-based model, using BioNetGen's own ODE network generation (no viva-nfsim). It is then fitted and
committed, and applied by a `MathExpressionStep`.

- **Source:** RuleWorld/RuleHub `Published/McMillan2021/McMillan_2021.bngl` at b84f0a7. It will be committed unedited,
  with its sha256, under `workspace/datasets/mcmillan2021_tnfr/raw/` when d1 lands; it is not in the repository yet.
- **Model:** the TNF trimer `T(1,2,3)` has three receptor-binding sites. The receptor `R(p,a)` binds TNF with its
  site `a`; its site `p`, for receptor–receptor pairing, stays unbound, because the published file leaves the pairing
  rules commented out. Receptors bind in three steps, each weaker than the last: dissociation constants $K_1 = 10$,
  $K_2 = 100$ and $K_3 = 1000$ nM for the first, second and third receptor, all with $k_\text{off} = 0.01\ \text{s}^{-1}$.
  McMillan et al. fitted these constants to native mass-spectrometry fractions of TNF with 0–3 receptors bound,
  solving the equilibria with BioNetGen (Methods).
- **The equilibrium, from the rules.** Each free site binds a receptor at rate $k_n [R]$, where $[R]$ is the free
  receptor concentration and $n$ the number of receptors the trimer will then hold, and each bond breaks at
  $k_\text{off}$, with $K_n = k_\text{off}/k_n$. At equilibrium every binding step is balanced by its reverse, so a
  trimer with one more particular site bound is $[R]/K_n$ times as likely as without it. There are $\binom{3}{n}$ ways
  to choose which $n$ sites are bound, so the fraction of trimers with $n$ receptors is
  $$
  P(n) \propto \binom{3}{n} \prod_{i=1}^{n} \frac{[R]}{K_i}, \qquad n = 0, 1, 2, 3,
  $$
  with free $[R]$ and free TNF fixed by conservation of total receptor and total TNF.
- **The oracle:** that closed form, solved independently, checks BioNetGen's ODE steady state.
- **Open choices, to be documented when d1 lands:**
  - which observable counts as "engaged" (any bound receptor, or ≥ 2 receptors per trimer, which clustering needs);
  - the receptor density on a cell surface, as against the paper's soluble ectodomain.

```{admonition} Assumption, recorded wherever the curve is used
:class: warning
The curve maps a receptor-engagement fraction onto Lipniacki's `TNF_R`, which the original model only ever sets to 0 or
1. The plan of record (`docs/design/plan-section-b.md`) records Lipniacki et al. 2007 (*BMC Bioinformatics* 8:376, in which receptor activation by single TNF trimers
is a stochastic on/off switch) as the precedent for that mapping; d1 will quote the relevant passage when it lands. The binding constants come from soluble
receptor in vitro, not from a cell membrane.
```

## v2 and later

A runtime NFSim receptor layer becomes worth having alongside a stochastic or multicellular core. It needs these
upstream viva-nfsim fixes first:
- carry every species' full state between intervals;
- add a parameter input port;
- give TNF its own clamped input;
- use a new RNG seed each interval.

Its oracles would be runs split into coupling intervals compared against one continuous NFsim run, and the Goldstein–Perelson equilibrium theory for
trivalent ligands clustering cell-surface receptors (Goldstein and Perelson 1984; {doc}`../reference/bibliography`).
