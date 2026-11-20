# Plan: the exposure studies (dose, distance, wave timing)

Status: draft 4, 2026-11-20. Steps 1 and 2 are done, step 3 is running, and E4 is decided (decisions 49 to 55).
Decision 37 (Alex) makes these the next work. The three studies are defined in `documentation/design/studies.md`. This plan makes them runnable and
puts to Alex what they still leave open.

## Decided (Alex, 2026-11-19)

- **Clocks (E5):** 30, 60 and 120 min per unit, equally ("30, 60 and 120 equally").
- **Geometry (E1, E1b):** cells at 100, 300 and 1000 µm, with the box widened to 6 mm so the far cell stays clear of
  the absorbing band ("Keep 1000 µm, 6 mm box").
- **Equivalence (E4):** a margin of ±0.05 in the alive fraction, with about 1,700 cells per point (decision 40b; 270 was a sizing error).
- **Readout (E6):** "whatever is most biologically accurate". That is the fraction of cells alive at 24 h.
  - A cell with no fate switched on is a living cell, and any viability measurement at 24 h counts it as alive. So
    "alive at 24 h" is the biological quantity, and the dose-matching test uses it.
  - Every cell is followed for the whole 24 h, so the survival curve (fraction alive against time) and the death mode
    (apoptosis or necrosis) are reported with it; no censoring rule is needed.
  - The draft's rule of switching readouts on the undecided fraction is dropped, because it was a statistical device,
    not biology.
  - Held survival is a model state, not something an experiment measures, so it is reported but not tested.
- **E2, E3, E7 and E8, accepted as recommended** (Alex, 2026-11-19: "Accept all four"); decisions 42 to 45.
- **E4's comparator (2026-11-19, from the 24 h field):** each distance configuration against its own matched decaying
  bath, with the same peak TNF and 24 h dose, by two one-sided tests ("Matched decaying bath"; decision 50). Bolus sizes
  1, 10 and 100 µM·µm² (decision 51).
