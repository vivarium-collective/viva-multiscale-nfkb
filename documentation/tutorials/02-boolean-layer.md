# 2. The cell-fate layer on its own

Run the reduced Calzone network ({doc}`../design/boolean`) with TNF on, holding its NF-κB input at five levels:

```{literalinclude} code/boolean_fates.py
:language: python
```

Output (20,000 trajectories, t = 40 Calzone units, MaBoSS's example rates):

```text
NF-kB input f = 0.00:  Survival 0.000  Apoptosis 0.911  NonACD 0.089
NF-kB input f = 0.25:  Survival 0.000  Apoptosis 0.997  NonACD 0.002
NF-kB input f = 0.50:  Survival 0.000  Apoptosis 0.998  NonACD 0.000
NF-kB input f = 0.75:  Survival 0.005  Apoptosis 0.980  NonACD 0.000
NF-kB input f = 1.00:  Survival 0.255  Apoptosis 0.678  NonACD 0.000
```

## What it shows

- **f = 0 is NF-κB loss of function.** TNF kills by apoptosis (91%) and necrosis (9%), as in
  `reduction-nfkb-knockout`.
- **Any NF-κB suppresses necrosis.** Necrosis needs `mROS`, whose logic is `NOT NFkB`.
- **Survival appears only at f = 1.** That is a finding about the *coupling*, not about the biology. With
  $u = f$, $d = 1-f$, the NFkB node flips about once per Calzone unit. The protective genes need NF-κB on continuously
  for about $1/\text{TransRate} = 24$ units, and they decay at rate 1 whenever it flips off. A node that flickers
  therefore never lets them accumulate.

```{admonition} Open: how fast the Boolean NF-κB node should follow Lipniacki
:class: important
The mapping gets the *average* right ($P(\text{on}) = f$; see {doc}`../math/switch`), but the *speed* of switching is
an artefact. The candidate fix puts it on Lipniacki's own clock: rates $f\kappa$ and $(1-f)\kappa$, with $\kappa$
measured from Lipniacki's NF-κB dynamics. That is decided in the investigation's calibration study (Study 0), not
here. See {doc}`../design/roadmap`.
```
