# Decision log

Every design decision in B, in order. "Alex" marks a decision Alex made; the others follow from the source or a
measurement cited in the evidence column. The plan of record is
[`docs/design/plan-section-b.md`](https://github.com/vivarium-collective/viva-multiscale-nfkb/blob/main/docs/design/plan-section-b.md).

| # | Decision | Made by | Why | Evidence | Page |
|---|---|---|---|---|---|
| 1 | Kinetic core is Lipniacki 2004 (BIOMD0000000786) | Alex (Q1) | Two sized compartments; one external stimulus; curated; engines agree | corpus NRMSE 3.6e-7 | {doc}`kinetic` |
| 2 | Tellurium, not COPASI, runs it | source | COPASI wrapper mis-sets initial concentrations, and its time doesn't accumulate | viva-copasi `processes.py:115,831` | {doc}`kinetic` |
| 3 | Remove the stimulus event; drive `TNF_R` | design | The spatial layer owns the stimulus | `lipniacki2004/prep.py` | {doc}`kinetic` |
| 4 | Pre-equilibrate once, then seed | design | Don't simulate 101 h of rest in every run | `preequilibrated-steady` | {doc}`kinetic` |
| 5 | viva-tellurium gets `parameters_in` (v0.2.3) | Alex (Q2) | Nothing could drive a parameter during a run | viva-tellurium#37 | {doc}`kinetic` |
| 6 | Spatial v1 is the extracellular TNF field | Alex (Q3) | One domain, no inter-region flux upstream yet | plan F6 | {doc}`spatial` |
| 7 | PDE first, particles later | design | Deterministic, stable, closed-form oracles; every error attributable | `checks/spatial/*` | {doc}`spatial` |
| 8 | Bolus, not a sustained source | source | Reaction rate is one scalar over the domain | viva-pde-particle `kinetics.py` | {doc}`spatial` |
| 9 | `RegionMean`/`RegionTotal` added upstream | design (U2) | No field → scalar adapter existed | viva-pde-particle#70 | {doc}`spatial` |
| 10 | Boolean engine is MaBoSS | source | BoolNet is R-only with no wrapper; MaBoSS is Python-native and rate-based | viva-maboss | {doc}`boolean` |
| 11 | Cut only RIP1ub, IKK, cIAP, mcIAP; keep TNF/TNFR/RIP1 | Alex ("most biologically accurate, model-native") | The first cut made death unreachable (Apoptosis = NonACD = 0) | `reduction-*` checks | {doc}`boolean` |
| 12 | NF-κB drives the Boolean layer via the nuclear fraction $f$ | design, under 11 | Lipniacki's own rule; dimensionless; no fitted constant | `pair-nfkb-analytic` | {doc}`coupling` |
| 13 | One `tnf_occupancy` store drives both `TNF_R` and the Boolean TNF node | design, under 11 | One owner, two readers | plan coupling graph | {doc}`coupling` |
| 14 | Seed every map key a Step writes into | measured | process-bigraph 1.9.1 drops writes to unseeded map keys | `pair-nfkb-analytic` negative | {doc}`coupling` |
| 15 | Calzone's clock is swept (`$k_time`), not fixed | Alex | No single factor fits both Lipniacki anchors | `pair-nfkb-seconds` | {doc}`time` |
| 16 | Gene expression anchored to Lipniacki ($r_\text{tx}$); `k_time` sweeps only death | Alex ("anchor to Lipniacki, sweep death") | TransRate decides the fate race; Lipniacki's transcription is fitted, death speed is not | `transcription-anchor-*` | {doc}`time` |
| 17 | No runtime rule-based layer in v1; offline dose–response instead | Alex (Q4) | Wrapper drops bound complexes; binding is quasi-steady | viva-nfsim `processes.py:84-96` | {doc}`rule-based` |
| 18 | Three headline studies from one composite | Alex ("all 1, 2, and 3") | They nest: control, headline, mechanism | — | {doc}`studies` |
| 19 | The design record lives in this workspace | Alex | Design next to the model it describes | `docs/design/` | — |
