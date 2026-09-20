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

**Consequence**: Every reference to the deleted files elsewhere in the repository was found and either removed, updated to point at the current equivalent document, or rewritten to describe the deletion honestly instead of the file. `docs/V1_VS_V2.md`, `docs/DECISION_LOG.md`'s own history, and `REPRODUCE_LOG.md` continue to describe what v1 was and why it was replaced, since a comparison document doesn't need the original files present to be accurate, only to have been accurate when it was written. Nothing in git history was rewritten or force-pushed; a `git log`/`git show` against a commit before this one recovers every deleted file.

## ADR-012: Delete genuinely dead code found during the purge, relocate misplaced files

**Decision**: While auditing for stale references during the ADR-011 purge, `src/leo_edge/mission.py` (a `MissionRequest` dataclass, zero imports anywhere, no test file) was deleted as confirmed dead code, and `tests/orbit_validation.py` (a standalone comparison script with no `test_` functions, never collected by pytest, misplaced in `tests/`) was moved to `scripts/validate_orbit_model.py` and documented in `docs/V_AND_V.md`. `src/leo_edge/scheduler.py`, `queues.py`, `link.py`, and `processing.py` were checked the same way and kept: each has a real test file, satisfying `AGENTS.md`'s "imported by at least one experiment or test" rule, even though `scheduler.py` and `queues.py` have no production consumer today.

**Rationale**: `mission.py` had no consumer and no test, the two things `AGENTS.md` says justify keeping a module; deleting it is exactly what that rule prescribes, not a new policy. `orbit_validation.py` wasn't dead, just filed in the wrong place in a way that made it invisible to `uv run pytest` (silently not run) and confusing to a reader expecting `tests/` to contain only pytest tests.

**Consequence**: `scheduler.py` and `queues.py` remain as documented, intentionally-kept modules with thin test coverage, not deleted on this pass; a future cleanup that wants to remove them should do so as its own explicit decision, not as a side effect of this one.

## ADR-013: Fix e02_image_benchmark_tiles.py mutating its own checked-in input data

**Decision**: `download_tile()` always re-fetched and overwrote `data/imagery/tiles/*.jpg` on every run regardless of whether the tile already existed, silently mutating checked-in input data (confirmed earlier this session: running it changed `tile_001.jpg` from 910,705 to 630,392 bytes). Fixed to reuse an existing tile file instead of re-fetching it.

**Rationale**: Input data that changes every time you run the script that consumes it isn't input data, it's disguised scratch output. `docs/ASSUMPTIONS.md`'s ASM-BENCH-001 and `docs/V_AND_V.md`'s benchmark-reproducibility claims depend on the tiles being stable across runs.

**Consequence**: Verified by hashing `tile_001.jpg` before and after a run (identical) and diffing the output CSV: `compressed_bytes`, `quicklook_bytes`, `roi_bytes`, `psnr`, and `ssim` are now byte-for-byte reproducible; only the timing columns vary, which is expected since those are real wall-clock measurements.

## ADR-014: Add A6_THREAD_AWARE_PRIORITY, closing the mission-thread-aware-prioritization gap

**Decision**: Added `ThreadAwarePriority` (A6) to `src/leo_edge/architectures.py`: it behaves like Progressive (same five tiers, same sizes) but reorders delivery so the active mission thread's specific needed tier is sent right after metadata, instead of Progressive's fixed metadata-thumbnail-quicklook-ROI-full order regardless of which thread is running. This directly closes the gap `docs/ALLOCATION_SPACE.md` named as "the most direct next experiment this repository doesn't yet run." Wired into `experiments/e11_mission_thread_success.py`, `experiments/e03_static_architectures.py`, `scripts/trade_study.py`, and `app/dashboard.py`.

While wiring A6 into `e11`, caught and fixed a real naming bug in the same change, before it was ever committed: the refactor to support per-thread architecture construction initially used the A-prefixed factory key (e.g. `"A0_GROUND_ONLY"`) as the CSV `architecture` value, instead of the class name (`"GroundOnly"`) that `e03_results.csv` and `scripts/trade_study.py`'s `ARCHITECTURES` list expect. That mismatch would have made `scripts/trade_study.py`'s `mission_thread_success` and `resilience` criteria silently fall back to 0 for every architecture, every future run, with no error. Fixed by deriving the CSV name from `type(architecture).__name__`.

