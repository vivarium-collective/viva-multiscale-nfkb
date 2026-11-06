# The three models

## Lipniacki 2004: the NF-κB module <span class="layer kinetic">kinetic</span>

Lipniacki T, Paszek P, Brasier AR, Luxon B, Kimmel M (2004). *Mathematical model of NF-κB regulatory module.*
J Theor Biol 228:195–215. BioModels **BIOMD0000000786** (curated).

- **What it is:** 16 species and 32 reactions in two compartments, cytoplasm and nucleus, with
  $K_v = V_\text{cyt}/V_\text{nuc} = 5$. It models IKK activation by TNF; IκBα:NF-κB binding and degradation; nuclear
  import and export; and NF-κB-induced transcription of IκBα, A20 and a generic control gene. Time is in seconds and
  concentrations in µM. The model, species by species and reaction by reaction: {doc}`lipniacki-model`.
- **Its input:** `TNF` is a boundary species (one that no reaction changes; only a rule sets it), set by the rule
  `TNF := TNF_R`. `TNF_R` is a receptor-activity parameter between 0 and 1: the original model switches it from 0 to 1,
  and in the composite it carries the receptor-engagement fraction. It enters the IKK reactions as a modifier, in the rates
  $k_1\,\text{TNF}\,\text{IKKn}$ (neutral IKK activated) and $k_2\,\text{TNF}\,\text{A20}\,\text{IKKa}$ (active IKK
  inactivated by A20).
- **Why this model** (Alex, 2026-11-04):
  - It has two sized compartments, so nuclear NF-κB is a real concentration.
  - Its stimulus is one external input, exactly the port a spatial layer drives.
  - COPASI and Tellurium (a Python modelling environment whose simulation engine is libRoadRunner) agree on its own
    simulation: their trajectories differ by a normalised root-mean-square
    error (NRMSE) of 3.6e-7 (viva-biomodels, a companion package that runs BioModels models in several engines and
    compares the results: `datasets/corpus_comparison/corpus_metrics.json`, BIOMD0000000786 `sim1`, mean NRMSE
    3.58×10⁻⁷ over 15 shared outputs).
- **Rejected alternatives** ({doc}`../design/kinetic`):
  - BIOMD0000000027: one compartment, no stimulus input.
  - BIOMD0000000407 (Schliemann 2011), a runner-up: three sized compartments, but a much larger parameter set (106
    parameters local to individual reactions) for the same role.
  - BIOMD0000000140 (Hoffmann 2002), a runner-up: its stimulus is written as a rate rule (an equation that sets a
    quantity's rate of change) plus an event (a timed change), not as one parameter another layer could set.

## Calzone 2010: the cell-fate decision <span class="layer boolean">Boolean</span>

Calzone L, Tournier L, Fourquet S, Thieffry D, Zhivotovsky B, Barillot E, Zinovyev A (2010). *Mathematical modelling
of cell-fate decision in response to death receptor engagement.* PLoS Comput Biol 6(3):e1000702.

- **What it is:** a Boolean network of 31 nodes. Each node is on or off: TNF, TNFR, FADD, DISC, CASP8, RIP1, cIAP,
  IKK, NF-κB and its targets, the mitochondrial nodes, CASP3, ATP and ROS. Its three outputs are **Survival**,
  **Apoptosis** and **NonACD** (non-apoptotic cell death, i.e. necrosis). Every node, rule and rate:
  {doc}`calzone-network`.
- **Semantics:** the paper uses asynchronous reachability with no rates ({doc}`boolean-networks`). In it, the wild-type cell under TNF reaches
  about **30% survival, 60% apoptosis and 10% necrosis** (Fig. 4, on a reduced model with some variables hidden but the
  same stable states; each possible transition from a state given equal probability; {doc}`boolean-networks`).
- **The rates used here** come from MaBoSS's continuous-time version of the same network (the files shipped in the
  MaBoSS repository): every rate 1, except transcription at `TransRate = 1/24`. Those rates are a modelling choice of
  that example, not of the paper. {doc}`../design/time` explains why that matters.

## McMillan 2021: TNF binding to its receptor <span class="layer adapter">adapter</span>

McMillan D, Martinez-Fleites C, Porter J, et al. (2021). *Structural insights into the disruption of TNF-TNFR1
signalling by small molecules stabilising a distorted TNF.* Nat Commun 12:582.

- **What it is:** a rule-based model ({doc}`../design/rule-based`; BioNetGen is its software) of the TNF trimer binding receptors one, two and three at a time,
  with dissociation constants $K_1$, $K_2$, $K_3$ (10, 100 and 1000 nM in the published model file, from RuleHub, RuleWorld's collection of rule-based models) and
  $k_\text{off} = 0.01\ \text{s}^{-1}$. The paper fitted these constants to native mass-spectrometry fractions of TNF
  with 0–3 receptors bound, using BioNetGen to solve the equilibria.
- **Its role here:** an offline dose–response from TNF concentration to receptor engagement. It is not a runtime layer;
  see {doc}`../design/rule-based`.
- **Caveat:** these measurements were made in vitro, with the receptor's soluble ectodomain. On a cell surface,
  receptor density and binding in two dimensions differ, so mapping this curve onto Lipniacki's 0/1 `TNF_R` is an
  assumption. It is recorded wherever the curve is used.
