# Model Reference

Derivation-level detail on how the simulation actually computes its
numbers, kept separate from the architecture-focused top-level docs
(`docs/ALLOCATION_SPACE.md`, `docs/TRADE_STUDY.md`) so those stay readable
without requiring the reader to follow the math first.

## Contact capacity

A contact window of duration `D` seconds at downlink rate `R` bits/second
holds `C = (R / 8) * D` bytes. This is the single formula everything in
`src/leo_edge/architectures.py` and `src/leo_edge/simulation.py` builds on.

## Single-window evaluation (`architecture.run()`)

Each architecture's `run()` method answers: given one contact window with
capacity `C`, what fits, and does the product this architecture cares about
(a single tier for A0/A1/A5, a two-tier sequence for A2/A3, a five-tier
sequence for A4/A6) complete within that one window? Bytes are always
capped to `C`; a tier that doesn't fully fit is not delivered, and `tfup_s`/
`tcp_s` are `NaN` for whatever didn't complete (`completed = False`), never
a fabricated number for a truncated delivery. See `docs/DECISION_LOG.md`
ADR-008 and `docs/V1_VS_V2.md` for why this matters and what changed.

A6 (`ThreadAwarePriority`) reorders A4's same five tiers around whichever
one the active mission thread needs (`docs/DECISION_LOG.md` ADR-014), so
unlike every other architecture, its tier sizes in priority order are not
monotonically increasing. Its `run()` therefore can't use A4's "stop at
the first tier that doesn't fit" shortcut; it must try every remaining
tier, since a smaller, lower-priority one can still fit after a larger,
higher-priority one didn't. Its `tiers()` method (used by
`simulate_multi_contact`, below) is inherited unchanged from Progressive
and does not carry this skip-ahead behavior into the multi-contact case:
across multiple windows, an undelivered priority tier's bytes still carry
forward strictly in order before any later tier is attempted, which is a
real, intentional difference between the single-window and multi-contact
evaluation of the same architecture, not a bug.

Processing time is charged as elapsed time from collection, not clipped to
the transmit window; the modeling choice is that processing happens before
or independent of the transmit-capacity check, and a product that would
take longer to process than the mission can tolerate shows up as a
timing failure downstream (in `docs/MISSION_THREADS.md`'s latency
tolerances), not as a bug in the single-window capacity math.

## Multi-contact delivery (`simulation.simulate_multi_contact`)

Real mission threads span more than one contact window. This function
walks an ordered list of `(window_start_s, duration_s)` pairs (relative to
a common clock, usually request time; see `contact_windows_from_access_windows`)
and, for each architecture's ordered tier plan (`architecture.tiers()`),
carries undelivered bytes forward:

1. Within a window, any processing time still owed on the tier currently
   in progress is spent first. If processing alone exceeds the window,
   the window closes with no bytes sent and the remaining processing time
   carries to the next window.
2. Remaining window time is spent transmitting toward the current tier's
   byte target, at `C = (R/8) * remaining_time`.
3. If the tier's target is reached, its completion timestamp (relative to
   the clock's zero point) is recorded in `tier_completion_s`, keyed by
   the tier's name, and the walk advances to the next tier (which may
   still have transmit capacity left in the same window).
4. If a window's capacity runs out mid-tier, the shortfall carries to the
   next window in the list.
5. A tier that never finishes across every window given is never recorded;
   `tfup_s` (first tier) and `tcp_s` (last tier) stay `NaN` and
   `completed` is `False`.

This is the engine `experiments/e11_mission_thread_success.py` uses to
check whether a mission thread's specific first-needed tier (not just
"the" product) was delivered within its latency tolerance.

## Mission-thread latency accounting

Total latency for a mission-thread trial is measured from the user's
request, not from image capture:

```
request_time  (random point in the simulated week)
  + tasking_delay_s          (docs/MISSION_THREADS.md tasking-path table)
  = earliest_usable_s        (collection cannot begin before this)

contact windows before earliest_usable_s are excluded entirely; the
remaining windows are re-based so time 0 = request_time, then walked by
simulate_multi_contact as above. The resulting tier_completion_s values
are therefore already measured from request_time, with the tasking delay
and the wait for the first usable contact both included, with no further
addition needed.
```

This is why `docs/TRADE_STUDY.md`'s mission-thread success rates are
dominated by contact-gap statistics, not by architecture-specific
processing speed: the wait-for-next-contact term is usually much larger
than any difference in `simulate_multi_contact`'s per-tier transmit time
between architectures.

## Energy

`processing_energy_j = processing_time_s * PROCESSING_POWER_W` and
`tx_energy_j = tx_time_s * RADIO_POWER_W`, both linear in time. Power
constants and all sizing ratios live in `config/product_sizing.yaml`; see
`docs/ASSUMPTIONS.md` for which are measured versus assumed.

## Contested-condition parameters

`docs/MISSION_THREADS.md`'s three DDIL parameters compose as follows in
`experiments/e11_mission_thread_success.py`:

- **Interference derate** multiplies the terminal class's nominal
  `rate_bps` before it's passed to `simulate_multi_contact`.
- **Contact denial** drops a random fraction of the candidate contact
  windows (per-window Bernoulli trial) before they're passed in, modeling
  EMCON/displacement/on-the-move contact loss.
- **Reachback loss** is modeled by forcing the tasking delay to the
  (longer) direct-edge value regardless of which path would otherwise be
  preferred, since reachback is unavailable by definition when this
  condition is active.

These compose independently (e.g., `COMBINED_DEGRADED` in
`experiments/e11_mission_thread_success.py` applies interference derate
and contact denial and the longer tasking delay together), rather than
requiring a separate hand-coded case for every combination.