Also discovered and fixed while adding A6: `ContactAware` (A5) had never been included in `e03_static_architectures.py`'s rate sweep, meaning its "latency" criterion in every prior trade-study run (including the version committed to `docs/TRADE_STUDY.md` before this ADR) was silently a fallback fill value (the worst observed latency among the other architectures), not a real measurement. Both `ContactAware` and the new `ThreadAwarePriority` were added to the `e03` sweep so all seven architectures now have real single-window latency data.

Note on the ID: `A6` previously named `A6_GROUND_CENTRIC_HYBRID`, deleted in ADR-003 as undocumented scope creep. Reusing `A6` for this unrelated architecture is intentional, not confusion between the two; this one is fully documented, tested, and evaluated, which is exactly what the deleted one wasn't.

**Rationale**: `docs/ALLOCATION_SPACE.md` explicitly named this as the highest-value next step, and it was tractable to implement well within this session rather than leaving it as a permanent stated gap.

**Consequence**: `docs/ALLOCATION_SPACE.md`, `docs/TRADE_STUDY.md`, and `docs/ACQUISITION_IMPLICATIONS.md` are updated with A6's real results: it achieves the highest mission-thread success (1.92% mean) and resilience (1.04% mean under degraded conditions) of any architecture tested, and wins the trade study outright under the tactical-user-leaning weight profile, while Progressive still wins the acquisition- and terminal-operator-leaning profiles because a fixed pipeline is simpler to specify in a multi-vendor contract than a per-request reordering rule. The headline finding (contact geometry, not architecture, is the binding constraint) is unchanged: A6's best-case success rate is still under 2% on average.

## ADR-015: v3 Part 1 -- A6 provenance tag, shared mission-thread module, MT-3 restored, MT-4 cadence fix

**Decision**: `ThreadAwarePriority.PROVENANCE = "proposed_post_v2"`; every other architecture gets `PROVENANCE = "original_candidate_set"`, enforced by a test. `src/leo_edge/mission_threads.py` is now the single source of truth for mission-thread tier/tolerance parameters, replacing hand-duplicated copies in `e11_mission_thread_success.py` and `app/dashboard.py`. MT-3 (battle damage assessment) is restored: its change/difference product is modeled as needing a P3_ROI-sized product (a documented proxy, not a new product type in `products.py`), gated on a per-trial `prior_reference_available` draw at `PRIOR_REFERENCE_PROB = 0.5` (ASSUMED); without a reference it degrades to MT-2's 15-minute tolerance per the doc's own dependency note. MT-4 is now genuinely cadence-based: `evaluate_cadence()` walks every real AOI overflight pass across the full mission horizon and checks whether a coarse product from that specific pass arrives within its tolerance, failing the thread on 2+ consecutive misses, instead of the v2 code's single-request evaluation that was mechanically identical to MT-1/MT-2 despite `docs/MISSION_THREADS.md` defining MT-4's tolerance as "measured from each collection," not from one request.

**Rationale**: The v3 task required a test that MT-4's code and the doc actually agree, and the honest answer on inspection was that v2's MT-4 code didn't implement the doc's cadence concept at all -- it just used a different `needed_tier`/`latency_tolerance_s` on the same single-request machinery as every other thread. Fixing the code to match the doc (rather than loosening the doc to match the code) was the right direction because MT-4's whole operational point, "persistent monitoring... defined by repeat collections... not a single request/response cycle," is unmet by a single-request evaluation regardless of what tolerance number is plugged in.

