# Allocation Space

This is the central document of the rework. It defines the decisions that
make up "how should imagery functions be allocated between the commercial
LEO space segment and the Army-owned edge segment," places the six
architectures this repository actually evaluates (A0-A5) as points within
that space, and states plainly which regions of the space are not covered
and why.

## The decision axes

An allocation is a choice along four axes. Two segments own the functions
from `docs/FUNCTIONAL_ARCHITECTURE.md`: the **commercial space segment**
(the satellite, owned and operated by the provider) and the **Army edge
segment** (the tactical terminal). A third, optional segment, the
**rear-echelon node**, participates only in the tasking axis.

1. **Processing allocation**: how much of the Process function (P0-P4
   tiering) happens onboard the satellite (commercial segment) versus at
   the edge terminal (Army segment) versus not at all (raw only). The
   satellite can only send what it has already produced or has capacity to
   transmit raw; the edge terminal can only re-derive further tiers from
   what it actually received, and only if its compute class allows it
   (`docs/MISSION_THREADS.md` terminal classes).
2. **Tasking path**: reachback through a rear-echelon tasking cell, or
   direct edge tasking of the commercial provider
   (`docs/MISSION_THREADS.md`).
3. **Product ordering and prioritization**: fixed priority order
   (metadata, thumbnail, quicklook, ROI, full, in that order regardless of
   mission thread) versus mission-thread-aware prioritization (e.g., MT-2
   prioritizes ROI over quicklook, since a coarse product doesn't serve a
   route-reconnaissance thread's fidelity floor).
4. **Policy adaptivity**: static (the same fixed choice every contact,
   regardless of conditions) versus contact-aware (the choice changes
   based on predicted contact margin, `docs/MISSION_THREADS.md`'s
   contested-condition parameters).

## The six architectures as points in this space

| Architecture | Processing allocation | Tasking path | Product ordering | Policy adaptivity |
|---|---|---|---|---|
| A0_GROUND_ONLY | None onboard; raw only | Not modeled (fixed) | N/A, single product | Static |
| A1_COMPRESSED_FULL | Full onboard compression, one atomic product | Not modeled (fixed) | N/A, single product | Static |
| A2_QUICKLOOK_FIRST | Onboard quicklook, then full if capacity allows | Not modeled (fixed) | Fixed: quicklook always first | Static |
| A3_ROI_FIRST | Onboard ROI crop, then full if capacity allows | Not modeled (fixed) | Fixed: ROI always first | Static |
| A4_PROGRESSIVE | Onboard, all five tiers in fixed order as capacity allows | Not modeled (fixed) | Fixed: metadata, thumbnail, quicklook, ROI, full | Static |
| A5_CONTACT_AWARE | Onboard compression, chosen only if margin allows; raw fallback otherwise | Not modeled (fixed) | N/A, single product per choice | Adaptive (contact-margin rule) |

Every one of A0-A5 fixes the tasking-path axis (none of them model tasking
latency at all, prior to this rework) and fixes the product-ordering axis
to a scene-agnostic priority order (none of them reorder based on which
mission thread is running). That is exactly what the next section states
as the space's biggest uncovered region.

## Uncovered regions

- **Mission-thread-aware prioritization** is not implemented by any of
  A0-A5. A3_ROI_FIRST always sends the ROI crop first regardless of
  whether the active thread is MT-1 (which doesn't want an ROI crop at
  all, it wants a coarse detection product) or MT-2 (which does).
  Evaluating this axis requires a seventh-ish "policy," not a new fixed
  architecture: a thread-aware prioritizer that picks among A2/A3/A4's
  underlying tier logic based on which mission thread is active. This is
  the most direct next experiment this repository doesn't yet run.
- **Tasking-path latency** is not modeled by any of A0-A5's `run()` methods
  today; `docs/MISSION_THREADS.md` defines the parameter, but no
  experiment yet adds it to total latency. The mission-thread-success
  experiments this rework's Part 2/3 work is meant to produce are where
  that gets wired in; as of this document, it's a defined-but-unused
  parameter, not yet evidence.
- **Split processing** (partial tiering onboard, remaining tiering at the
  edge terminal) is not modeled at all. Every architecture here either does
  all its processing onboard or none; there's no architecture where the
  satellite sends a partially-processed intermediate product and the edge
  terminal finishes deriving further tiers locally, which is exactly the
  kind of allocation a vehicle-mounted terminal's "meaningful edge compute"
  (`docs/MISSION_THREADS.md`) would make possible and a dismounted
  terminal's minimal compute would not.
- **Terminal-class-dependent allocation** is defined as a parameter
  (`docs/MISSION_THREADS.md`) but no architecture in `architectures.py`
  currently branches on terminal class; today's architectures behave
  identically regardless of which terminal receives their output. A
  terminal-aware version of A5's rule (fall back differently for a
  dismounted vs. vehicle-mounted terminal) is a natural adaptive-policy
  extension this repository doesn't yet have.
- **Change-detection-specific processing** (MT-3's need for a stored prior
  reference and a difference product) has no corresponding function
  allocation at all; `docs/FUNCTIONAL_ARCHITECTURE.md`'s Store-to-Exploit
  path for a prior reference is defined conceptually but not implemented in
  `src/leo_edge/`.

## Why these gaps are stated, not filled

Filling all of these would turn this into a much larger simulation project
than an undergraduate-scope study should attempt (`docs/RESEARCH_DESIGN.md`).
The trade study (`docs/TRADE_STUDY.md`) evaluates the six architectures that
exist, honestly, against the mission threads that exist, and states these
gaps as exactly that: gaps, not findings the data can speak to. A reader
should not conclude from the trade study's results that mission-thread-aware
prioritization or split processing would perform worse than what's here;
that comparison was never run.
