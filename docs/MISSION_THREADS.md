# Mission Threads

All notional. Latency tolerances and fidelity floors below are modeling
parameters chosen to be operationally plausible and distinct from each
other, not sourced Army requirements; each is marked ASSUMED. Where a
number could plausibly be sourced (e.g., "time-sensitive" meaning minutes
not hours), it still isn't backed by a specific document, so it stays
ASSUMED rather than being dressed up with a citation it doesn't have.

Four notional threads, chosen to have genuinely different demands on the
delivery pipeline, so the allocation question ("what goes where") has real
tradeoffs to show instead of one thread trivially dominating every metric.

## The four threads at a glance

| Thread | Needs first | Tolerance | Measured from |
|---|---|---|---|
| MT-1 cueing | P2 quicklook | 120 s | the request |
| MT-2 route recon | P3 ROI | 900 s | the request |
| MT-3 damage assessment | a P3-sized change product | 600 s with a prior reference, else 900 s | the request |
| MT-4 persistent monitoring | P1 thumbnail | 300 s per pass; fails on 2 misses in a row | each collection pass |

The values are the code's source of truth (`src/leo_edge/mission_threads.py`),
checked against the tables below by `tests/test_mission_thread_consistency.py`.

## MT-1: Time-sensitive cueing

A unit needs to know quickly whether something of interest is present in an
area, to decide whether to commit further collection or maneuver assets.
Speed matters more than resolution; a coarse, fast answer beats a slow,
perfect one.

| Field | Value | Label |
|---|---|---|
| First-needed product | Coarse detection product (quicklook-class, P2) | ASSUMED |
| Complete product | Not required for this thread; the coarse product is the terminal product | ASSUMED |
| Fidelity floor | Coarse resolution acceptable, lossy compression acceptable | ASSUMED |
| Latency tolerance (first product) | 2 minutes from user request | ASSUMED |
| Priority if contact-constrained | Highest: sacrifice everything else in the window to deliver this first | ASSUMED |

## MT-2: Pre-movement route reconnaissance

A unit planning a route or objective needs full-resolution coverage of the
area before committing to move through it. A coarse product isn't enough:
route hazards (obstacles, damage, terrain features) need to be visible at
native resolution across the whole area of interest, not just a cued spot.

| Field | Value | Label |
|---|---|---|
| First-needed product | ROI crop at full resolution (P3), covering the planned route corridor | ASSUMED |
| Complete product | Full-scene product (P4) covering the full area of interest | ASSUMED |
| Fidelity floor | Full resolution required for the route corridor; lossy compression acceptable elsewhere in the scene | ASSUMED |
| Latency tolerance (first product) | 15 minutes | ASSUMED |
| Latency tolerance (complete product) | 60 minutes, tied to planning-cycle timing, not real-time maneuver | ASSUMED |

## MT-3: Battle damage assessment (change detection)

A unit needs to know what changed at a location since a prior collection.
This thread is different in kind from the other three: its "first useful
product" isn't a new image at all, it's a difference product between the
new collection and a stored prior one, so it depends on having a usable
prior reference already on hand (at the edge terminal or reachable via
tasking) as well as the new collection.

| Field | Value | Label |
|---|---|---|
| First-needed product | Change/difference product between new coarse collection and stored prior reference | ASSUMED |
| Complete product | Full-resolution change product plus the full new-collection scene | ASSUMED |
| Fidelity floor | Full resolution required to assess damage confidently; a coarse change product is a screening step, not the final answer | ASSUMED |
| Latency tolerance (first product) | 10 minutes | ASSUMED |
| Latency tolerance (complete product) | 45 minutes | ASSUMED |
| Dependency | Requires a prior reference image already available at or reachable from the edge terminal; if none exists, this thread degrades to MT-2's behavior (no change product possible, just report the new full scene) | ASSUMED |

## MT-4: Persistent monitoring of an area of interest

A unit wants standing awareness of an area over time (a route, a
checkpoint, a border segment), not a single answer to a single question.
This thread is defined by repeat collections over a mission duration
rather than a single request/response cycle, and its success criterion is
about the delivered cadence, not any one delivery's speed.

| Field | Value | Label |
|---|---|---|
| First-needed product | Coarse product (P1/P2) per collection pass | ASSUMED |
| Complete product | Full-resolution product per collection pass, when contact capacity allows | ASSUMED |
| Fidelity floor | Coarse acceptable per-pass; full resolution valuable but not required every pass | ASSUMED |
| Latency tolerance (first product, per pass) | 5 minutes from each collection | ASSUMED |
| Cadence requirement | At least one coarse product delivered per contact opportunity over the mission duration; missing more than one consecutive opportunity is a thread failure, not just a slow delivery | ASSUMED |

