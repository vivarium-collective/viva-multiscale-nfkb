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

## The ownership boundary: what each model owns

This decision changed twice. Both rounds are recorded here, because the reasons are the design.

### Round 1: cutting TNF, TNFR, RIP1 and IKK made death unreachable

Lipniacki already models TNF → IKK → NF-κB, and Calzone has its own version of that chain. Under the one-owner
principle ({doc}`architecture`), the first plan cut Calzone's copy: TNF, TNFR, RIP1 and IKK. In Calzone, though,
TNF→TNFR also drives **both death arms**:
- apoptosis: TNFR → DISC_TNF → CASP8 → BAX → MOMP → … → CASP3;
- necrosis: TNFR → RIP1 → RIP1K → ROS → MPT → NonACD.

Measured through `MaBoSSProcess` with TNF on at t = 40, that cut left P(Apoptosis) = P(NonACD) = 0, whatever NF-κB did.

### Round 2: cutting only the "duplicated" arm dropped death's feedback on NF-κB

The next version kept TNF, TNFR and RIP1, and removed only RIP1ub, IKK, cIAP and mcIAP. Those looked like they served
only the activation route. That cut was exact *with NF-κB clamped*. An adversarial review showed the composite never
runs that way, because those nodes are also how death **shuts NF-κB down**:
- **caspase-8 cleaves RIP1:** CASP8 ⊣ RIP1 → RIP1ub → IKK → NF-κB;
- **SMAC sequesters cIAP:** SMAC ⊣ cIAP → RIP1ub;
- **NF-κB keeps cIAP topped up:** NF-κB → mcIAP → cIAP, a pro-survival loop.

Lipniacki has none of these. On the full network with TNF on, t = 40:

| Network | Survival | Apoptosis | NonACD |
|---|---|---|---|
| Calzone, unmodified | 0.0136 | 0.9534 | 0.0291 |
| Only those loops cut | 0.1281 | 0.8312 | 0.0001 |

The loops carry almost all of Calzone's necrosis.

### The decision (Alex, 2026-11-04): "Remove nothing; Calzone gates"

The two models don't describe the same *thing*, so there is nothing to remove:

- **Lipniacki owns how much.** Its fitted kinetics say how much NF-κB is free in the nucleus over time once TNF acts:
  the nuclear fraction $f$.
- **Calzone owns whether the route is open.** Its chain says whether NF-κB activation is still possible: the receptor
  complex is intact, RIP1 isn't cleaved, the cIAPs aren't sequestered, and caspase-3 is off. That is crosstalk with
  the death machinery, which Lipniacki lacks.

All 31 Calzone nodes and every logic rule are kept. Only rates change:

| Node | Change | Why |
|---|---|---|
| NFkB | logic kept (`IKK AND NOT CASP3`); rates `@logic ? $u_NFkB : 0`, `@logic ? $d_NFkB : 1` | while the route is open, NF-κB follows Lipniacki ($u = f$, $d = 1-f$); when it closes, NF-κB switches off as in Calzone; `$High_NFkB` is kept |
| TNF | rates `$u_TNF` / `$d_TNF` | driven by the same receptor-occupancy signal as Lipniacki's `TNF_R` |
| every node | each rate × `$k_time` | the death-machinery clock the studies sweep ({doc}`time`) |
| cIAP, cFLIP, BCL2, mROS, mcIAP, mXIAP, Survival | `$TransRate` → `$r_tx / $k_time` | Calzone's transcription-scale steps (NF-κB-induced cFLIP, BCL2, mXIAP, mcIAP; cIAP from mcIAP; mROS, induced when NF-κB is *off*; the Survival phenotype) switch on at Lipniacki's rate ({doc}`time`) |

`workspace/datasets/calzone2010_cellfate/prep.py` writes `processed/cellfate_coupled.bnd` (31 nodes) and
`processed/coupling.json`. It refuses to write unless:
- the input is the pinned file;
- each node it rewrites is exactly the expected upstream text;
- every rate is wrapped in `$k_time`.

### Proof that the coupling is Calzone wherever it should be

At $u = 1$, $d = 0$ (NF-κB switching like Calzone's own node), $k_	ext{time} = 1$ and $r_	ext{tx} = 1/24$, the
coupled network **is** Calzone's network. Four checks compare it with the unmodified network run on the MaBoSS engine
directly, TNF on, all 31 nodes, abs 0.01:

| Check | What it adds |
|---|---|
| `coupled-equals-full` | t = 40, where the death arms have acted |
| `coupled-equals-full-early` | the window [7, 8], while caspase-3 switches on. The gate's `NOT CASP3` term is visible only here: P(NF-κB) is 0.215 with it and 0.244 without. Later, caspase-8 has closed the route anyway. |
| `coupled-equals-full-seconds` | `k_time = 1/60` over 2400 s with $r_\text{tx} = k_\text{time}/24$: a pure change of clock at t = 40. An unclocked race-deciding rate (CASP8) fails it. |
| `coupled-equals-full-early-seconds` | the same over [420, 480] s, while the cascade moves: unclocked BAX or MOMP fail it |
| `coupled-nfkb-knockout` | no nuclear NF-κB against Calzone's NF-κB loss of function: the death arms are intact |

**Proven to fail:**
- the caspase-3 term removed: NF-κB 0.243 instead of 0.215;
- caspase-8's rates left off the clock: apoptosis 0.972 instead of 0.953;
- BAX's rates left off the clock (early window): apoptosis 0.449 instead of 0.323;
- Round 2's cut: survival 0.25 instead of 0.014, necrosis 4e-5 instead of 0.029.

## Clock

Calzone's rates have no time unit. {doc}`time` covers how they were put on the composite's clock: one swept factor
`$k_time`, and gene expression anchored to Lipniacki.
