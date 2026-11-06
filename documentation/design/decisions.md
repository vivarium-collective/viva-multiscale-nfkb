# Decision log

Every design decision in this workspace, in order. "Alex" marks a decision made by Alex Patrie, who leads the
project, with their words where they were recorded. "design", "source" and "measured" mark decisions that follow from the
design principles ({doc}`architecture`), from a model's source, or from a measurement; the evidence column cites it. The plan of record is
[`docs/design/plan-section-b.md`](https://github.com/vivarium-collective/viva-multiscale-nfkb/blob/main/docs/design/plan-section-b.md).

| # | Decision | Made by | Why | Evidence | Page |
|---|---|---|---|---|---|
| 1 | Kinetic core is Lipniacki 2004 (BIOMD0000000786) | Alex | Two sized compartments; one external stimulus; curated; engines agree | COPASI and Tellurium trajectories differ by NRMSE 3.6e-7 (viva-biomodels' screen) | {doc}`kinetic` |
| 2 | Tellurium, not COPASI, runs it | source | COPASI wrapper mis-sets initial concentrations, and its time doesn't accumulate | viva-copasi `processes.py:115,831` | {doc}`kinetic` |
| 3 | Remove the stimulus event; drive `TNF_R` | design | The spatial layer owns the stimulus | `lipniacki2004/prep.py` | {doc}`kinetic` |
| 4 | Pre-equilibrate once, then seed | design | Don't simulate 101 h of rest in every run | `preequilibrated-steady` | {doc}`kinetic` |
| 5 | viva-tellurium gets `parameters_in` (v0.2.3) | Alex | Nothing could drive a parameter during a run | viva-tellurium#37 | {doc}`kinetic` |
| 6 | Spatial v1 is the extracellular TNF field | Alex | One domain, no inter-region flux upstream yet | `docs/design/plan-section-b.md` (spatial layer) | {doc}`spatial` |
| 7 | PDE first, particles later | design | Deterministic, stable, closed-form oracles; every error attributable | `checks/spatial/*` | {doc}`spatial` |
| 8 | Bolus, not a sustained source | source | Reaction rate is one scalar over the domain | viva-pde-particle `kinetics.py` | {doc}`spatial` |
| 9 | `RegionMean`/`RegionTotal` added upstream | design (an upstream change) | No field → scalar adapter existed | viva-pde-particle#70 | {doc}`spatial` |
| 10 | Boolean engine is MaBoSS | source | BoolNet is R-only with no wrapper; MaBoSS is Python-native and rate-based | viva-maboss | {doc}`boolean` |
| 11 | ~~Cut only RIP1ub, IKK, cIAP, mcIAP~~ (superseded by 11b) | Alex ("most biologically accurate, model-native") | The first cut (TNF/TNFR/RIP1) made death unreachable | a test run of the cut network ({doc}`boolean`, Round 1) | {doc}`boolean` |
| 11b | **Remove nothing; Calzone gates.** NFkB keeps `IKK AND NOT CASP3` and follows Lipniacki's $f$ while it holds | Alex | Round-2 cut dropped Calzone's death → NF-κB feedbacks (adversarial review; NonACD 0.029 → 0.0001) | `coupled-*` checks | {doc}`boolean` |
| 12 | NF-κB drives the Boolean layer via the nuclear fraction $f$ | design, following row 11 | Lipniacki's own rule; dimensionless; no fitted constant | `pair-nfkb-analytic` | {doc}`coupling` |
| 13 | One `tnf_occupancy` store drives both `TNF_R` and the Boolean TNF node | design, following row 11 | One owner, two readers | `docs/design/plan-section-b.md` (coupling graph) | {doc}`coupling` |
| 14 | Seed every map key a Step writes into | measured | process-bigraph 1.9.1 drops writes to unseeded map keys | `pair-nfkb-analytic` negative | {doc}`coupling` |
| 15 | Calzone's clock is swept (`$k_time`), not fixed | Alex | No single factor fits both Lipniacki anchors | `pair-nfkb-seconds` | {doc}`time` |
| 16 | Gene expression anchored to Lipniacki ($r_\text{tx}$); `k_time` sweeps only death | Alex ("anchor to Lipniacki, sweep death") | TransRate decides the fate race; Lipniacki's transcription is fitted, death speed is not | `transcription-anchor-*` | {doc}`time` |
| 17 | No runtime rule-based layer in v1; offline dose–response instead | Alex | Wrapper drops bound complexes; binding is quasi-steady | viva-nfsim `processes.py:84-96` | {doc}`rule-based` |
| 18 | Three headline studies from one composite | Alex ("all 1, 2, and 3") | They nest: control, headline, mechanism | — | {doc}`studies` |
| 19 | The design record lives in this workspace | Alex | Design next to the model it describes | `docs/design/` | — |
| 20 | Calibrate κ and the death clock in a study (Study 0) before the headline studies | Alex ("investigation + studies") | Neither model gives either speed; the headline studies depend on both | `s0-coupling-calibration/study.yaml` | {doc}`calibration` |
| 21 | Studies run in the pinned `compose/` environment; the workbench only records them | Alex ("Pinned env; workbench records") | Results are what compose-api produces; the workbench needs a newer process-bigraph | `run_grid.py` | {doc}`calibration` |
| 22 | 24 h of model time at every clock | Alex ("24 hours everywhere") | At 8 h, 77–85% of cells were undecided at 120 min per unit | void 8 h grid | {doc}`calibration` |
| 23 | ~~Count each cell once, by its end state~~ (superseded by 23b); never sum fate nodes | measured | Calzone's fate nodes overlap; the 8 h grid double-counted and was voided | `analysis.py` | {doc}`calibration` |
| 23b | **A cell is dead from the first tick any death node is on; "alive" is the primary readout** | measured (biology: death is irreversible) | Calzone's death nodes are not absorbing: they switch off when CASP3 or ATP loss reverses. The end state showed 10–27% of cells as alive after they had died | `analysis.py` (`ever_dead`, `revived`) | {doc}`calibration` |
| 24 | Variants reuse the grid's seeds and are compared cell by cell (exact McNemar) | adversarial review | Unpaired fractions hid a consistent shift | `data/paired.json` | {doc}`calibration` |
| 25 | κ = ln 2 / 337 s, Lipniacki's NF-κB speed | Alex | Measured, not fitted; independent of the death clock. Study 0: at 2–30 min per Calzone unit no κ leaves any cell alive; at 120 min this κ leaves the most alive (16%, against 6.5% and 9.5%) | `data/fate-table.json` | {doc}`coupling` |
| 26 | ~~Protective-protein decay at A20's turnover (Study 0b)~~ (confounded; superseded by 26b) | Alex ("Anchor protein decay") | The edit also slowed mROS (a necrosis driver) and the Survival readout | `data/paired.json` (decay-*) | {doc}`calibration` |
| 26b | Persistence bound first (Study 0c): cFLIP, BCL2, mXIAP, mcIAP never switch off | Alex ("Run 0c bound first"); node set from review | Decides whether persistence is a lever at all before modelling its rate | `population.py` `persist-protective` | {doc}`calibration` |
| 26c | Protein decay at A20's turnover on the four protective products only (Study 0d, the corrected 26) | Alex ("Anchor protein decay"), executed as intended | Measures how much of 26b's bound the real turnover gives | `population.py` `decay-protective` | {doc}`calibration` |
| 27 | **The next lever is exposure (d1, McMillan 2021's TNF → receptor dose–response), not graded transcription** | Alex (2026-11-06) | Under held, saturating TNF the protective products save no cell at their measured turnover (Study 0d). Graded transcription keeps the time-averaged induction $f\,r_\text{tx}$, so it predicts no rescue; exposure is what the spatial studies vary | `s0-coupling-calibration/study.yaml` (f9, f10) | {doc}`calibration` |
| 28 | **Death is absorbing in the composite's network**: Apoptosis and NonACD never switch off once on, through a parameter `absorb_death` (0 = Calzone's network exactly, 1 = the composite) | Alex (2026-11-06) | Death is irreversible, and the readout already counts it that way (23b), but Calzone's death nodes switch off when CASP3 or ATP loss reverses. In tissue a dead cell must not keep signalling. A parameter, written as a switch `($absorb_death ? 0 : 1)`, keeps the `coupled-equals-full` checks valid at 0 and can give no negative rate | `prep.py`; `checks/boolean/absorbing-death` (analytic; 0 fails it); `checks/boolean/coupled-*`; Study 0 rerun on its seeds (no first death moved) | {doc}`boolean` |