**Consequence**: `tests/test_mission_thread_consistency.py` hand-transcribes the doc's tables independently and checks the module against them, including a dedicated assertion that MT-4 is flagged `cadence=True` and the other three are not. `experiments/e11_mission_thread_success.py` now writes separate summary files for single-request threads (`e11_mission_thread_success.csv`) and the cadence thread (`e11_cadence_success.csv`), since they track different fields (a per-pass cadence rate has no equivalent in a single request/response evaluation) and forcing them into one schema either loses information or crashes on the field mismatch (caught before committing: an early version of this change tried to merge both into one CSV and `csv.DictWriter` raised on the cadence-only `mean_cadence_rate` field).

## ADR-016: v3 Part 1 items 3, 6, 7 -- paired trials, collection timing, definitional zeros

**Decision**: `experiments/e11_mission_thread_success.py` now draws one shared trial context (`request_time_s`, a per-downlink-window denial roll, and a prior-reference roll) per trial index per (thread, terminal, condition) cell, and evaluates every architecture against that same draw (`draw_request_context`), instead of v2's architecture-outer loop where each architecture got its own independent random draws. This makes architecture comparisons genuinely paired, which is what `paired_bootstrap_diff_ci` (`src/leo_edge/stats.py`) requires to be a valid paired test rather than a mislabeled one.

Added a real collection-opportunity model: a request must wait for the next actual SGP4 overflight of a notional AOI location (45N, 5E, offset from the 40N/0E ground terminal, documented ASSUMED) before any downlink window becomes usable, computed the same way as the existing ground-terminal access windows (`generate_access_windows`, just at a different lat/lon). v2 treated collection as instantaneous at request time, which was never stated as an assumption anywhere and was simply an omission.

Every trial row now separately records `structural_incapacity` (the architecture's `.tiers()` never includes the thread's needed tier at all) versus `produced_tier` combined with missing the latency tolerance (produced the tier, too slowly), instead of collapsing both into a single `success=False`.

**Rationale**: All three were named explicitly in the reopened v3 task as confirmed problems, not open design choices.

**Consequence**: Re-running `e11` with the collection-timing model added pushes mission-thread success rates down further than v2's already-low numbers (v2: best architecture ~1.9% mean; v3 first run: 7 successes out of 9000 paired trials for the best architectures, i.e. under 0.1%), because a second real SGP4 wait (for the AOI pass) now stacks on top of the downlink wait v2 already modeled. This is a real, if severe, consequence of modeling collection honestly, not a bug; see `docs/V2_VS_V3.md` for the full before/after once Part 2's access sweep provides context for how this changes with more satellites/terminals.

## ADR-017: v3 Part 1 items 1, 2, 8 -- fix terminal SWaP inversion, derive criteria from code, censoring-aware latency

**Decision**: `scripts/trade_study.py` rewritten. `terminal_swap_burden` (v2: GroundOnly scored 1.0/best, which was backwards -- GroundOnly does zero onboard processing, so it pushes ALL interpretation work onto the Army terminal) is replaced by two criteria derived from real `e03_results.csv` fields: `space_segment_processing_burden` (mean `processing_energy_j`, higher energy = more provider-side burden = worse) and `terminal_processing_burden` (fraction of rows with `processing_energy_j == 0`, i.e. raw/unprocessed delivery = worse for the terminal). `fidelity` is now derived from the real `fidelity_lossy` field instead of a hand-picked 1.0/0.6 split. `acquisition_lock_in_risk` is now derived from each architecture's actual tier count (`.tiers()`) plus a new `CONDITIONAL_LOGIC` class flag (true for ContactAware and ThreadAwarePriority, which branch per request) instead of a hand-picked number. `latency` now comes from a Kaplan-Meier-style censored median over `e11_mission_thread_trials.csv`'s per-trial latency data (`src/leo_edge/stats.py::kaplan_meier_median`) instead of a mean over completed-only `e03` rows, which silently dropped every non-completion. Every ranking is now printed twice: `SIMULATED_ONLY` (mission_thread_success, latency, resilience -- the three criteria that come directly from simulation) and `COMBINED` (all seven), with every case where the two disagree on the top architecture reported explicitly. A6 is scored in a separate `WITH_A6` table alongside the original `ORIGINAL_SET` table in every view, never silently merged into one ranking.

