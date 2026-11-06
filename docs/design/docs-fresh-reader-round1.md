# Docs fresh-reader pass, round 1 (2026-11-06)

Step 8 of `plan-docs-first-principles.md`. A subagent with no project context, playing a scientist new to the project,
read all 44 pages of `documentation/` in toctree order, read-only, at commit 73e0c2f. It re-derived most of the
arithmetic and found it holds: the half-lives, Wilson intervals, McNemar p values, window averages, the image-term
bound, the absorbing-death integral and the occupancy table.

The 99 items below are claims from that report. Each must be verified against the source before it is fixed.

The legend says how far each one has got:
- [ ] open;
- [x] fixed, with the commit;
- [-] checked and found not to be a defect, with the reason.

## The 10 most serious

1. [x] (fixed: index says only kinetic→Boolean is checked; spatial→kinetic and d1 next) index.md:80 and 25–26 say every pairwise coupling "has been built and checked". roadmap.md:10–11 says the
   spatial→kinetic coupling is next and d1 is in progress. The two contradict each other.
2. [x] (fixed: wording says negatives where recorded; six checks lack one (counted from the catalogue, not five or seven)) composite-primer.md:67–71 and verification/index.md:5,14 say every check has a proven-failing negative, but the
   catalogue (verification/index.md:44–53) shows "—" for 7 checks.
