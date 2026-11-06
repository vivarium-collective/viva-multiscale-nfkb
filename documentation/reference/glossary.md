# Glossary

Each term links to the page that builds it up.

`absorb_death`
: The fate network's switch for death (decision 28). 0 is Calzone's network, where Apoptosis and NonACD switch off
  again when their cause reverses; any nonzero value (the composite uses 1) keeps them on once on
  ({doc}`../design/boolean`).

Adapter
: A Step that translates one layer's quantity into the form another layer reads, for example `RegionMean` and
  `MathExpressionStep` ({doc}`../design/composite-primer`).

Alive
: A cell with no death node (Apoptosis, NonACD) on at any tick of the run. Death is irreversible, but Calzone's own
  death nodes can switch off again, so a cell's end state alone could show a dead cell as alive. The composite now makes
  them absorbing (`absorb_death = 1`), so there a dead cell's end state also shows it dead.

Asynchronous updating
: One node of a Boolean network changes at a time, and which one goes next is not fixed in advance
  ({doc}`../science/boolean-networks`).

Attractor
: Where a Boolean network settles: a stable state (no node wants to change) or a cycle of states. A fate is an
  attractor read through output nodes ({doc}`../science/boolean-networks`).

BNGL
: The BioNetGen language for rule-based models: molecules with binding sites, and rules for which sites bind
  ({doc}`../design/rule-based`).

Boolean network
: A model in which every molecule or process is on or off, and a logical rule says when each should be on
  ({doc}`../science/boolean-networks`).

Calzone unit
: The fate network's own time unit. Most of its steps have rate 1 per unit; a unit lasts $1/k_\text{time}$ seconds,
  where `k_time` is the death clock ({doc}`../science/calzone-network`, {doc}`../design/time`).

Check
: A compose-api compliance case: a document, an interval and expectations scored by `compliance.evaluate`. It always
  has an independent oracle, and a proven-failing negative where one is recorded ({doc}`../design/composite-primer`).

compose-api
: The BioSimulations service that runs process-bigraph documents on HPC. Its runner and scorer are what the checks use.

Corpus
: viva-biomodels' collection of reference runs of BioModels models in several engines; the kinetic checks take
  COPASI's run of the NF-κB model from it ({doc}`datasets`).

Continuous-time Markov chain
: A random process that jumps between states after exponential waiting times, with rates that depend only on the
  current state. MaBoSS simulates the fate network as one ({doc}`../math/maboss`).

Coupling interval
: How often two layers exchange values: 30 s for the kinetic → fate edge in Study 0, which satisfies the rule in {doc}`../math/timescales`
  ($0.1 \times 337\ \text{s} \approx 34$ s); the spatial edge will need about 1 s.
  Each layer holds the last value it received in between.

d1
: The dose–response step: TNF concentration at the cell to receptor occupancy, from McMillan 2021's binding model
  ({doc}`../design/rule-based`).

Durable survival
: Alive at 24 h with the Survival node on. In the composite the Survival node follows the flickering NFkB node,
  so most protected cells are alive with Survival off; *alive* is the primary readout.

Duty cycle
: The fraction of time a switching node is on. For the fate network's NF-κB node it is $f$ ({doc}`../math/switch`).

Emitter
: A step that records chosen stores each time the composite advances; its records are the run's results
  ({doc}`../design/composite-primer`).

End state
: A cell's fate nodes at the end of a run, encoded as Survival + 2·Apoptosis + 4·NonACD. Fate nodes can overlap,
  so they are never summed across nodes.

First fate
: The first fate node a cell switches on. Reported next to the end state; a tie means two switched on within one
  coupling interval (30 s in the studies).

Gate
: NF-κB's rule in Calzone's network, `IKK AND NOT CASP3`: NF-κB can be active only while IKK is on and caspase-3 is
  off. The death machinery closes it in three ways: caspase-8 cleaves RIP1 and SMAC removes cIAP (both switch IKK off),
  and caspase-3 blocks NF-κB directly. While the gate is open, the composite's NF-κB node follows Lipniacki
  ({doc}`../design/boolean`).

Generator
: The matrix $Q$ of a Markov chain's switching rates; probabilities obey $dP/dt = PQ$ ({doc}`../math/maboss`).

