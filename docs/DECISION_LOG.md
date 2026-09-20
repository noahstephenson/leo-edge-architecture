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

**Decision**: The research question changes from "should a satellite process imagery onboard or on the ground" to "how should imagery functions be allocated between a commercial LEO space segment acquired as a service and an Army-owned tactical edge segment, and how does the preferred allocation shift with mission need, terminal class, and contested conditions." The v1 processing-placement simulation becomes one evaluation engine inside this larger allocation question, not the whole story. The rework plan was deleted later; git history has it.

**Rationale**: AGENTS.md's own governance rule required this: "Do not silently change this question. If results suggest a different question is stronger, document the proposed pivot here before changing the design." The Army does not own LEO imaging satellites in the scenario this repo studies; it buys imagery as a service and owns the tactical edge terminal. A processing-placement question with no owner on either side was never asking the question that actually matters operationally.

**Consequence**: Every document that restated the old research question (README, AGENTS.md, both architecture-view docs, the full DoDAF operational-viewpoint package, most of `docs/*.md`, the dashboard) needs rewriting, not patching. `paper/manuscript.md` is explicitly out of scope for this pivot and is not touched. All new operational content is notional and unofficial; this repository does not represent an Army position, requirement, or acquisition decision.

## ADR-008: Fix architecture correctness bugs before building on top of them

**Decision**: Eight confirmed bugs in `architectures.py` and `simulation.py` were fixed before any allocation work began:
- QuicklookFirst and RoiFirst did not cap bytes sent at window capacity (the cause of `contact_utilization` reaching 2.667 in the v1 audit).
- Three different `contact_utilization` implementations were collapsed into one clamped version.
- `tcp_s` was silently set equal to `tfup_s` when a product did not fully deliver; it is now `NaN` with `completed = False`.
- `simulate_multi_contact` was added so undelivered bytes carry across real SGP4 windows instead of being judged in one window.
- A `fidelity_lossy` / `fidelity_resolution_class` field was added to every architecture's output.
- Sizing ratios moved to `config/product_sizing.yaml`.
- `AdaptivePolicy` (A5) now returns and runs a real architecture class instead of a label approximated with Progressive.
- `scripts/audit_paper_numbers.py` now uses relative paths and fails on `contact_utilization > 1`.

**Rationale**: a trade study built on an engine that scores failed deliveries as instant successes is worthless however good the surrounding architecture work is.

**Consequence**: results were regenerated with the fixed code, and several v1 conclusions did not survive.

## ADR-009: Mark LEO_EDGE_OPERATIONAL_VIEWPOINTS.md superseded rather than rewrite it section-by-section (superseded by ADR-011)

**Decision**: `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` is a ~7,000-word, 37-section DoDAF-style operational viewpoint package built entirely around the retired onboard-vs-ground-processing question. Rather than rewrite all 37 sections to match ADR-007's pivot, the document's header was updated with an explicit "Superseded" status pointing readers to the new `docs/OPERATIONAL_CONTEXT.md`, `docs/MISSION_THREADS.md`, `docs/STAKEHOLDERS.md`, and `docs/ALLOCATION_SPACE.md`. `docs/ARCHITECTURE_VIEWS.md` (the shorter, ~1,000-word 4+1 software-views document) was fully rewritten instead, and now also carries the OV-2/OV-5b/OV-6c operational content this rework introduced, since duplicating that content into two large documents would be harder to keep consistent than putting it in one.

**Rationale**: Rewriting 37 sections of DoDAF-structured content built around a retired research question, sentence by sentence, would not produce a better document than writing the new operational content fresh in the Part 2/3 docs this rework already produced; it would mostly produce busywork disguised as thoroughness. The old document remains useful as a historical artifact showing how the project's operational framing looked before the pivot, the same reason `results/frozen/v1/` is kept.

