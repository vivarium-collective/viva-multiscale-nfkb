# 3. The kinetic → Boolean coupling

The coupling is a `MathExpressionStep` between Lipniacki's NF-κB species and MaBoSS's parameters
({doc}`../design/coupling`). The document `checks/boolean/pair-nfkb-analytic/document.pbg` is that coupling with the
kinetic layer held at one stimulated state (414 s after TNF, NF-κB still rising), in its simplest case,
$\kappa = k_\text{time}$. The composite writes $u = f\kappa/k_\text{time}$ and $d = (1-f)\kappa/k_\text{time}$
({doc}`../math/switch`). With $\kappa = k_\text{time}$ those are $u = f$ and $d = 1 - f$, which is what the adapter
below writes, so the check isolates the one new quantity, the nuclear fraction $f$.

## The adapter

```json
"nuclear_fraction": {
  "_type": "step",
  "address": "local:viva_basic_processes.math_expression.MathExpressionStep",
  "config": {
    "expressions": [
      {"out": "NFKB_total", "expr": "IKKactive_IkB_NFKB + NFKB + IkB_NFKB + (NFKB_nuc + IkB_NFKB_nuc) / Kv"},
      {"out": "u_NFkB", "expr": "(NFKB_nuc / Kv) / NFKB_total"},
      {"out": "d_NFkB", "expr": "1 - u_NFkB"}
    ],
    "params": {"Kv": 5.0}
  },
  "inputs": {"NFKB_nuc": ["kinetic", "NFKB_nuc"], "...": "the other four species"},
  "outputs": {"NFKB_total": ["nfkb_total"], "u_NFkB": ["parameters", "u_NFkB"], "d_NFkB": ["parameters", "d_NFkB"]}
}
```

The first expression is the curated SBML's own `NFKB_total` rule, word for word.

## The one wiring rule that bit

The `parameters` store **must already hold** `u_NFkB` and `d_NFkB` before the Step writes them. In process-bigraph
1.9.1, a Step's write to a map key the store doesn't hold yet is silently dropped. Delete the seeded keys and rerun:
NF-κB stays at 0, and the check fails on `parameters.u_NFkB` (no number) and on P(NFkB on).

```bash
bash compose/check.sh boolean pair-nfkb-analytic
```
