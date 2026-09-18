# Rework Plan: Commercial LEO / Army Edge Allocation Study

Status: in progress. This document is the working plan for the v2 rework and is
updated as work proceeds. It is not a permanent architecture doc; once the
rework lands, its content is superseded by `docs/ALLOCATION_SPACE.md`,
`docs/DECISION_LOG.md` (ADR-007), and the other Part 2-5 docs it produces.

## Why this rework

The v1 repo answers one question: given a single satellite and a single
ground terminal, should imagery be processed onboard or on the ground? That
is a processing-placement question with no notion of who owns anything.

The Army does not own LEO imaging satellites in this scenario. It buys
imagery as a service from commercial providers and owns the tactical edge
terminal. The real architectural question is which imagery functions
(tasking, collection, processing, prioritization, delivery) should sit in
the commercial space segment versus the Army-owned edge segment, and how
that changes with mission need, terminal class, and contested conditions.
The v1 processing-placement simulation becomes one evaluation engine inside
that larger question, not the whole story.

Everything below is notional and unofficial. Nothing here represents an
actual Army requirement, program, doctrine position, or acquisition
decision. Every Army/DoD-context claim is either cited to a real public
source or marked UNVERIFIED and treated as a parameter, never a fact.

## Ground rules (binding for every step below)

- No invented numbers, citations, doctrine, or program facts.
- Public, unclassified information only; all operational content notional.
- `results/frozen/v1/` is untouched. New results go in `results/frozen/v2/`.
- Every modeling/architecture decision gets an ADR in `docs/DECISION_LOG.md`.
- Small, separated commits with descriptive messages as each part lands.
- `paper/manuscript.md` is not edited in this pass.

## Part 1: Correctness fixes (do first)

Confirmed bugs, from direct code audit (`src/leo_edge/architectures.py`,
`simulation.py`):

1. **Uncapped bytes_transmitted.** `QuicklookFirst` (L102) and `RoiFirst`
   (L137) assign `bytes_transmitted = quicklook_bytes` / `roi_bytes`
   directly, never `min()`-ed against `contact_capacity_bytes`, unlike
   `GroundOnly`/`CompressedFull`/`ContactAware`. This is the exact and only
   cause of the 2.667 contact_utilization in the v1 audit (reproduced:
   RoiFirst at 1 Mbps, roi_bytes=100,000,000 vs capacity=37,500,000).
   Fix: cap at assignment in both classes.
2. **Three divergent contact_utilization implementations.** A clamped
   version exists in `metrics.py` but is dead code — never called by
   `architectures.py` or `simulation.py`. Both of those instead recompute it
   inline, unclamped. Fix: delete both inline recomputations, call
   `metrics.contact_utilization` from `_finalize_metrics`, delete the
   duplicate calc in `simulation.py::run_static_architecture`.
3. **tcp_s = tfup_s masks failed delivery.** In `QuicklookFirst`, `RoiFirst`,
   and effectively in `GroundOnly`/`CompressedFull` when truncated, an
   incomplete delivery gets the same timestamp as first-usable-product,
   scoring failure as instant success. Fix: carry undelivered bytes forward
   across subsequent SGP4 contact windows (using `orbit/access.py`'s window
   generator) so `tcp_s` means true time to full delivery. A product that
   never completes within the simulation horizon is censored: `tcp_s = NaN`,
   `completed = False`, never a number.
4. **Processing time never bounded by the contact window.** `tfup_s`/`tcp_s`
   are processing time plus transmit time with no clip to
   `contact_duration_s` — CompressedFull can report 320s inside a 300s
   contact. Fix: processing happens between capture and AOS (acquisition of
   signal) or is charged against contact time explicitly; transmit time is
   what's left of the window after processing, not stacked on top of it
   without bound.
5. **No product fidelity attribute.** No architecture output carries
   resolution or lossy/lossless information; `product_completeness` (byte
   fraction) is the only proxy. Fix: give every product tier a fidelity
   attribute in `products.py` (tier already exists; add resolution class and
   lossy/lossless flag) and never rank unlike products on TFUP/TCP alone
   without labeling the fidelity difference.
6. **Hardcoded, disconnected ratios.** 0.3 / 0.02 / 0.1 size ratios and
   Progressive's separately hardcoded byte sizes (20KB/512KB/10MB/50MB) are
   literals in `architectures.py`, inconsistent with each other, and never
   derived from `imagery/benchmark.py`'s `MEASURED_CONFIG` (which measures
   real Pillow timing on a laptop, not compression ratios or flight
   hardware). Fix: move ratios to `config/product_sizing.yaml`. In
   `docs/ASSUMPTIONS.md`, label every parameter MEASURED (script + hardware)
   or ASSUMED, and state plainly that laptop benchmarks are not flight- or
   terminal-representative.
