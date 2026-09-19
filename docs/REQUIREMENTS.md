# Requirements

Numbered, verifiable shall-statements, each traced to a stakeholder need
(`docs/STAKEHOLDERS.md`) and a mission thread (`docs/MISSION_THREADS.md`)
where applicable, with a verification method. All notional; none of these
are sourced Army requirements. Requirement IDs from the v1 pass (MR/SR/GR/
SIM) are retired; the mapping from old to new is in
`docs/DECISION_LOG.md` ADR-007's consequence.

## Allocation and tasking

- **REQ-ALLOC-001**: The system shall support delivering at least one
  reduced-fidelity product tier before the complete product, when contact
  capacity does not allow immediate delivery of the complete product.
  Verification: unit test (`tests/test_architectures.py`), demonstrated by
  every tiered architecture (A2-A4).
- **REQ-ALLOC-002**: The system shall support both a reachback tasking path
  (through a rear-echelon tasking cell) and a direct edge tasking path, and
  shall model the added latency of each explicitly rather than treating
  tasking as instantaneous.
  Verification: `docs/MISSION_THREADS.md`'s tasking-path parameters, applied
  in the mission-thread-success experiments (Part 3 trade study).
- **REQ-ALLOC-003**: The system shall evaluate at least one adaptive
  allocation policy (A5) that selects a delivery approach based on
  contact-capacity margin, in addition to the fixed static allocations
  (A0-A4).
  Verification: `tests/test_architectures.py::test_architecture_registry_matches_arch_ids`,
  `experiments/e07_adaptive_policy.py`.
- **REQ-ALLOC-004**: The system shall evaluate at least one
  mission-thread-aware prioritization policy (A6) that reorders product
  delivery around the active mission thread's specific needed tier,
  instead of a single fixed priority order for every thread.
  Verification: `tests/test_architectures.py::test_thread_aware_priority_reorders_around_priority_tier`,
  `experiments/e11_mission_thread_success.py`.

## Mission-thread success

- **REQ-THREAD-001**: For MT-1 (time-sensitive cueing), the system shall
  report whether the coarse detection product was delivered within its
  latency tolerance, as a boolean success/failure, not just a raw time.
  Verification: mission-thread experiment (Part 3), traced to
  `docs/MISSION_THREADS.md` MT-1.
- **REQ-THREAD-002**: For MT-2 (route reconnaissance), the system shall
  distinguish delivery of the ROI-first product from delivery of the
  complete scene, and report both against their separate latency
  tolerances.
  Verification: mission-thread experiment, traced to MT-2.
- **REQ-THREAD-003**: For MT-3 (battle damage assessment), the system shall
  report thread failure, not a fabricated result, when no prior reference
  image is available for change detection.
  Verification: mission-thread experiment, traced to MT-3's dependency row.
- **REQ-THREAD-004**: For MT-4 (persistent monitoring), the system shall
  track delivery cadence across a mission duration (multiple contact
  opportunities), not just a single request/response latency.
  Verification: mission-thread experiment, traced to MT-4.

## Correctness (carried forward from Part 1, restated as requirements)

- **REQ-CORRECT-001**: The system shall never report `bytes_transmitted`
  exceeding the contact window's byte capacity.
  Verification: `tests/test_architectures.py::test_never_exceeds_contact_capacity`.
- **REQ-CORRECT-002**: The system shall never report `contact_utilization`
  outside [0, 1].
  Verification: `tests/test_architectures.py::test_contact_utilization_never_exceeds_one`,
  `scripts/audit_paper_numbers.py` (fails the audit if violated).
- **REQ-CORRECT-003**: The system shall censor (report as not completed,
  not as a fabricated number) any product that does not finish delivering
  within the contact windows evaluated.
  Verification: `tests/test_architectures.py::test_censored_when_capacity_too_small`,
  `tests/test_simulation.py::test_multi_contact_censors_when_horizon_runs_out`.
- **REQ-CORRECT-004**: Every delivered product shall report a fidelity
  label (lossy/lossless, resolution class); no result shall compare two
  architectures' timing without also stating what was delivered.
  Verification: `tests/test_architectures.py::test_fidelity_always_reported`.

## Terminal class

- **REQ-TERM-001**: The system shall model at least two terminal classes
  with different downlink rate ranges and edge-compute capability, and
  shall show at least one case where the preferred allocation differs
  between them.
  Verification: `docs/MISSION_THREADS.md` terminal-class table; trade study
  weight-sensitivity analysis (`docs/TRADE_STUDY.md`).

## Contested conditions

- **REQ-DDIL-001**: The system shall support evaluating any candidate
  allocation under interference derate, contact denial, and reachback
  loss, individually and in combination.
  Verification: mission-thread experiment with degradation parameters
  applied, traced to `docs/MISSION_THREADS.md`'s DDIL table.
- **REQ-DDIL-002**: The system shall report mission-thread success rates
  with confidence intervals across degraded-condition Monte Carlo runs, not
  single-run point estimates.
  Verification: reuses the bootstrap-CI approach in
  `scripts/compute_confidence_intervals.py`, applied to mission-thread
  outcomes.

## Traceability matrix

| Need (stakeholder) | Requirement | Function | Candidate allocation(s) | Experiment | Test |
|---|---|---|---|---|---|
| Tactical user: fast first product (MT-1) | REQ-THREAD-001, REQ-ALLOC-001 | process (tiered), transmit | A2, A4, A5, A6 | mission-thread experiment | `test_architectures.py` |
| Tactical user: full-fidelity route coverage (MT-2) | REQ-THREAD-002, REQ-CORRECT-004 | process (ROI), transmit | A3, A4, A6 | mission-thread experiment | `test_fidelity_always_reported` |
| Tactical user: honest failure when no reference exists (MT-3) | REQ-THREAD-003 | store (reference retention), process (change detection) | not yet allocated, see `docs/ALLOCATION_SPACE.md` gaps | mission-thread experiment | n/a (new) |
| Tactical user: sustained cadence (MT-4) | REQ-THREAD-004 | task, collect, transmit | A0-A6 evaluated repeatedly | mission-thread experiment | n/a (new) |
| Terminal operator: SWaP-appropriate processing (dismounted vs. vehicle) | REQ-TERM-001 | process | allocation depends on terminal class | trade study | n/a (analysis) |
| Rear-echelon tasking cell: deconfliction vs. speed | REQ-ALLOC-002 | task | reachback vs. direct edge | mission-thread experiment | n/a (new) |
| Acquisition: evidence-based, not fabricated results | REQ-CORRECT-001 through REQ-CORRECT-004 | all | all | Part 1 fixes | `tests/test_architectures.py`, `tests/test_simulation.py` |
| Provider/acquisition: adaptive policy as real candidate | REQ-ALLOC-003 | task, process, transmit | A5 | `experiments/e07_adaptive_policy.py` | `test_architecture_registry_matches_arch_ids` |
| Tactical user: mission-thread-aware prioritization beats a fixed order | REQ-ALLOC-004 | process (tiered, reordered), prioritize | A6 | `experiments/e11_mission_thread_success.py`, `scripts/trade_study.py` | `test_thread_aware_priority_reorders_around_priority_tier`, `test_thread_aware_priority_skips_ahead_to_smaller_fitting_tier` |