**Rationale**: All three were named as confirmed problems in the reopened v3 task, not open design choices. The terminal-SWaP inversion in particular was a real methodological bug (docs/TRADE_STUDY.md v2 recommended GroundOnly as best-in-class on a criterion it should have scored worst on), not a modeling simplification.

**Consequence**: With real v3 data (`results/frozen/v3/e03_results.csv`, `e11_mission_thread_trials.csv`), `SIMULATED_ONLY` picks Progressive (or A6, when included) as the top architecture in every profile, while `COMBINED` picks RoiFirst in every single profile and architecture set -- a materially different, and now honestly-labeled, result from v2's Progressive-wins-everything story. RoiFirst's smaller tier count (2, vs. Progressive's 4) gives it a real, code-derived advantage on `acquisition_lock_in_risk` that outweighs Progressive's edge on the simulated criteria once acquisition/lock-in concerns are weighted at all. See `docs/TRADE_STUDY.md` for the full result and `docs/V2_VS_V3.md` for what this changes about the v2 story.

## ADR-018: v3 Part 2 -- access/revisit sweep, and a real single-plane-phasing limitation found while validating it

**Decision**: Added `experiments/e12_access_sweep.py`, sweeping satellite count (1/2/4/8/16/32) and Army ground-terminal count (1/2/4) as the independent variable, extending `orbit/constellation.py`'s existing phase-offset approach (cheap time-shifting of one real SGP4-computed base access-window set per site, not a second propagation per satellite) rather than duplicating it, and reusing `e11_mission_thread_success.py`'s Part-1-fixed evaluation functions directly via import. Downlink windows from multiple terminal sites are unioned (merged into non-overlapping intervals) under the stated assumption that the tactical unit has one logical delivery pipe, not parallel simultaneous radios to every visible satellite/terminal pair. For tractability across 18 access-level cells (documented, not silent): 2 conditions (NOMINAL and COMBINED_DEGRADED) instead of e11's 5, and fewer trials per cell.

While validating the sweep (checking why some very-high-access cells showed 0% success despite ~49% total coverage duration), found a real, worth-documenting property of the phase-shift approach: spreading N satellites within one orbital plane produces clustered bursts of closely-spaced passes separated by long gaps, not evenly-spaced revisits, because a single plane's ground track only crosses a given site's visibility circle during specific parts of its precession cycle. Total contact-duration coverage still rises monotonically and substantially with satellite count (confirmed: ~1.5% of the week at 1 satellite to ~27% at 32, single terminal), but a mission thread with a tight latency tolerance can still fail even at high total coverage if its request happens to land in one of the remaining long gaps. This is a real property of single-plane phasing, not a bug in the sweep; a true global-revisit constellation would need multiple orbital planes, which is out of scope for extending (not duplicating) `orbit/constellation.py`'s existing single-plane machinery.

**Rationale**: The task named the access/revisit sweep as the core new experiment, built explicitly on `e09`'s existing constellation machinery rather than a from-scratch multi-plane orbital model, which would be a much larger undertaking than "extend, don't duplicate."

**Consequence**: `docs/V2_VS_V3.md` and `docs/ACQUISITION_IMPLICATIONS.md` report the access-level threshold (or lack of one) honestly, including this single-plane clustering caveat, rather than presenting a clean monotonic "more satellites always helps proportionally" curve that the data doesn't actually show. Figures `fig19`-`fig21` (`figures/scripts/`) visualize the sweep, the best-significant-architecture heatmap, and the notional cost-tradeoff curve.

## ADR-019: v4 item 1 -- real Walker-delta constellations, retracting the ADR-018 clustering explanation

**Decision**: `orbit/constellation.py::_phase_shift_windows`'s approach (used by both `e12_access_sweep.py` and `generate_constellation_contacts`) is retracted as a constellation model. Added `generate_walker_delta_tles(total_sats, planes, phasing_factor, altitude_km, inclination_deg)`, which builds a real synthetic TLE per satellite (distinct RAAN spread evenly across `planes`, distinct mean anomaly spread within each plane and offset between planes by `phasing_factor`, standard Walker-delta T/P/F notation), and `per_satellite_access_windows`, which propagates each of those TLEs independently through `orbit/access.py::generate_access_windows` (real SGP4, not a time-shifted copy). `orbit/access.py`'s elevation scan was vectorized (one skyfield call over the whole time array, not one per 30s step) to keep a many-satellite sweep tractable; confirmed behavior-preserving against the existing `tests/test_access.py`/`tests/test_simulation.py` suite before this change was trusted. `access.py` windows now also carry a `"peak"` field (the time of maximum elevation, i.e. closest approach), which v4 item 2 needs for the same-pass collection-timing fix. `generate_constellation_contacts` is kept, marked deprecated in its docstring rather than deleted, since `experiments/e09_constellation_handoff.py` still calls it and fixing e09 was not in the v4 task's scope; e09's results should be read with the same limitation this ADR retracts for e12.

**Rationale**: ADR-018's "single-plane precession clustering" explanation for the 32-satellite success-rate drop was itself built entirely on the flawed time-shift model -- it explained an artifact of the approximation as if it were a property of real orbital mechanics. Once satellites are genuinely propagated with different RAAN/mean-anomaly (i.e. actually different orbits, not phase-delayed copies of the same one), there is no reason to expect that same clustering pattern, and there isn't one in the real data (see the rerun `e12` results, `docs/V3_VS_V4.md`). The v4 task required this retraction explicitly, and it is retracted, not softened: ADR-018's clustering explanation was a real, verified mistake, not a valid finding stated with a caveat.

**Consequence**: `docs/V2_VS_V3.md`'s pooled-success-by-satellite-count table and its clustering explanation are superseded by `docs/V3_VS_V4.md`'s rerun. Every new access-sweep number in `results/frozen/v4/` comes from real per-satellite SGP4 propagation of a genuine multi-plane constellation, not an approximation, for every configuration where that was computationally tractable in this session; where the sweep stopped short of the 80-90% success target the v4 task named as ideal, `docs/V3_VS_V4.md` states the largest configuration actually run and why (propagation cost), rather than extrapolating past it.

## ADR-020: v4 item 2 -- same-pass collect-and-downlink

**Decision**: `experiments/e11_mission_thread_success.py` now models collection as complete at the AOI pass's time of closest approach (`access.py`'s new `"peak"` field), not pass end, and tracks downlink windows per satellite instead of one merged list. A request's image can only be downlinked by the satellite that collected it (no crosslink model; would be a separate, documented option if added later). `usable_downlink_same_satellite()` allows any of that satellite's downlink windows that are still open at or after collection -- including the remaining portion of the very pass that did the collection -- clipped to that remaining duration, instead of requiring the whole window to start after collection (v3's `_usable_downlink`, which made same-pass delivery structurally impossible).

**Rationale**: The v4 task named this as a confirmed modeling error, not an open design choice: forbidding same-pass downlink rules out the defining capability of direct-to-edge (image collected and delivered without waiting for a second, later pass) by construction, regardless of how good the architecture or constellation is.

**Consequence**: Isolated at the single-satellite baseline (Progressive, MT-1, VEHICLE_MOUNTED, NOMINAL, 500 trials, `report_same_pass_effect()` in `e11_mission_thread_success.py`): the v3 model produced 0/500 successes; the v4 same-pass model produces successes where none were structurally possible before, and mean latency for trials that did produce the tier dropped from ~26,900s to ~16,900s. Across the full baseline paired-trial run, ThreadAwarePriority's success count rises from 7/9000 (0.08%, v3) to 142/9000 (1.6%, v4), and unlike v3 (where the top three architectures were tied exactly), v4's baseline now shows real, statistically significant separation between architectures (e.g. ThreadAwarePriority vs. Progressive: 142 vs. 129 of 9000, significant=True) -- a materially different starting point for the trade study and the access sweep, addressed in `docs/V3_VS_V4.md`. Added `tests/test_same_pass_delivery.py` covering the same-pass clip, the fully-before-collection skip, the fully-after-collection whole-window case, and denial independent of timing.
