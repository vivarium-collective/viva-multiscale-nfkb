# The NF-κB model (Lipniacki 2004)

The composite's kinetic layer is the NF-κB model of Lipniacki et al. (2004), as curated in BioModels
(BIOMD0000000786). This page builds it up from its parts, so that the quantity the fate layer reads, NF-κB's nuclear
fraction $f$, and the three rates taken from it can be followed back to the model.

## What kind of model it is

It is a set of ordinary differential equations: each **species** (a molecule or complex) has a concentration in µM,
and each **reaction** changes concentrations at a rate set by mass action (a rate constant times the concentrations
that take part). Time is in seconds. Unlike the fate network ({doc}`calzone-network`), nothing is random: one stimulus
gives one trajectory.

There are two compartments, the **cytoplasm** and the **nucleus**. The cytoplasm's volume is $K_v = 5$ times the
nucleus's.

## At rest: NF-κB held outside the nucleus

NF-κB is a transcription factor: in the nucleus it switches genes on. In a resting cell almost all of it is held in the
cytoplasm by its inhibitor **IκBα**. In the model's rest state (computed once, {doc}`../design/kinetic`), 98.7% of
NF-κB is in the IκBα–NF-κB complex (`IkB_NFKB`, 0.0592 of 0.06 µM), and the fraction free in the nucleus is
$f = 0.0077$.

The kinase that releases NF-κB, **IKK**, is all in its neutral form at rest. It is made at a constant rate
$K_\text{prod} = 2.5\times10^{-5}$ µM/s and lost at $K_\text{deg} = 1.25\times10^{-4}$ s⁻¹, so its rest level is where
the two balance: $K_\text{prod}/K_\text{deg} = 0.2$ µM.

## When TNF arrives

`TNF` in the model is the signal at the receptor, between 0 and 1. Each step below is a reaction in the tables at the end.

1. **IKK is activated.** Neutral IKK becomes active at rate $k_1 \cdot \text{TNF}$ ($k_1 = 0.0025$ s⁻¹).
2. **IκBα is marked and destroyed.** Active IKK binds IκBα, free or bound to NF-κB, and the bound IκBα is degraded.
3. **NF-κB is freed and enters the nucleus** (import rate $i_1 = 0.0025$ s⁻¹).
4. **Nuclear NF-κB orders new mRNA** for three genes: IκBα, A20, and a control gene that nothing reads (a reporter of
   transcription). The mRNA is translated into protein.

## Two negative feedbacks, and why NF-κB comes in waves

NF-κB's own products switch it off again, by two routes:

- **IκBα.** New IκBα enters the nucleus, binds NF-κB and carries it back out.
- **A20.** A20 protein inactivates active IKK, at rate $k_2 \cdot \text{TNF} \cdot \text{A20}$, so fewer new IκBα
  molecules are destroyed. Inactive IKK does not return to the neutral pool; it is only degraded.

Both act only after transcription and translation. Lipniacki's own timing puts A20 protein's half-rise 2107 s (35 min)
after nuclear NF-κB's ({doc}`../design/time`). A negative feedback that acts late overshoots: NF-κB keeps entering the
nucleus until the inhibitors catch up, then is pushed below its level once they have, and the inhibitors themselves
decay. Each swing is smaller than the last. Under TNF held at saturation (TNF = 1), from the rest state:

| Time after TNF | $f$, the free nuclear fraction |
|---|---|
| 0 | 0.0077 |
| 24 min | 0.933 (first peak) |
| 65–100 min | below 0.1 |
| 2–5 h | between about 0.2 and 0.38 |
| from about 6 h | 0.28 (settled) |