**Consequence**: A reader who opens `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` directly, without going through the README first, sees the superseded notice immediately and is redirected. `docs/OV1_SPEC.md` states that the OV-1 image this document references is retired and describes what a current concept graphic should show instead, without generating one.

## ADR-010: Skip the SysML v2 textual model

**Decision**: No `model/` directory or SysML v2 textual model was produced in this rework pass.

**Rationale**: The rework's guidance was explicit that a SysML model was optional, preferred only "if feasible," and should be "small and correct rather than large." Building a genuinely small, correct SysML v2 model of stakeholders, requirements, functions, allocations, and traces well enough to be useful (rather than a token stub that adds a maintenance burden without adding traceability beyond what `docs/REQUIREMENTS.md`'s matrix already provides) was judged to need more dedicated time than was available in this pass alongside Parts 1-5's other deliverables.

**Consequence**: `docs/REQUIREMENTS.md`'s traceability matrix remains the machine-readable-in-spirit (a markdown table, not machine-checkable) traceability artifact. A SysML model, if built later, should be scoped to formalize that same matrix rather than invent new structure, and should be added as new work, not treated as something this pass silently dropped without a record.

## ADR-011: Delete v1/pre-rework material instead of keeping it as a historical record

**Decision**: `results/frozen/v1/` (the original, buggy frozen results), `paper/manuscript.md` and `paper/hand_calc_break_even.md` (the v1 paper draft and its hand-calculation check), and `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` (the ~7,000-word DoDAF package built around the retired research question) were deleted from the working tree, along with the old OV-1 concept image (`docs/figures/ov1_concept.png`), `SUBMISSION_PACKAGE.md`, and the paper-submission tooling that only worked against that deleted material (`scripts/build_paper.sh`, `scripts/publish_zenodo.py`, the `paper` Makefile target). `docs/HAND_CALC_BREAK_EVEN.md` preserves the still-valid break-even math from `paper/hand_calc_break_even.md`, rewritten with current `results/frozen/v2/` numbers, since that formula itself was never part of the retired framing.

**Rationale**: ADR-008 and ADR-009 originally chose to keep this material as a historical record, the same way a git history is kept. The user explicitly asked for it to be purged instead, after being asked to confirm that scope given it reversed those two prior decisions (a destructive, hard-to-undo-in-the-working-tree action warranted confirming before acting). Once that confirmation was given, keeping stale, superseded material around serves no purpose the git history (where all of it remains recoverable) doesn't already serve, and a repository that visibly contains two competing framings is harder to trust than one with a single, current one.

**Consequence**: Every reference to the deleted files elsewhere in the repository was found and either removed, updated to point at the current equivalent document, or rewritten to describe the deletion honestly instead of the file. `docs/DECISION_LOG.md`'s own history and `REPRODUCE_LOG.md` continue to describe what v1 was and why it was replaced, since a comparison document doesn't need the original files present to be accurate, only to have been accurate when it was written. Nothing in git history was rewritten or force-pushed; a `git log`/`git show` against a commit before this one recovers every deleted file.

## ADR-012: Delete genuinely dead code found during the purge, relocate misplaced files

**Decision**: While auditing for stale references during the ADR-011 purge, `src/leo_edge/mission.py` (a `MissionRequest` dataclass, zero imports anywhere, no test file) was deleted as confirmed dead code, and `tests/orbit_validation.py` (a standalone comparison script with no `test_` functions, never collected by pytest, misplaced in `tests/`) was moved to `scripts/validate_orbit_model.py` and documented in `docs/V_AND_V.md`. `src/leo_edge/scheduler.py`, `queues.py`, `link.py`, and `processing.py` were checked the same way and kept: each has a real test file, satisfying `AGENTS.md`'s "imported by at least one experiment or test" rule, even though `scheduler.py` and `queues.py` have no production consumer today.

