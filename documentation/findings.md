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

## The more TNF, the fewer cells survive

The dose study bathed cells, starting at rest, in uniform TNF, held steady or fading away, at three speeds of the fate
network's clock, with NF-κB working and with it knocked out ({doc}`design/studies`):

- **Survival falls steadily with dose.** Held at the lowest dose (0.5% of the receptors bound), 93 to 99 cells in 100
  are alive after a day. With every receptor bound, none are at the fastest clock; at the slowest, a quarter are with
  NF-κB working and 14 in 100 without it.
- **NF-κB saves few cells:** knocking it out costs at most about 10 cells in 100, at the highest doses and the slowest
  clock, close to the limit Study 1 found.
- **At low doses most cells have not committed to any fate within the day,** and under held TNF cells are still dying
  when the day ends.
- **More TNF brings NF-κB into the nucleus sooner:** its first peak comes about 24 minutes after a full dose arrives,
  against about 40 at the lowest dose.
- **In fading TNF, few cells are still dying when the day ends:** at most 3 in 100 in the last 4 hours, against up to
  15 under steady TNF. Each fading bath is matched to a cell of the distance study, with the same peak TNF and the same
  dose as the cell's receptors sense it. The weakest third leave at least 96 cells in 100 alive.

## Distance matters mostly through dose

The distance study placed cells 100 µm, 300 µm and 1 mm from a pulse of TNF in an open medium, at three pulse sizes,
and compared each with its matched fading bath: the same peak TNF and the same dose as its receptors sense it, but
without the delay before TNF arrives or the pulse's shape ({doc}`design/studies`). The rule for a match (survival at 24 h
within 5 cells in 100) was fixed before any distance run.

- **In 41 of the 54 comparisons, survival matches the bath within 5 cells in 100:** every cell 1 mm away and every
  cell at the smallest pulse.
- **Close to the larger pulses, cells survive a little more than in their bath,** by 3 to 7 cells in 100. All 13
  comparisons that don't match lean this way, 11 of them at the largest pulse. In 6 the difference is statistically
  clear, though not shown to reach 5 in 100; 7 can't be called either way. So the pulse's timing protects slightly where exposure
  is strong; which part of it, the delay or the shape, is still open.
- **The lean runs through the whole map.** Where nearly every cell lives, a match says little, and in 16 of those 20
  comparisons there are also fewer deaths beside the pulse than in the bath.
- **Cells without NF-κB show the same lean, a little weaker,** so the effect does not seem to need NF-κB.

## Next

- **Wave timing:** when the TNF front reaches a cell against when NF-κB enters its nucleus, from the distance study's
  runs, to see why cells survive a pulse more often than its matched bath.
- **Many cells:** a field of cells, each with its own signalling and fate, so that cells taking up TNF shade their
  neighbours.

The plan and its progress: {doc}`design/roadmap`.
