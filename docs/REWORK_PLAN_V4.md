# Rework Plan v4

Short plan for the v4 fixes to v3's access-sweep modeling errors. Full
detail lands in `docs/DECISION_LOG.md` ADRs as each item is implemented;
this file is the checklist, not the record.

## What's wrong with v3, in one line each

1. `e12_access_sweep.py`'s satellite count was one satellite's access
   windows time-shifted, not real additional satellites. Not a
   constellation model.
2. `e11_mission_thread_success.py` treated collection as complete at the
   END of the AOI pass, so it could never use a downlink window that
   started before the pass ended -- forbidding same-pass delivery, which is
   direct-to-edge's whole point.
3. No tolerance-feasibility floor was computed, so an infeasible thread's
   zeros looked like the same kind of failure as a merely-unlucky one.
4. "No significant difference" was reported the same way whether nothing
   worked (floor effect) or architectures genuinely tied at real success
   rates.
5. Acquisition lock-in risk was a tier-count proxy, not tied to the actual
   provider/Army ownership boundary in `docs/INTERFACES.md`.

## Fix order

1. **Real constellations** (`src/leo_edge/orbit/constellation.py`): add
   `generate_walker_delta_tles` + `per_satellite_access_windows`, each
   satellite individually SGP4-propagated via a real per-satellite TLE
   (distinct RAAN/mean-anomaly), not a time-shifted copy. Vectorize
   `orbit/access.py`'s elevation scan (behavior-preserving, confirmed by
   the existing test suite) so a many-satellite sweep is tractable.
   `_phase_shift_windows` deleted from `e12`; `generate_constellation_contacts`
   marked deprecated in place (still used by `e09`, out of scope here).
2. **Same-pass delivery** (`e11_mission_thread_success.py`): collection
   time is now the AOI pass's time of closest approach (`peak`, from
   `access.py`), not pass end. Downlink windows are tracked per satellite;
   a request can only be delivered by the satellite that collected it
   (no crosslink model), and any of that satellite's downlink windows
   still open after collection (including the pass in progress) can be
   used, clipped to its remaining duration.
3. **Feasibility floors, KM curves, tolerance sensitivity**
   (`mission_threads.py`, `stats.py`, `e11`/`e12`): compute each thread's
   physically-minimum latency given the swept constellation; flag threads
   infeasible at every tested configuration instead of averaging their
   zeros in. Add a full KM survival-curve function (not just the median).
   Sweep tolerance at 0.5x/1x/2x/4x.
4. **Re-test the headline** (`e12`): architecture comparisons only run in
   cells where the best architecture's success exceeds 30%; cells are
   labeled UNINFORMATIVE (floor effect) / SEPARATES (significant
   difference) / TIES (high success, no significant difference).
5. **Lock-in proxy** (`trade_study.py`): replaced with a count of
   provider-side functions and non-standard interfaces the Army would
   depend on, read from `docs/INTERFACES.md`'s function-to-segment table
   plus each architecture's conditional-logic flag.
6. Rerun e11/e12/trade_study, write `docs/V3_VS_V4.md`, rewrite
   `docs/ACQUISITION_IMPLICATIONS.md` and the README headline.

## Constraints carried over from v3

Outputs go in `results/frozen/v4/`; `results/frozen/v3/` is left untouched.
Every ADR from this pass is logged in `docs/DECISION_LOG.md`, continuing
from ADR-018. `paper/manuscript.md` is not touched (it's deleted).
`docs/NOVELTY.md` is ignored. No invented numbers.