**Rationale**: `mission.py` had no consumer and no test, the two things `AGENTS.md` says justify keeping a module; deleting it is exactly what that rule prescribes, not a new policy. `orbit_validation.py` wasn't dead, just filed in the wrong place in a way that made it invisible to `uv run pytest` (silently not run) and confusing to a reader expecting `tests/` to contain only pytest tests.

**Consequence**: `scheduler.py` and `queues.py` remain as documented, intentionally-kept modules with thin test coverage, not deleted on this pass; a future cleanup that wants to remove them should do so as its own explicit decision, not as a side effect of this one.

## ADR-013: Fix e02_image_benchmark_tiles.py mutating its own checked-in input data

**Decision**: `download_tile()` always re-fetched and overwrote `data/imagery/tiles/*.jpg` on every run regardless of whether the tile already existed, silently mutating checked-in input data (confirmed earlier this session: running it changed `tile_001.jpg` from 910,705 to 630,392 bytes). Fixed to reuse an existing tile file instead of re-fetching it.

**Rationale**: Input data that changes every time you run the script that consumes it isn't input data, it's disguised scratch output. `docs/ASSUMPTIONS.md`'s ASM-BENCH-001 and `docs/V_AND_V.md`'s benchmark-reproducibility claims depend on the tiles being stable across runs.

**Consequence**: Verified by hashing `tile_001.jpg` before and after a run (identical) and diffing the output CSV: `compressed_bytes`, `quicklook_bytes`, `roi_bytes`, `psnr`, and `ssim` are now byte-for-byte reproducible; only the timing columns vary, which is expected since those are real wall-clock measurements.

## ADR-014: Add A6_THREAD_AWARE_PRIORITY

**Decision**: Added `ThreadAwarePriority` (A6). It has Progressive's five tiers but sends the active mission thread's needed tier right after metadata, instead of Progressive's fixed order. It closes the gap `docs/ALLOCATION_SPACE.md` named as the most direct missing experiment. It is wired into `e11`, `e03`, `trade_study.py`, and the dashboard.

Two bugs were found and fixed while adding it, before it was committed:
- An early refactor wrote the A-prefixed factory key (`"A0_GROUND_ONLY"`) into the CSV `architecture` column instead of the class name (`"GroundOnly"`). That would have made the trade study's success and resilience criteria silently fall back to 0 for every architecture.
- ContactAware (A5) had never been in `e03`'s rate sweep, so its latency criterion in every earlier trade study was a fallback fill value, not a measurement. Both A5 and A6 are now in the sweep.

The ID `A6` once named `A6_GROUND_CENTRIC_HYBRID`, deleted in ADR-003. Reusing it is intentional: this A6 is documented, tested, and evaluated, which the deleted one was not.

**Consequence**: A6 was later re-evaluated under the corrected model (ADR-020); see `docs/TRADE_STUDY.md` for current numbers.

## ADR-015: A6 provenance, shared mission-thread module, MT-3 restored, MT-4 as a cadence thread

**Decision**:
- `ThreadAwarePriority.PROVENANCE = "proposed_post_v2"`; every other architecture is `"original_candidate_set"`, enforced by a test, so A6 is always reported separately from A0-A5.
- `src/leo_edge/mission_threads.py` is the single source of truth for thread tiers and tolerances, replacing copies in `e11` and the dashboard.
- MT-3 (battle damage assessment) is restored. Its change product is modeled as a P3_ROI-sized product, gated on a per-trial prior-reference draw (`PRIOR_REFERENCE_PROB = 0.5`, ASSUMED). Without a reference it falls back to MT-2's 15-minute tolerance.
- MT-4 is now evaluated as a cadence: every collection pass across the horizon is checked against the per-pass tolerance, and two misses in a row fail the thread.

**Rationale**: v2's MT-4 used the same single-request machinery as the other threads, even though `docs/MISSION_THREADS.md` defines its tolerance as measured per collection. The code was changed to match the doc, not the reverse.

**Consequence**: `tests/test_mission_thread_consistency.py` checks the module against the doc's tables independently. Single-request and cadence results go to separate CSVs because they track different fields.

