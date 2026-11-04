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

`prep.py` writes `processed/cellfate_reduced.bnd` (27 nodes, sha256 `a6b32632ecfad48522db1d564985d67a5c61cc8231bd16bccc3afee895550745`,
deterministic) and `processed/reduction.json` (every removed or rewritten node and why).

Ownership, from Alex's ruling (2026-11-04: "the most biologically accurate and overall model-native option"):
- **Lipniacki 2004 owns NF-kB activation.** Its lumped TNF → IKK step stands in for Calzone's RIP1 → RIP1ub → IKK → NFkB.
  The reduction removes the nodes whose only role is that arm: RIP1ub and IKK, plus cIAP and mcIAP, which only fed
  RIP1ub. `$Low_cIAP` goes with them.
- **Calzone owns the death arms** and how NF-kB's targets hold them back:
  - DISC_TNF → CASP8 → BAX → MOMP → … → CASP3 → Apoptosis;
  - RIP1 → RIP1K → ROS → MPT → NonACD;
  - cFLIP, BCL2, XIAP.

  TNF, TNFR and RIP1 are kept for these arms. Removing them, as first planned, makes death unreachable (see
  `checks/boolean/reduction-nfkb-knockout`).
- **NFkB** becomes `logic = NOT CASP3` with rates `$u_NFkB` / `$d_NFkB` in place of IKK's 1 and 0, and `$High_NFkB` is
  kept. The composite sets `u = f`, `d = 1 − f`, where `f` is Lipniacki's free nuclear NF-kB as a fraction of all NF-kB,
  `(NFKB_nuc / Kv) / NFKB_total`, from its own `NFKB_total` rule (Kv = 5; NFKB_total = 0.06, conserved). It is
  dimensionless, with no fitted constant: about 0.0077 at the unstimulated steady state.
- **TNF** becomes an input with rates `$u_TNF` / `$d_TNF`, driven by the same receptor-occupancy signal as Lipniacki's
  TNF_R.

The cut is checked as exact against the full network under Calzone's NF-kB mutants
(`checks/boolean/reduction-high-nfkb`, `reduction-nfkb-knockout`): all 27 kept nodes agree.
- **Time.** Every rate is multiplied by `$k_time` (Calzone time units per composite second), so Calzone's internal
  rate ratios are untouched. Alex chose (2026-11-04) to **sweep `k_time` as a study axis** rather than fix one value.
  The anchors to compare against, measured: Lipniacki's NF-kB → target protein (A20) delay is about 35 min. Calzone's
  NF-kB target induction half-time is 16.6 units, and its apoptosis half-time after TNF is 8.5 units. One factor
  cannot match both; see docs/design/plan-section-b.md. Checked by `checks/boolean/pair-nfkb-seconds`.
- **Gene expression keeps Lipniacki's clock** (Alex, 2026-11-04: "anchor to Lipniacki, sweep death"). Fate is a race
  between the death arms and NF-kB's protective genes. Under TNF the full network's split depends on `$TransRate`:
  Survival 0.02 at 1/24 (MaBoSS's example), 0.20 at 1; Calzone 2010 reports about 0.30 / 0.60 / 0.10 from
  rate-free asynchronous reachability. So `$TransRate` becomes `$r_tx / $k_time`, and target genes switch on at
  `r_tx` per second whatever `k_time` is. `anchor_transcription.py` measures `r_tx` from Lipniacki itself:
  NFKB_nuc half-rise to A20 half-rise is 2107 s (35.1 min), so r_tx = ln 2 / 2107 s = 3.29e-4/s, written to
  `processed/transcription_anchor.json`. `k_time` then sweeps only the death machinery's clock. Checked by
  `checks/boolean/transcription-anchor-{fast,slow}`.