7. **No semantic tests.** `architectures.py` and `simulation.py` have zero
   direct test coverage. Fix: add `tests/test_architectures.py` covering:
   censoring when delivered bytes < product size, no completion timestamp
   before processing ends, per-contact capacity never exceeded (regression
   test for bug 1), and `contact_utilization` never exceeds 1.0 by
   construction.
8. **Path leak.** `results/frozen/v1/audit_report.md` embeds the absolute
   local filesystem path. Fix: `scripts/audit_paper_numbers.py` emits paths
   relative to the repo root.

Also fix in passing, found during the audit but not in the original bug
list: `Architecture` dataclass in `architecture.py` and the class names in
`architectures.py` are wired to each other by convention only (no
`.name`/`.description` cross-check) — add that link so drift is caught;
`policies/adaptive.py` is currently unwired to the real architecture classes
and returns strings that match nothing (`"compressed_full"` vs
`CompressedFull`) — this is A5's actual policy logic and must be made to
select and run a real architecture instance, since the rework requires A5
evaluated as a first-class candidate.

Rerun everything into `results/frozen/v2/`. Write `docs/V1_VS_V2.md` stating
plainly which v1 conclusions survive the fix and which don't (expectation
going in: the quicklook/ROI-dominates-the-middle-of-the-grid result is
likely to shrink or move once truncated deliveries are censored instead of
scored as complete; this is a real hypothesis to test, not a predetermined
conclusion).

## Part 2: Army operational context

