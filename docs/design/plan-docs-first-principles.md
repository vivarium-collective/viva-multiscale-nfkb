# Plan: documentation that explains itself from first principles

**Standard (Alex, 2026-11-06):** "make sure the model explanation and explained content in documentation is fully self
explaining from first principles". A scientist new to the project must be able to follow every page without
study.yaml, the code, chat history or the cited papers. Every concept is built from what it rests on before it is used.
Every symbol and term is defined where it first appears, or linked to the page that derives it. Every formula is
derived or sourced. Internal shorthand is replaced in prose, not only glossed: d1, d7, Q1–Q4, U1/U2, plan F-ids,
finding ids f1–f10, variant codes like `decayp`, "section B", "the agenda".

**Source:** a read-only audit of `documentation/` on 2026-11-06 (branch `tnf-fate-in-space`, after 2b6421b). Line
numbers below refer to that state. Each step is one commit, built with `sphinx-build -W`.

## Status

- [x] Decision 28, absorbing death: documented in design/boolean.md with its check; glossary "Alive" updated; the
      math bug at boolean.md:97 (`\t` in `\text`) fixed; "Four checks" corrected to five.
- [x] Step 1.2, the Calzone network: science/calzone-network.md, with the node table generated from the pinned
      network (documentation/science/code/calzone_network.py; `--check` fails when stale). The wiring diagram is
      still open: conf.py has no diagram extension.
- [x] Step 2, math/maboss.md: @logic and $parameters, asynchronous updating, exponential waiting times (no memory;
      competing switches), Gillespie's algorithm, the generator and forward equation with a one-node example, T and
      W, MaBoSSProcess's one-cell readout (sample_count 1, the sampled state, seeds), and the tolerance's false-fail
      rate. Gillespie 1977 added to the bibliography.
- [x] Step 1.3, science/lipniacki-model.md: the rest state (IKK = Kprod/Kdeg = 0.2 µM; 98.7% of NF-κB bound to
      IκBα; f = 0.0077), the TNF chain, both negative feedbacks and the damped waves (the measured f(t)), the volume
      factor Kv, the NFKB_total derivation, f, and the three rates taken from the model. Species and reaction
      tables are generated from the SBML (documentation/science/code/lipniacki_model.py, `--check`), and conservation
      is proved symbolically (dropping 1/Kv fails the proof).
- [x] Step 1.1, science/boolean-networks.md:
      - why on/off; nodes, states and rules; the synchronous, asynchronous and rated updating schemes;
      - attractors and basins;
      - reachability against probability, with the rate table measured at t = 40 by
        documentation/science/code/transrate_race.py (TransRate 1/24 gives 0.014/0.952/0.030; 1 gives
        0.201/0.540/0.259).
      time.md's stale 1/24 row is logged under step 6.
- [x] Step 1.4, design/composite-primer.md (first in the design section): stores, processes, steps, ports and wiring,
      updates and types (a float update is a delta; overwrite replaces; both checked in bigraph-schema 1.8.1's source),
      time and the emitter, compose-api (runner, mash-up, registry levels), what a check is (oracle, negative), and
      compose/check.sh.
- [x] Step 1.5, math/statistics.md: binomial SE, the Wilson interval (as run_grid.py computes it), paired seeds, the
      exact McNemar test (as analysis.py computes it, with three Study 0 examples recomputed), and the quasi-steady
      occupancy estimate with its validity condition.
- [x] Step 1.6, math/timescales.md:
      - linearisation, the Jacobian, and what each kind of eigenvalue means;
      - the model's modes from analysis/d7/kinetic_timescales.json: fastest 6–10 s; slowest exactly 1/Kdeg = 8000 s;
        one zero mode, the conserved NF-κB; growth in 1 of 361 states;
      - stiffness and CVODE;
      - the 0.1× coupling rule, derived as a sample-and-hold error bound.
- [x] Step 3, reading order (2026-11-06): the top level runs getting-started → science → math → design → tutorials →
      verification → reference, with the design order below. The tutorials index has a prerequisites box. Step 1.7
      (biology yardstick, needs literature) is deferred by Alex until after steps 3–6.
- [x] Step 4, stale or contradictory statements (2026-11-06):
      - clock.md no longer says NF-κB's switching scales with k;
      - the architecture diagram shows fκ/k_time;
      - tutorial 03 states its κ = k_time case;
      - studies.md reads out alive and durable survival, and the dose is c₀ (not D);
      - tutorial 02 compares half-times (16.6 against 8.5), and its Open box became "decided in Study 0";
      - decision 25 states what Study 0 found;
      - scales.md says 31 nodes;
      - the glossary's First fate and Occupancy entries define their terms;
      - the index status and the roadmap are dated 11-06, and the roadmap gains Study 0, decision 28 and d1.
      Left for step 6: time.md's TransRate table and the unsourced "99–106 min" figure.
- [x] Step 5, calibration.md for a newcomer (2026-11-06): 0b/0c/0d defined up front; the f-ids dropped. The design
      table names the composite's layers, how TNF is held, the κ × clock grid (κ candidates, k_time formula, 200 seeded
      cells) and the 30 s one-sampled-state coupling. A variants table lists each edit and its question. r_deg is named
      as Lipniacki's c5, with A20 standing in for all four products stated as an assumption. The 1/25 and 1/7200
      arithmetic is shown, and the "Calzone alone" row is flagged as a different readout.
