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
- **Survival is rare under TNF at every f.** This is Calzone's own result at MaBoSS's example rates. Two things act
  against NF-κB:
  - **Calzone's gate:** caspase-8 cleaves RIP1 and SMAC sequesters cIAP, which closes NF-κB's route, so a dying cell
    loses NF-κB whatever Lipniacki supplies.
  - **The race:** the protective genes need NF-κB on for about $1/\text{TransRate} = 24$ units, while death arrives in
    about 8.5.

```{admonition} Open: the clocks, not the wiring
:class: important
Two calibration questions decide how much survival the composite can show. The investigation's calibration study
(Study 0) decides both; see {doc}`../design/time` and {doc}`../design/roadmap`.
- **How fast should the NF-κB node follow Lipniacki?** With $u = f$, $d = 1-f$, it flips about once per Calzone
  unit.
- **How fast is the death machinery?** That is `k_time`, tutorial 4.
```
