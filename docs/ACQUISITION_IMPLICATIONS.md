# Acquisition Implications

Notional guidance derived from `docs/TRADE_STUDY.md` and
`docs/V2_VS_V3.md`'s v3 evidence, not a real acquisition recommendation.
Every item below is tied to a specific finding; none is asserted without
that link.

## The headline finding: buy access first; processing allocation only matters above an access threshold, and even there, barely

**Evidence**: `experiments/e12_access_sweep.py` swept satellite count
(1-32) and Army ground-terminal count (1-4), 18 cells, and tested every
pair of the seven candidate architectures for a statistically significant
difference in mission-thread success at each cell
(`src/leo_edge/stats.py::paired_bootstrap_diff_ci`, `figures/fig20.png`).
**17 of 18 cells show no statistically significant difference between any
pair of architectures.** Pooled mission-thread success rate (single
terminal) rises from under 0.1% at 1-4 satellites to about 1.0% at 16
satellites, an order-of-magnitude improvement driven entirely by access
density, not by which architecture was used (`docs/V2_VS_V3.md` has the
full table). The one cell that does show a significant difference (16
satellites, 1 terminal) favors ThreadAwarePriority (A6), the
mission-thread-aware design proposed after seeing v2's results, not any of
the original A0-A5 candidates -- and even there, the underlying rate is
still about 1%, not a working system.

**Implication**: this is the single most load-bearing finding in this
repository, replacing v2's "contact frequency dominates at one access
level" with the stronger "contact frequency dominates at essentially every
access level tested, up to 32 satellites and 4 ground terminals." An
acquisition strategy that specifies an onboard processing architecture in
detail before securing enough constellation access to make mission-thread
success non-trivial is optimizing a second-order variable. Access --
number of satellites reachable from a terminal, and number of terminal
sites -- should be the primary acquisition lever; which processing
architecture the provider uses should be a secondary, much lower-stakes
requirement, at least until real-world evidence (not this notional model)
establishes where a real access threshold sits.

## Require: tiered product generation, not just compression -- necessary but nowhere near sufficient

**Evidence**: GroundOnly, CompressedFull, and ContactAware scored exactly
0% mission-thread success at every access level tested, for a structural
reason: none of them ever produce anything but a single, full-scene-scale
product. Only QuicklookFirst, RoiFirst, Progressive, and ThreadAwarePriority
-- the architectures with a real early tier matching a thread's need --
ever succeed at all. But per the headline finding above, which *of those
four* is used essentially never makes a statistically detectable
difference across the swept access range.

**Implication**: requiring tiered product generation from a commercial
provider is a real, load-bearing requirement (it's the difference between
"can ever succeed" and "structurally cannot"), but it is not where the
acquisition effort should concentrate once that baseline is met. Beyond
"produce more than one tier," further refining which specific tiered
architecture is used is not supported by this evidence as a priority.

## Require: direct edge tasking as an available path, not just reachback

**Evidence**: `docs/MISSION_THREADS.md` models both a reachback tasking
path and a direct edge path, the former adding more latency. Across the
v3 sweep, this added delay is consistently small relative to the wait for
the next usable contact, so it rarely changes a trial's outcome on its
own.

**Implication**: unchanged from v2's assessment. A service architecture
that *only* supports reachback tasking has no fallback if that link is
lost; requiring a direct-edge tasking interface as a standard,
always-available capability costs little given how small its measured
effect is here, and removes a real single point of failure.

## Build: terminal-side capability -- not a priority until access is addressed

**Evidence**: neither terminal class (vehicle-mounted vs.
dismounted/manpack) nor terminal count (1 vs. 2 vs. 4 sites) produced a
consistent, significant difference in mission-thread success across the
v3 sweep. Some cells favor more terminals, some show no difference, and
`docs/V2_VS_V3.md`'s cost-tradeoff figure (`figures/fig21.png`) shows the
4-terminal curve is not uniformly better than 1 or 2 terminals -- it's
noisier, including cells that drop to zero success despite higher notional
cost, a combination of the single-orbital-plane clustering effect
(`docs/DECISION_LOG.md` ADR-018) and sampling variance at these still-low
rates.

**Implication**: don't over-invest in terminal-side upgrades (compute,
additional sites) as the primary lever; satellite access density is the
stronger, more consistent driver in this data. This doesn't mean terminal
investment is worthless, only that it's not where the evidence says to
spend first.

## Standardize: the tasking and product-tier interface, not the onboard implementation

**Evidence**: `docs/STAKEHOLDERS.md`'s acquisition/commercial-provider
conflict, and `docs/TRADE_STUDY.md`'s v3 finding that `RoiFirst` beats
`Progressive` on the `COMBINED` (simulated + derived) ranking specifically
because it requires fewer distinct provider-side functions
(`acquisition_lock_in_risk`, derived from real tier counts, not a
hand-picked number) -- a genuine, code-derived acquisition-relevant
tradeoff, distinct from and additional to the access-dominates finding
above.

**Implication**: specify the tiered-product interface (what tiers exist,
what each one's fidelity floor is, how to request one directly, and how to
request which tier is prioritized first) as the acquisition requirement,
not a specific onboard compression algorithm or processing architecture.
Given the access-dominates finding, favor the *simplest* tiered
architecture that clears the "produces the needed tier" bar (e.g.
`RoiFirst`'s two tiers) over a more elaborate one (`Progressive`'s five,
or `ThreadAwarePriority`'s reordering logic) unless a specific,
demonstrated need justifies the added acquisition complexity -- since this
data shows the more elaborate options don't reliably buy back
statistically detectable mission-thread performance at the access levels
tested.
