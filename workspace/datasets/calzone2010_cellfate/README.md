# calzone2010_cellfate

Calzone L, Tournier L, Fourquet S, Thieffry D, Zhivotovsky B, Barillot E, Zinovyev A (2010), "Mathematical modelling of
cell-fate decision in response to death receptor engagement", PLoS Comput Biol 6(3):e1000702 (PubMed 20221256).

- `raw/` (never edited), fetched 2026-11-04 from `sysbio-curie/MaBoSS@375ffadb346adf4173536705fc7efad6c4602714`,
  `engine/tests/maboss/cellfate/` (the files last changed in e844529, 2025-08-24):
  - `cellfate.bnd`, sha256 `cfef1e7054d77f4736d8e36e712946ad1043c2f967913e400ec449b56a3d26dc` (31 nodes)
  - `cellfate.cfg`, sha256 `3734729982e66a71c5f491171a2ae37086fb7f81c0f705a58dc9ec514f20ab21` (TNF off; `$TransRate = 1/24`;
    max_time 10, time_tick 0.1, 100000 samples; every node's istate 0 or 1)
  - `res_probtraj.csv` (from `refer/`), sha256 `cb88e0760d6487d8942727900192588d2282ea6594ba3bb4b18fc1a228ce32ae`: MaBoSS's
    own reference output for that configuration, the oracle of `checks/boolean/calzone-reference`.

`MaBoSSProcess` (viva-maboss@3fdccd7) writes its own `.cfg`, so the composite carries the `$` parameters in
`config.parameters` and the initial states (0 or 1 only; a value >= 0.5 is on) in `config.initial_state`.