(Measured in Study 0's runs, which record $f$ under the name `nfkb_fraction`; {doc}`../design/calibration`.)

## Volumes, total NF-κB and the fraction $f$

**Crossing the nuclear membrane changes concentrations unequally.** Moving $n$ molecules from cytoplasm (volume $V_c$)
to nucleus (volume $V_n = V_c/K_v$) lowers the cytoplasmic concentration by $n/V_c$ but raises the nuclear one by
$n/V_n = K_v\,n/V_c$. So in the model, import removes cytoplasmic NF-κB at $i_1\,[\text{NFKB}]$ and adds nuclear NF-κB
at $K_v\,i_1\,[\text{NFKB}]$. Export has the same factor in the other direction.

**Total NF-κB.** NF-κB is carried by five species: three in the cytoplasm (free, bound to IκBα, and bound to IκBα and
IKK) and two in the nucleus (free, and bound to IκBα). To add them up, each nuclear concentration is divided by $K_v$,
which converts it to cytoplasm-volume units:

$$
\text{NFKB\_total} = [\text{IKKactive\_IkB\_NFKB}] + [\text{NFKB}] + [\text{IkB\_NFKB}]
+ \frac{[\text{NFKB\_nuc}] + [\text{IkB\_NFKB\_nuc}]}{K_v}.
$$

That is the model's own assignment rule. No reaction makes or destroys NF-κB, so this total never changes: 0.06 µM,
the amount the model starts with (all of it in `IkB_NFKB`). The generator of the tables below proves this from the
reactions themselves: the rule's rate of change is identically zero. Dropping the $1/K_v$ makes the proof fail on
exactly the import and export terms.

**The fraction $f$.** The fate layer needs one number: how much of the cell's NF-κB is active, free in the nucleus.
That is the free nuclear NF-κB, in the same units, divided by the total:

$$
f = \frac{[\text{NFKB\_nuc}]/K_v}{\text{NFKB\_total}} .
$$

It has no fitted constant and lies between 0 and 1. How the fate network's NF-κB node follows it is in
{doc}`../design/coupling` and {doc}`../math/switch`.

## What the composite changes, and what it takes from the model

- **One change.** In BioModels' file, `TNF` follows a parameter through the rule `TNF := TNF_R`, and a timed event sets
  `TNF_R = 1` after 363,600 s (101 h) of rest. The composite removes that event, so `TNF_R` is set by the composite's
  TNF input instead. Nothing else changes (`workspace/datasets/lipniacki2004/prep.py`).
- **The rest state** is computed once, by running those same 101 h with no TNF, and every run starts from it
  ({doc}`../design/kinetic`).
- **Three rates measured from this model**, used to put the fate network on a clock:
  - $\kappa = \ln 2/(337\ \text{s})$: from nuclear NF-κB's half-rise after TNF, 337 s (the time to get half-way from its rest level to its first
    peak), the speed of the fate network's NF-κB node
    ({doc}`../design/coupling`);
  - $r_\text{tx} = \ln 2/(2107\ \text{s})$: from the delay from nuclear NF-κB to A20 protein, the speed at which NF-κB's target genes
    switch on ({doc}`../design/time`);
  - $r_\text{deg} = c_5 = 3\times10^{-4}$ s⁻¹: A20 protein's degradation rate, a 38.5 min half-life, used in Study 0's
    protein-turnover test ({doc}`../design/calibration`).

## Every species

Generated from the pinned SBML (`processed/lipniacki2004_driven.xml`). The value at t = 0 is the file's own starting
point. The composite starts instead from the rest state above.

```{include} _lipniacki_species.md
```

## Every reaction

Generated from the same file, with the model's function definitions expanded by libSBML, so each rate is the
expression the model computes. Both compartments have size 1 in the file, so a rate is a change of concentration per
second. The volume ratio appears as the explicit $K_v$ factors in the transport reactions: each crossing is written as
one reaction that removes the species on one side and one that adds it on the other.

```{include} _lipniacki_reactions.md
```

Two naming quirks of the SBML file: the reactions `NFKB_export` and `IkB_export` *remove* NF-κB and IκBα from the
cytoplasm on their way *into* the nucleus (each is paired with a reaction that adds them there), so they are imports
as this page uses the word. `ModelValue_1` in the conservation rule is a parameter set to $K_v$ at the start of every
run.

```{note}
Regenerate both tables after any change to the SBML:
`uv run --project compose python -I documentation/science/code/lipniacki_model.py`. Its `--check` mode fails when the
committed tables are stale, and it stops if total NF-κB is no longer conserved.
```
