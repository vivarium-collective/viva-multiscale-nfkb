# Couplings

Each edge is data flowing from the layer that owns a quantity to the layer that reads it. Each store has one writer.

| From | Port | Adapter | To | Port |
|---|---|---|---|---|
| <span class="layer spatial">spatial</span> `FVReactionDiffusion` | `fields.TNF` | `RegionMean`: masked mean over the cell-surface voxels | store `tnf_at_cell` (µM) | |
| `tnf_at_cell` | | `MathExpressionStep`: the dose–response (d1) | store `tnf_occupancy` (0–1) | |
| `tnf_occupancy` | | direct (writer declares `overwrite`) | <span class="layer kinetic">kinetic</span> Tellurium | `parameters_in.TNF_R` |
| `tnf_occupancy` | | `MathExpressionStep`: $u = \text{occ}$, $d = 1-\text{occ}$ (on Calzone's unit rate, then scaled by `$k_time` like every rate) | <span class="layer boolean">Boolean</span> MaBoSS | `parameters.u_TNF`, `parameters.d_TNF` |
| Tellurium | five NF-κB species | `MathExpressionStep`: nuclear fraction $f$; $u = f$, $d = 1-f$ | MaBoSS | `parameters.u_NFkB`, `parameters.d_NFkB` |
| MaBoSS | `node_probabilities.Apoptosis`/`NonACD` | gate (*candidate*) | Tellurium | `parameters_in.…` |

The last edge, fate feeding back into kinetics, ships only with a cited biological basis. Without one, the Boolean
layer in v1 is a readout.

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
  - Total NF-κB is conserved (0.06 µM through the whole stimulated `sim1` run), so $f$ is a true fraction.
- **Its range:**
  - At rest (the pre-equilibrated state), $f \approx 0.0077$.
  - At NF-κB's first peak after TNF (NFKB_nuc 0.280 µM, 23.7 min), $f = 0.933$.
  - The checks hold one sampled stimulated state, 414 s after TNF and still rising (NFKB_nuc 0.1688 µM), where
    $f = 0.5627$.
- **How it drives the node:** $u_\text{NFkB} = f$ and $d_\text{NFkB} = 1-f$. With caspase-3 off, the NFkB node is
  then a two-state switch with stationary P(on) $= f$ ({doc}`../math/switch`).

**Check:** `pair-nfkb-analytic` wires exactly this.
- **Inputs:** the five species, held at the peak; the adapter evaluates the rule; MaBoSS runs the coupled network's NF-κB node verbatim, with its gate held open
  with TNF off.
- **Result:** P(NFkB on) over the last window matches the analytic 0.48259, and the death arms stay at 0.
- **Proven failing:** with $K_v = 4$ in the adapter, and with the `parameters` store unseeded.

## Wiring rules

Each rule was found by running composites, and each is enforced by a check that fails when the rule is broken.

- **Seed every map key a Step writes into.** In process-bigraph 1.9.1, a Step's write to a `map[float]` key the store
  doesn't hold yet is **silently dropped**. An overwrite to `["parameters","u"]` on an empty map leaves it empty. So
  every document seeds MaBoSS's `parameters` (`u_NFkB`, `d_NFkB`, `u_TNF`, `d_TNF`, `k_time`, `r_tx`) and Tellurium's
  `parameters_in` (`TNF_R`). Negative check: `pair-nfkb-analytic` with an empty store leaves NF-κB at 0.
- **A writer to `parameters_in` must declare `overwrite[...]`.** A plain `map[float]` output adds to the store on every
  update (viva-tellurium 0.2.3).
- **Set `"global_time_precision": 6`** at the document's top level. Without it, floating-point drift skips the last
  tick.
- **Put no expectation on emitter row 0.** It is t = 0, before any process has written.
- **Adapters fire on every tick their inputs are touched,** not on change, even for a zero delta. "Event-driven"
  coupling is therefore just scheduling (process-bigraph 1.9.1 `composite.py:2541-2563`).
