# The Boolean layer <span class="layer boolean">Boolean</span>

## Engine: MaBoSS through `MaBoSSProcess`

MaBoSS simulates a Boolean network as a continuous-time Markov chain. Every node flips with a rate given by the
network's logic, and an ensemble of trajectories gives each node's probability of being on. viva-maboss wraps it as
`MaBoSSProcess`. Its configuration keys, verified at viva-maboss@3fdccd7, are:
- `network`;
- `parameters`, a default for every `$name`;
- `initial_state`, 0 or 1 per node;
- `sample_count`, `windows_per_interval` and `seed`.

Two properties of the wrapper shape the design:

- **One joint state is carried between intervals.** MaBoSS starts a run from per-node initial values, not from a
  joint distribution, so the Process samples one joint state from the ensemble and starts the next interval from it.
  A single interval is the exact ensemble. Several intervals behave like one trajectory per seed, and many seeds
  together recover the ensemble.
- **Probabilities are window averages.** MaBoSS reports each probability averaged over a time window. The Process
  reports the interval's last window (see {doc}`../math/switch`).

## Why MaBoSS and not BoolNet

The agenda first asked about BoolNet. BoolNet is an R package with no process-bigraph wrapper, while MaBoSS is
Python-native through `cmaboss`, and its stochastic, rate-based semantics fit a composite with a real-time clock.
viva-maboss was built for this purpose; its README gives the full comparison.

## Source

Calzone 2010's network as MaBoSS ships it: `cellfate.bnd`, `cellfate.cfg` and MaBoSS's own reference output
`refer/res_probtraj.csv`. All three are from sysbio-curie/MaBoSS@375ffad, kept unedited in
`workspace/datasets/calzone2010_cellfate/raw/` with their sha256.

**First check:** `checks/boolean/calzone-reference` runs the full 31-node network through `MaBoSSProcess` in the
reference configuration. Every node matches MaBoSS's own reference output (abs 0.008). The one node that moves, mROS,
also matches its analytic value: run 0.339387, reference 0.339405, analytic 0.339384.

## The ownership boundary: what to cut

### The question

Lipniacki already models TNF → IKK → NF-κB. Calzone's network has its own version of that chain. Under the
one-owner principle ({doc}`architecture`), one of them has to go. Which nodes exactly?

### The first plan, and why it was wrong

The plan first cut **TNF, TNFR, RIP1 and IKK**. Reading the network shows that in Calzone, TNF→TNFR does more than
lead to NF-κB. It also drives **both death arms**:

- apoptosis: TNFR → DISC_TNF → CASP8 → BAX → MOMP → … → CASP3 → Apoptosis;
- necrosis: TNFR → RIP1 → RIP1K → ROS → MPT → NonACD.

Measured through `MaBoSSProcess`, with TNF on and t = 40:

| Network | Survival | Apoptosis | NonACD |
|---|---|---|---|
| Full Calzone, TNF off | 0.00 | 0.00 | 0.00 |
| Full Calzone, TNF on | 0.015 | 0.949 | 0.032 |
| **First plan's cut**, NF-κB driven on | 0.794 | **0.000** | **0.000** |
| **First plan's cut**, NF-κB driven off | 0.000 | **0.000** | **0.000** |

The first cut made death unreachable. Every headline study would then show only survival.

### The decision (Alex, 2026-11-04: "the most biologically accurate and overall model-native option")

Cut **only the nodes whose sole role is the arm Lipniacki models**. Lipniacki's lumped TNF→IKK step stands in for
Calzone's RIP1 → RIP1ub → IKK → NFkB, so:

| Node | Change | Why |
|---|---|---|
| RIP1ub | removed | its only output is IKK |
| IKK | removed | its only output is NFkB; Lipniacki models IKK |
| cIAP | removed | its only output was RIP1ub |
| mcIAP | removed | its only output was cIAP |
| `$Low_cIAP` | removed | used only by cIAP |
| TNF, TNFR, RIP1, RIP1K, DISC_TNF | **kept** | the death arms need them |
| NFkB | `logic = NOT CASP3`, rates `$u_NFkB` / `$d_NFkB` | NF-κB activity comes from Lipniacki; caspase-3 can still shut NF-κB off, as in Calzone; `$High_NFkB` is kept |
| TNF | rates `$u_TNF` / `$d_TNF` | driven by the same receptor-occupancy signal as Lipniacki's `TNF_R` |

`workspace/datasets/calzone2010_cellfate/prep.py` does this and writes `processed/cellfate_reduced.bnd` (27 nodes) and
`processed/reduction.json`, which records each change and why. It refuses to write unless:
- the input is the pinned file;
- each node it rewrites is exactly the expected upstream text;
- no kept node still refers to a removed one.

### Proof that the cut is exact

If the removed nodes act on the rest of the network only through NFkB, then once NFkB is fixed, the reduced and full
networks must agree on every kept node. Calzone's own mutants fix NFkB:

- **`reduction-high-nfkb`:** reduced vs full, both with `$High_NFkB = 1` (NF-κB forced on). Survival 0.80,
  apoptosis 0.065; all 27 kept nodes agree within 0.01.
- **`reduction-nfkb-knockout`:** reduced with no NF-κB input vs full with NF-κB loss of function. Apoptosis 0.91,
  necrosis 0.09; all 27 agree.

The full network runs on the MaBoSS engine directly, and the reduced one through `MaBoSSProcess`. Both checks have
been shown to fail on wrong reductions:
- **the first plan's cut:** apoptosis 0 instead of 0.91;
- **a cut that also drops cFLIP:** CASP8 locks on (1.0 instead of 0.21).

These two mutants also reproduce the paper's central point: NF-κB protects the cell from TNF.

## Clock

Calzone's rates have no time unit. {doc}`time` covers how they were put on the composite's clock: one swept factor
`$k_time`, and gene expression anchored to Lipniacki.
