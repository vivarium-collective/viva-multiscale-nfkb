# Datasets

Each dataset lives in `workspace/datasets/<name>/`.
- `raw/` holds the original files, never edited, with their sha256.
- `prep.py` is the deterministic script that writes `processed/`.
- `README.md` gives provenance.

All are registered in `workspace.yaml`.

| Dataset | Source (pinned) | Processed outputs |
|---|---|---|
| `lipniacki2004` | BioModels BIOMD0000000786: SBML, SED-ML, curation notes | `lipniacki2004_driven.xml` (stimulus event removed); `lipniacki2004_steady_state.json` (pre-equilibrated state) |
| `calzone2010_cellfate` | sysbio-curie/MaBoSS@375ffad `engine/tests/maboss/cellfate/`: `cellfate.bnd`, `cellfate.cfg`, `refer/res_probtraj.csv` | `cellfate_reduced.bnd` (27 nodes); `reduction.json` (every change and why); `transcription_anchor.json` ($r_\text{tx}$ from Lipniacki) |
| `mcmillan2021_tnfr` (d1, in progress) | RuleWorld/RuleHub@b84f0a7 `Published/McMillan2021/` | the fitted dose–response, when d1 lands |

External data read by the generators (not copied):
- viva-biomodels' corpus (`datasets/corpus_comparison/corpus_timecourse.parquet`), for COPASI's `sim1` trajectory.
