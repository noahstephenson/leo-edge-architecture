# v1 vs v2: what changed and which conclusions survive

`results/frozen/v1/` held the original, buggy results; it has since been
deleted from the working tree (available in git history if needed) once
this document and the fixes below were verified against it. This document
says plainly what was wrong with it, what changed in the code
(`docs/DECISION_LOG.md` ADR-008 has the full list), and which v1 conclusions
hold up once the fixes are applied. `results/frozen/v2/` is regenerated from
the fixed code with the same experiment parameters used in v1 unless noted.

## The core bug, in one number

The v1 audit report flagged `contact_utilization` reaching 2.667 (should
never exceed 1.0) as a warning, not a failure. The root cause: `RoiFirst`
and `QuicklookFirst` assigned `bytes_transmitted` directly from the product
size without capping it to what the contact window could actually hold. At
1 Mbps, a 300 s contact holds 37.5 MB; `RoiFirst`'s ROI product is 100 MB.
v1 reported that 100 MB as "transmitted" anyway, both inflating
`contact_utilization` to 2.667 and reporting `tcp_s = tfup_s = 820s` as a
successful delivery of a product that never arrived.

The v2 audit (`results/frozen/v2/audit_report.md`) shows
`contact_utilization` genuinely bounded in [0, 1] across all 54,012 rows,
and the invariant check now fails (not warns) if that ever regresses.

## What "completed" changes about the headline e03 sweep

The clearest before/after is the core rate sweep
(`results/frozen/v{1,2}/e03_results.csv`, 1 GB scene, 300 s contact):

| Architecture | Rate | v1 tcp_s (reported as "done") | v2 tcp_s | v2 completed |
|---|---|---|---|---|
| GroundOnly | 1-25 Mbps | 300s (all four rates) | NaN | False |
| CompressedFull | 1-5 Mbps | 320s, 320s | NaN | False |
| QuicklookFirst | 1-25 Mbps | 162s, 34s, 18s, 8.4s | NaN | False |
| RoiFirst | 1-25 Mbps | 820s, 180s, 100s, 52s | NaN | False |
| Progressive | 1-25 Mbps | 108s, 122s, 71s, 40s | NaN | False |

At 1 GB scene size and a single 300 s contact window, **nothing completes a
full delivery below 50 Mbps**, for any architecture. Every one of those v1
numbers was a truncated delivery reported as a finished one. This is not a
small correction: of the 30 architecture x rate combinations in e03, only
12 (40%) actually complete full delivery within one window; the other 18
were previously scored as complete and now are correctly censored.

QuicklookFirst still achieves `tfup_s` (the quicklook itself) at every
rate tested, since the quicklook is small enough to fit even at 1 Mbps.
That part of the v1 story is real: QuicklookFirst is genuinely fast to a
first usable product. What was never real is the claim that it, or any
other architecture, was also fast to a *complete* product at low rates.

## Which v1 conclusions die

- **"Quicklook-first dominates the middle of the regime map" (the
  manuscript's headline claim, based on `fig04.png`/v1 `tcp_s`)**: does not
  survive as stated. The v1 regime map compared `tcp_s` values that were
  frequently fabricated completions. The v2 regime map
  (`figures/fig04.png`, built from `results/frozen/v2/fig04_data.csv`, a
  6x6 rate/duration grid x 5 architectures = 180 individual evaluations)
  shows 105 of those 180 (58%) did not complete, and 13 of the 36 grid
  cells (36%) have zero architectures completing at all, plotted as "no
  completion" rather than picking a winner. A2 (QuicklookFirst)'s advantage
  in TFUP still holds; its advantage in TCP does not, because in the regime
  where it previously "won," it usually wasn't actually finishing.
- **"Progressive's TFUP is invariant to contact-capacity noise" (v1 e08)**:
  the TFUP claim itself is unaffected (Progressive's first tier is tiny and
  always fits), but the companion claim that Progressive reliably
  completes under noise does not hold: at the e08 scenario's parameters (1
  GB scene, 10 Mbps, ~300 s ± 10%), Progressive's full-delivery completion
  rate is 0% across all 100 Monte Carlo runs, not previously visible
  because tcp_s was never censored.
- **The v1 Pareto frontier (old `fig05.png`, formerly `fig12`)**: was
  computed over all 30 e03 rows including the 18 that didn't complete. The
  v2 version (`figures/fig05.png`) drops those 18 rows explicitly (printed
  at generation time) and plots the frontier over the 12 real completions
  only. The shape of the frontier changes since 60% of its input points
  were never real.

## Which v1 conclusions survive

- **QuicklookFirst reaches a usable first product fast, at every rate
  tested.** This was true in v1 and remains true in v2; `tfup_s` for
  QuicklookFirst was never subject to the capping bug in the low/mid-rate
  regime (its issue was always about the *second* tier, the full scene).
- **CompressedFull wins at high rates (50-100 Mbps).** These rows completed
  in both v1 and v2 with identical numbers, since the capacity was never
  the constraint there.
- **The analytical break-even model itself
  (`paper/hand_calc_break_even.md`)** is unaffected; it was never wired
  through the buggy simulation code.
- **The orbit/contact-window generation (`e01`, `fig06`)** is unaffected;
  `orbit/access.py` was not part of the bug.
- **`e09` (constellation handoff) and `e10` (storage wear)** don't call
  `architectures.py` at all and are unaffected by the fix; they were
  re-run into `results/frozen/v2/` only so the versioned directory is
  self-consistent, not because their numbers changed.

## New in v2

- **Multi-contact delivery** (`leo_edge.simulation.simulate_multi_contact`):
  carries undelivered bytes forward across a real sequence of SGP4 contact
  windows instead of evaluating a single window in isolation. A single-pass
  evaluation was answering "does this complete in one contact," which is
  now honestly censored when the answer is no; the multi-contact simulator
  answers the operationally real question, "how long until it actually
  arrives, across however many passes it takes." This is the evaluation
  engine Part 2/3's mission-thread-success experiments use.
- **Fidelity labeling** (`fidelity_lossy`, `fidelity_resolution_class` on
  every architecture output): no result compares two architectures' timing
  without also stating what was actually delivered.
- **A5 (ContactAware/adaptive) is now a real, runnable candidate** in
  `AdaptivePolicy.choose()`, which returns an actual architecture class
  instead of a string label that had no corresponding implementation for
  two of its three cases.

## What this means going forward

The regime map is not "quicklook-first wins the middle, compressed-full
wins the high end" (the v1/manuscript framing). It's closer to: **at this
scene size and this single-window model, most architectures cannot
complete a full delivery below roughly 50 Mbps at all, and the real
question is which architecture gets the most useful product to the user
given that constraint** — which is exactly the mission-thread-success
framing Part 2 of the rework introduces (first-actionable-product and
mission-thread success, not an assumed-complete TCP). `paper/manuscript.md`
is not edited in this pass; its v1 claims should be treated as superseded
by this document, not as still-true background.