New docs, all headed with the same explicit disclaimer block used in
`LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` ("notional, non-operational, not an
official Army position"), strengthened with that exact sentence since no
file currently states it that explicitly:

- `docs/OPERATIONAL_CONTEXT.md` — notional problem statement: tactical unit
  needs timely AOI imagery, commercial LEO providers can collect it, Army
  owns edge terminals of varying capability. Cite real public sources on
  Army/DoD commercial-space-imagery use and tactical ground terminals where
  I can verify them; everything else marked UNVERIFIED and turned into a
  parameter.
- `docs/MISSION_THREADS.md` — 3-4 notional threads with genuinely different
  demands: time-sensitive cueing (fast/coarse), pre-movement route
  reconnaissance (full coverage), battle damage assessment (change
  detection against a prior image), persistent AOI monitoring. Each thread
  specifies: first-needed product, complete product, fidelity floor, latency
  tolerance (sourced or parameterized, never invented as fact).
- Terminal classes: vehicle-mounted (higher rate, real ground compute) and
  dismounted/manpack (low rate, minimal compute), modeled as a parameter set
  affecting where processing can even happen.
- Contested/DDIL parameterization: interference reducing effective rate,
  missed/shortened contacts (EMCON, displacement, on-the-move), loss of
  reachback. Core results must show allocation performance as conditions
  degrade, not just at nominal rates.
- Tasking path modeled explicitly: reachback through a rear-echelon tasking
  cell vs. direct edge tasking, each a parameterized delay with stated
  assumptions, added to total latency measured from user need (not capture).
- Operational metrics: time-to-first-actionable-product and
  time-to-complete-product measured from user need; primary metric is
  mission-thread success (required product arrived within tolerance at
  required fidelity), with Monte Carlo success rates and confidence
  intervals across conditions.

## Part 3: Systems architecture (core of the rework)

- `docs/STAKEHOLDERS.md` — tactical user, terminal operators, rear-echelon
  tasking cell, commercial provider, acquisition/program office; what each
  values and where values conflict.
- `docs/REQUIREMENTS.md` (rewritten) — numbered shall-statements traced to
  stakeholder needs and mission threads, each with a verification method,
  plus a traceability matrix: need to requirement to function to allocation
  to experiment to test.
- `docs/FUNCTIONAL_ARCHITECTURE.md` — task, collect, store, process (tiered
  P0-P4), prioritize, transmit, receive, exploit, disseminate.
- `docs/ALLOCATION_SPACE.md` — the central artifact. Decisions: which
  functions sit in the commercial segment vs. the Army edge segment vs.
  split; tasking path; product ordering/prioritization; static vs.
  contact-aware policy. The six v1 architectures (A0-A5, with A5 fixed and
  now a real evaluated candidate) become instances within this space.
  States plainly which regions of the space are left uncovered and why.
- `docs/TRADE_STUDY.md` plus a script — multi-criteria evaluation of
  candidate allocations against stakeholder-weighted criteria: mission-
  thread success, latency, fidelity, terminal SWaP burden, resilience under
  degradation, acquisition lock-in risk (qualitative, stated rubric). Uses
  v2 simulation output as evidence for the quantitative criteria, plus a
  weight-sensitivity analysis showing where rankings flip.
- Resilience analysis: which allocations degrade gracefully (still deliver
  a first actionable product) vs. catastrophically as conditions worsen.
- `docs/ACQUISITION_IMPLICATIONS.md` — the payoff document. What the Army
  should require of a commercial imagery service, what belongs in the
  terminal, what interfaces must be standardized, each tied to specific
  trade-study evidence.
- Architecture views: `docs/OV1_SPEC.md` (describes what the recommended
  concept graphic should show; no image generated in this pass), OV-2
  resource flows, OV-5b activities per mission thread, OV-6c event trace for
  one thread end to end, SV-1-equivalent system interfaces, SV-4
  function-to-system allocation. Retire views that no longer match the
  reframed question (the existing OV/4+1 docs get heavily rewritten, not
  patched).
- `model/` — SysML v2 textual notation for stakeholders/requirements/
  functions/allocations/traces, kept small and correct, only if it stays
  genuinely small; otherwise documented as a gap in ALLOCATION_SPACE.md
  rather than forced.
- `docs/MODEL_REFERENCE.md` — derivation-level physics/timing detail moved
  out of top-level docs so they stay architecture-focused.

## Part 4: Novelty (`docs/NOVELTY.md`, replaces `NOVELTY_AUDIT.md`)

1. Literature scan across: onboard vs. ground EO smallsat processing,
   satellite edge computing, progressive/tiered image delivery, commercial
   space imagery integration for military users, tactical ground terminals
   and direct-to-edge downlink, space-ground architecture trade studies.
   Only verified real papers/reports, full citation with DOI/URL. Anything
   uncertain is UNVERIFIED, not cited. Few real references beats many
   doubtful ones.
2. Honest summary of what prior work covers and where the actual gap is.
3. Ranked candidate claims, each tied to a repo artifact with a
   falsification condition, evaluated (not assumed) against the scan:
   allocation-across-ownership-boundary as the unit of analysis;
   mission-thread-driven evaluation showing preferred allocation shifts with
   terminal class and contested conditions; acquisition guidance derived
   traceably from the trade study; the open reproducible pipeline itself.
4. One-paragraph recommended contribution statement, scoped strictly to
   what the repo actually demonstrates.

## Part 5: Repo presentation

- README rewrite leading with the research question, the allocation
  decision space, the headline trade-study result, and acquisition
  implications, reporting v2 findings only, everything marked notional.
- `REPRODUCE_LOG.md` fresh end-to-end run entry.
- `app/dashboard.py` — add controls for mission thread, terminal class,
  degradation level, keep it working.
- `AGENTS.md` updated: the "Do not silently change this question" guardrail
  gets satisfied by ADR-007 in `docs/DECISION_LOG.md` recording the pivot,
  then the stated research question in AGENTS.md itself is updated to match.

## Sequencing

Part 1 is a hard prerequisite for everything else (trade study and results
would otherwise sit on a broken evaluation engine). Parts 2-4 can proceed
somewhat in parallel once Part 1's v2 results exist, but ALLOCATION_SPACE.md
(Part 3) is the pivot document everything else in Parts 2-5 needs to agree
with, so it gets drafted early and refined as Parts 2 and 4 surface new
constraints. Part 5 is last, once the actual v2 findings exist to report.

## Deliverables checklist

- [x] Part 1 fixes, each with a test; `uv run pytest` passes
- [x] `results/frozen/v2/`, regenerated figures, `V1_VS_V2.md`
- [ ] OPERATIONAL_CONTEXT, MISSION_THREADS, STAKEHOLDERS, REQUIREMENTS (with
      traceability), FUNCTIONAL_ARCHITECTURE, ALLOCATION_SPACE, TRADE_STUDY
      (with sensitivity), ACQUISITION_IMPLICATIONS, MODEL_REFERENCE,
      OV1_SPEC, updated views
- [ ] A5 and degraded conditions evaluated, with confidence intervals
- [ ] NOVELTY.md with verified citations only
- [ ] README and REPRODUCE_LOG updated
- [ ] Final summary: what changed, which v1 claims died, headline
      allocation result, open questions, all UNVERIFIED items
