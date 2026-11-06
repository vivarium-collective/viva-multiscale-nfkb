# Docs fresh-reader pass, round 2 (2026-11-06)

This is a second independent reader, with the same brief as round 1. It did not read round 1's report, and read at
commit d325ad1. It found 26 items, down from round 1's 99, and re-derived all the arithmetic it could; every number
checked out. Each item still has to be verified against the source before it is fixed.

The marks mean:
- [ ] open;
- [x] fixed, with the commit;
- [-] not a defect, with the reason.

## The 10 most serious

1. [x] (fixed: the pair checks run a 3-node fragment (read in make_pair_nfkb_analytic.py); 'death arms at 0' removed) switch.md:66, coupling.md:63–65 and verification:55 say the pair checks hold the gate "open with TNF off". In the
   full network, TNF off closes IKK. The check actually runs a reduced network with IKK and CASP3 as constant nodes
   (make_pair_nfkb_analytic.py), and no page says so. "The death arms stay at 0" cannot be followed either.
2. [x] (fixed) architecture.md:70–71 says every check has "a mutated copy proven to fail"; six checks do not.
3. [x] (fixed: 'each coupling built so far') index.md:22–23 says "each coupling is checked against an independent oracle", but the spatial→kinetic coupling and
   d1 are not built.
4. [x] (fixed: 30 s is the kinetic→fate edge; the spatial edge will need ~1 s) composite-primer.md:47–49 and glossary:55 justify 30 s from f alone. The TNF-at-cell edge changes over about
   8 s, which by the 0.1× rule would need about 1 s. Either explain, or say that 30 s is the kinetic–Boolean interval
   (Study 0 had no spatial layer).
5. [x] (fixed: 16 species × 7 rows + 1 row count, read from the case) kinetic.md:31 says "113 expectations" but not how they are made up (113 is prime).
6. [x] (fixed: flicker turns Survival off at rate 1) tutorial 02:26–32 says Survival is 0.014 at f = 1 but 0 at f ≤ 0.75, and neither reason given explains the drop.
   The real one: the node flickers off, and Survival (`NFkB`) switches off at rate 1.
7. [x] (fixed: 'its rate' (original or rewritten, 11 nodes)) verification:53 says "62 rates exactly `$k_time * (original)`"; 11 nodes have rewritten rates.
8. [x] (fixed: one definition (NFkB's rule; three ways to close it) in glossary and calibration) "Gate" is defined differently across pages: coupling:51 (IKK on, CASP3 off), glossary:82 (three conditions),
   calibration:87 (two), boolean:84 (four). Use one definition.
9. [x] (fixed: anchor_transcription.py says half-way from start to peak; lipniacki-model and calibration corrected) lipniacki-model:100 and calibration:97 define half-rise as "half its first peak", while clock.md:47 says
   "half-way from its pre-stimulus value to the peak". Use one definition, verified against anchor_transcription.py.
10. [x] (fixed: rule added to coupling.md's wiring rules with its source) composite-primer:27–28 cites coupling.md for the whole-map write rule, but coupling.md does not state it.

## Other items

- [ ] boolean-networks:50: where t = 40 Calzone units comes from (presumably MaBoSS's example configuration).
- [ ] models:20: Tellurium is undefined.
- [ ] scales:18: the half-rise and A20 delay rows come from simulation (anchor_transcription.py), not from the Jacobian.
- [ ] switch:59: the calzone-reference window [9.9, 10] and its reference configuration are not explained.
- [ ] switch:60: 0.482590 needs f = 0.56268 unrounded; with 0.5627 the value is 0.482609. Give f to five digits.
- [ ] composite-primer:64: "two files" against tutorial 01's "three things", where the generator lives outside the
  folder.
- [ ] spatial:41–43: VCell and pyvcell are undefined.
- [ ] boolean:31: cmaboss is undefined.
- [ ] boolean:62, calibration:35 and decisions:21, 35, 38: "adversarial review" is never described.
- [ ] boolean:138 says 22.5–27% and calibration:90 says 22–27%.
- [ ] calibration:30: 2 to 120 min is a factor of 60, about 1.8 orders of magnitude, not two.
- [ ] calibration:34, 57, 76, 183: "first fate" is used without a link, and it is ambiguous whether Survival counts.
- [ ] decisions:3 says "every design decision", but the `bulk_species: false` decision has no row.
- [ ] decisions:40 (row 27): "save no cell" overstates the result (9 newly alive against 17 newly dead; no net change).
- [ ] tutorial 04:43: "the open question of tutorial 2" is now settled; the reference is stale.
- [ ] bibliography:32–34: the Noé & Nüske plan is mentioned on no page.