## ADR-016: Paired trials, collection timing, structural incapacity

**Decision**:
- Every architecture in a trial now shares one draw (request time, denial rolls, prior-reference roll), so paired bootstrap comparisons are valid. v2 gave each architecture independent draws.
- A request must wait for a real overflight of a notional AOI (45N, 5E, ASSUMED) before any downlink window is usable. v2 treated collection as instant.
- Each trial row separately records `structural_incapacity` (the architecture never produces the needed tier) and slowness (produced it, too late).

**Consequence**: honest collection timing pushed success down sharply (7 of 9,000 for the best architectures under the v3 model). ADR-020 later corrected part of that model.

## ADR-017: Fix the terminal-SWaP inversion, derive criteria from code, censor latency properly

**Decision**: `scripts/trade_study.py` was rewritten.
- v2's `terminal_swap_burden` scored GroundOnly best, which is backwards: GroundOnly does no onboard processing, so the Army terminal does all the interpretation. It is replaced by `space_segment_processing_burden` and `terminal_processing_burden`, both derived from real `e03` data.
- `fidelity` comes from the real `fidelity_lossy` field instead of a hand-picked split.
- `acquisition_lock_in_risk` is derived from tier count and a `CONDITIONAL_LOGIC` flag (redefined in ADR-021).
- Latency is a Kaplan-Meier median over `e11`'s per-trial data, censoring non-completions at the 168 h horizon, instead of a mean over completed rows only.
- Rankings are printed twice, SIMULATED_ONLY and COMBINED, and every disagreement is reported. A6 is always scored in a separate table.

**Consequence**: SIMULATED_ONLY picks Progressive (or A6), while COMBINED picks RoiFirst in every profile. That RoiFirst result survives the later corrections (ADR-021).

## ADR-018 (superseded by ADR-019 and ADR-024): v3 access/revisit sweep and its single-plane-phasing explanation

**Superseded.** The explanation below was built on a time-shift constellation model and is retracted; it is kept so the reasoning trail is visible.

**Decision**: Added `experiments/e12_access_sweep.py`, sweeping satellite count (1/2/4/8/16/32) and Army ground-terminal count (1/2/4) as the independent variable, extending `orbit/constellation.py`'s existing phase-offset approach (cheap time-shifting of one real SGP4-computed base access-window set per site, not a second propagation per satellite) rather than duplicating it, and reusing `e11_mission_thread_success.py`'s Part-1-fixed evaluation functions directly via import. Downlink windows from multiple terminal sites are unioned (merged into non-overlapping intervals) under the stated assumption that the tactical unit has one logical delivery pipe, not parallel simultaneous radios to every visible satellite/terminal pair. For tractability across 18 access-level cells (documented, not silent): 2 conditions (NOMINAL and COMBINED_DEGRADED) instead of e11's 5, and fewer trials per cell.

While validating the sweep (checking why some very-high-access cells showed 0% success despite ~49% total coverage duration), found a real, worth-documenting property of the phase-shift approach: spreading N satellites within one orbital plane produces clustered bursts of closely-spaced passes separated by long gaps, not evenly-spaced revisits, because a single plane's ground track only crosses a given site's visibility circle during specific parts of its precession cycle. Total contact-duration coverage still rises monotonically and substantially with satellite count (confirmed: ~1.5% of the week at 1 satellite to ~27% at 32, single terminal), but a mission thread with a tight latency tolerance can still fail even at high total coverage if its request happens to land in one of the remaining long gaps. This is a real property of single-plane phasing, not a bug in the sweep; a true global-revisit constellation would need multiple orbital planes, which is out of scope for extending (not duplicating) `orbit/constellation.py`'s existing single-plane machinery.

**Rationale**: The task named the access/revisit sweep as the core new experiment, built explicitly on `e09`'s existing constellation machinery rather than a from-scratch multi-plane orbital model, which would be a much larger undertaking than "extend, don't duplicate."

