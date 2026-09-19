# Project Roadmap

What's actually built, and how the pieces connect.

## The chain

Every piece of this repo traces the same path: operational need,
stakeholder value, requirement, function, allocation, experiment, trade
study, acquisition implication (`AGENTS.md`).

1. **Operational need**: `docs/OPERATIONAL_CONTEXT.md` and `docs/MISSION_THREADS.md` describe who needs what and why, grounded in real public Army programs without claiming to model them.
2. **Stakeholder values**: `docs/STAKEHOLDERS.md` states what each party values and where those values conflict.
3. **Requirements**: `docs/REQUIREMENTS.md` (with a full traceability matrix) and `docs/INTERFACES.md` pin down what the system must do and how its pieces talk to each other.
4. **Functions and allocation**: `docs/FUNCTIONAL_ARCHITECTURE.md` decomposes the pipeline; `docs/ALLOCATION_SPACE.md` is the central document placing the six candidate architectures within the allocation decision space and stating what isn't covered.
5. **Model**: `src/leo_edge/` implements the architectures, product tiers, power, storage, link, and orbit models described above.
6. **Experiment**: `experiments/e00` through `e11` run that model under different conditions and write CSVs to `results/frozen/v2/`.
7. **Figures**: `figures/scripts/` turn those CSVs into the figures in `figures/`.
8. **Trade study**: `scripts/trade_study.py` turns experiment output into weighted multi-criteria scores; `docs/TRADE_STUDY.md` states the result.
9. **Acquisition implication**: `docs/ACQUISITION_IMPLICATIONS.md` ties specific recommendations back to specific trade-study evidence.

## Status

The model, the test suite (74 tests), all 12 core experiments, the
mission-thread Monte Carlo (`e11`), all figures, and the trade study run
clean from a fresh clone (`uv sync && uv run pytest && make experiments &&
make figures && make trade_study`). The headline result is in
`docs/TRADE_STUDY.md`: three of six architectures score 0% mission-thread
success structurally; contact geometry, not architecture choice, is the
binding constraint for the rest.

## History

This repository originally asked a narrower question (should a satellite
process imagery onboard or downlink raw for ground processing). That
version's results, paper draft, and DoDAF operational-viewpoint document
have been deleted from the working tree (`docs/DECISION_LOG.md` ADR-007,
ADR-011); git history has them if needed. `docs/V1_VS_V2.md` documents
what changed and why, including a real correctness bug the original
version had.

## What's intentionally out of scope

Target recognition, tracking, weapon cueing, classified workflows, real
Army tactical collection plans, and detailed orbital-warfare scenarios.
This is a systems-architecture study using public/synthetic imagery and
generic ground-terminal geometry, and everything operational is notional
and unofficial. See `AGENTS.md`'s non-negotiable scope boundaries for the
full list.
