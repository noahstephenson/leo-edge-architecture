# Project Roadmap

What's actually built, and how the pieces connect.

## The chain

Every piece of this repo traces the same path: operational need,
stakeholder value, requirement, function, allocation, experiment, trade
study, acquisition implication (`AGENTS.md`).

1. **Operational need**: `docs/OPERATIONAL_CONTEXT.md` and `docs/MISSION_THREADS.md` describe who needs what and why, grounded in real public Army programs without claiming to model them.
2. **Stakeholder values**: `docs/STAKEHOLDERS.md` states what each party values and where those values conflict.
3. **Requirements**: `docs/REQUIREMENTS.md` (with a full traceability matrix) and `docs/INTERFACES.md` pin down what the system must do and how its pieces talk to each other.
4. **Functions and allocation**: `docs/FUNCTIONAL_ARCHITECTURE.md` decomposes the pipeline; `docs/ALLOCATION_SPACE.md` is the central document placing the seven candidate architectures within the allocation decision space and stating what isn't covered.
5. **Model**: `src/leo_edge/` implements the architectures, product tiers, power, storage, link, and orbit models described above.
6. **Experiment**: `experiments/e00` through `e12` run that model under different conditions and write CSVs to `results/frozen/v4/`.
7. **Figures**: `figures/scripts/` turn those CSVs into the figures in `figures/`.
8. **Trade study**: `scripts/trade_study.py` turns experiment output into weighted multi-criteria scores; `docs/TRADE_STUDY.md` states the result.
9. **Acquisition implication**: `docs/ACQUISITION_IMPLICATIONS.md` ties specific recommendations back to specific trade-study evidence.

## Status

The model, the test suite (105 tests), experiments `e00` to `e12`, all
figures, and the trade study run from a fresh clone (`uv sync && uv run
pytest && make experiments && make figures && make trade_study`; add `make
access_sweep`, about an hour, for the constellation sweep). The headline is
in `docs/ACQUISITION_IMPLICATIONS.md`: access moves mission-thread success
most (about 3% at one satellite to about 31% at 24 satellites in 8 planes),
tiering is necessary, and architecture choice starts to matter once access
is high enough to test it.

## History

This repository first asked a narrower question (onboard or ground
processing). It then pivoted to allocation across the commercial/Army
ownership boundary, and later versions corrected the evaluation engine
several times. `docs/DECISION_LOG.md` is the record of each change and each
retraction; git history has the older documents and results.

## What's intentionally out of scope

Target recognition, tracking, weapon cueing, classified workflows, real
Army tactical collection plans, and detailed orbital-warfare scenarios.
This is a systems-architecture study using public/synthetic imagery and
generic ground-terminal geometry, and everything operational is notional
and unofficial. See `AGENTS.md`'s non-negotiable scope boundaries for the
full list.