**Consequence**: `docs/ACQUISITION_IMPLICATIONS.md` reported the access-level threshold, including this single-plane clustering caveat (retracted in ADR-019), rather than presenting a clean monotonic "more satellites always helps proportionally" curve that the data doesn't actually show. Figures `fig19`-`fig21` (`figures/scripts/`) visualize the sweep, the best-significant-architecture heatmap, and the notional cost-tradeoff curve.

## ADR-019: v4 item 1 -- real Walker-delta constellations, retracting the ADR-018 clustering explanation

**Decision**: `orbit/constellation.py::_phase_shift_windows`'s approach (used by both `e12_access_sweep.py` and `generate_constellation_contacts`) is retracted as a constellation model. Added `generate_walker_delta_tles(total_sats, planes, phasing_factor, altitude_km, inclination_deg)`, which builds a real synthetic TLE per satellite (distinct RAAN spread evenly across `planes`, distinct mean anomaly spread within each plane and offset between planes by `phasing_factor`, standard Walker-delta T/P/F notation), and `per_satellite_access_windows`, which propagates each of those TLEs independently through `orbit/access.py::generate_access_windows` (real SGP4, not a time-shifted copy). `orbit/access.py`'s elevation scan was vectorized (one skyfield call over the whole time array, not one per 30s step) to keep a many-satellite sweep tractable; confirmed behavior-preserving against the existing `tests/test_access.py`/`tests/test_simulation.py` suite before this change was trusted. `access.py` windows now also carry a `"peak"` field (the time of maximum elevation, i.e. closest approach), which v4 item 2 needs for the same-pass collection-timing fix. `generate_constellation_contacts` is kept, marked deprecated in its docstring rather than deleted, since `experiments/e09_constellation_handoff.py` still calls it and fixing e09 was not in the v4 task's scope; e09's results should be read with the same limitation this ADR retracts for e12.

**Rationale**: ADR-018's "single-plane precession clustering" explanation for the 32-satellite success-rate drop was itself built entirely on the flawed time-shift model -- it explained an artifact of the approximation as if it were a property of real orbital mechanics. Once satellites are genuinely propagated with different RAAN/mean-anomaly (i.e. actually different orbits, not phase-delayed copies of the same one), there is no reason to expect that same clustering pattern, and there isn't one in the real data (see the rerun `e12` results in `docs/ACQUISITION_IMPLICATIONS.md`). The v4 task required this retraction explicitly, and it is retracted, not softened: ADR-018's clustering explanation was a real, verified mistake, not a valid finding stated with a caveat.

**Consequence**: The v3 pooled-success table and its clustering explanation are superseded by the rerun. Every new access-sweep number in `results/frozen/v4/` comes from real per-satellite SGP4 propagation of a genuine multi-plane constellation, not an approximation, for every configuration where that was computationally tractable in this session; where the sweep stopped short of the 80-90% success target the v4 task named as ideal, `docs/ACQUISITION_IMPLICATIONS.md` states the largest configuration actually run and why (propagation cost), rather than extrapolating past it.

## ADR-020: v4 item 2 -- same-pass collect-and-downlink

