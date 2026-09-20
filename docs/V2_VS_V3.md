# v2 vs v3: what changed and which conclusions survive

> **Superseded in part by `docs/V3_VS_V4.md`.** The access-sweep table, the "single-plane clustering" explanation, and the "architecture is second-order" headline below were built on a time-shift constellation approximation and are retracted.

`results/frozen/v2/` is left untouched. `results/frozen/v3/` is
regenerated with the Part 1 fixes (`docs/DECISION_LOG.md` ADR-015 through
ADR-017) and adds the access/revisit sweep (`experiments/e12_access_sweep.py`,
ADR-018) as new evidence, not a replacement for `e11`.

## The core methodological bug, in one number

v2's trade study scored `GroundOnly` best-in-class (1.0/1.0) on "terminal
SWaP burden." GroundOnly sends raw, unprocessed bytes; it does zero
onboard processing, meaning the Army terminal has to do all of the
interpretation work itself. That's the *worst* case for terminal burden,
not the best. The criterion was measuring the wrong segment's burden.
`docs/TRADE_STUDY.md`'s v3 version fixes this by splitting it into two
correctly-signed, code-derived criteria; GroundOnly now scores worst on
`terminal_processing_burden` (0.0) and best on
`space_segment_processing_burden` (1.0), which is what should have been
true all along.

## What changed in the evaluation engine

- **Paired trials.** v2 drew each architecture's random request time and
  contact-denial mask independently, architecture-outer. v3 draws one
  shared trial context per trial index, reused across every architecture,
  which is what makes `src/leo_edge/stats.py::paired_bootstrap_diff_ci`'s
  significance tests valid rather than mislabeled.
- **Collection timing.** v2 treated collection as instantaneous at request
  time; only the downlink wait was modeled. v3 adds a real SGP4
  imaging-opportunity model: a request must wait for the next actual
  overflight of a notional AOI location before any downlink window is
  usable. This alone pushed the best architectures' mean success rate from
  v2's ~1.9% down to well under 0.1% in the single-satellite/single-terminal
  baseline, since a second real orbital wait now stacks on the first.
- **MT-3 restored, MT-4 fixed.** v2 dropped MT-3 (battle damage assessment)
  entirely and evaluated MT-4 (persistent monitoring) with the same
  single-request machinery as every other thread, despite
  `docs/MISSION_THREADS.md` defining MT-4's tolerance as measured per
  collection pass, not per request. v3 restores MT-3 (modeled as needing a
  P3_ROI-sized change product, gated on prior-reference availability) and
  makes MT-4 genuinely cadence-based (walks every real pass across the
  horizon; 2+ consecutive misses fails the thread).
- **Structural incapacity separated from slowness.** Every v3 trial row
  records whether the architecture ever produces the needed tier at all,
  separately from whether it produced it too slowly. v2's success rate
  numbers folded both into one boolean.
- **Censoring-aware latency.** v2's "latency" trade-study criterion
  averaged TFUP over completed `e03` rows only, silently dropping every
  non-completion. v3 uses a Kaplan-Meier-style median over `e11`'s
  per-trial data, treating non-completions as censored at the evaluation
  horizon.

## Which v2 conclusions die

