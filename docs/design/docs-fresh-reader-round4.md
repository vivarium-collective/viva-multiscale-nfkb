# Docs fresh-reader pass, round 4 (2026-11-06)

A fourth independent reader, same brief, read at 9692d10 (before 5eb8425). It found 19 items, recomputed every derived
number (Study 0 and Study 1 counts and percentages included), and found them all correct. The main item is real:
several pages say `k_time` moves only the death machinery, which Study 1 showed is not how the composite is built.
Each item is verified against its source before it is fixed.

The marks mean:
- [ ] open;
- [x] fixed, with the commit;
- [-] not a defect, with the reason.

## The 10 most serious

1. [x] (e9e343f) "`k_time` moves only the death machinery" (math/clock.md:33, design/time.md:72, decisions row 16,
   tutorials/04:30) against validation.md:19-21: every rate but the genes and the NF-κB node runs on `k_time`,
   NF-κB's activation route included.
2. [x] (e9e343f) "The race" means two things: the death route against the slow protective genes (boolean.md:6-7, time.md:43,
   calzone-network.md:64-65) and caspase-8 against NF-κB's activation route (validation.md:71); index, studies:35 and
   calibration:221 do not say which. calzone-network's "Why held TNF mostly kills" explains it by `$TransRate` alone,
   which Phase A shows cannot be the whole reason.
3. [x] (e9e343f) d1 "in progress" (roadmap:10, rule-based:30, reference/datasets:14) against "after the validation study" and
   "before d1" (roadmap:17, :27-28, index).
4. [x] (5eb8425) roadmap:24 "proposed standard" against validation:5 "accepted".
5. [x] (e9e343f) validation:32 "Survival saturates near 25%"; the table reports Alive.
6. [x] (e9e343f) validation:27-31: Phase A's Alive sits beside earlier Survival fractions (0.156 alive against 0.201 Survival at
   TransRate 1) with no explanation of how Survival can exceed Alive.
7. [x] (e9e343f) validation:67-69: "real survival" is a criterion never stated beforehand; the standard at :4-5 is qualitative.
8. [x] (e9e343f) statistics.md:41-47: b, c, "gained", "lost" used before the McNemar section defines them; n never defined.
9. [x] (e9e343f) NRMSE 3.6e-7 (models.md:22-23, kinetic.md:10, decisions:12) has no stated source.
10. [x] (e9e343f) calzone-network.md:24-25 and glossary:176: `$TransRate` marks "NF-κB's target genes, and cIAP"; the node table
    also puts it on mROS and Survival.

## The rest

- [x] (e9e343f) boolean-networks.md:58: "1/24 (MaBoSS's example)" unexplained until models.md, unlinked.
- [x] (e9e343f) maboss.md:97-98: the studies' W = 10 is unsourced.
- [x] (e9e343f) kinetic.md:31: "floating species" undefined.
- [x] (e9e343f) spatial.md:7 (and later): "PDE" never expanded or tied to the diffusion equation.
- [x] (e9e343f: the sentence is dropped; no committed data backs it) boolean.md:160-161: "A review found the same at 0.5 and 2 min per unit (6 h)": which review, and what is 6 h.
- [x] (e9e343f) boolean.md:165-178 and verification/index.md:57: $k$ reused as the death node's switch-on rate, though clock.md
  defines $k$ as `k_time`.
- [x] (e9e343f) rule-based.md:20, :74: "RNG" not expanded.
- [x] (e9e343f) studies.md:8: "optional linear decay" against diffusion.md's first-order decay $-\lambda c$.
- [x] (e9e343f) tutorials/04:23-24: "by 8 h" is the last window's average, 7.6 to 8 h.

Total: 19, all fixed.