Harness
: Two of compose-api's own checks, copied unchanged into `checks/harness`, which show that this repository scores checks
  exactly as the service does ({doc}`../verification/index`).

Jacobian
: The matrix of how each rate of change depends on each concentration. Its eigenvalues give the model's timescales
  ({doc}`../math/timescales`).

`k_time`
: Calzone time units per composite second. It multiplies every Boolean rate and is swept as the death machinery's
  clock.

Kappa (κ)
: How fast the Boolean NFkB node flips, in s⁻¹. It switches on at $f\kappa$ and off at $(1-f)\kappa$. The
  composite uses ln 2 / 337 s, Lipniacki's NF-κB half-rise (Study 0).

MaBoSS
: The engine that runs the fate network as a continuous-time Markov chain with Gillespie's algorithm
  ({doc}`../math/maboss`).

Mash-up (inferred mash-up)
: An environment compose-api builds automatically from the simulator packages a document's processes come from;
  "inferred" because the service works out which packages from the document itself.

McNemar test
: An exact test for whether a change shifts a yes/no outcome, using only the cells whose outcome changed
  ({doc}`../math/statistics`).

NRMSE
: Normalised root-mean-square error: the typical difference between two trajectories, relative to their size.

Nuclear fraction $f$
: $(\text{NFKB\_nuc}/K_v)/\text{NFKB\_total}$: Lipniacki's free nuclear NF-κB as a fraction of all NF-κB
  ({doc}`../science/lipniacki-model`).

Occupancy
: The fraction of time a Boolean node is on. For an NF-κB target product it is set by induction (`r_tx`, only while
  NFkB is on) against switch-off (only while NFkB is off), weighted by the fraction $f$ of time the NF-κB node is on
  ({doc}`../math/statistics`).

Oracle
: The source of a check's expected values, independent of the code under test.

Paired seeds
: A variant reuses the baseline's random seeds, so each cell can be compared with its own twin
  ({doc}`../math/statistics`).

Process, step, store, port
: A process computes over time intervals; a step computes when a store it reads is written to; a store holds a value; a port is how
  a process or step reads or writes a store ({doc}`../design/composite-primer`).

Quasi-steady
: Treating a fast process as always at its equilibrium, because everything that reads it changes much more slowly
  ({doc}`../design/rule-based`, {doc}`../math/statistics`).

`r_deg`
: Lipniacki's A20 protein degradation rate $c_5 = 3\times10^{-4}$ s⁻¹ (38.5 min half-life), used in Study 0's
  turnover test ({doc}`../design/calibration`).

`r_tx`
: The rate at which NF-κB target genes switch on, per second, measured from Lipniacki
  ($\ln 2 / 2107\ \text{s}$).

`rate_up`, `rate_down`, `@logic`
: A fate-network node's switch-on rate (used while it is off) and switch-off rate (used while it is on). `@logic` is the
  node's own rule, 1 when true ({doc}`../science/calzone-network`).

SBML, BioModels
: SBML is the standard file format for biochemical models; BioModels is the curated repository the NF-κB model comes
  from ({doc}`../science/models`).

Study 0, and variants 0b, 0c, 0d
: The calibration study run before the headline studies, and its three follow-up variants on protein persistence
  ({doc}`../design/calibration`).

Study, investigation
: A study in a viva workspace (a research repository set up with the vivarium-workbench tools, like this one) runs a
  research question through design, build, simulate, evaluate and decide, with its
  decisions and evidence recorded. An investigation groups studies under one question.

U1, U2
: The two upstream changes this project needed: U1, viva-tellurium's `parameters_in` port (released); U2,
  viva-pde-particle's `RegionMean` and `RegionTotal` (in review) ({doc}`../design/roadmap`).

`TransRate`
: Calzone's rate for steps that need new protein to be made (1/24 per unit in MaBoSS's example). The composite replaces
  it so these steps run at `r_tx` per second ({doc}`../design/time`).

Variant
: A run of Study 0 with one named change to the fate network, compared cell by cell with the baseline grid
  ({doc}`../design/calibration`).

Workbench, workspace
: vivarium-workbench is the dashboard that records studies and their runs; a workspace is a research repository set up
  for it, like this one.

Window average
: What MaBoSS reports: a probability averaged over a time window, not at an instant ({doc}`../math/maboss`).
