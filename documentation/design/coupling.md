# Couplings

Each edge is data flowing from the layer that owns a quantity to the layer that reads it. Each store has one writer.

| From | Port | Adapter | To | Port |
|---|---|---|---|---|
| <span class="layer spatial">spatial</span> `FVReactionDiffusion` | `fields.TNF` | `RegionMean`: masked mean over the cell-surface voxels | store `tnf_at_cell` (µM) | |
| `tnf_at_cell` | | `MathExpressionStep`: the dose–response (d1) | store `tnf_occupancy` (0–1) | |
| `tnf_occupancy` | | direct (writer declares `overwrite`) | <span class="layer kinetic">kinetic</span> Tellurium | `parameters_in.TNF_R` |
| `tnf_occupancy` | | `MathExpressionStep`: $u = \text{occ}$, $d = 1-\text{occ}$ (on Calzone's unit rate, then scaled by `$k_time` like every rate) | <span class="layer boolean">Boolean</span> MaBoSS | `parameters.u_TNF`, `parameters.d_TNF` |
| Tellurium | five NF-κB species | `MathExpressionStep`: nuclear fraction $f$; $u = f\kappa/k_\text{time}$, $d = (1-f)\kappa/k_\text{time}$ | MaBoSS | `parameters.u_NFkB`, `parameters.d_NFkB` |
| MaBoSS | `node_probabilities.Apoptosis`/`NonACD` | feedback (*candidate*, not built; below) | Tellurium | `parameters_in.…` |

Symbols in the table:
- **occ** is a receptor-engagement fraction, between 0 and 1; which bound states count as engaged (any receptor bound
  to a TNF trimer, or at least two) is chosen when d1 is built ({doc}`rule-based`). The dose–response step **d1** computes it from the
  TNF concentration at the cell ({doc}`rule-based`). Through $u = \text{occ}$, $d = 1 - \text{occ}$, the fate network's
  TNF node is on a fraction occ of the time ({doc}`../math/switch`).
- **$f$** is NF-κB's nuclear fraction (below; derived on {doc}`../science/lipniacki-model`).
- **κ** is how fast the fate network's NF-κB node flips, in s⁻¹ (below).
- **`k_time`** is the death clock, Calzone units per second ({doc}`time`). Every network rate is multiplied by it, so
  dividing by it here makes the NF-κB node's speed independent of it.

The last edge, fate feeding back into kinetics, ships only with a cited biological basis. Without one, no edge leaves
the Boolean layer in v1: it is a readout. Absorbing death (decision 28, {doc}`boolean`) keeps a death flag set so that
a later edge can stop a dead cell signalling; no such edge is built yet.

## Kinetic → Boolean: the nuclear fraction

**The quantity.** The Boolean NFkB node means "NF-κB is active as a transcription factor". In Lipniacki, the active
pool is free nuclear NF-κB, so the model's own measure of activity is the fraction of all NF-κB that is free in the
nucleus:

$$
f = \frac{\text{NFKB\_nuc}/K_v}{\text{NFKB\_total}}, \qquad
\text{NFKB\_total} = \text{IKKactive\_IkB\_NFKB} + \text{NFKB} + \text{IkB\_NFKB} + \frac{\text{NFKB\_nuc} + \text{IkB\_NFKB\_nuc}}{K_v}
$$

- **Why this form:**
  - It is dimensionless, in [0, 1], and has no fitted constant.
  - `NFKB_total` is the curated SBML's own assignment rule. It is a rule variable, not a species output, so the
    adapter evaluates the rule verbatim from the five species.
  - Total NF-κB is conserved (0.06 µM through the whole stimulated `sim1` run), so $f$ is a true fraction. Why each
    nuclear term is divided by $K_v$, and a proof of the conservation from the reactions:
    {doc}`../science/lipniacki-model`.
- **Its range:**
  - At rest (the pre-equilibrated state), $f \approx 0.0077$.
  - At NF-κB's first peak after TNF (NFKB_nuc 0.280 µM, 23.7 min), $f = 0.933$.
  - The checks hold one sampled stimulated state, 414 s after TNF and still rising (NFKB_nuc 0.1688 µM), where
    $f = 0.5627$.
- **How it drives the node:** $u_\text{NFkB} = f\,\kappa/k_\text{time}$ and
  $d_\text{NFkB} = (1-f)\,\kappa/k_\text{time}$. The composite's network multiplies every rate by `$k_time`
  (`workspace/datasets/calzone2010_cellfate/prep.py`, {doc}`../math/clock`), so in seconds the node
  switches on at $f\kappa$ and off at $(1-f)\kappa$. While its gate holds (IKK on, caspase-3 off), the NFkB node is a
  two-state switch with stationary P(on) $= f$ ({doc}`../math/switch`).
  - **$f$ sets how often the node is on; κ sets how fast it flips.** Neither model gives κ.
  - **Study 0 chose κ = ln 2 / 337 s,** Lipniacki's own nuclear half-rise (Alex, 2026-11-06; {doc}`calibration`). The
    checks below use the special case κ = `k_time`, where $u = f$ and $d = 1 - f$.
  - **The consequence: graded NF-κB becomes a duty cycle.** Once $f$ settles at 0.28 under held TNF (from about 6 h;
    measured in Study 0's runs, {doc}`../science/lipniacki-model`), the node stays on
    for about 11 min at a time ($1/((1-f)\kappa)$) and off for about 29 min ($1/(f\kappa)$).
  - **Calzone's NFkB is different:** it switches on at rate 1 per unit and stays on while its gate holds. Study 0
    measured what that difference does to fate.

**Check:** `pair-nfkb-analytic` wires exactly this.
- **Inputs:** the five species, held at the state 414 s after TNF (still rising, $f = 0.5627$); the adapter evaluates the rule; MaBoSS runs the coupled network's NF-κB node verbatim in a three-node document, with IKK and CASP3 as constant nodes
  (IKK on, CASP3 off), so its gate is always open.
- **Result:** P(NFkB on) over the last window matches the analytic 0.48259.
- **Proven failing:** with $K_v = 4$ in the adapter, and with the `parameters` store unseeded.

## Wiring rules

Each rule was found by running composites, and each is enforced by a check that fails when the rule is broken.

- **Seed every map key a Step writes into.** In process-bigraph 1.9.1, a Step's write to a `map[float]` key the store
  doesn't hold yet is **silently dropped**. An overwrite to `["parameters","u"]` on an empty map leaves it empty. So
  every document seeds MaBoSS's `parameters` (`u_NFkB`, `d_NFkB`, `u_TNF`, `d_TNF`, `k_time`, `r_tx`, `absorb_death`) and Tellurium's
  `parameters_in` (`TNF_R`). Negative check: `pair-nfkb-analytic` with an empty store leaves NF-κB at 0.
- **A writer to `parameters_in` must declare `overwrite[...]`.** A plain `map[float]` output adds to the store on every
  update (viva-tellurium 0.2.3).
- **Set `"global_time_precision": 6`** at the document's top level. Without it, floating-point drift skips the last
  tick.
- **Put no expectation on emitter row 0.** It is t = 0, before any process has written.
- **Adapters fire on every tick their inputs are touched,** not on change, even for a zero delta. "Event-driven"
  coupling is therefore just scheduling (process-bigraph 1.9.1 `composite.py:2541-2563`).
- **A write to a whole map does not trigger a Step that reads one of its keys.** A Step runs when an updated path, or
  one of that path's prefixes, is one of its input paths. `TelluriumProcess` writes the whole `species` map, which is a
  parent of the per-species paths the nuclear-fraction Step reads, so those inputs alone never trigger it. The
  composite therefore also wires the kinetic layer's time into that Step, which is written every update (process-bigraph
  1.9.1 `composite.py:2541-2569`; `make_kinetic_boolean.py`).