## Terminal classes

Two terminal classes, chosen because they represent genuinely different
points in the SWaP (size, weight, and power) tradeoff, which is exactly
what determines whether processing can happen at the edge at all. These
are notional parameter sets for this simulation, not a claim about any
real fielded terminal's specifications (RGT, NGTT, or otherwise; see
`docs/OPERATIONAL_CONTEXT.md`).

| Field | Vehicle-mounted | Dismounted / manpack |
|---|---|---|
| Downlink rate | Higher: modeled range 10-100 Mbps | Lower: modeled range 1-10 Mbps |
| Edge compute | Meaningful: can run real image processing (crop, compress, tier generation) locally | Minimal: limited to lightweight operations (metadata parsing, thumbnail display), not full reprocessing | 
| Power budget for processing | Not a binding constraint in the model (vehicle power available) | Binding constraint: sustained processing draws down a limited battery budget | 
| Label | ASSUMED | ASSUMED |

Terminal class changes where processing can happen, not just how fast: a
dismounted terminal with minimal compute cannot locally re-derive a full
product from a partial one even if it had the bytes, so for that class,
more of the tiering/processing burden has to be pushed to the commercial
space segment or to a rear-echelon processing node, not left for the
terminal to do.

## Contested and DDIL conditions

Three independent degradation parameters, applied to the underlying
contact/link model (`src/leo_edge/orbit/access.py` and
`src/leo_edge/simulation.py`) rather than to any single architecture, so
every candidate allocation is evaluated under the same degraded conditions:

| Parameter | What it represents | Model effect | Label |
|---|---|---|---|
| Interference derate | Jamming or interference reducing effective downlink rate during a contact | Effective `rate_bps` scaled down by a configurable factor (e.g., 0.5x, 0.25x) for affected windows | ASSUMED |
| Contact denial | EMCON, terminal displacement, or being on the move causing a contact window to be missed or shortened | A fraction of scheduled contact windows are dropped entirely or truncated in duration before being passed to the delivery simulator | ASSUMED |
| Reachback loss | Loss of connectivity from the edge terminal back to a rear-echelon tasking or processing node | Disables the reachback tasking path (see below), forcing direct edge tasking whether or not that's the preferred path under nominal conditions | ASSUMED |

These are not independent from `docs/ASSUMPTIONS.md`'s existing parameters;
they compose with them (e.g., interference derate multiplies the nominal
`rate_bps`, it doesn't replace the ASM-LINK-001 constant-rate-per-window
simplification).

## Tasking path

Total latency in this model starts at the point the user expresses a need,
not at image capture, which is why the tasking path itself is modeled as
an architectural choice with its own latency, not assumed to be
instantaneous or ignored:

- **Reachback tasking**: the request goes from the edge user to a
  rear-echelon tasking cell, which schedules the collection with the
  commercial provider. Modeled as an added fixed delay before collection
  can occur, representing coordination and scheduling overhead.
- **Direct edge tasking**: the edge terminal tasks the commercial provider
  directly, with a shorter added delay, representing less coordination
  overhead but also less deconfliction/prioritization against other
  requests in the system (a tradeoff this repository does not attempt to
  quantify beyond the latency parameter itself).

| Parameter | Reachback tasking | Direct edge tasking | Label |
|---|---|---|---|
| Added tasking delay | Longer, modeled range 5-20 minutes | Shorter, modeled range 1-5 minutes | ASSUMED |
| Available when reachback is lost | No (this path requires reachback) | Yes | By construction |

## Operational metrics

- **Time to first actionable product**: elapsed time from user need
  (request submission) to delivery of the thread's first-needed product,
  including the tasking delay above. This replaces `tfup_s`'s old
  from-capture framing; see `docs/MODEL_REFERENCE.md` for how the two
  relate.
- **Time to complete product**: elapsed time from user need to delivery of
  the thread's complete product, when the thread has one (MT-1 and MT-4 do
  not require a complete product to succeed).
- **Mission-thread success** (primary metric): whether the thread's
  first-needed product arrived within its latency tolerance at or above
  its fidelity floor. This is a boolean per mission execution, aggregated
  across Monte Carlo runs into a success rate with a confidence interval
  (see `docs/TRADE_STUDY.md`), not averaged as if latency alone were the
  outcome.
