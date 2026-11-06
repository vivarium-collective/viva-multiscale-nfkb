# calzone2010_cellfate

Calzone L, Tournier L, Fourquet S, Thieffry D, Zhivotovsky B, Barillot E, Zinovyev A (2010), "Mathematical modelling of
cell-fate decision in response to death receptor engagement", PLoS Comput Biol 6(3):e1000702 (PubMed 20221256).

- `raw/` (never edited), fetched 2026-11-04 from `sysbio-curie/MaBoSS@375ffadb346adf4173536705fc7efad6c4602714`,
  `engine/tests/maboss/cellfate/` (the files last changed in e844529, 2025-08-24):
  - `cellfate.bnd`, sha256 `cfef1e7054d77f4736d8e36e712946ad1043c2f967913e400ec449b56a3d26dc` (31 nodes)
  - `cellfate.cfg`, sha256 `3734729982e66a71c5f491171a2ae37086fb7f81c0f705a58dc9ec514f20ab21` (TNF off; `$TransRate = 1/24`;
    max_time 10, time_tick 0.1, 100000 samples; every node's istate 0 or 1)
  - `res_probtraj.csv` (from `refer/`), sha256 `cb88e0760d6487d8942727900192588d2282ea6594ba3bb4b18fc1a228ce32ae`: MaBoSS's
    own reference output for that configuration, the oracle of `checks/boolean/calzone-reference`.

`MaBoSSProcess` (viva-maboss@3fdccd7) writes its own `.cfg`, so the composite carries the `$` parameters in
`config.parameters` and the initial states (0 or 1 only; a value >= 0.5 is on) in `config.initial_state`.

## The composite's Boolean layer: `prep.py` → `processed/`

`prep.py` writes `processed/cellfate_coupled.bnd` (all 31 nodes, sha256 `f90525f153859a4cd7e64e18bb1514015d14ff4673c7385c7425c00a229902fa`, deterministic) and
`processed/coupling.json` (every rewrite and why).

### Ownership: remove nothing, Calzone gates

Alex's ruling (2026-11-04) was "Remove nothing; Calzone gates". It supersedes a first version that cut RIP1ub, IKK, cIAP
and mcIAP. An adversarial review found that those nodes also carry Calzone's death → NF-kB feedbacks:
- caspase-8 cleaves RIP1 (CASP8 ⊣ RIP1 → RIP1ub → IKK → NFkB);
- SMAC sequesters cIAP (SMAC ⊣ cIAP → RIP1ub);
- the pro-survival NFkB → mcIAP → cIAP loop.

Cutting only those loops changes the full network under TNF, at t = 40:

| Network | Survival | NonACD |
|---|---|---|
| Full | 0.0136 | 0.0291 |
| Loops cut | 0.1281 | 0.0001 |

The models now divide the work as follows:
- **Lipniacki owns how much.** The nuclear fraction `f = (NFKB_nuc / Kv) / NFKB_total`, from its own `NFKB_total`
  rule (Kv = 5; NFKB_total = 0.06, conserved), is supplied as `$u_NFkB = f`, `$d_NFkB = 1 − f`. It is dimensionless,
  with no fitted constant: about 0.0077 at the unstimulated steady state.
- **Calzone owns whether the route is open.** NFkB keeps its own logic, `IKK AND (NOT CASP3)`. While that holds, the
  node switches on at `$u_NFkB` and off at `$d_NFkB`; when the route closes, it switches off at rate 1, as in Calzone.
  At u = 1, d = 0 it is Calzone's node exactly. `$High_NFkB` is kept.
- **TNF** becomes an input with rates `$u_TNF` / `$d_TNF`, driven by the same receptor-occupancy signal as Lipniacki's
  TNF_R.
- **Death can be absorbing** (Alex, 2026-11-06, decision 28). Apoptosis and NonACD keep their logic, but their
  switch-off rate becomes `($absorb_death ? 0 : 1)`. `$absorb_death = 0` is Calzone's network, where a death node
  switches off again when its cause (caspase-3, ATP loss) reverses; any nonzero value (the composite uses 1) makes
  death irreversible. Checked by `checks/boolean/absorbing-death` (analytic oracle; 0 fails it).

### Time

- **Every rate is multiplied by `$k_time`** (Calzone time units per composite second). Alex chose (2026-11-04) to
  **sweep `k_time` as a study axis** for the death machinery's clock. k_time must be > 0. With r_tx = k_time / 24,
  every rate scales together and k_time is a pure change of clock. `prep.py` guarantees that every rate is wrapped:
  it refuses to write unless each of the 62 rates is exactly `$k_time * (its rate)`, where "its rate" is the upstream
  rate or, for NFkB, TNF, Apoptosis and NonACD, the rewritten one. The `-seconds` checks show
  that the rates which decide the race are on the clock.
- **Transcription-scale steps keep Lipniacki's clock** (Alex: "anchor to Lipniacki, sweep death"). `$TransRate`
  becomes `$r_tx / $k_time` in the 7 nodes that use it, so each switches ON at `r_tx` per second whatever `k_time` is:
  - NF-kB-induced cFLIP, BCL2, mXIAP and mcIAP;
  - cIAP's production from mcIAP;
  - mROS, induced when NF-kB is *off* (`NOT NFkB`);
  - the Survival phenotype node.
- **How `r_tx` is measured.** `anchor_transcription.py` takes it from Lipniacki itself: NFKB_nuc half-rise to A20
  half-rise is 2107 s (35.1 min), so r_tx = ln 2 / 2107 s = 3.29e-4/s, written to `processed/transcription_anchor.json`.
- **Why the anchor matters.** Fate is a race between the death arms and NF-kB's protective genes, and TransRate decides
  it. Under TNF (t = 40) the full network's Survival is 0.014 at MaBoSS's example 1/24 and 0.20 at 1. Calzone 2010 reports about
  0.30 / 0.60 / 0.10 from rate-free asynchronous reachability.
- **Not yet anchored:**
  - those nodes' switch-OFF rates (when their logic fails; cIAP's when SMAC is on) stay on the `k_time` clock;
  - the NF-kB node's own switching speed (u + d = 1, in Calzone units) flickers too fast for its target genes to
    accumulate.

  The calibration study (Study 0) decides both.
