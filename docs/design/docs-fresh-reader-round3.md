# Docs fresh-reader pass, round 3 (2026-11-06)

A third independent reader, with the same brief as rounds 1 and 2, read at commit c82987a (after step 1.7). It found
29 items, down from 26 in round 2 only because Study 1 and absorbing death had not been carried back into earlier
pages. It recomputed every derived number it could (window averages, Wilson intervals, occupancies, McNemar p values,
absorbing-death formulas, the image term, the 2D/3D formulas, the conservation algebra, net protection); all match.
Each item is verified against its source before it is fixed.

The marks mean:
- [ ] open;
- [x] fixed, with the commit;
- [-] not a defect, with the reason.

## The 10 most serious

1. [x] (46872ef) calibration.md:219 ("A held, saturating dose cannot show NF-κB protection in this composite") and
   studies.md:35-37 ("protection is not expected to add a signal") contradict validation.md:47-50 (net protection
   10.5 points at 120 min per unit, 12.5 at 180) and roadmap.md:23.
2. [x] (46872ef) studies.md:33 and tutorials/04:45-46 say nearly every cell dies "at every death clock"; Study 0 ran 2–120 min
   per unit, and validation.md shows 46.5–98% alive at 180–480.
3. [x] (0957494) composite-primer.md:51 "about 8 s across 40 µm" contradicts scales.md:24 (4 s).
4. [x] (46872ef) decisions.md:45 (row 29) "the cited experiments also held saturating TNF"; Lee 2016 is about a short pulse.
5. [x] (46872ef) validation.md:44 column "Calzone alone, matched" has no stated quantity; :55 claims the knocked-out composite
   matches Calzone alone, with no column showing it.
6. [x] (d6528dd) occ is "the fraction of TNF receptors occupied" (architecture.md:29, coupling.md:15, glossary:60), but
   rule-based.md:57 says the observable is open, and :46-54 derives P(n) per trimer.
7. [x] (d6528dd) coupling.md:23-24 says the Boolean layer is a readout in v1 (no Boolean → spatial edge), but boolean.md:148-150,
   calibration.md:233-234 and decisions row 28 justify the death flag by stopping a dead cell signalling.
8. [x] (d6528dd) decisions.md:30 (row 17) gives "binding is quasi-steady" as settled; rule-based.md:24-26 and roadmap.md:29-30
   call it open (a factor of about 3).
9. [x] (d6528dd) timescales.md:65-66 says TNF at the cell changes over minutes; the primer and glossary say seconds; time.md:94
   says seconds to minutes.
10. [x] (d6528dd) coupling.md:12 `node_probabilities.Apoptosis`/`NonACD` is undefined; maboss.md:88 says the process writes
    `node_state`.

## The rest, by page

- [x] (46872ef) index.md:68: the Verification card says every check has a proven-failing negative; verification/index.md:15-16
  says six do not.
- [x] (46872ef) index.md:89-90: Status says d1 is next and omits Study 1 and the open Option A decision.
- [x] (9692d10) science/scales.md:18-20: broken parenthetical; "d7" path in prose.
- [x] (9692d10) science/lipniacki-model.md:59: `nfkb_fraction` unexplained.
- [x] (d6528dd) science/calzone-network.md:69-70 and `_calzone_nodes.md`: initial states "from cellfate.cfg, with TNF switched
  on"; switch.md:59,65 says the cfg has TNF off. Say the file sets it off and the generator forces it on.
- [x] (d6528dd) science/calzone-network.md:85: `prep.py` used before it is explained, unlinked; there are two.
- [x] (d6528dd) math/switch.md:27-28 and design/coupling.md:50: "MaBoSS multiplies every rate by `$k_time`"; the composite's
  rewritten network (prep.py) does.
- [x] (d6528dd) math/clock.md:19: which `prep.py`; no link.
- [-] (real file paths; renaming the directory would break committed references, and the pages say what each script computes) math/timescales.md:29-30 and design/time.md:84: "d7" in paths.
- [x] (9692d10) design/boolean.md:161: "knockout variants were not rerun"; Study 0 has no knockout variant.
- [x] (9692d10) design/time.md:25: IFNγ and why HeLa cells are sensitised are not explained.
- [x] (d6528dd) design/rule-based.md:21-23: broken sentence; the point argues against its own heading.
- [x] (9692d10) design/calibration.md:32 (and decisions.md:35): "undecided" not defined.
- [x] (9692d10) design/calibration.md:34, :88: "(glossary)" unlinked, forward; "the three ways the death machinery closes the
  gate" not listed.
- [x] (9692d10) design/calibration.md:133: "every pair" undefined.
- [x] (46872ef) design/validation.md:8: "decision 29" unlinked.
- [x] (46872ef) design/validation.md:56-58: "never protects more than Calzone alone" and "equal at 240" against 9.0 vs 8.8; noise
  not stated.
- [x] (46872ef) design/validation.md:61: "24 h is only 3 to 12 Calzone units at these clocks"; 48 at the 30 min clock.
- [-] (the codes are keys into the cited data files, in the evidence column; each row's prose names the study) design/decisions.md:40-42: variant codes `decay-*`, `persist-protective`, `decay-protective` unexplained.
- [x] (9692d10) design/roadmap.md:46-47: "the timescale analysis's planned second use" is not on the timescales page.
- [x] (9692d10) tutorials/02:43: "(tutorial 4)" unlinked.

Total: 31 entries (the reader counted 29 issues, counting an issue that spans pages once): 29 fixed, 2 not defects.
