# The biology: one signal, three fates

## TNF

Tumour necrosis factor (TNF) is a cytokine, a signalling protein that immune cells release during inflammation. It
spreads through the fluid between cells. A cell senses it through **TNF receptor 1 (TNFR1)** on its surface. TNF is a
trimer, a complex of three identical subunits, so one TNF molecule can bind up to three receptors. Receptors bound
together in a cluster are what start the signal inside the cell.

## One receptor, opposite outcomes

TNF binding to TNFR1 does not decide the cell's fate. It starts **three programmes at once**, and they compete:

1. **Survival through NF-κB.** The receptor recruits the kinase RIP1. Once RIP1 is ubiquitinated (by cIAP), it activates
   the IKK complex. IKK phosphorylates IκBα, the inhibitor that holds NF-κB in the cytoplasm, and marks it for
   degradation. Freed NF-κB moves into the nucleus and switches on genes. Some of those genes are **protective**
   (cFLIP, BCL2, XIAP, cIAP). Others are **negative feedback**: IκBα itself, and A20. Because the inhibitors must first
   be made, the feedback acts late, so NF-κB overshoots, is pushed back, and enters the nucleus in shrinking waves
   rather than once ({doc}`lipniacki-model`).
2. **Apoptosis.** The receptor can instead form a **death-inducing signalling complex (DISC)**: the adaptor protein
   **FADD** links the receptor to inactive caspase-8 molecules and holds them close together, so that they activate one
   another. Active **caspase-8** starts a cascade: BAX, mitochondrial outer membrane permeabilisation (MOMP), and the
   release of cytochrome c and SMAC from the mitochondria. Cytochrome c assembles the **apoptosome** (with Apaf-1 and
   caspase-9), which needs ATP and activates **caspase-3**. Caspase-3 dismantles the cell in an orderly way, and it
   also shuts NF-κB down.
3. **Necrosis.** When caspase-8 is not active, RIP1 can act as a kinase instead. Reactive oxygen species (ROS) then
   build up, the mitochondrial permeability transition (MPT) opens, ATP collapses, and the cell dies by necrosis.

**Apoptosis and necrosis differ in how the cell dies.** Apoptosis is run by caspases: the cell is taken apart from
inside while its outer membrane stays intact, and the fragments are cleared by neighbouring cells with little
inflammation. Necrosis needs no caspases: the cell loses its energy supply, swells, and its membrane ruptures, so its
contents spill out and provoke inflammation. In the fate network the two are separate output nodes, Apoptosis
(caspase-3 active) and NonACD (non-apoptotic cell death: ATP gone). Every node of that network, with the molecule or
process it stands for: {doc}`calzone-network`.

**What decides the winner is timing and amount.** NF-κB's protective genes have to be made (transcribed and
translated) before the death machinery finishes. That takes tens of minutes. Whether they arrive in time depends on
how strongly and how fast NF-κB enters the nucleus, which depends on how much TNF reached the receptors and when.

## Why space matters

In tissue, TNF comes from a source: an immune cell, or a site of damage. It diffuses outward, so a cell farther away
sees **less** TNF and sees it **later**, and the concentration rises gradually rather than switching on. The question
the headline study asks ({doc}`../design/studies`) is whether a cell's fate depends only on the *dose* that reached
it, or also on the *timing* of its arrival.

## What the model does not include, and why

v1 is the composite being built now (one cell, the layers on the landing page); v2 collects planned extensions
({doc}`../design/roadmap`).

| Not modelled | Why it is left out of v1 |
|---|---|
| TNFR2, membrane-bound TNF | The fate network and the NF-κB model are built around TNFR1 signalling. |
| The nuclear envelope as a spatial boundary | The spatial engine has one domain and no flux between regions yet. Lipniacki's two well-mixed compartments carry nuclear transport. This is planned for v2 ({doc}`../design/spatial`). |
| Several cells | v1 models one cell. The same TNF field can feed N cells later; see {doc}`../design/roadmap`. |
| Receptor clustering dynamics at runtime | Receptor binding relaxes within about 100 s, faster than NF-κB's rise (337 s half-rise, {doc}`lipniacki-model`), so v1 uses its equilibrium as an approximation, to be checked when that step is built. See {doc}`../design/rule-based`. |