**Decision**: `experiments/e11_mission_thread_success.py` now models collection as complete at the AOI pass's time of closest approach (`access.py`'s new `"peak"` field), not pass end, and tracks downlink windows per satellite instead of one merged list. A request's image can only be downlinked by the satellite that collected it (no crosslink model; would be a separate, documented option if added later). `usable_downlink_same_satellite()` allows any of that satellite's downlink windows that are still open at or after collection -- including the remaining portion of the very pass that did the collection -- clipped to that remaining duration, instead of requiring the whole window to start after collection (v3's `_usable_downlink`, which made same-pass delivery structurally impossible).

**Rationale**: The v4 task named this as a confirmed modeling error, not an open design choice: forbidding same-pass downlink rules out the defining capability of direct-to-edge (image collected and delivered without waiting for a second, later pass) by construction, regardless of how good the architecture or constellation is.

**Consequence**: Isolated at the single-satellite baseline (Progressive, MT-1, VEHICLE_MOUNTED, NOMINAL, 500 trials, `report_same_pass_effect()` in `e11_mission_thread_success.py`): the v3 model produced 0/500 successes; the v4 same-pass model produces successes where none were structurally possible before, and mean latency for trials that did produce the tier dropped from ~26,900s to ~16,900s. Across the full baseline paired-trial run, ThreadAwarePriority's success count rises from 7/9000 (0.08%, v3) to 142/9000 (1.6%, v4), and unlike v3 (where the top three architectures were tied exactly), v4's baseline now shows real, statistically significant separation between architectures (e.g. ThreadAwarePriority vs. Progressive: 142 vs. 129 of 9000, significant=True) -- a materially different starting point for the trade study and the access sweep, addressed in `docs/ACQUISITION_IMPLICATIONS.md`. Added `tests/test_same_pass_delivery.py` covering the same-pass clip, the fully-before-collection skip, the fully-after-collection whole-window case, and denial independent of timing.

## ADR-021: v4 item 5 -- lock-in proxy tied to the ownership boundary

**Decision**: `scripts/trade_study.py`'s `acquisition_lock_in_risk` criterion is now explicitly justified against `docs/INTERFACES.md`'s function-to-segment table rather than being a bare tier count. That table shows Process/Prioritize/Transmit are allocated to the commercial segment for every architecture in this repository -- the FUNCTION allocation doesn't vary by architecture, so it can't be the thing distinguishing lock-in risk between them. What varies is (a) how many of `docs/INTERFACES.md`'s named data-format interfaces (Metadata, Thumbnail, Quicklook, ROI, Full) the Army terminal depends on receiving from a given provider's implementation -- the non-metadata tier count, kept as the base of the proxy -- and (b) whether the architecture's behavior is `CONDITIONAL_LOGIC`: a runtime, per-request decision (A5's margin check, A6's priority-tier choice) that can't be pinned to a static format spec the way a fixed tier list can, which is a difference in kind from one more format, not degree. The conditional-logic term's weight was raised from 1 to 2 to reflect that.

**Rationale**: The v4 task asked for a proxy "tied to the actual ownership boundary... per docs/INTERFACES.md," not simply a differently-weighted version of the same tier count. Since every architecture here allocates the same functions to the same segment, the real per-architecture ownership-boundary variable is interface count and interface predictability (static vs. runtime-conditional), which is what this version measures.

**Consequence**: RoiFirst (2 non-metadata tiers, no conditional logic, lock-in score 2) still wins the `COMBINED` ranking in every stakeholder profile after this change -- the flip to RoiFirst reported in v3 is NOT an artifact of the old proxy; it persists under the new one. ThreadAwarePriority's score actually gets worse under the new proxy (4 non-metadata tiers + 2 for conditional logic = 6, vs. v3's 4+1=5), widening its `COMBINED` gap to RoiFirst rather than closing it. `docs/TRADE_STUDY.md` reports this explicitly, since the v4 task specifically asked whether the flip survives a real ownership-boundary-based proxy, and the honest answer is yes.

## ADR-022: v4 item 4 -- restrict architecture testing to informative cells

**Decision**: `experiments/e12_access_sweep.py::cell_pairwise_significance` now only runs pairwise architecture comparisons when the best architecture's overall success rate in that cell exceeds `INFORMATIVE_THRESHOLD = 0.30`. Every cell is labeled one of three ways: `UNINFORMATIVE` (best success <= 30%, a floor effect -- testing whether two near-zero architectures "differ significantly" isn't a meaningful statement), `SEPARATES` (informative, and one architecture beats every other by a significant margin), or `TIES` (informative, tested, no significant difference). `figures/scripts/fig20_access_heatmap.py` greys out `UNINFORMATIVE` cells distinctly from `TIES`.