- **The measured anchors.** Lipniacki's NF-kB → A20 delay is about 35 min. Calzone's target-induction half-time is 16.6
  units and its apoptosis half-time after TNF about 8.5 units, so one conversion factor cannot match both.

### Checks (`checks/boolean/`)

Each check has an independent oracle and a negative that has been run and failed.

| Check | Oracle | What it guards |
|---|---|---|
| `calzone-reference` | MaBoSS's own reference run | `MaBoSSProcess` on the full network |
| `coupled-equals-full` | the full network on the engine | with u = 1, d = 0 and TNF on, the coupled network equals the full one on all 31 nodes, at t = 40 |
| `coupled-equals-full-early` | the full network on the engine | the same over [7, 8], where the gate's NOT CASP3 term is visible |
| `coupled-equals-full-seconds` | the full network on the engine | k_time is a change of clock at t = 40; an unclocked race-deciding rate (CASP8) fails it |
| `coupled-equals-full-early-seconds` | the full network on the engine | the same over [420, 480] s, while the cascade moves; unclocked BAX or MOMP fail it |
| `coupled-nfkb-knockout` | the full network with NF-kB loss of function | the death arms intact without NF-kB |
| `pair-nfkb-analytic`, `pair-nfkb-seconds` | closed form | the coupling, with the NF-kB rule read from the SBML; the node taken verbatim with its gate held open |
| `transcription-anchor-fast`, `-slow` | closed form | NF-kB's target genes switch on at Lipniacki's rate at any k_time |