- **Arms and verdict (2026-11-20):** the distance study runs NF-κB intact and knocked out ("Intact and knocked out";
  decision 52). Each configuration comes out equivalent, different (Holm-corrected) or inconclusive ("Three outcomes
  per config"; decision 53).
- **Correction (decision 49):** the dose pilot started every cell with TNF on (Study 1's builder seeds the fate
  network's state store that way), which killed about a quarter of the cells at any dose. The dose study starts TNF
  off, as the field composite does; finding 2's numbers carry the artifact.

## What the sources say

- **The investigation's question** (`investigation.yaml`): "does space act only through the dose that arrives, or
  also through when it arrives?"
- **The three studies** (`studies.md`):
  - **Dose:** a uniform bath at $c_0$, with optional decay λ.
  - **Distance:** a point bolus at distance $r$ (sweeping $r$, the bolus size and `k_time`).
  - **Wave timing:** the distance runs' TNF front arrival against NF-κB's nuclear peaks.
  - **The test:** map each distance run onto the dose curve by the TNF dose that reached the cell, its peak and its
    integral. The collapse statistic is fixed before the distance runs.
- **Study 1 and decision 37.** The composite does not reproduce NF-κB-dependent survival under held TNF, so these
  studies rest on differences in fate between exposures. Survival lapsing as NF-κB's node cycles is read from the
  rules and not tested (`validation.md`).
- **The MVP** (decisions 31–36):
  - field → RegionMean (the cell's ring) → one-site occupancy ($K_d$ 19 pM) → Lipniacki + MaBoSS;
  - a 2-D, 200 µm reflecting box, D 100 µm²/s, dx 2 µm, dt 0.05 s;
  - coupling every 30 s, and a 990 s field run takes 8 s.
- **Study 0's population builder** shares one Lipniacki model between 200 seeded fate networks (seeds 1–200), over 24 h.
- **compose-api refuses runs longer than 1000 s.**

## What the design has to get right

**1. Arrival timing is testable only if arrival is slow on the system's own clock.**
- **The MVP's box hides timing.** A bolus there is uniform within about $L^2/4D$ ≈ 100 s, while fate is decided over
  hours. A review probe put rings at 20, 40 and 80 µm: occupancy at the first coupling sample (30 s) was 0.922, 0.919
  and 0.910, then identical.
- **A steady source with decay hides it too.** Each ring then holds a constant dose within about 1/λ, so both designs
  collapse onto the dose curve by construction.
- **Arrival takes $r^2/4D$:** 5 min at about 350 µm, and 1 h at about 1.2 mm (D 100). Lipniacki's NF-κB half-rise is
  5.6 min, and fate takes hours. So a test of timing needs distances of hundreds of µm to about 1 mm, in a box of about
  3 mm, so the farthest cell stays clear of the walls.
- **A closed box keeps the whole bolus.** It ends uniform at $M/A$ after about $L^2/4D$ (6 h for 3 mm), while the
  peak at radius $r$ is about $M/(\pi e r^2)$. So the plateau-to-peak ratio is $\pi e r^2/A$: in a 3 mm box, 0.009
  at 100 µm, 0.09 at 300 µm and 0.95 at 1000 µm. The far cell would then see the box filling up, not a pulse.
  Uniform decay doesn't separate them, because it multiplies the whole field by $e^{-\lambda t}$. In 2-D, the time
  integral at a fixed distance also grows without bound in an open plane (late times go as $1/t$), so the dose
  integral needs an outer boundary that removes TNF, or a finite window.
- **The coupling interval** of 30 s is then short against arrival. The interval rule in `time.md` (about 0.1 × the
  fastest timescale crossing an edge) is still untested (roadmap phase 5), and the pilot tests it for this geometry.

**2. The dose pilot (done 2026-11-19; its numbers carry a TNF pulse at t = 0, decision 49).**
- **Method:** Study 1's builder with held sub-saturating occupancy; intact cells; 200 cells; 24 h; seeds 1–200;
  viva-maboss 0.1.2. Scratchpad only, not committed.
- **Alive at 24 h** (cells with no fate in brackets):

  | Clock (min per unit) | occupancy 0.05 | 0.2 | 0.5 | 1.0 |
  |---|---|---|---|---|
  | 30 | 0.50 (80) | 0.11 (16) | 0.005 | 0 |
  | 60 | 0.595 (102) | 0.31 (41) | 0.085 (5) | 0.005 |
  | 120 | 0.745 (127) | 0.61 (88) | 0.32 (36) | 0.15 (5) |

- **What it shows:**
  - Alive falls steadily with dose at every clock.
  - 120 min per unit at occupancy 1.0 gives 0.15, against Study 1's 0.16.
  - The curve is steepest below occupancy 0.2, so the dose study must reach down to about 0.005.
  - **60 min per unit** spans almost the whole range (0.6 to 0.005), with few undecided cells from 0.2 up.
  - The lowest dose leaves 40–64% of cells undecided at every clock.

**3. The engine's capabilities and limits** (viva-pde-particle 25e8a05, probed 2026-11-19).
- **Local terms.** A reaction term is mass action over any species, and `external_conc` species are arrays over the
  grid. So a local source, or uptake by a cell, can be expressed.
- **Inside a process-bigraph 1.9.1 Composite:**
  - a seeded static mask works (mass $sAt$ exactly);
  - an unseeded or unwired mask is silently zero;
  - a Step that rewrites the mask needs the type `map[overwrite[array[float]]]`, because the default adds.
- **Not needed here.** The recommended exposure design doesn't use these. The tissue plan's v2 does.

**4. Cost, measured where possible.**
- **Population points:** a 200-cell 24 h point took 357 s with four running at once (review probe). The "40 min for
  12 points" in the 11-06 notes was an estimate.
- **Emission:** field documents emit every second (991 rows for 990 s). The studies emit every 30 s, the coupling
  interval.
- **The field: the geometry pilot (done 2026-11-19).** A 3 mm box, bolus at the centre, cells at 100, 300 and 1000 µm,
  3 h.
  - dx 10 µm at dt 0.25 s gives the same TNF at every cell as dx 5 µm or dt 0.05 s, to three decimals. So the cheap
    grid is converged here.
  - It takes about 5 min per 3 h of model time in the 3 mm box. The decided 6 mm box (601² nodes) took 20 min per
    3 h, so about 2.6 h per 24 h document.
  - Diffusion is backward-Euler implicit; reactions are explicit.

## Corrections to the docs (their own item)

**The spatial.md correction.** `spatial.md` ("a bolus, not a sustained source"), `decisions.md` row 8 and `studies.md`
("Why a bolus") all say a localised source can't be expressed, because the reaction rate is one scalar. That is wrong
(finding 3).
- **The correction:** the reason is withdrawn, and the bolus stays for the studies on the merits of finding 1.
- **The pages:**
  - decision 8 is struck through, with a successor row giving the real reason;
  - spatial.md and studies.md are corrected;
  - a check that a seeded masked source works through a Composite is added, with negative copies for an unseeded and
    an unwired mask.
- **Its own PR,** under Alex's standing approval for this repository: done 2026-11-19 (decision 8b,
  `checks/spatial/local-source`).

## Decisions for Alex (each with a recommendation)

| # | Question | Recommendation | Why |
|---|---|---|---|
| E1 | The distance study's geometry | **Decided:** a bolus at the centre of a **6 mm** box, with cells at 100, 300 and 1000 µm (TNF peaks at each about 25 s, 4 min and 41 min after release). **dx 10 µm, dt 0.25 s**, which the geometry pilot found converged (finding 4) | Only slow arrival can separate timing from dose (finding 1). The MVP's 200 µm box and a steady source both collapse by construction. Cost: decision 34 found the ring's error first order in dt and independent of dx at 1–2 µm, so a coarser dx may hold. If dx 10 µm passes the ring check, a 3 mm box is 301² nodes, about 9× the MVP. To be measured, not assumed |
| E1b | Where the bolus goes once it has passed: the box keeps it (finding 1) | **Decided: an absorbing outer band**, a local uptake term on the box's edge nodes (finding 3), **in a 6 mm box** | Geometry pilot, against the open-medium (free-space) solution over 3 h. A 3 mm closed box: the 1000 µm cell plateaus (last/peak 0.90; dose 1.31×). A 3 mm box with the band: the 1000 µm cell, 350 µm from the band, is pulled down (peak 0.94×, dose 0.69×). **The 6 mm box with the band: every cell matches** (peak 0.997, 0.999 and 0.9999; 3 h dose 1.000, 1.000 and 0.999 at 100, 300 and 1000 µm). Uniform clearance λ can't separate peak from plateau (finding 1). The band stands for an open medium, not a biological mechanism |
| E2 | The bolus sizes | **Chosen from the free-space solution before running** (the band makes the medium open), so that the peak occupancy at the three distances spans the dose curve's range at the chosen clock | `studies.md` sweeps the bolus size. With $K_d$ at 19 pM, the size decides whether every ring saturates |
| E3 | The dose study's exposures | **Held baths from occupancy about 0.005 up to the highest peak E2's cells reach (up to 1), denser below 0.2 where the pilot's curve is steepest, plus decaying baths**, one matched to each distance-study ring and bolus size (decision 50, which replaced half-lives spanning the free-space pulse durations) | The dose curve must cover what the distance runs deliver, both peak and duration. A decay fast against 30 s (half-life under a minute) never registers at the first coupling sample |
| E4 | The collapse test, fixed before the distance runs | **Decided: two one-sided tests** with a margin of ±0.05 in the alive fraction and about 1,700 cells per side (decision 40b), **each distance configuration against its own matched decaying bath** (same peak TNF, same 24 h dose; decision 50). Each configuration is equivalent, different (Holm-corrected) or inconclusive (decision 53). The unit is the cell (one seed) | A pulse's peak occupancy (0.006 to 0.98) and its occupancy averaged over 24 h (0.001 to 0.12) are far apart, so a one-number map onto the held curve would be decided by the choice of number. The matched bath differs from the pulse only in what space adds: arrival delay and shape |
| E5 | Clocks | **Decided: 30, 60 and 120 min per unit, equally** | Dose pilot (finding 2): at 60 the curve spans 0.6 to 0.005; at 30 it falls to near zero by occupancy 0.5; at 120 undecided cells dominate the low doses. Running all three shows whether a conclusion depends on the clock |
| E6 | The readout | **Decided: alive at 24 h**, the fraction of cells with no death node ever on, which is what a viability measurement counts. The survival curve and the death mode are reported with it; held survival is reported, not tested | See "Decided" above |
| E7 | Where runs execute | **Locally** for the dose study, in `compose/` through compose-api's runner, plus one 990 s live run per new composite. The distance study and the many-cells work run on compose-api instead (decision 54; Alex, 2026-11-20), planned in `plan-compose-api-dispatch.md` | 24 h is 86 times compose-api's cap, and compose-api can't resume a run. For the distance study the cap is lifted for signed-in runs instead (the dispatch plan's route A, Alex's choice) |
| E8 | D | **100 µm²/s** (decision 33). This closes the roadmap's open question | It's already the MVP's value |

## Work (atomic steps, each checked)

1. **The pilot**, done 2026-11-19 (findings 2 and 4), to be committed with the dose study:
   - 12 dose points;
   - one geometry probe: TNF at the cell at 100, 300 and 1000 µm against the free-space solution, with the
     absorbing band (E1b), at candidate dx and dt (finding 4) and with 30 s coupling. It reports each cell's peak,
     integral and arrival, and the band's reflection error.
2. **The geometry check** `spatial/far-bolus`: the chosen box, band and grid against the free-space solution at the
   three rings, within the measured band error. Its negatives are D 50 and a misplaced ring (done 2026-11-19: `checks/spatial/far-bolus`).
   The band acts only after about 6 h, beyond the check's hour, so its effect is measured in the 24 h exposure runs.
3. **The dose study** (`s2-dose`, running since 2026-11-19), at E5's clocks, intact and knocked out, 7 batches of 270
   seeds (1,890 cells per point; decision 40b): 8 held baths and the 9 matched decaying baths (decision 50), with
   every cell's TNF off at the start (decision 49). The decaying bath is checked by `checks/coupled/decaying-bath`.
4. **Pre-register E4** in the distance study before any distance run: decisions 40, 40b and 50 to 53. The scorer is
   written and tested (`s2-dose/e4_verdict.py`, `tests/test_e4_verdict.py`): Newcombe's hybrid score 90% interval
   inside ±0.05 is equivalent; otherwise Fisher's exact test, Holm-corrected over the 54 configurations, rejecting at
   5% is different; otherwise inconclusive. A configuration that passes both tests (a difference inside the margin
   that is still significant) is equivalent, with both tests reported (decision 55).
5. **The distance study:**
   - several rings in one document, which is valid because cells only sample the field;
   - one Lipniacki model and 270 fate networks per ring per batch, 7 batches (decision 40b);
   - at bolus sizes 1, 10 and 100 µM·µm² (decision 51), E5's clocks, and both arms (decision 52);
   - its first document measures the cost before the rest run.
6. **Score E4; the wave-timing analysis** from the distance runs: front arrival (the half-peak time at the ring)
   against NF-κB's first nuclear peak. No new runs.
7. **Docs:** decisions rows, a page with generated tables (`--check`), and a fresh-reader round.

## Not in this plan

- Cells taking up TNF, which is the tissue plan's v2.
- Secretion, which neither plan covers: no provided source gives it.
- 3-D, and the nuclear envelope.
- Changing how Survival reads NF-κB (decision 37 leaves it open).
- Lifting compose-api's cap, which decision 54 now needs: planned separately in `plan-compose-api-dispatch.md`.

## Relation to the tissue plan

The distance study's composite, several cells on one field, each fed by RegionMean, is the tissue plan's v1 structure,
and one generator serves both. The shared decisions are in `plan-tissue.md` §Shared.
