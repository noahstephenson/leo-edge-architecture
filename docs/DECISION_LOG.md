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

## ADR-007: Pivot the research question to allocation across the commercial/Army ownership boundary

**Decision**: The research question changes from "should a satellite process imagery onboard or on the ground" to "how should imagery functions be allocated between a commercial LEO space segment acquired as a service and an Army-owned tactical edge segment, and how does the preferred allocation shift with mission need, terminal class, and contested conditions." The v1 processing-placement simulation becomes one evaluation engine inside this larger allocation question, not the whole story. See `docs/REWORK_PLAN.md` for the full scope of the rework this triggers.

**Rationale**: AGENTS.md's own governance rule required this: "Do not silently change this question. If results suggest a different question is stronger, document the proposed pivot here before changing the design." The Army does not own LEO imaging satellites in the scenario this repo studies; it buys imagery as a service and owns the tactical edge terminal. A processing-placement question with no owner on either side was never asking the question that actually matters operationally.

**Consequence**: Every document that restated the old research question (README, AGENTS.md, both architecture-view docs, the full DoDAF operational-viewpoint package, most of `docs/*.md`, the dashboard) needs rewriting, not patching. `paper/manuscript.md` is explicitly out of scope for this pivot and is not touched. All new operational content is notional and unofficial; this repository does not represent an Army position, requirement, or acquisition decision.

## ADR-008: Fix architecture correctness bugs before building on top of them

**Decision**: Before any allocation-space work began, eight confirmed correctness bugs in `src/leo_edge/architectures.py` and `simulation.py` were fixed: uncapped `bytes_transmitted` in `QuicklookFirst`/`RoiFirst` (the exact cause of `contact_utilization` reaching 2.667 in the v1 audit), three divergent and mostly-unclamped `contact_utilization` implementations collapsed into one clamped one, `tcp_s` no longer silently set equal to `tfup_s` when a product didn't fully deliver (now censored: `tcp_s = NaN`, `completed = False`), a new multi-contact delivery simulator (`simulate_multi_contact`) that carries undelivered bytes across real SGP4 contact windows instead of evaluating only a single window, a `fidelity_lossy`/`fidelity_resolution_class` field added to every architecture's output, sizing ratios moved to `config/product_sizing.yaml`, `AdaptivePolicy` (A5) rewired to return and run a real architecture class instead of a string label that was approximated with `Progressive` for two different cases, and `scripts/audit_paper_numbers.py` fixed to emit relative paths and to treat `contact_utilization > 1` as a failure instead of a tolerated warning. See `docs/V1_VS_V2.md` for what this changes about the actual results.

**Rationale**: A trade study and acquisition guidance built on top of an evaluation engine that scores failed deliveries as instant successes would be worthless regardless of how good the surrounding architecture work is.

**Consequence**: `results/frozen/v1/` is left untouched as the historical record. All new results are in `results/frozen/v2/`, generated with the fixed code. Several v1 conclusions do not survive the fix; see `docs/V1_VS_V2.md`.