- [~] Step 6, per-page gaps, in progress:
      - time.md's TransRate table is generated by documentation/science/code/transrate_race.py (t = 40, 50,000
        cells, `--check`); its stale 1/24 row (0.018) is now 0.014.
      - analysis/d7/kinetic_timescales.py now records the least-damped oscillating pair per state. From 2 h after
        TNF it has period 98–102 min and e-folding 55–90 min. That figure replaces the unsourced "99–106 min,
        55–105 min" in time.md, scales.md and timescales.md; every pre-existing JSON value is unchanged.
      - coupling.md: a symbols legend (occ, d1, f, κ, k_time, each linked), and links for the NFKB_total derivation and
        the source of "f settles at 0.28";
      - switch.md: links the derivation of its ODE, and shows k_time·fκ/k_time = fκ;
      - boolean.md: a prerequisites intro (network, primer, MaBoSS; "the race" defined), and how NF-κB loss of
        function is set.
      - kinetic.md: internal ids (Q1, Q2, U1, plan F3, d7) replaced in prose; NRMSE, sim1 and species_overrides
        defined. The unverified "couples the rest state to coupling intervals" claim was dropped.
      - models.md: boundary species, IKKn/IKKa and NRMSE defined; TNF_R is 0 to 1 (not 0/1); links to the new pages.
      - rule-based.md: what rule-based models and BNGL notation are; quasi-steady defined; the McMillan model's sites
        (a binds TNF; p, for pairing, stays unbound because the published pairing rules are commented out); the
        stepwise-binding equilibrium P(n) ∝ C(3,n)·∏[R]/K_i derived from the rules. The stale claim that the BNGL
        is committed is fixed (it is untracked in the -boolean worktree). Q4 is gone. Lipniacki 2007 and
        Goldstein–Perelson citations wait for step 7, with web verification.
      - biology.md: why the waves (delayed feedback, linked); DISC, FADD and the apoptosome explained; apoptosis
        against necrosis (caspases, membrane, inflammation) and their output nodes; a link to the node page.
      - architecture.md: a diagram legend (each symbol linked) and section B explained inline.
- [ ] The rest of steps 1–8 below.

## Step 1: foundation pages (new)

1. **science/boolean-networks.md**, before models.md:
   - what a Boolean network is, and what logic rules are;
   - synchronous, asynchronous and continuous-time (MaBoSS) updating;
   - reachability and attractors;
   - why rates matter for fate fractions.
2. **science/calzone-network.md**: all 31 nodes, each with its biological meaning, logic rule and default rates, a
   legend (⊣ = inhibits) and a wiring diagram. Every rule an argument relies on must be visible here: `IKK AND NOT
   CASP3`, `NOT NFkB` (mROS), "Apoptosis follows CASP3", "Survival follows NFkB", "products switch off after one unit",
   "no node reads Apoptosis".
3. **science/lipniacki-model.md**:
   - a table of the 16 species;
   - the IKK three-state cycle;
   - IκBα/A20 delayed negative feedback, which damps the oscillations;
   - the role of K_v (nuclear concentrations to cytoplasm-volume equivalents);
   - conservation of NF-κB (no synthesis or degradation) and the NFKB_total derivation, with the 0.06 µM source.
4. **A process-bigraph and compose-api primer** (design/ or reference/):
   - Process, Step, store, port, wiring, interval, tick, emitter;
   - the composite document, `map[float]`, `overwrite`;
   - how compose-api runs and scores a check: runner, compliance case, `compliance.evaluate`, mash-up, registry levels.
5. **math/statistics.md**:
   - the binomial standard error;
   - paired seeds (the same random stream per cell, so per-cell outcomes pair);
   - the exact McNemar test, p = 2·P(Bin(b+c, ½) ≤ min(b, c));
   - the quasi-steady occupancy derivation: a two-state switch with effective rates f·r_tx and (1−f)·r_off, the
     u/(u+d) step, and the timescale-separation condition.
6. **math/timescales.md**:
   - Jacobian eigen-analysis, relaxation times, damped modes, e-folding;
   - the reason for the 0.1× coupling-interval rule (or a source for it).
