# Glossary

Adapter
: A Step that translates one layer's quantity into the form another layer reads, for example `RegionMean` and
  `MathExpressionStep`.

Alive
: A cell with no death node (Apoptosis, NonACD) on at any tick of the run. Death is irreversible, but Calzone's own
  death nodes can switch off again, so a cell's end state alone could show a dead cell as alive. The composite now makes
  them absorbing (`absorb_death = 1`), so there a dead cell's end state also shows it dead.

Check
: A compose-api compliance case: a document, an interval and expectations scored by `compliance.evaluate`. It always
  has an independent oracle and a proven-failing negative.

compose-api
: The BioSimulations service that runs process-bigraph documents on HPC. Its runner and scorer are what the checks use.

Durable survival
: Alive at 24 h with the Survival node on. In the composite the Survival node follows the flickering NFkB node,
  so most protected cells are alive with Survival off; *alive* is the primary readout.

End state
: A cell's fate nodes at the end of a run, encoded as Survival + 2·Apoptosis + 4·NonACD. Fate nodes can overlap,
  so they are never summed across nodes.

First fate
: The first fate node a cell switches on. Reported next to the end state; a tie means two switched on within one
  coupling step.

`k_time`
: Calzone time units per composite second. It multiplies every Boolean rate and is swept as the death machinery's
  clock.

Kappa (κ)
: How fast the Boolean NFkB node flips, in s⁻¹. It switches on at $f\kappa$ and off at $(1-f)\kappa$. The
  composite uses ln 2 / 337 s, Lipniacki's NF-κB half-rise (Study 0).

Mash-up
: An environment compose-api builds automatically from the simulator packages a document's processes come from.

Nuclear fraction $f$
: $(\text{NFKB\_nuc}/K_v)/\text{NFKB\_total}$: Lipniacki's free nuclear NF-κB as a fraction of all NF-κB.

Occupancy
: The fraction of time a Boolean node is on. For an NF-κB target product it is set by induction (`r_tx`, only while
  NFkB is on) against switch-off (only while NFkB is off), weighted by NF-κB's duty cycle $f$ (Study 0d).

Oracle
: The source of a check's expected values, independent of the code under test.

`r_tx`
: The rate at which NF-κB target genes switch on, per second, measured from Lipniacki
  ($\ln 2 / 2107\ \text{s}$).

Study, investigation
: A viva workspace study runs a research question through design, build, simulate, evaluate and decide, with its
  decisions and evidence recorded. An investigation groups studies under one question.

Window average
: What MaBoSS reports: a probability averaged over a time window, not at an instant.
