# The Boolean layer <span class="layer boolean">Boolean</span>

This page records how Calzone's cell-fate network was brought into the composite and why. It assumes the network itself
({doc}`../science/calzone-network`: every node, rule and rate, and how to read `@logic ? 1 : 0`), what a Boolean network
and asynchronous updating are ({doc}`../science/boolean-networks`), and how MaBoSS turns rates into probabilities
({doc}`../math/maboss`). The **race** this page refers to is the one explained there: a fast death route against
NF-κB's slow protective genes.

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

The project's initial plan asked about BoolNet. BoolNet is an R package with no process-bigraph wrapper, while MaBoSS is
Python-native through `cmaboss` (MaBoSS's Python binding), and its stochastic, rate-based semantics fit a composite with a real-time clock.
viva-maboss was built for this purpose; its README gives the full comparison.

## Source

Calzone 2010's network as MaBoSS ships it: `cellfate.bnd`, `cellfate.cfg` and MaBoSS's own reference output
`refer/res_probtraj.csv`. All three are from sysbio-curie/MaBoSS@375ffad, kept unedited in
`workspace/datasets/calzone2010_cellfate/raw/` with their sha256.

**First check:** `checks/boolean/calzone-reference` runs the full 31-node network through `MaBoSSProcess` in the
reference configuration. Every node matches MaBoSS's own reference output within 0.008 (both runs use 100,000 trajectories, so each estimate's
standard error is at most 0.0016 and their difference's at most $\sqrt 2 \times 0.0016 = 0.0023$; 0.008 is 3.5 of those). The one node that moves, mROS,
also matches its analytic value: run 0.339387, reference 0.339405, analytic 0.339384.

## The ownership boundary: what each model owns

This decision changed twice. Both rounds are recorded here, because the reasons are the design.

### Round 1: cutting TNF, TNFR, RIP1 and IKK made death unreachable

Lipniacki already models TNF → IKK → NF-κB, and Calzone has its own version of that chain. Under the one-owner
principle ({doc}`architecture`), the first plan cut Calzone's copy: TNF, TNFR, RIP1 and IKK. In Calzone, though,
TNF→TNFR also drives **both death arms**:
- apoptosis: TNFR → DISC_TNF → CASP8 → BAX → MOMP → … → CASP3;
- necrosis: TNFR → RIP1 → RIP1K → ROS → MPT → NonACD.

Measured through `MaBoSSProcess` with TNF on, read at t = 40, that cut left P(Apoptosis) = P(NonACD) = 0, whatever NF-κB did.

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
| NFkB | logic kept (`IKK AND NOT CASP3`); rates `@logic ? $u_NFkB : 0`, `@logic ? $d_NFkB : 1` | while the route is open, NF-κB follows Lipniacki ($u = f\kappa/k_\text{time}$, $d = (1-f)\kappa/k_\text{time}$, which is $u = f$, $d = 1-f$ in the checks that set $\kappa = k_\text{time}$; {doc}`coupling`); when it closes, NF-κB switches off as in Calzone; `$High_NFkB` is kept |
| TNF | rates `$u_TNF` / `$d_TNF` | driven by the same receptor-occupancy signal as Lipniacki's `TNF_R` |
| Apoptosis, NonACD | switch-off `@logic ? 0 : ($absorb_death ? 0 : 1)` | death is irreversible: with `absorb_death` nonzero (the composite) a death node stays on; 0 is Calzone's network (below) |
| every node | each rate × `$k_time` | the death-machinery clock the studies sweep ({doc}`time`) |
| cIAP, cFLIP, BCL2, mROS, mcIAP, mXIAP, Survival | `$TransRate` → `$r_tx / $k_time` | Calzone's transcription-scale steps (NF-κB-induced cFLIP, BCL2, mXIAP, mcIAP; cIAP from mcIAP; mROS, induced when NF-κB is *off*; the Survival phenotype) switch on at Lipniacki's rate ({doc}`time`) |

`workspace/datasets/calzone2010_cellfate/prep.py` writes `processed/cellfate_coupled.bnd` (31 nodes) and
`processed/coupling.json`. It refuses to write unless:
- the input is the pinned file;
- each node it rewrites is exactly the expected upstream text;
- every rate is wrapped in `$k_time`.

### Proof that the coupling is Calzone wherever it should be

At $u = 1$, $d = 0$ (NF-κB switching like Calzone's own node), $k_\text{time} = 1$ and $r_\text{tx} = 1/24$, the
coupled network **is** Calzone's network (with `absorb_death = 0`, below). Five checks compare it with the unmodified network run on the MaBoSS engine
directly, TNF on, all 31 nodes, abs 0.01:

| Check | What it adds |
|---|---|
| `coupled-equals-full` | t = 40, where the death arms have acted |
| `coupled-equals-full-early` | the window [7, 8], while caspase-3 switches on. The gate's `NOT CASP3` term is visible only here: P(NF-κB) is 0.215 with it and about 0.24 without (two separate runs gave 0.244 and 0.243). Later, caspase-8 has closed the route anyway. |
| `coupled-equals-full-seconds` | `k_time = 1/60` over 2400 s with $r_\text{tx} = k_\text{time}/24$: a pure change of clock at t = 40. An unclocked race-deciding rate (CASP8) fails it. |
| `coupled-equals-full-early-seconds` | the same over [420, 480] s, while the cascade moves: unclocked BAX or MOMP fail it |
| `coupled-nfkb-knockout` | no nuclear NF-κB ($u_\text{NFkB} = 0$, $d_\text{NFkB} = 1$) against Calzone's network with NF-κB's switch-on rate set to 0 (loss of function): the death arms are intact |

**Proven to fail:**
- the caspase-3 term removed: NF-κB 0.243 instead of 0.215;
- caspase-8's rates left off the clock: apoptosis 0.972 instead of 0.953;
- BAX's rates left off the clock (early window): apoptosis 0.449 instead of 0.323;
- the Round 2 network (RIP1ub, IKK, cIAP and mcIAP removed) run in this check, with NF-κB driven at $u = 1$, $d = 0$:
  survival 0.25 instead of 0.014, necrosis 4e-5 instead of 0.029. (The table above is a different manipulation: the
  full network with only those feedback loops cut, NF-κB following its own rule.)

### Death is absorbing in the composite

**The problem.** In MaBoSS every node is a switch with two rates: a switch-on rate while it is off, and a switch-off
rate while it is on ({doc}`../math/maboss`). Calzone writes each death node as a mirror of its cause:

| Node | Logic (when it is "true") | Switch-on rate | Switch-off rate |
|---|---|---|---|
| Apoptosis | `CASP3`: caspase-3 is active | 1 while CASP3 is on | 1 while CASP3 is off |
| NonACD (necrosis) | `NOT ATP`: the cell has run out of ATP | 1 while ATP is gone | 1 while ATP is back |

So if caspase-3 switches off again, for example because XIAP returns and blocks it, the Apoptosis node switches off
too. That makes sense for a node read as "caspase-3 is active", but not for a node read as "the cell has died": death
is irreversible. In Study 0, up to 27% of the cells in a run had shown a death node and lost it again by 24 h (7.5% in the
baseline at 120 min per Calzone unit; 22.5–27% with Calzone's gates removed; {doc}`calibration`).

**The change (Alex, 2026-11-06; {doc}`decisions`, row 28).** Both death nodes' switch-off rate is switched by a
parameter $a$, `absorb_death`:

```text
rate_down = $k_time * (@logic ? 0 : ($absorb_death ? 0 : 1));
```

- $a = 0$ gives Calzone's network unchanged. Every check above sets it, so they still compare against Calzone exactly.
- Any nonzero $a$ (the composite uses 1) gives a death node that never switches off, so a dead cell stays dead. The
  rest of the network keeps running after death; what the change gives is a death flag that stays set, which a later
  edge can use to stop a dead cell signalling (none is built yet; {doc}`coupling`).
- It is written as a switch rather than as a factor $1 - a$, so no value can make a rate negative.

**What it should not change.** No node's logic reads Apoptosis or NonACD: they are outputs only. In MaBoSS's
continuous-time trajectory, every other node therefore behaves the same with $a = 0$ or $a = 1$ up to the moment a death
node first switches on. The composite, however, records each cell once per 30 s coupling interval, as a joint state sampled
from that interval's last window (*Engine*, above; {doc}`../math/maboss`). A death node that switched on and off again within one
interval can be missed with $a = 0$, while with $a = 1$ it stays on and is recorded. So absorbing death can, in
principle, make a recorded first death earlier; it cannot make a dead cell alive. Whether that matters is an empirical
question. Study 0 was run with $a = 0$. Rerunning its baseline with $a = 1$ on the same 200 seeds, at 30 and 120 min
per Calzone unit, gave no cell whose first death moved (0 of 400), the same alive cells, and no revived cell. A review
found the same at 0.5 and 2 min per unit (6 h). The decay, persistence and knockout variants were not rerun.

**The check, `absorbing-death`.** Take the two death nodes verbatim and give each a cause that is present at $t = 0$
and goes away once, for good, at rate $r$ (caspase-3 starts on and switches off; ATP starts off and switches on).
While the cause is present, the death node switches on at rate $k$. With $a = 1$ a death node is on at time $t$
exactly when it switched on before its cause went away. At time $s$ the cause is still present with probability
$e^{-rs}$, and the node switches on in $[s, s + ds]$ with probability $k\,e^{-ks}\,ds$, so

$$
P(\text{on at } t) = \int_0^t k\,e^{-ks}\,e^{-rs}\,ds = \frac{k}{k + r}\left(1 - e^{-(k + r)t}\right).
$$

At $k = r = 1$ and $t = 8$ this is 0.5 (MaBoSS reports the average over the window [7, 8], which is also 0.5 to six
places). Both nodes read 0.5 within 0.01 (50,000 trajectories).

**Proven to fail.** With $a = 0$ the node also switches off at rate $k$ once its cause is gone. Solving the same
four-state chain gives $P(\text{on at } t) = t\,e^{-t}$ at $k = r = 1$, whose average over [7, 8] is
$8e^{-7} - 9e^{-8} = 0.0043$. The same document with $a = 0$ reads 0.0048 (Apoptosis) and 0.0042 (NonACD), and fails.

## Clock

Calzone's rates have no time unit. {doc}`time` covers how they were put on the composite's clock: one swept factor
`$k_time`, and gene expression anchored to Lipniacki.
