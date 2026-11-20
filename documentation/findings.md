# What the model shows

## The three scales run as one model

The TNF field, the NF-κB signalling and the cell's fate run together, on a laptop and on
[compose-api](https://compose.cam.uchc.edu), BioSimulations' service for running these models on a compute cluster. A
run there, on Linux, matches a run on macOS to within floating-point noise. Every part of the model, and every
connection between parts, is checked against an answer that doesn't come from the code under test
({doc}`verification/index`).

## Under constant TNF, too many cells die

In experiments, cells with working NF-κB mostly survive TNF alone, and die when NF-κB is blocked. The model doesn't
reproduce that yet. Under constant, saturating TNF, NF-κB protects at most about 12 cells in 100, at every speed
tested for the fate network's clock ({doc}`design/validation`).

The limit lies in a race inside the fate network. The death signal (caspase-8) is two steps from the bound receptor,
NF-κB is four, and active caspase-8 shuts NF-κB's route. Letting NF-κB switch on with the signalling model's own timing
wins that race, but most cells still don't survive, so that change was not adopted. The gap is an open question, not
something tuned away.

## Next: what exposure does

The next studies ask whether space matters only through how much TNF reaches a cell, or also through when it arrives
({doc}`design/studies`):

- **Dose:** survival at 24 hours across TNF doses, held steady or fading as a real dose does.
- **Distance:** cells 100 µm, 300 µm and 1 mm from a pulse of TNF, compared with cells given the same dose evenly.
- **Many cells:** a field of cells, each with its own signalling and fate, so that cells taking up TNF shade their
  neighbours.

The plan and its progress: {doc}`design/roadmap`.
