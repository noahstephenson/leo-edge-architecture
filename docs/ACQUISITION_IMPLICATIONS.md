# Acquisition Implications

Notional guidance derived from `docs/TRADE_STUDY.md`'s evidence, not a
real acquisition recommendation. Every item below is tied to a specific
finding; none is asserted without that link.

## Require: tiered product generation, not just compression

**Evidence**: GroundOnly, CompressedFull, and ContactAware scored exactly
0% mission-thread success on every thread and every condition tested
(`docs/TRADE_STUDY.md`), for a structural reason: none of them ever
produce anything but a single, full-scene-scale product. QuicklookFirst,
RoiFirst, Progressive, and ThreadAwarePriority, the only architectures
with a real early tier matching a thread's need, are the only ones that
ever succeed, and ThreadAwarePriority (which reorders around whichever
tier the active thread actually needs, instead of a fixed order) scores
highest of the four.

**Implication**: a commercial imagery service the Army buys into should be
required to produce genuinely tiered products (at minimum a coarse
detection tier and an ROI tier, distinct from the full scene) AND support
requesting a specific tier first, not just a fixed delivery order. "Onboard
processing" as a checkbox requirement is not the same as "onboard
tiering," and tiering alone is not the same as "tiering the Army can
prioritize per request": this data shows the latter has the best, though
still small, chance of serving a time-sensitive or fidelity-differentiated
mission thread.

## Require: direct edge tasking as an available path, not just reachback

**Evidence**: `docs/MISSION_THREADS.md` models both a reachback tasking
path (through a rear-echelon cell) and a direct edge path, with the
former adding more latency. `docs/TRADE_STUDY.md`'s REACHBACK_LOST
condition (which forces the direct path) did not measurably worsen
outcomes versus NOMINAL in this dataset, since contact-gap latency already
dominates both paths' added delay.

**Implication**: this specific dataset does not show a strong case either
way on tasking-path latency, because contact geometry swamps the
difference (see below). What it does show is that a service architecture
that *only* supports reachback tasking has no fallback if that link is
lost; requiring a direct-edge tasking interface as a standard, always-
available capability (not just an emergency mode) costs little given how
small its measured effect was here, and removes a real single point of
failure.

## Build: terminal-side capability matched to what the architecture actually needs

**Evidence**: `docs/MISSION_THREADS.md`'s terminal classes did not produce
a measurable difference in mission-thread success rate in this dataset
(overall-by-terminal-class breakdown: 0.44% dismounted vs. 0.49%
vehicle-mounted, both near the noise floor). That is not evidence that terminal
class doesn't matter; it's evidence that, in this dataset, contact
scarcity dominates so completely that neither terminal class's extra
downlink rate or compute made a visible difference. `docs/ALLOCATION_SPACE.md`
also notes that no architecture here actually branches on terminal class at
all, so this finding says more about a gap in the model than about the
real world.

**Implication**: don't over-invest in terminal-side compute upgrades to
solve a latency problem, until the contact-frequency problem (next item) is
addressed; a faster or smarter terminal cannot compensate for a satellite
that isn't in view.

## The headline finding: contact frequency, not architecture, is the binding constraint

**Evidence**: mission-thread success rates topped out around 5% for the
best single architecture/thread/condition cell, and averaged under 2% even
for the best architecture (ThreadAwarePriority) across all threads and
conditions (`docs/TRADE_STUDY.md`). A single ground site sees about 28
contact opportunities per week
(`results/frozen/v2/e01_access_windows.csv`), several hours apart on
average. Every mission thread's latency tolerance (2-15 minutes) is far
shorter than that gap, so unless a request happens to land right before an
already-scheduled pass, no architecture choice, mission-thread-aware or
not, changes the outcome much. This repository's separate
constellation-handoff experiment
(`experiments/e09_constellation_handoff.py`) already shows a 3-satellite
constellation roughly doubling ground-contact coverage fraction (1.7% to
3.7%) versus a single satellite over the same site.

**Implication**: the acquisition lever that actually moves mission-thread
success is contact frequency, not which onboard processing architecture is
required. That means either (a) requiring the commercial provider to offer
a constellation-scale service (more satellites reachable from a given
terminal, not just one), (b) fielding or contracting for more ground sites
so the same constellation is reachable more often, or (c) restricting
tight-latency mission threads (MT-1 in particular) to scenarios where a
pass is already known to be imminent, rather than treating "request now,
need it in 2 minutes" as a general capability. Any acquisition strategy
that focuses only on the onboard-processing requirement while leaving
contact frequency unaddressed will not move the mission-thread-success
number this trade study actually measured.

## Standardize: the tasking and product-tier interface, not the onboard implementation

**Evidence**: `docs/STAKEHOLDERS.md`'s acquisition/commercial-provider
conflict, and `docs/TRADE_STUDY.md`'s weight-sensitivity sweep, which shows
GroundOnly (the architecture with nothing onboard to specify) becoming
competitive once lock-in-risk avoidance is weighted heavily, purely
because there's nothing proprietary to lock into.

**Implication**: specify the tiered-product interface (what tiers exist,
what each one's fidelity floor is, how to request one directly, and how to
request which tier is prioritized first for a given collection) as the
acquisition requirement, not a specific onboard compression algorithm or
processing architecture. That gets the mission-thread benefit of both
tiering and mission-thread-aware prioritization (the first, most
load-bearing requirement above, and the small-but-real edge
ThreadAwarePriority showed over a fixed order) without locking the Army
into one provider's specific onboard implementation, which is exactly the
tension `docs/STAKEHOLDERS.md` identifies between the commercial provider
and the acquisition office.
