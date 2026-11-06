# Docs fresh-reader pass, round 5 (2026-11-06)

A fifth independent reader, same brief, read at e0d5d6b. It found 16 items and recomputed the numbers it could; all
held. Two items are factual errors that survived every earlier round: the kinetic state has 15 floating species, not
16 (TNF is a boundary species; libRoadRunner's full Jacobian on the driven SBML is 15 × 15, and the sim1 check's 113
expectations are 15 species and the time at 7 points, plus a row count). An adversarial review of round 4's fixes
(5eb8425..e0d5d6b) ran alongside and found 9 more; they are listed here too, marked R. Each item is verified against
its source before it is fixed.

The marks mean:
- [ ] open;
- [x] fixed, with the commit;
- [-] not a defect, with the reason.

## Round 5

1. [x] (a81b823) kinetic.md:31-32 "16 species at each of 7 time points": 15 floating species plus the time.
2. [x] (a81b823) timescales.md:8 "the vector of 16 concentrations": the state is 15 (a 16th, constant TNF would add a zero mode).
3. [x] (a81b823) validation.md:23-26: the comparator differs from the composite in the NF-κB node; the "So" hides that.
4. [x] (a81b823) scales.md:24 "40 µm" unsourced; the 4 s and 0.4 s figures rest on it.
5. [x] (a81b823) durable survival (studies, calibration) and held survival (validation) never related; no glossary entries for
   held survival or net protection.
6. [x] (a81b823) time.md:31, :41 "Decision 1", "Decision 2" clash with the log's rows 15 and 16.
7. [x] (a81b823) glossary "Variant: a run of Study 0" against "a Study 1 variant".
8. [x] (a81b823) coupling.md:12 "gate (*candidate*)" overloads Gate.
9. [x] (a81b823) biology.md:57 337 s used before it is derived, unlinked.
10. [x] (a81b823) lipniacki-model.md:9, scales.md:10: every species "in µM", but TNF is a 0-to-1 signal.
11. [x] (a81b823) spatial.md:13 "each node's control volume": a grid point.
12. [x] (a81b823) boolean.md:63, calibration.md:35 "adversarial review" unlinked before decisions.md defines it.
13. [x] (a81b823) validation.md:17-18 net protection defined as a count, reported in points; the Phase B table's "No fate at
    all (intact / KO)" holds counts in a table of fractions, and "KO" is undefined.
14. [x] (a81b823) studies.md:4 "investigation" unlinked.
15. [x] (a81b823) decisions row 18: the mapping of "1, 2 and 3" to the named studies is ambiguous.
16. [x] (a81b823) history.md:26 "a core short name such as `local:RAMEmitter`" unexplained.

## Adversarial review of round 4's fixes

- [x] (a81b823) R1 spatial.md:7-8 and :10-11, kinetic.md:11-12: table rows wrapped onto two source lines break the table.
- [x] (a81b823) R2 calzone-network.md:73-74 "Both races are what the studies vary": the activation race runs wholly on
  `k_time`; the studies vary the protection race.
- [x] (a81b823) R3 roadmap.md:24 "real survival" left over.
- [x] (a81b823) R4 studies.md:28, boolean.md:6, decisions row 16: "race" unnamed, or "there" points at the wrong page.
- [x] (a81b823) R5 clock.md, time.md, tutorial 04: `k_time` also runs the protective products' switch-off (and, in tutorial
  4's sweep, the NF-κB node); clock.md:27 "NF-κB's own switching does not" holds only while its route is open.
- [x] (a81b823) R6 validation.md:22 "the results below give both": held survival is shown only at 200 min per unit.
- [x] (a81b823) R7 kinetic.md:10, decisions.md:12: NRMSE 3.6e-7 still has no file named.
- [x] (a81b823) R8 plan-section-b.md:210 "the sweep moves only the death machinery".
- [x] (a81b823) R9 s1 study.yaml claim: "does not meet the standard" needs "read as held survival".

Total: 25, all fixed. R1 also covered a fourth wrapped row the review missed (getting-started.md:27).