3. [x] (verified narrower: the run-env pins equal compose-api's manifest exactly (4 packages); viva-tellurium's bump landed in 0.7.79 (#502), so the roadmap row was stale; RegionMean (#70, open) needs a pin move later. Fixed in architecture, roadmap, diffusion) getting-started.md:26, architecture.md:76–77 and history.md:31 say the run environment is "pinned exactly" to
   production and that the composite needs "no new registry entry". Against that:
   - viva-tellurium 0.2.3's pin bump is still pending;
   - RegionMean is an unmerged PR (#70).
   It is unclear what environment the checks actually use.
4. [x] (fixed: Calzone's method from the paper's own Methods (equal probability per transition; fraction of paths; 'a strong assumption'); reduced model defined) boolean-networks.md:47–61 (also models.md:36–37 and time.md:50–51) says rate-free reachability cannot give
   fractions, yet quotes the Calzone paper's 30/60/10%. "Reduced model" is never defined.
5. [x] (fixed: κ derived (half-rise of f(1−e^{−κt}) at ln2/κ; 337 s = NFKB_nuc half-rise to half its first peak, transcription_anchor.json)) calibration.md:97–98 and coupling.md:54 justify κ = ln 2/337 s only as "Lipniacki's half-rise". The step from a
   concentration's half-rise to a node's flip rate is never derived.
6. [x] (fixed: one unit lasts 1/k_time s (calzone-network, glossary)) glossary.md:36 and calzone-network.md:22 say `k_time` is "how many seconds a unit lasts". glossary.md:89,
   clock.md:5 and time.md:32 say it is units per second, the inverse.
7. [x] (fixed: coupling.md inputs at 414 s) coupling.md:63 says the check's inputs are "held at the peak". coupling.md:47–48 and tutorial 03:5 say they are
   held at 414 s, still rising.
8. [x] (fixed: two different manipulations, both stated (loops cut on the full network, against the Round 2 network in the check at u = 1, d = 0)) boolean.md:72 gives Round 2 as survival 0.1281 and NonACD 0.0001. boolean.md:120 and verification:50 give
   0.25 and 4e-5, and the conditions are not stated.
9. [x] (fixed: 30 s shown to satisfy the 0.1× rule (0.1 × 337 ≈ 34 s); base step and global_time_precision defined; roadmap's d7 labels replaced) The 30 s coupling interval is never derived. time.md:95 uses "base step" without defining it, and roadmap.md:12
   uses "d7 intervals" and "d7 step 5".
10. [x] (fixed: a step runs when a store it reads is written to, even without change (process-bigraph 1.9.1; make_kinetic_boolean.py's note)) composite-primer.md:26 and glossary.md:127 say a step runs when its input *changes*. coupling.md:81 says it
    fires every tick its inputs are touched, even for a zero delta.

## By page, in reading order

**index.md**
- [x] (batch A) :9–14: the engine and adapter names (FVReactionDiffusion, viva-*, MathExpressionStep, RegionMean) and BioModels
  are not glossed or linked. The "viva" prefix is unexplained.
- [x] (batch A: two published models and a TNF field) :6–7: "three published models, each running in its own engine". models.md's three are Lipniacki, Calzone and
  McMillan; McMillan is not a runtime layer, and the spatial layer is not a published model.
- [-] :81: Study 0 and "headline studies" are bare names. (Both are linked to their pages; a link counts as defined.)
- [ ] :83: plan-section-b.md ("section B") is not explained or linked to history.

**getting-started.md**
- [x] (batch A) :14: "workspace" and "image build" are undefined.
- [x] (batch A) :26: see top-10 item 3; "bigraph-schema" is undefined.
- [x] (batch A) :27: "the workspace package, its dashboard" is undefined.
- [x] (batch A) :36: "pre-equilibrated steady state" is unlinked.
- [x] (batch A) :38: "full network" and "clock" are unlinked.

**science/biology.md**
- [x] (batch A) :49–53: v1 and v2 are undefined.

**science/boolean-networks.md**
- [x] (batch A) :50: "Calzone units" and the `$` prefix are used before they are defined, with no link.
- [x] (batch A) :51: "cells" here means trajectories, which are defined only later.
- [x] (145c27d) :47–61: see top-10 item 4.

**science/models.md**
- [x] (batch A: defined on the landing page's "New here?") :17 and later: "Alex" is used as known everywhere before decisions.md defines it (also in kinetic, spatial,
  boolean, time, rule-based, coupling, calibration, studies and roadmap).
- [x] (batch A) :20–21: "viva-biomodels' screen" is undefined, and the NRMSE normalisation is not stated.
- [x] (batch A: runners-up, stated neutrally; rate rule and event defined) :24–25: the rejection reasons don't follow: why do "106 local parameters" or "rate rule + event" disqualify a
  model? "Rate rule" and "event" are undefined.
- [x] (145c27d) :37: "reduced model" is undefined.
- [x] (batch A) :48: RuleHub and BioNetGen are undefined here.

**science/lipniacki-model.md and _lipniacki_reactions.md**
- [x] (batch A) The reactions `NFKB_export` and `IkB_export` move species *into* the nucleus. The SBML's names conflict with the
  page's "import".
- [x] (batch A) `ModelValue_1` is undefined (it is set to Kv).
- [x] (batch A) :100: the source of 337 s is only linked forward; the units read as "s" rather than s⁻¹.

**science/calzone-network.md**
- [x] (145c27d) :22: the direction of `k_time` (top-10 item 6).
- [x] (batch A) :26–28 and :64: check ids are not linked to the verification page.

**science/scales.md**
- [-] :19: the "d7" path. (A file path in the repository, not shorthand used as explanation.)
- [ ] :23: D is assumed, with no source.

**math/maboss.md**
- [ ] :76: `interval` is defined only later, with no link.
- [ ] :88: the "step" in `SeedSequence([seed, step])` is undefined.
- [ ] :95: the studies' W (10) is never stated as theirs.

**math/switch.md**
- [ ] :60: f = 0.5627 has no source here.
- [ ] :57–62: check names are not linked; "with the clock converted" gives no factor.

**math/clock.md**
- [ ] :5: the direction of `k_time` (top-10 item 6).

**math/statistics.md**
- [ ] :61–63: 0c and 0d are used before they are defined.

**math/timescales.md**
- [ ] :29–30: the "d7" path.
- [ ] :63: "edge" is used before the primer defines it, with no link.

**math/diffusion.md**
- [ ] :11: why the grid is 2D is not argued (an admitted gap).
- [ ] :44: "rel" is undefined.
- [ ] :49–50: RegionTotal is called "added upstream", but it is an open PR.

**design/composite-primer.md**
- [ ] :5: bigraph-schema is undefined.
- [ ] :26: when a step runs (top-10 item 10).
- [ ] :45–46: 30 s (top-10 item 9).
- [ ] :57–58: the registry levels are not listed.
- [ ] :60–63: a check folder's contents disagree with tutorial 01 (case.yaml, document.pbg, and a generator outside the
  folder).
- [ ] :67–71: negatives (top-10 item 2).

**design/architecture.md**
- [ ] :12, 29: the name "d1" is unexplained.
- [ ] :61–66: principle 3 says "as a release", but RegionMean is unreleased.
- [ ] :76–77: "inferred mash-up" and viva-basic-processes are undefined; "no new registry entry" (top-10 item 3).
- [ ] :81–83: sections A and B are only partly explained.

**design/kinetic.md**
- [ ] :11: the COPASI rejection needs the source to be read; "time does not accumulate" is unexplained.
- [ ] :28: SED-ML is undefined.

**design/spatial.md**
- [ ] :7: plan F5 and F6, the Smoldyn hybrid, transfer adapters, viva-smoldyn and viva-fenics are undefined.
- [ ] :8: "(Alex, Q3)".
- [ ] :9: "splitting error" is undefined.
- [ ] :11: "(U2)".
- [ ] :39–41: operator split, transport deltas, "re-seeded from the kinetic store" and VCell are undefined.
  "viva-pde-particle wraps VCell's solver" appears nowhere else.

**design/boolean.md**
- [ ] :30: "the agenda".
- [ ] :41: the tolerance abs 0.008 is not derived, and the reference run's N is not given.
- [ ] :56: "with TNF on at t = 40" reads as TNF switched on at 40.
- [ ] :72 against :120: Round 2's numbers (top-10 item 8).
- [ ] :90: the NFkB row says u = f, d = 1 − f; the composite uses fκ/k_time.
- [ ] :111 against :117: 0.244 against 0.243.
- [ ] :134–135: 7.5% conflicts with decisions.md:34's "10–27%".

**design/time.md**
- [ ] :16 against :20: where 8.6 comes from (the script prints it, but the page quotes only 8.9 for the script).
- [ ] :25: "hours usually reported" (citation pending; step 1.7).
- [ ] :53–54: "at 1/24 the cell dies whatever the dose", with no dose-varied run shown.
- [ ] :76: the uniform-clock 0.014 is not derived, and its k_time is not stated.
- [ ] :81: the "d7" path.
- [ ] :95: "base step" and global_time_precision are used before they are explained.

**design/rule-based.md**
- [ ] :1, 8: the name "d1".
- [ ] :16–17: the BNGL `~` states and `R(l,l)` are undefined.
- [ ] :19–21: quasi-steady fails as stated: binding takes ~100 s against NF-κB's 337 s half-rise, which is not a
  separation of timescales.
- [ ] :33–34: "not on this branch yet" is internal.
- [ ] :58: "the plan" is internal.
- [ ] :72: "chunked" is undefined.

**design/coupling.md**
- [ ] :7: the cell's size, position and representation on the grid are never specified ("cell-surface voxels").
- [ ] :10: why the TNF node's flip speed is scaled by k_time while NF-κB's is not is never argued.
- [ ] :47 against :63: peak against 414 s (top-10 item 7).
- [ ] :54: κ (top-10 item 5).
- [ ] :74: the seeded parameter list omits absorb_death.
- [ ] :81: when a step runs (top-10 item 10).

**design/calibration.md**
- [ ] :11–16, 86, 106: 0b, 0c and 0d are called "follow-ups/variants" in one place and "Studies" in another.
- [ ] :30: "Calzone's own flicker" for κ = k_time, while coupling.md:59 says Calzone's own node does not flicker.
- [ ] :30: "brackets κ between the fastest and slowest NF-κB timescale" does not follow: κ = k_time spans 1/120 to
  1/7200 s⁻¹.
- [ ] :36: "workbench" is undefined.
- [ ] :90: the clock is not stated for "200 of 200".
- [ ] :97–98: κ (top-10 item 5).
- [ ] :138: refers to the page's own edit history.

**design/studies.md**
- [ ] :9: "phase" is undefined for a damped signal.

**design/decisions.md**
- [ ] :20: row 11's first cut is "TNF/TNFR/RIP1", while boolean.md:51 says it also included IKK.
- [ ] :22–23: "following row 11", but 11 is superseded (11b).
- [ ] :25: "No single factor fits both Lipniacki anchors" contradicts time.md (Lipniacki against Calzone).
- [ ] :34: "10–27%" against 7.5% and 22.5–27%.
- [ ] :40: "(f9, f10)".

**design/roadmap.md**
- [ ] :3–4, 8–9: U1 and U2.
- [ ] :9, 17: pin bumps and the open PR, against "no new registry entry" (top-10 item 3).
- [ ] :12: "d7 intervals" and "d7 step 5" (top-10 item 9).

**tutorials/01-checks.md**
- [ ] :15–21: the folder contents (see composite-primer).

**tutorials/04-death-clock.md**
- [ ] :29: "changes both who wins and how the cell dies", against time.md:53 and calibration.md:75.

**verification/index.md**
- [ ] :5, 14 against :44–53: negatives (top-10 item 2).
- [ ] :45–46: "corpus" is defined only in reference/datasets.md.
- [ ] :63: "every case is written by a script beside it", but the harness cases are copied.

**reference/glossary.md**
- [ ] :36 against :89: the direction of `k_time` (top-10 item 6).
- [ ] :51: 30 s is cited to timescales, which does not derive it.
- [ ] :127: when a step runs (top-10 item 10).
- [ ] :151: "viva" and "workspace" are undefined.
- [ ] The glossary lacks the internal ids still used: Study 0, 0b/0c/0d, U1/U2, d7, F5/F6, Q3, f9/f10, workbench,
  workspace, harness, corpus, inferred mash-up.

**reference/history.md**
- [ ] :3: agenda-onboarding.md is an internal document.
- [ ] :12–20: viva-pde-particle and viva-basic-processes are not among Section A's seven, so how they are registered is
  unexplained.
