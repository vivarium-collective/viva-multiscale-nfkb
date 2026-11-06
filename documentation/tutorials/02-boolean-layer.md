# 2. The cell-fate layer on its own

Run the coupled Calzone network ({doc}`../design/boolean`) with TNF on, holding its NF-κB input at five levels:

```{literalinclude} code/boolean_fates.py
:language: python
```

Output (20,000 trajectories, t = 40 Calzone units, MaBoSS's example rates):

```text
NF-kB input f = 0.00:  Survival 0.000  Apoptosis 0.910  NonACD 0.090
NF-kB input f = 0.25:  Survival 0.000  Apoptosis 0.935  NonACD 0.065
NF-kB input f = 0.50:  Survival 0.000  Apoptosis 0.952  NonACD 0.048
NF-kB input f = 0.75:  Survival 0.000  Apoptosis 0.961  NonACD 0.038
NF-kB input f = 1.00:  Survival 0.014  Apoptosis 0.950  NonACD 0.032
```

## What it shows

- **f = 1 is Calzone itself.** With NF-κB switching as Calzone's own node, the layer gives Calzone's wild type under TNF
  (survival 0.014, apoptosis 0.950, necrosis 0.032), as `coupled-equals-full` checks to 0.01.
- **f = 0 is NF-κB loss of function.** TNF kills by apoptosis (91%) and necrosis (9%), as `coupled-nfkb-knockout`
  checks.
- **Less NF-κB, more necrosis.** Necrosis needs mROS, whose logic is `NOT NFkB`.
- **Survival is rare under TNF at every f, and 0 below f = 1.** Below f = 1 the NF-κB node keeps switching off (it is
  on only a fraction f of the time), and each time it is off the Survival node, whose rule is `NFkB`, switches off at
  rate 1. At f = 1 the node stays on while its gate is open, and survival reaches Calzone's own 1.4%. Two things act
  against NF-κB even then:
  - **Calzone's gate:** caspase-8 cleaves RIP1 and SMAC sequesters cIAP, which closes NF-κB's route, so a dying cell
    loses NF-κB whatever Lipniacki supplies.
  - **The race:** a protective gene, switching on at $\text{TransRate} = 1/24$ per unit while NF-κB is on, is on in
    half of the cells after $\ln 2 \times 24 \approx 16.6$ units, while half of the eventual apoptosis arrives by about 8.6
    ({doc}`../design/time`).

```{admonition} The clocks, not the wiring (decided in Study 0)
:class: note
Two speeds decide how much survival the composite can show, and Study 0 ({doc}`../design/calibration`) settled the
first:
- **How fast the NF-κB node follows Lipniacki.** Here, with $u = f$, $d = 1-f$, it flips about once per Calzone unit.
  The composite instead uses $\kappa = \ln 2/337$ s, Lipniacki's own NF-κB speed, whatever the clock
  ({doc}`../math/switch`).
- **How fast the death machinery runs.** That is `k_time`, which stays a swept axis ({doc}`04-death-clock`).
```
