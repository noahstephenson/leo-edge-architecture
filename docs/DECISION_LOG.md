# Decision Log

Real architecture and project decisions, in the order they were made.

## ADR-001: Use Skyfield for contact-window generation

**Decision**: Use the Skyfield library instead of writing an orbital propagator from scratch.

**Rationale**: Orbit dynamics are not the research contribution here. The research question is about processing placement given contact windows, not about how those windows are computed.

**Alternatives considered**: Basilisk, Orekit, a custom SGP4 implementation.

**Consequence**: Lower-fidelity orbit modeling than a full mission-design tool, but much faster development, and Skyfield's SGP4 propagation is accurate enough to produce realistic access-window statistics.

## ADR-002: Model architectures as simple analytic classes, not a full discrete-event simulator

**Decision**: Each architecture (`A0_GROUND_ONLY` through `A5_CONTACT_AWARE`) is a class in `architectures.py` with a `run()` method that computes closed-form timing and energy from scene size, contact capacity, rate, and processing time.

**Rationale**: A full discrete-event simulator with per-byte scheduling would take much longer to build and validate than an undergrad-scope project should spend on infrastructure. The closed-form approach is checked against the analytical break-even model in `paper/hand_calc_break_even.md`.

**Consequence**: Some second-order effects (queueing delay across multiple scenes, partial-contact retransmission) are only modeled in the separate queue-stress and adaptive-policy experiments (`e06`, `e07`), not in the core architecture comparison.

## ADR-003: Remove A6_GROUND_CENTRIC_HYBRID and A7_ONBOARD_AI_TIER

**Decision**: Two extra architectures existed only in `architectures.py`, were never documented in the project's own architecture list, were never used by any experiment, and were not referenced by the dashboard or the operational/architecture-view docs. They were removed.

**Rationale**: `A0` through `A5` are the architectures consistent across every document in this repo. Adding two more, silently, in code only, is scope creep. `A7` in particular ("onboard AI model") sits close to the project's own stated non-goal of not building an AI benchmark.

**Consequence**: The architecture set is now consistent everywhere: code, docs, dashboard, and figures.

## ADR-004: Retire the internal planning roadmap document

**Decision**: `ARMY_LEO_DIRECT_TO_EDGE_AEROCONF_ROADMAP.md`, a 115 KB internal planning document, was mined for its real content (requirements, assumptions, decision records, experiment descriptions, research design) into the proper files under `docs/`, then deleted.

**Rationale**: The roadmap document was written as planning notes to self (checklists, "candidate" ideas, venue strategy) and had grown to overlap and duplicate the real `docs/` files, most of which were still empty placeholders. One coherent set of docs is easier for a reader to trust than two overlapping ones.

**Consequence**: `docs/*.md` are now the single source of truth for requirements, assumptions, decisions, and research design.

## ADR-005: Drop citation-dependent claims from the paper

**Decision**: `literature/` contained only empty citation scaffolding (no real sources were ever collected). Rather than publish placeholder citations or claim novelty against literature that was never actually reviewed, the paper's contribution claims are written to stand on this project's own results.

**Rationale**: A claim that depends on a literature comparison that was never done is worse than not making the claim.

**Consequence**: This repository does not claim to have done a literature review, and the paper's contribution claims are scoped accordingly, see `docs/NOVELTY_AUDIT.md`.

## ADR-006: Delete the CLI stub

**Decision**: `src/leo_edge/cli.py` contained five commands that only printed `"stub"`, wired into `pyproject.toml` as installable scripts. It was deleted, along with the `[project.scripts]` entries.

**Rationale**: Nothing in the repo used it. Experiments run directly as `python experiments/eXX_name.py`, and figures as `python figures/scripts/figXX_name.py`, both already documented in the `Makefile`.