**Rationale**: v3's `docs/TRADE_STUDY.md` reported "17 of 18 cells show no significant difference between any pair of architectures" as if it were one finding. It wasn't: at the v3 baseline, every architecture was near 0% success, so "no significant difference" there meant "nothing works," not "architectures were tested and tied." The v4 task required this distinction explicitly, since "processing architecture is second-order" is only a supported claim in cells where architectures actually had room to differ.

**Consequence**: `docs/ACQUISITION_IMPLICATIONS.md` reports the cell types across the real Walker sweep, and the headline claim about architecture mattering (or not) is scoped to `SEPARATES`/`TIES` cells only, never to `UNINFORMATIVE` ones.

## ADR-023: v4 sweep stopped at 24 satellites, incremental writes added

**Decision**: `experiments/e12_access_sweep.py`'s first full-sweep attempt (32 satellites/8 planes as the largest configuration) was killed by the host's memory-pressure protection partway through that config, and lost every row computed in the run because output was only written once, at the very end of `main()`. Rewrote output to an `IncrementalCsvWriter` that flushes each cell's rows to disk immediately, and reduced the largest swept configuration from 32/8/1 to 24/8/1 satellites/planes/phasing-factor -- the largest confirmed to complete reliably in this session.

**Rationale**: the v4 task explicitly allows stopping the satellite-count extension short of the 80-90% ideal and documenting why, rather than requiring it be reached regardless of cost; real per-satellite SGP4 propagation at 32+ satellites, run alongside whatever else is using memory on this machine, is not reliably completable in one session. Incremental writes were added regardless of the config-size decision, since losing an entire run's output to one late-stage kill is a real robustness gap independent of how large the sweep gets.

**Consequence**: `results/frozen/v4/e12_*.csv` reflect real Walker-delta configurations up to 24 satellites / 8 planes. `docs/ACQUISITION_IMPLICATIONS.md` states this as the stopping point and why, per the task's own instruction, rather than presenting 24 as if it were always the intended ceiling.

## ADR-024: v4 first sweep invalidated by a TLE column bug; rerun

**Decision**: `orbit/constellation.py::_build_synthetic_tle` dropped the separator column before the mean-anomaly field, so SGP4 (which parses fixed columns) read every satellite's mean anomaly as 0. RAAN was correct, but all satellites within a plane were co-located. Noticed because two satellites 180 degrees apart in one plane returned identical access windows. The first full e12 sweep was discarded, the TLE builder now uses exact fixed-width columns, and `tests/test_walker_tle.py` parses generated TLEs back with `sgp4` and checks RAAN, mean anomaly, and distinct in-plane ground tracks. The single-satellite baseline (e11) is unaffected (its mean anomaly is 0 by design).

**Rationale**: a sweep that silently places satellites on top of each other reports the flattest possible access curve and would have supported a false "nothing works up to 24 satellites" headline (that run's best cell was ~13%).

**Consequence**: all v4 e12 numbers come from the corrected rerun. Success reaches ~31% (best architecture, pooled) at 24 satellites/8 planes/4 terminals, the sweep's stopping point (ADR-023).

## ADR-025: Delete the v2 and v3 frozen results and the history docs

**Decision**: `results/frozen/v2/`, `results/frozen/v3/`, and the six history documents (rework plans and the v1-v2, v2-v3, v3-v4 comparisons) were deleted. `results/frozen/v4/` is the only frozen result set. This log is the retained record of what each version claimed and what was retracted.

**Rationale**: with the comparison documents gone, the old result sets had no reader, and two of them (v2, v3) were produced by models later shown to be wrong (ADR-019, ADR-020, ADR-024). Keeping them invited citing numbers the log says not to trust.

**Consequence**: older numbers quoted in ADRs cannot be re-derived from the working tree; `git log` recovers every deleted file.
