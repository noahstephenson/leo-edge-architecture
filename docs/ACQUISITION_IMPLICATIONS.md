# Acquisition Implications

Notional guidance derived from `docs/TRADE_STUDY.md` and
`docs/V3_VS_V4.md`'s v4 evidence, not a real acquisition recommendation.
Every item below is tied to a specific finding. All numbers come from
`results/frozen/v4/`; access-sweep cells use 40 trials per thread, so treat
differences under ~3 percentage points as noise.

## The headline finding: access moves mission-thread success most; tiering is necessary; among tiered designs the differences are real but smaller

**Evidence**: `experiments/e12_access_sweep.py` swept real Walker-delta
constellations (each satellite propagated individually with SGP4) from 1 to
24 satellites and 1 to 4 ground terminals, with same-pass
collect-and-downlink allowed. The best architecture's pooled success rate
rose from about **3%** (1 satellite) to about **31%** (24 satellites in 8
planes, 4 terminals). It never reached 50%, and it had not flattened when
the sweep stopped at 24 satellites (a 32-satellite run was killed by host
memory pressure, `docs/DECISION_LOG.md` ADR-023), so the access level at
which success becomes "substantial" (50% or more) is **not found in this
sweep**, and is not extrapolated.

Architectures could only be compared where success was high enough to be
meaningful (best architecture above 30%). That happens in **one of 21
cells**: 24 satellites, 8 planes, 4 terminals (504 paired trials). There,
ThreadAwarePriority (31.2%) and Progressive (30.8%) are statistically tied,
and both beat RoiFirst by about 7 points (significant) and every other
architecture by 24-31 points. RoiFirst never sustains MT-4 (0 of 24 trials,
versus 12 of 24 for the other two). The other 20 cells are uninformative:
nothing worked well enough to test.

**Implication**: v3's claim that processing architecture is "second-order"
is not supported as stated. By magnitude, adding access (about 3% to 31%)
still matters more than choosing among tiered architectures (about 7
points), and tiering itself is decisive (0% versus roughly 31%). But once
access is high enough that anything works, the choice among tiered designs
does matter, and it favors the full-tier designs over RoiFirst. An
acquisition strategy should therefore secure access first, require tiered
products, and expect the architecture choice to start to matter only after
access approaches the level where success passes about 30% (here, roughly
16-24 satellites with 4 ground terminals in this notional model). That one
informative cell is thin evidence and should be re-tested with more trials
and a larger constellation before anyone leans on it.

## Require: tiered product generation, not just compression

**Evidence**: GroundOnly, CompressedFull, and ContactAware score exactly 0%
at every access level tested, because none produces an early tier. Only
QuicklookFirst, RoiFirst, Progressive, and ThreadAwarePriority can ever
succeed, and QuicklookFirst almost never does (about 0-1%).

**Implication**: requiring tiered product generation is the difference
between "can ever succeed" and "structurally cannot." At the
single-satellite baseline, the ordering among tiered designs is already
statistically significant (ThreadAwarePriority 142, Progressive 129, RoiFirst
109 successes of 9,000 paired trials), so the choice among them is not
irrelevant, only smaller than tiering itself.

## Require: same-pass delivery, as an explicit service term

**Evidence**: allowing an image to be downlinked on the same pass that
collected it (v4, `docs/DECISION_LOG.md` ADR-020) moved ThreadAwarePriority
from 7 of 9,000 baseline successes (v3) to 142 of 9,000, with no change to
any architecture.

**Implication**: whether a provider can deliver on the collecting pass is a
larger lever in this model than any processing-architecture difference at
the baseline. It should be a stated requirement, not an assumed capability.

## Require: direct edge tasking as an available path, not just reachback

**Evidence**: `docs/MISSION_THREADS.md` models reachback and direct-edge
tasking paths; the reachback path adds a tasking delay (180 s versus 60 s).
That delay is small compared with the wait for the next overflight
(median gaps of roughly 700-5,700 s across the swept constellations).

**Implication**: unchanged from earlier versions. Direct-edge tasking costs
little in measured effect and removes a single point of failure if
reachback is lost.

## Note on the shortest-tolerance threads

**Evidence**: MT-1 (120 s) and MT-4 (300 s) are flagged infeasible at every
constellation swept on the revisit-aware floor (`docs/V3_VS_V4.md`); no
thread is structurally infeasible. MT-1 reached only about 1% at 24
satellites and 0% at one satellite even with 4x the tolerance.

**Implication**: do not expect these two thread types to be met by
constellation size alone within the range studied; they depend on
overflight timing more than on architecture. This is a limit of the swept
range and the assumed tolerances (all ASSUMED), not a proven impossibility.

## Build: terminal-side capability is secondary to satellite access

**Evidence**: at 24 satellites, success rose from 19.8% (1 terminal) to
27.4% (2) to 31.2% (4), a real but smaller gain than satellite count
provides. At smaller sizes the terminal effect is inside sampling noise
(for example 8 satellites: 7.9%, 10.5%, 6.2% for 1, 2, 4 terminals).

**Implication**: satellite access is the stronger driver; extra terminal
sites help mainly once the constellation is already large.

## Standardize: the tasking and product-tier interface, not the onboard implementation

**Evidence**: `docs/TRADE_STUDY.md`. Under the v4 lock-in proxy (tier count
plus a doubled weight for per-request conditional logic, tied to
`docs/INTERFACES.md`), RoiFirst wins the COMBINED ranking in every
stakeholder profile, even though ThreadAwarePriority and Progressive beat
it on mission-thread success and latency with statistical significance.
The RoiFirst flip is not an artifact of the earlier proxy: it persists
under the ownership-boundary version.

**Implication**: specify the tiered-product interface (which tiers exist,
their fidelity floor, how to request one, how to prioritize) rather than an
onboard algorithm. Choosing RoiFirst buys a simpler interface but costs
roughly 7 points of success in the one informative cell and cannot sustain
MT-4; choosing Progressive or ThreadAwarePriority buys that performance
with a larger, and for ThreadAwarePriority a runtime-conditional, interface
to specify. That is a real tradeoff for the requirement owner to weigh, not
one this model resolves.

## Notional cost tradeoff

`figures/fig21.png` plots success against a relative cost proxy
(satellites x10, terminals x3, processing tiers x1). These weights are
ASSUMED relative units, not dollars.
