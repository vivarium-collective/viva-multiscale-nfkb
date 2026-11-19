# Plan: many cells on one TNF field (the tissue step)

Status: draft 3, 2026-11-19: revised after an adversarial review, a review by the tyssue session and the exposure pilot. Nothing is built. Source: the roadmap's "Later:
Many cells" (one TNF field feeding N cells, each with its own kinetic and Boolean stack). The MVP plan named it the
next step after one cell (decision 31).

## Decided (Alex, 2026-11-19)

- **T1 (decision 46):** v1 as infrastructure now, with no study of its own; v2 after the distance study.
- **T2, T3 (decision 47):** the layout as recommended. The number of runs is decided after measuring cost at 6 and 24
  cells.
- **T4, T5 (decision 48):** no variation between cells in v1. v2's uptake is drafted as a proposal from the binding
  numbers ($K_d$, $k_\text{off}$), with the receptor number and the internalisation rate swept, for Alex's approval.
  Binding alone removes no TNF at equilibrium.

## What the sources say

- **Scale.** compose-api's scale ladder (`docs/plan/plan-scaling-classification.md`): "Many cells of a multicellular
  organism → `tissue`". So N cells on a field is tissue whether or not they interact. The MVP is `cell`.
- **The MVP's stack per cell:**
  - RegionMean (the ring mask) → `tnf_at_cell` → the dose-response Step (`priority` 1) → Lipniacki → nuclear
    fraction → MaBoSS;
  - coupling every 30 s.
  - The `priority` works around process-bigraph#284. #285 fixed it upstream (73ca6fb), but no release has it yet, so
    the workaround stays.
- **Death is absorbing** (decision 28).
- **The roadmap cites Schliemann et al. 2011** for this kind of heterogeneity.
- **The engine** (viva-pde-particle 25e8a05; probes 2026-11-19; see `plan-exposure-studies.md`, finding 3):
  - mask arrays in `external_conc` express local uptake;
  - a seeded static mask works through a Composite;
  - a Step that rewrites one needs `map[overwrite[array[float]]]`, since the default adds;
  - an unseeded or unwired mask is silently zero;
  - reactions are explicit, so a local rate times dt must stay well below 1.
- **Document size** (the MVP composite JSON is 713 KB):
  - the inline SBML is 250 KB per cell;
  - the initial field is 273 KB;
  - each RegionMean mask is 92 KB at the MVP's 101² grid.
  - RegionMean requires a dense grid-shaped mask (`steps/transfer.py`). At the exposure geometry's 601² grid (6 mm, dx 10 µm), each
    mask is about 3 MB, so 24 cells come to about 80 MB of masks plus the field. That makes U3 (below) close to necessary. A region given geometrically (a
    centre and radius) or as sparse node indices would need a viva-pde-particle change, which is a follow-up (U3).
  - `TelluriumProcess` accepts `model_file`, and compose-api's runner resolves it inside an .omex. The MVP inlined the
    SBML on purpose (`make_tnf_field_cell.py`). Whether the workbench's dispatch sends an .omex is unconfirmed.

## Two parts

**v1, cells that only sample.**
- N cells on the exposure studies' field (`plan-exposure-studies.md`, E1).
- Each cell has its own stack: RegionMean, the dose-response Step, Lipniacki and one fate network.
- The cells are independent, so each cell's fate depends only on its position, its TNF history and its seed.
- It adds no new mechanism, and **no study of its own**. With no uptake, every cell at one radius receives the same
  field, so their Lipniacki trajectories are identical and only the fate seeds differ. That is the distance study's
  "one Lipniacki model and 200 fate networks per ring", at greater cost.
- So v1 is an **infrastructure milestone**: the generator, the independence check, scheduling under N priority
  Steps, cost, document size, and one live demonstration. Per-cell stacks pay off in v2, once uptake makes cells
  differ.