- **"Progressive wins every stakeholder-weight profile" (v2's headline
  trade-study result).** Does not survive. With the terminal-SWaP fix and
  code-derived lock-in-risk criterion, `RoiFirst` wins the `COMBINED`
  ranking (all seven criteria) under every single profile tested, because
  its smaller tier count (2, vs. Progressive's 4) gives it a real
  advantage on `acquisition_lock_in_risk` that outweighs Progressive's
  edge on the purely simulated criteria. Progressive (or A6, once added)
  still wins the `SIMULATED_ONLY` view in every profile -- the flip only
  happens once the derived architecture-property criteria are included,
  and `docs/TRADE_STUDY.md` now states that explicitly instead of hiding
  it inside one blended score.
- **"A6 (ThreadAwarePriority) is a clear improvement" (v2's framing).**
  Does not survive as stated. Tested directly (the task's own example: 73
  vs. 69 successes out of 6,000 v2 trials), the gap was never large enough
  to matter on its own, and v3's paired bootstrap test on the *v3* data
  (7 vs. 7 successes out of 9,000 paired trials at the single-satellite
  baseline) finds literally zero difference. Across the full 18-cell
  access sweep, A6 is the statistically significant best architecture in
  exactly one cell out of 18 (16 satellites, 1 terminal); everywhere else,
  including the highest-access cells, there is no significant difference
  between it and the other tiered architectures. A6 remains a reasonable
  proposed design (`docs/DECISION_LOG.md` ADR-014), but "it wins" was
  never a tested claim in v2, and now that it has been tested, it mostly
  doesn't.
- **"Contact geometry, not architecture, is the binding constraint"
  framed as a single-satellite artifact.** The specific numbers die (v2's
  ~2% best-case average is now well under 0.1% at the same access level,
  once collection timing is modeled honestly), but the *qualitative*
  conclusion is not just preserved, it's confirmed far more strongly: the
  access sweep (`experiments/e12_access_sweep.py`) shows 17 of 18
  satellite x terminal cells have no statistically significant difference
  between architectures at all. This was v2's headline finding tested at
  one access level; v3 tests it at 18, and it holds at all but one.

## Which v2 conclusions survive

- **QuicklookFirst, RoiFirst, and Progressive-family architectures are the
  only ones that can ever succeed a tiered mission thread; GroundOnly,
  CompressedFull, and ContactAware structurally cannot.** Confirmed again
  in v3's `structural_incapacity` field, now tracked explicitly rather
  than folded into a success rate.
- **Access, not processing, dominates.** Confirmed and substantially
  strengthened; see above.
- **The correctness fixes from v1->v2 (censoring, capacity capping,
  fidelity labeling) are unaffected by this pass** and remain load-bearing
  under the v3 evaluation engine.

## New in v3: the access threshold

The access/revisit sweep is the first evidence in this repository that
directly answers "how much access is enough." Pooled across all threads
and both swept conditions, single-terminal mission-thread success rate by
satellite count:

| Satellites | 1 | 2 | 4 | 8 | 16 | 32 |
|---|---|---|---|---|---|---|
| Success rate | 0.07% | 0.07% | 0.04% | 0.41% | **1.03%** | 0.56% |

Success rate rises roughly an order of magnitude starting at **8
satellites** and peaks around **16**, then falls at 32. That fall is not
evidence that more satellites hurt; it's a real, documented limitation of
this sweep's phase-offset approach (`docs/DECISION_LOG.md` ADR-018):
spreading many satellites within one orbital plane produces clustered
bursts of passes with long gaps between them, not evenly-spaced revisits,
so total contact-duration coverage keeps rising (confirmed: ~1.5% of the
week at 1 satellite to ~27% at 32) even as tight-tolerance threads can
still land in a remaining gap and fail. A true multi-plane constellation,
not modeled here, would be expected to convert that rising coverage into
a more monotonic success-rate gain.

Architecture separation with statistical significance: **essentially
never**, within the swept range. 17 of 18 (satellite, terminal) cells show
no significant difference between any pair of architectures
(`figures/fig20.png`). This is a real result, not a null finding to
explain away: it says the allocation-of-processing-architecture question
this whole repository studies is, empirically, second-order compared to
the allocation-of-access-and-terminal question, across every access level
this sweep tested.

## Every ASSUMED value driving this headline

- AOI location offset (45N, 5E vs. the 40N/0E ground terminal):
  `experiments/e11_mission_thread_success.py`, notional, not a real
  geodesic claim.
- `PRIOR_REFERENCE_PROB = 0.5` for MT-3.
- Mission-thread tiers/tolerances: `src/leo_edge/mission_threads.py`,
  all labeled ASSUMED in `docs/MISSION_THREADS.md`.
- Contested-condition parameters (interference derate, contact denial
  fraction, tasking delay): `docs/MISSION_THREADS.md`.
- Terminal-site coordinates for the access sweep (4 notional sites):
  `experiments/e12_access_sweep.py::TERMINAL_SITES`.
- The relative cost proxy behind `figures/fig21.png`
  (`RELATIVE_COST_PER_SATELLITE = 10`, `_PER_TERMINAL = 3`,
  `_PER_PROCESSING_TIER = 1`): explicitly labeled ASSUMED, relative units,
  not a dollar estimate, in `experiments/e12_access_sweep.py` and
  `docs/ACQUISITION_IMPLICATIONS.md`.
- The single-orbital-plane phasing approach itself
  (`docs/DECISION_LOG.md` ADR-018): a real limitation, not an ASSUMED
  parameter, but it shapes the headline access-threshold number and is
  stated as such above.
