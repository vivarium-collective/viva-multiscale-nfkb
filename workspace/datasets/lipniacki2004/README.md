# lipniacki2004

Lipniacki T, Paszek P, Brasier AR, Luxon B, Kimmel M (2004), "Mathematical model of NF-kappaB regulatory module",
J Theor Biol 228:195-215 (PubMed 15094015). BioModels BIOMD0000000786 (curated).

- `raw/` (never edited), downloaded 2026-11-04 from `https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000786?filename=<name>`:
  - `Lipniacki2004.xml`, sha256 `78ff021b45d4ca35dd6f3a4de371196625a3a6a908531ff028b3ed946142d39c` (SBML L2V4)
  - `Lipniacki2004.sedml`, sha256 `f86d3b52a0cee09115634acdca59a2cff4d60008084a6845ceaba8c499bf8302` (sim1: 0-385200 s, 1000 steps)
  - `curation_notes.txt`, sha256 `164c25c03447e6ea1a9ec1bfe50d2f1c5430aa82c07fedd2262fe54b002da62b`
- `prep.py` writes `processed/lipniacki2004_driven.xml` (sha256 `e3d357b9ac0a1e508ea68d690aea107f3fd7408ffb13d618d307901cd8d17718`,
  deterministic): the `TNF_stimulation` event removed so that the composite's spatial layer drives `TNF_R`; nothing else
  changes. Run: `uv run --project compose python -I workspace/datasets/lipniacki2004/prep.py`.

Facts used by the composite (libSBML, 2026-11-04): Kv = V_cyt/V_nuc = 5 (rule `NFKB_total = ... + NFKB_nuc/Kv`);
nuclear transport is the one-way first-order fluxes `i1` (NF-kB in), `i1a` (IkB in), `e1a` (IkB out),
`e2a` (IkB:NF-kB out); time in seconds; `TNF` is a boundary species set by `TNF := TNF_R`.