**v2, cells that take up TNF.**
- Each cell removes TNF at its ring, so neighbours shade each other.
- It needs a whole mechanism that no provided source gives: the uptake's form (for example, removal proportional to
  bound receptors, with ring mask × $k_u$ × occupancy) and its numbers (receptors per cell, internalisation, and how
  they map onto the 2-D model's 1 µm layer). They are a `pending` proposal for Alex, not facts.
- A dead cell's uptake must stop (decision 28), which is one reason each cell needs its own stack.

**Not here:** secretion (no provided source gives it), cells as obstacles (that needs v2 spatial's regions), 3-D,
movement and division.

## Decisions for Alex (each with a recommendation)

| # | Question | Recommendation | Why |
|---|---|---|---|
| T1 | Scope | **v1 (infrastructure) now; v2 after the distance study** | v1 needs nothing unprovided and adds no study. v2 changes each cell's dose, so it should come after the exposure studies show how dose alone acts |
| T2 | Layout | **24 cells: 8 at each of the distance study's three radii** (100, 300 and 1000 µm; exposure E1, decided), around one bolus | The cells at one radius share a TNF history, so they are replicates. Each has its own seed (no two cells share one), so no trajectories repeat |
| T3 | Replication for v2's study | **Decided after the cost step.** 8 cells per radius per document is too few for fate statistics, so several documents with disjoint seed sets reach the exposure plan's n per radius (E4) | The cost of 24 stacks is unknown. It's measured first (step 4) |
| T4 | Heterogeneity beyond position and seed | **Not in v1** | The roadmap cites Schliemann 2011, but which property varies, and how much, would come from that paper, as a pending proposal |
| T5 | v2's uptake mechanism | **Alex provides it, or approves a proposed form and sweeps its rate** | Neither its form nor its numbers are in the provided sources |

## Work (atomic steps, each checked)

1. **One generator for N cells**, shared with the distance study (`make_field_cells.py`):
   - positions → ring masks, and one stack per cell;
   - emission every 30 s;
   - it asserts that rings don't overlap and stay inside the box, and that seeds are distinct.
2. **Check `coupled/cells-independent`:** with no uptake, each cell's rows in an N-cell document equal a one-cell
   document at that position and seed, to rel 1e-12. Its negatives are two rings swapped, and two cells given the
   same seed.
3. **Check scheduling under N:** a sweep over six hash seeds gives identical rows (the #284 workaround holding with N
   priority-1 Steps).
4. **Cost** at N = 6 and N = 24, for 24 h locally: wall time, memory and document size, with the SBML inline and as
   `model_file`. The numbers go to Alex before T3 is set.
5. **A live demonstration:** the N = 24 document, 990 s, on compose-api as an inferred mash-up. It uses the same
   entries as the MVP, so no new registry entry; this outward step is confirmed with Alex. It proves the
   infrastructure, not a result: in 990 s the 100 µm and 300 µm cells see their peaks (arrival about 25 s and 4 min),
   and the 1000 µm cells see almost nothing (their TNF peaks about 41 min in).
6. **v2, after T1 and T5:**
   - an uptake Step writes each living cell's weighted ring mask into `external_conc` (as overwrite, seeded);
   - check `spatial/uptake-mass-balance`: the field's mass loss equals the summed uptake, and one cell's steady state
     matches its closed form. Its negatives are an unseeded mask, the default type that adds, and a dead cell still
     taking up TNF;
   - the scheduling seed sweep also covers the uptake Steps;
   - then the v2 study, against the distance study at matched positions, applying the exposure studies' test per
     cell.
7. **Docs:** decisions rows, a tissue page, and a fresh-reader round.

## Shared with the exposure studies (decided once, not twice)

| Question | Decided in | How the tissue step uses it |
|---|---|---|
| The cell on the grid (ring sampling, no volume exclusion, 9 µm radius) | MVP decision 33, kept by the exposure plan | Unchanged in v1. In v2 the ring is also where uptake acts |
| The geometry, absorbing band, bolus sizes and grid | Exposure E1, E1b, E2, and its step 2 check | The tissue field is the distance study's field. In v2, cell uptake joins the band as a second local sink |
| The coupling interval (30 s) and the interval rule | Decision 35; tested in the exposure pilot | The same interval, unless the pilot says otherwise |
| compose-api's 1000 s cap | Exposure E7 | Science runs locally, plus one 990 s live demonstration |
| The death clock | Exposure E5 (the pilot) | One clock, the one the exposure studies keep |
| The readout and collapse test | Exposure E4, E6 | Applied per cell, by its own TNF dose |
| Seeds | Exposure: seeds 1–200 per condition | Each cell gets a distinct seed, and documents use disjoint seed sets |
| Emission cadence | Every 30 s (both plans) | The same |
| D | Decision 33 (exposure E8) | Unchanged |
