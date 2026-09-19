# Research Design

## Central research question

How should imagery functions (tasking, collection, processing,
prioritization, delivery) be allocated between a commercial LEO space
segment acquired as a service and an Army-owned tactical edge segment, and
how does the preferred allocation shift across mission needs, terminal
classes, and contested or DDIL conditions? (`docs/DECISION_LOG.md`
ADR-007.) Everything operational is notional and unofficial.

## The design principle behind every experiment

The study does not ask "which architecture is best?" It asks "under what
conditions does each allocation become advantageous, and where does the
whole approach hit a wall that no allocation choice can fix?" The output
is a set of transition boundaries and honestly-reported limits, not a
single winner. `docs/TRADE_STUDY.md`'s weight-sensitivity sweep exists for
exactly this reason: to show where the ranking of candidate allocations
changes as stakeholder priorities change, not to declare one permanent
champion.

## Supporting questions

- **Processing allocation**: how do onboard compute time, product
  tiering, downlink rate, and contact duration change which architecture
  completes fastest within a single contact window? (`docs/TRADE_STUDY.md`'s
  single-window evidence, `figures/fig04.png`.)
- **Mission-thread success**: does the preferred allocation change
  depending on which mission thread (`docs/MISSION_THREADS.md`) is being
  served, given its specific first-needed tier and latency tolerance?
- **Terminal class**: does a vehicle-mounted terminal's higher rate and
  compute change which allocation wins, versus a dismounted terminal's
  lower rate and minimal compute?
- **Contested conditions**: how does mission-thread success degrade under
  interference, contact denial, and reachback loss, and do any
  architectures degrade gracefully versus catastrophically?
  (`docs/TRADE_STUDY.md`'s resilience section.)
- **Acquisition implication**: what does the evidence say the Army should
  require of a commercial provider, build into the terminal, or
  standardize between them? (`docs/ACQUISITION_IMPLICATIONS.md`.)

## Working hypotheses

These were testable, not conclusions, and the experiments were allowed to
reject them. Stated here as originally posed, with what actually happened
noted, not silently updated to match the result.

1. **Tiered architectures serve tighter-latency mission threads better
   than atomic (single-product) architectures.** Confirmed, and more
   starkly than expected: GroundOnly, CompressedFull, and ContactAware
   scored exactly 0% mission-thread success on every thread tested,
   structurally, because they never produce an early tier at all
   (`docs/TRADE_STUDY.md`).
2. **Terminal class changes which allocation wins.** Not supported by this
   dataset: mission-thread success rates were statistically indistinguishable
   between vehicle-mounted and dismounted terminals
   (`docs/ACQUISITION_IMPLICATIONS.md`), because contact scarcity dominated
   before terminal-class differences could matter. This is a real result
   about the model's current scope, not a claim that terminal class doesn't
   matter in general; see `docs/ALLOCATION_SPACE.md`'s uncovered-regions
   section.
3. **Contested conditions will separate resilient architectures from
   fragile ones.** Not supported: no architecture in this dataset degraded
   gracefully in the sense of holding onto success under degraded
   conditions it didn't already have under nominal ones
   (`docs/TRADE_STUDY.md`'s resilience section). Degradation only ever made
   things worse or left already-zero success rates at zero.
4. **A single ground site's contact schedule would be dense enough to test
   meaningful architecture differentiation against minute-scale mission
   thread latency tolerances.** Rejected. This was an implicit assumption
   in the original mission-thread latency tolerances
   (`docs/MISSION_THREADS.md`), not a hypothesis stated going in, but it's
   worth recording as a real finding: contact geometry (~28 passes/week,
   hours apart) dominates total latency far more than any architecture
   difference, which is the actual headline result
   (`docs/ACQUISITION_IMPLICATIONS.md`).

## What the results actually showed

See `docs/TRADE_STUDY.md` for the full write-up and
`docs/ACQUISITION_IMPLICATIONS.md` for what it implies. In short:
mission-thread success tops out around 5% for the best architecture
(Progressive); three of six architectures never succeed at all, for a
structural reason unrelated to speed; and the dominant constraint across
the whole dataset is contact frequency, not which onboard processing
architecture is chosen.
