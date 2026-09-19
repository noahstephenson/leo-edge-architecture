# v3 Rework Plan: Fix v2 Evaluation Problems + Access/Revisit Sweep

Status: in progress. `paper/manuscript.md` doesn't exist (deleted in the
v2 cleanup pass); `docs/NOVELTY.md` is explicitly out of scope for this
pass. `results/frozen/v2/` stays untouched; new output goes in
`results/frozen/v3/`.

## Context

v2's trade study and mission-thread evaluation have real methodological
problems: an inverted terminal-SWaP criterion, hand-picked rubric numbers
driving rankings that could mostly be derived from architecture properties
instead, unpaired trials with no significance testing, A6 added after
seeing results and not labeled as such, an inconsistency between
`docs/MISSION_THREADS.md`'s MT-4 cadence definition and what the code
actually evaluates, an implicit assumption that collection is instantaneous
at request time (no imaging-pass model), structural incapacity averaged
into performance scores, and a latency criterion computed only over
completed deliveries (survivorship bias). Part 1 fixes all of these. Part
2 makes ground-segment access density (satellite count x terminal count)
the swept independent variable, since v2's own finding was that access,
not architecture, is the binding constraint. Part 3 rewrites the
downstream narrative docs to match whatever v3 actually shows.

## Part 1: Fix confirmed problems

1. **Terminal SWaP burden.** Replace `trade_study.py`'s single inverted
   `terminal_swap_burden` criterion with two, both derived from
   architecture properties, not hand-picked: `space_segment_processing_burden`
   (derived from `e03_results.csv`'s `processing_energy_j`, higher energy =
   higher burden = worse) and `terminal_processing_burden` (derived: 1 iff
   the architecture ever delivers a raw/lossless product with zero onboard
   processing, i.e. GroundOnly only, since an unprocessed product pushes
   all interpretation work to the terminal; 0 otherwise). One-line rule
   documented in the script for each.
2. **Rubric vs. simulated separation.** `fidelity` becomes derived from the
   real `fidelity_lossy` field (already simulated, not hand-picked).
   `acquisition_lock_in_risk` becomes derived from a count of distinct
   provider-side functions each architecture's `.tiers()` requires (number
   of non-metadata tiers, +1 for conditional/adaptive logic in
   ContactAware/A6). After this, every criterion is either simulated
   (mission_thread_success, latency, resilience) or derived from a stated,
   code-level rule (fidelity, both burden criteria, lock-in risk) -- no
   free-floating hand-assigned numbers remain. Report rankings on simulated
   criteria alone, then with derived criteria added, and name every flip
   that only appears once derived criteria are included.
3. **Paired trials + significance testing.** Restructure `e11` to draw
   request time and contact-denial mask once per trial index per
   (thread, terminal, condition) cell, then evaluate every architecture
   against that same draw (trial-outer loop, not architecture-outer).
   Add a paired bootstrap test on the success-rate difference between
   architecture pairs (resample trial indices, not individual outcomes),
   reporting a CI on the difference and explicit "no significant
   difference" where the CI includes 0. Increase trial count where base
   rates are low enough that this matters.
4. **A6 provenance.** Tag `ThreadAwarePriority` with a provenance marker
   (`PROVENANCE = "proposed_post_v2"`) checked by a test. Report it in a
   separate results section/table from the neutral A0-A5 comparison in
   both `e11`'s output and `docs/TRADE_STUDY.md`.
5. **Mission-thread consistency.**
   - Restore MT-3: model the change/difference product's size and
     processing cost as equal to the P3_ROI tier (a stated, documented
     proxy, not a new product type), gated on a `prior_reference_available`
     draw (parameterized probability, ASSUMED); when unavailable, MT-3
     degrades to MT-2 behavior per the doc's own dependency note.
   - Fix MT-4 in code to match the doc: cadence measured per actual
     contact opportunity across the mission horizon (fraction of contacts
     delivering a coarse product within 5 minutes of that specific pass,
     with 2+ consecutive misses = failure), not a single request/response
     evaluation identical in mechanics to MT-1/MT-2.
   - Add `tests/test_mission_thread_consistency.py` asserting every
     thread's needed tier and latency tolerance in `e11` matches
     `docs/MISSION_THREADS.md`'s tables (hand-transcribed constants checked
     against the experiment's constants, not a docstring parser).
6. **Collection timing.** Add an imaging-opportunity model: request time
   -> next AOI overflight (a second `generate_access_windows` call at a
   distinct notional AOI location, not the ground terminal) -> processing
   -> next downlink contact at/after collection. Report the latency delta
   this adds vs. the v2 instant-collection assumption.
7. **Definitional zeros.** Track "never produces needed tier" (structural,
   from `architecture_supports_tier`) separately from "produced it, missed
   the tolerance" in both the trial CSV and the summary; report each
   separately in docs, never averaged into one number silently.
8. **Censoring-aware latency.** Replace the trade study's
   completed-only mean TFUP with a Kaplan-Meier-style median time-to-product
   that treats non-completions as censored at the evaluation horizon, not
   dropped.

## Part 2: Access/revisit sweep

New experiment `experiments/e12_access_sweep.py`, built on
`orbit/constellation.py`'s existing phase-offset machinery (extended, not
duplicated): for each of several ground-terminal locations (documented,
notionally distinct sites), compute base single-satellite access windows
once (real SGP4), then time-shift cheaply for additional satellites (as
`generate_constellation_contacts` already does) and union across terminals
for additional ground sites. Sweep satellites in {1,2,4,8,16,32} and
terminals in {1,2,4}. At each (sat_count, terminal_count) cell, run the
Part-1-fixed mission-thread evaluation (paired trials, all threads,
terminal classes, conditions) with trial counts scaled up where success
rates are low. Outputs: `results/frozen/v3/e12_access_sweep.csv` (per-cell
success rates + CIs), `figures/fig19_access_sweep_by_thread.png` (success
vs. access level, one panel per thread, CI bands, lines per architecture),
`figures/fig20_access_heatmap.png` (best statistically-distinguishable
architecture over sat x terminal, "no significant difference" cells
labeled), and a notional cost-tradeoff figure/table
(`figures/fig21_cost_tradeoff.png`) using an explicit, labeled ASSUMED
relative-cost proxy for "one more satellite of access" vs. "one more
onboard processing tier."

## Part 3: Update the story

- Re-run `scripts/trade_study.py` against `results/frozen/v3/`.
- Rewrite `docs/ACQUISITION_IMPLICATIONS.md` from v3 evidence.
- Write `docs/V2_VS_V3.md`: which v2 claims survive, which die, why.
- Update `README.md`'s headline to the v3 result.

## Sequencing and commits

Part 1 lands first as a sequence of small, separately-tested commits (one
per numbered fix, where practical), since Part 2's sweep depends on the
fixed evaluation engine. Part 2 lands as the new experiment plus figures.
Part 3 lands last, once real v3 numbers exist to write about. Every
modeling decision gets an ADR in `docs/DECISION_LOG.md` as it's made, not
batched at the end.