7. **science/biology.md, an empirical yardstick:**
   - the fraction of cells TNF alone kills, with and without NF-κB or protein synthesis;
   - death timing (the citation time.md:23 marks pending).

## Step 2: expand math/maboss.md

- Define `@logic` (the node's rule evaluated in state s), the default rates, and `$name` parameters.
- Define the generator Q (off-diagonal entries are flip rates) and the forward equation dP/dt = PQ, with P(t) = P(0)e^{tQ}.
- Explain the Gillespie algorithm in one paragraph, citing Gillespie 1977.
- Define T and W.
- Give the rationale for the 3.5–4 SE tolerance.
- Explain the single-trajectory readout: sample_count 1, the window average rounded to 0/1 (run_grid.py).
- Add a two-node worked example.

## Step 3: reading order

- Top level: science → math → design → tutorials.
- Design: composite-primer → architecture → kinetic → spatial → boolean → time → rule-based → coupling → calibration →
  studies → decisions → roadmap. Time (k_time, r_tx) and rule-based (d1) come before coupling, which uses both;
  calibration (Study 0) comes before the headline studies, whose page depends on its result.
- Tutorials get a prerequisites box, or come last.
- history.md's definition of the agenda sections moves up front, or is replaced in prose.

## Step 4: stale or contradictory statements

- **clock.md:26:** "NF-κB's switching scales with k". It is restricted to the κ = k_time check case (decision 25).
- **NF-κB switch rates shown as u_NFkB = f.** They become fκ/k_time in:
  - architecture.md:21;
  - tutorials/03:4-5, which calls u = f "exactly as the composite wires it" (it is the check case);
  - kinetic.md, where it applies.
- **studies.md:7:** readouts P(Survival)/P(Apoptosis)/P(NonACD) become alive and durable survival (decision 23b).
  Dose "D" collides with the diffusion coefficient D.
- **tutorials/02:33-39:** the "Open" box is stale (κ decided). It compares the mean time 1/TransRate = 24 with the
  half-time 8.5; compare half-times instead (16.6 against 8.5).
- **decisions.md:35:** "durable survival insensitive to κ" is unsupported: alive varies 6.5–16% with κ at
  120 min/unit. Correct it.
- **scales.md:11:** "27 on/off nodes" should be 31.
- **roadmap.md:** dated 2026-11-04, with no Study 0, d1 or absorbing-death phase. Phases start at 3.
- **index.md:75-80:** the status omits Study 0.
- **Glossary "Occupancy":** relies on the undefined "duty cycle" and "Study 0d". "First fate" relies on the undefined
  "coupling step".

## Step 5: calibration.md (Study 0) for a newcomer

- Add a design table:
  - grid = κ × clock, 200 seeded cells each;
  - κ candidates: Calzone's flicker κ = k_time, ln2/337 s, ln2/2107 s;
  - clocks: 2/10/30/120 min per unit;
  - the layers present (kinetic + Boolean; no spatial layer, no dose–response);
  - "held at saturation": occupancy 1, so TNF_R = 1, and the TNF node is held on (u_TNF = d_TNF = 0, starting on);
  - the coupling interval of 30 s;
  - sample_count 1 and the rounding rule.
- Add a variants table: the gate removals, 0b (decay-lipniacki), 0c (persist) and 0d (decay-protective). Give each
  its edited nodes, its edit and its biological reason. Define 0b/0c/0d in one sentence each at the top. Drop the
  f-ids.
- Show the products' rate_up and rate_down from the network page. Explain why 0b's edit also hit mROS and Survival
  (they share the TransRate form).
- r_deg: name the Lipniacki parameter (A20 degradation c5). State the assumption that A20's turnover stands for cFLIP,
  BCL2, XIAP and cIAP. Define "constitutive" (acts regardless of NF-κB state).
- Show the arithmetic:
  - 1/25 against 1/24: r_tx/k_time = 3.29e-4 × 120 ≈ 0.040;
  - k_time = 1/7200 s;
  - 1/r_tx = 51 min and 1/r_deg = 56 min.
- The "Calzone alone" row is an ensemble end-state P(Survival). Say it is a different readout, compared only roughly.
- Line 4: "can't be read from either model" becomes "which of Lipniacki's timescales maps to Boolean flipping".

## Step 6: per-page gaps (from the audit)

- **boolean.md:**
  - define the rate syntax, `$High_NFkB` and the mutant switches;
  - define RIP1ub, mcIAP, SMAC, DISC_TNF and ⊣ (link the network page);
  - explain why sampling one joint state per interval gives one realised trajectory per seed;
  - link time.md's TransRate table for 0.0136/0.9534/0.0291 against the paper's 30/60/10;
  - define "race";
  - give the parameter setting for NF-κB loss of function.
- **switch.md:**
  - derive Ṗ = u(1−P) − dP by marginalising the forward equation for a node whose rates depend on no other node;
  - show k_time·fκ/k_time = fκ;
  - give the interval and W behind each window.
- **clock.md:** define Q, and state the condition that the inputs are time-homogeneous (or rescaled too).
- **coupling.md:**
  - introduce κ before the table;
  - derive NFKB_total (why the nuclear terms are divided by K_v) and explain why only *free* nuclear NF-κB counts;
  - source "f settles at 0.28";
  - explain the TNF node as a switch with P(on) = occ, and define "overwrite" and the wiring terms (primer).
- **time.md:**
  - derive the half-time 16.6 = ln2·24;
  - commit or cite the apoptosis half-time probe (8.5 units);
  - show 2.1 min, 18 min, 17 h and 30× as arithmetic;
  - state the time point and the CTMC-against-reachability reason for 30/60/10;
  - link "moves when, not who wins" to math/clock, with the fixed-horizon caveat;
  - its TransRate table states no time point or cell count, and its 1/24 row (0.018/0.951/0.031) disagrees with
    t = 40 (0.014/0.952/0.030, 50,000 cells, 2026-11-06; the check oracle gives 0.014/0.953/0.029). Generate the
    table with a script, at a stated t and N;
  - replace d7 and define the timescale terms (math/timescales).
- **models.md:**
  - define boundary species, assignment rules, IKKn/IKKa, k₁/k₂ and A20's role;
  - link the network page;
  - define NRMSE and name the comparison;
  - reorder after the Boolean primer.
- **biology.md:**
  - explain why delayed negative feedback damps the waves;
  - expand DISC, FADD and the apoptosome;
  - define apoptosis against necrosis by membrane integrity, caspase dependence and inflammation;
  - map biological entities to Calzone node names.
- **scales.md:** replace d7 use 1; define the Jacobian terms (or link them); source D = 50 µm²/s (also diffusion.md:16
  and spatial.md:29).
- **architecture.md:**
  - add a legend for d1, u_TNF/d_TNF and parameters_in;
  - add a compose-api primer link;
  - explain "section B" inline.
- **kinetic.md:**
  - drop Q1/Q2, F3, d7, U1 and species_overrides, or define them;
  - say what sim1 is (BioModels' SED-ML simulation);
  - spell out "couples the rest state to coupling intervals";
  - apply the NFKB_total derivation.
- **rule-based.md:**
  - define "quasi-steady" (100 s against hours);
  - explain the BNGL notation T(1,2,3) and R(p,a);
  - add the stepwise binding equations;
  - cite Lipniacki 2007 and Goldstein–Perelson;
  - move before coupling, since d1 is used from architecture.md onward.
- **studies.md:13-16:** give the statistic and threshold behind "collapses onto study 2's curve".
- **decisions.md:** replace Q1–Q4, U2, F6, "probe", f-ids, variant codes, `ever_dead`/`revived` and "workbench" with
  plain descriptions.
- **diffusion.md:**
  - rename the decay k (it collides with k_time) and define M;
  - derive or cite the Gaussian kernel and source the 2.5σ threshold;
  - justify 2D;
  - define finite-volume, backward Euler and control volume.
- **index.md and getting-started.md:**
  - add a "concepts in one paragraph" section (process-bigraph composite, Process/Step, oracle, gating);
  - gloss compose-api, compliance.evaluate, mash-up, harness, registry pins, COPASI and pre-equilibrated.
- **tutorials/04:** "about 79% reached no fate" was removed with decision 28 (2026-11-06). Its κ still scales with
  k_time, which is flagged in its admonition.
- **verification/index.md:** say which of Study 0's numerical claims (p-values, occupancy) have verification, or state
  the scope.

## Step 7: glossary and bibliography

- **Glossary additions:**
  - Boolean network, CTMC, MaBoSS, rate_up/rate_down, @logic;
  - Calzone unit, TransRate, u/d, r_deg;
  - duty cycle, quasi-steady, gate;
  - interval, tick, window; Process, Step, store, port;
  - paired seeds, McNemar, grid/variant, NRMSE, BioModels/SBML.
- **Bibliography additions:**
  - Lipniacki 2007, Gillespie 1977, McNemar 1947, Goldstein–Perelson;
  - COPASI, libRoadRunner/Tellurium, process-bigraph, CVODE/SUNDIALS, VCell;
  - a source for D(TNF).
  - Also define "(d7, eDMD/VAC.)" at bibliography.md:12.

## Step 8: verify

- Run `sphinx-build -W`.
- Have a fresh reader, a subagent with no project context, read in toctree order and list every term it could not
  follow. Repeat until it lists none.
