# v3 vs v4: what changed and which conclusions survive

`results/frozen/v3/` is left untouched. `results/frozen/v4/` is
regenerated with the fixes below (`docs/DECISION_LOG.md` ADR-019 through
ADR-022).

## The core methodological bugs, in one line each

1. v3's "access sweep" wasn't a constellation model: additional satellites
   were one satellite's access windows time-shifted by an orbital-period
   offset, which ignores Earth rotation and plane geometry entirely.
2. v3 modeled collection as complete at the END of the imaging pass, which
   made same-pass collect-and-downlink -- the defining capability of
   direct-to-edge -- structurally impossible, regardless of architecture
   or constellation size.
3. v3 had no feasibility floor: an infeasible thread's zeros were averaged
   into the results exactly like an ordinary, access-limited failure.
4. v3 labeled every cell that failed to show a significant architecture
   difference "no significant difference," whether that was because
   nothing worked (a floor effect) or because architectures were tested
   and genuinely tied.
5. v3's acquisition lock-in-risk criterion was a bare tier count, not
   explicitly tied to `docs/INTERFACES.md`'s real ownership-boundary
   table.

## Retraction: the "single-plane precession clustering" explanation is wrong

`docs/V2_VS_V3.md` explained v3's 32-satellite success-rate drop as a real
property of single-plane phasing (satellites clustering into bursts of
close passes separated by long gaps). That explanation was built entirely
on the flawed time-shift approximation and is retracted
(`docs/DECISION_LOG.md` ADR-019): it explained an artifact of the
approximation as if it were orbital mechanics. Once satellites are
propagated with real, distinct RAAN/mean-anomaly (i.e. actually different
orbits), there is no reason to expect that pattern, and the real Walker
sweep below does not show it.

## What changed in the evaluation engine

- **Real Walker-delta constellations.** `orbit/constellation.py::generate_walker_delta_tles`
  builds one real synthetic TLE per satellite (distinct RAAN across
  planes, distinct mean anomaly within a plane, standard T/P/F notation);
  `per_satellite_access_windows` propagates each one independently with
  real SGP4. `orbit/access.py`'s elevation scan was vectorized to keep
  this tractable. The sweep (`experiments/e12_access_sweep.py`) covers
  single-plane comparison points (1/2/4 satellites, 1 plane) and a
  multi-plane Walker main sweep (4/8/16/24 satellites across 4-8 planes; 24 is the largest that completed, see the stopping-point note below).
- **Same-pass collect-and-downlink.** Collection now happens at the AOI
  pass's time of closest approach (`"peak"`, a new field on every access
  window), not pass end, and downlink is tracked per satellite: an image
  can only be downlinked by the satellite that collected it, using any of
  that satellite's downlink windows still open after collection --
  including the remaining portion of the collecting pass itself.
- **Feasibility floors.** Each mission thread's physically minimum
  achievable latency (minimum tasking delay + processing time + minimal
  transmit time at the best rate, ignoring access entirely) is now
  computed and compared against its tolerance. A thread whose floor
  already exceeds tolerance is flagged `INFEASIBLE_STRUCTURAL` -- no
  constellation size can ever save it -- distinct from
  `INFEASIBLE_AT_THIS_ACCESS` (feasible in principle, not yet at this
  configuration's revisit rate).
- **Informative-cell testing.** Architecture comparisons only run where
  the best architecture's success rate exceeds 30%. Every cell is labeled
  `UNINFORMATIVE` (floor effect), `TIES` (tested, no significant
  difference), or `SEPARATES` (a real, significant winner).
- **Ownership-boundary lock-in proxy.** `acquisition_lock_in_risk` is now
  explicitly justified against `docs/INTERFACES.md`'s function-to-segment
  table: non-metadata tier count (named data-format interfaces) plus a
  higher weight (2, up from 1) for per-request conditional logic, since a
  runtime decision is a non-standard interface in a way a fixed format
  isn't.

## Same-pass delivery, isolated at the single-satellite baseline

Isolated comparison (Progressive, MT-1, VEHICLE_MOUNTED, NOMINAL, 500
trials, `experiments/e11_mission_thread_success.py::report_same_pass_effect`):

| | v3 (collection at pass end) | v4 (collection at closest approach, same-pass allowed) |
|---|---|---|
| Successes | 0/500 | 1/500 |
| Mean latency (trials that produced the tier) | ~26,900s | ~16,900s |

Across the full paired-trial baseline run, this fix alone moves
ThreadAwarePriority's success count from **7/9000 (0.08%, v3)** to
**142/9000 (1.6%, v4)**. More importantly, v3's top three architectures
were tied EXACTLY (7 vs. 7 vs. 7); v4's baseline shows real, statistically
significant separation:

| Comparison | v4 result |
|---|---|
| ThreadAwarePriority vs. Progressive | 142 vs. 129 of 9,000, **significant** |
| Progressive vs. RoiFirst | 129 vs. 109 of 9,000, **significant** |
| ThreadAwarePriority vs. RoiFirst | 142 vs. 109 of 9,000, **significant** |
| Progressive vs. QuicklookFirst | 129 vs. 2 of 9,000, **significant** |

GroundOnly, CompressedFull, and ContactAware remain at exactly 0
successes (structurally incapable of ever producing an early tier),
unchanged from v3.

## The access sweep: real Walker constellations

Pooled success rate of the best architecture per cell (all threads,
terminal classes, and both swept conditions; 40 trials per thread-cell, so
expect roughly +/-3pp of sampling noise; source:
`results/frozen/v4/e12_access_sweep.csv`):

| Constellation (sats/planes) | 1 terminal | 2 terminals | 4 terminals |
|---|---|---|---|
| 1/1 | 3.2% | 3.8% | 4.0% |
| 2/1 (single plane) | 4.2% | 4.8% | 4.8% |
| 4/1 (single plane) | 6.9% | 6.7% | 7.3% |
| 4/4 (Walker) | 8.7% | 8.5% | 7.5% |
| 8/4 (Walker) | 7.9% | 10.5% | 6.2% |
| 16/4 (Walker) | 17.7% | 18.5% | 22.6% |
| 24/8 (Walker) | 19.8% | 27.4% | **31.2%** |

- **Success rises with real constellation size**, from ~3% (1 satellite)
  to ~31% (24 satellites, 8 planes, 4 terminals). It never reaches the
  50% the task named as the minimum "substantial" level. **The sweep
  stopped at 24 satellites**: a 32-satellite/8-plane run was killed by
  host memory pressure (not a code failure), and 24 was the largest
  configuration that completed reliably (ADR-023). Whether 50-90% is
  reached at larger sizes is not tested here and is not extrapolated.
- **The 8/4 row is not monotonic** (4 terminals: 6.2%, below 2
  terminals' 10.5%). That is sampling noise at 40 trials per cell, not a
  finding.
- **Single-plane vs. Walker at 4 satellites** (6.9-7.3% vs. 7.5-8.7%) is
  within noise; this sweep does not resolve a plane-geometry effect at
  that size.
- **Only 1 of 21 cells is informative** (best architecture > 30%):
  24 satellites/8 planes/4 terminals. The other 20 are `UNINFORMATIVE`
  (`figures/fig20.png`). In the one informative cell (504 paired trials),
  ThreadAwarePriority (31.2%) and Progressive (30.8%) are **not**
  significantly different from each other (-0.4pp), so the strict label is
  `TIES`; but both beat RoiFirst significantly (by 7.1pp and 6.7pp) and
  every other architecture by 24-31pp. RoiFirst never succeeds MT-4
  (0/24 vs. 12/24 for Progressive and ThreadAwarePriority). So once access
  is high enough for anything to work, the architectures do separate,
  just not at the top: the two full-tier designs tie and beat the rest.
  This rests on a single cell only slightly above the 30% threshold.

Kaplan-Meier latency at that cell (`e12_km_summary.csv`, censored at the
168h horizon): the time by which half the trials had delivered the needed
tier is ~905s for ThreadAwarePriority and ~922s for Progressive, versus
~6,607s for RoiFirst; QuicklookFirst never reaches half. ThreadAwarePriority
and Progressive deliver in every trial within the horizon (final survival
0.0); RoiFirst leaves 34% of trials undelivered and QuicklookFirst 67%.

## Feasibility floors: which threads are infeasible, and where

`results/frozen/v4/e12_feasibility_floors.csv`. The structural floor
(minimum tasking delay + processing + minimal transmit at the best rate,
ignoring access) is 80-88s for every thread, below every tolerance
(shortest: MT-1, 120s). **No thread is structurally infeasible**: none is
impossible at every access level regardless of constellation size.

The revisit-aware floor adds half the median gap between AOI collection
opportunities across the constellation (a heuristic, not a bound). On it:
**MT-1 (120s) and MT-4 (300s) are infeasible at every configuration
swept** (revisit floors of 440-2,930s), i.e. their tolerances are shorter
than the typical wait for the next overflight even at 24 satellites. MT-2
is feasible at 4/1, 16/4, and 24/8; MT-3 only at 16/4. The heuristic is
coarse (feasibility is not monotonic in satellite count because the
median gap depends on plane geometry), and MT-1 still succeeded in 2 of
160 trials at 24 satellites by lucky alignment, so "infeasible" here means
"needs luck," not "impossible." The pooled rates above still include
these threads' near-zeros; they are flagged here rather than hidden.

## Tolerance sensitivity

`results/frozen/v4/e12_tolerance_sensitivity.csv`, 1 terminal, pooled
over all seven architectures (so absolute values are low; compare across
columns, not to the best-architecture table above):

| Satellites | Thread | 0.5x | 1x | 2x | 4x |
|---|---|---|---|---|---|
| 1 | MT-1 | 0.0% | 0.0% | 0.0% | 0.0% |
| 1 | MT-2 | 0.0% | 0.8% | 1.8% | 4.9% |
| 1 | MT-3 | 0.0% | 0.3% | 0.6% | 1.5% |
| 24 | MT-1 | 0.0% | 0.8% | 2.1% | 9.6% |
| 24 | MT-2 | 7.2% | 12.9% | 17.0% | 17.4% |
| 24 | MT-3 | 2.3% | 8.8% | 16.3% | 20.0% |

Loosening tolerances raises success but does not change the conclusion:
MT-1 stays at 0% at one satellite even at 4x (480s), and no thread
approaches 50% even at 24 satellites and 4x tolerance, so the failure is
not just an artifact of the assumed thresholds. Run at the baseline and
largest configuration only, not every cell (scope note in
`e12_access_sweep.py`).

## Lock-in proxy: does the RoiFirst flip survive?

Yes. Under the new ownership-boundary-based proxy (non-metadata tier count
plus a doubled weight for conditional logic), RoiFirst (2 tiers, no
conditional logic, lock-in score 2) still wins the `COMBINED` ranking in
every stakeholder profile. ThreadAwarePriority's score gets *worse* under
the new proxy (4 tiers + 2 for conditional logic = 6, vs. v3's 4+1=5),
widening rather than closing its `COMBINED` gap to RoiFirst. This flip was
never an artifact of the old tier-count proxy; it reflects a real
structural property (RoiFirst genuinely has the fewest, simplest
interfaces among the architectures that can ever succeed a mission
thread).

## Which v3 conclusions die

- **"17 of 18 cells show no significant difference" as the headline.**
  Dies as stated. Those cells were floor effects, not genuine ties; in v4
  20 of 21 cells are still `UNINFORMATIVE`, but that is now stated as
  "not testable," and the one informative cell shows real separation
  below the top pair (see above).
- **"Processing architecture is second-order."** Not supported as stated.
  At the single-satellite baseline, differences among the tiered
  architectures are already statistically significant (N=9,000), and at
  the one informative cell the top two beat RoiFirst by ~7pp and
  everything else by 24-31pp. By magnitude, access still moves success
  more (~3% to ~31%) than choosing among tiered architectures (~7pp), and
  tiering itself is decisive (0% vs. ~31%). What the data supports is
  "access moves success most; tiering is necessary; among tiered designs
  the differences are real but smaller."
- **v3's 16-satellite success peak and 32-satellite dip.** Both were
  artifacts of the time-shift approximation; the real sweep is roughly
  monotonic up to 24 satellites.
- **This pass's own first v4 sweep.** A TLE formatting bug (dropped
  column separator) parsed every satellite's mean anomaly as 0, co-locating
  satellites within a plane; that first sweep (all 21 cells uninformative,
  best ~13%) was invalid, discarded, and rerun after the fix
  (`tests/test_walker_tle.py`, ADR-024).
- **The single-plane clustering explanation for the 32-satellite dip.**
  Retracted outright (see above); it was a property of the flawed
  approximation, not of orbital mechanics.
- **The single-satellite baseline "exact tie" (7 vs. 7 vs. 7 successes).**
  Dies. The same-pass fix alone produces real separation at the same
  access level v3 called an exact tie.

## Which v3 conclusions survive

- **Structural incapacity.** GroundOnly, CompressedFull, and ContactAware
  remain unable to ever succeed a tiered mission thread, for the same
  structural reason (no early tier).
- **RoiFirst wins the COMBINED trade-study ranking.** Survives under an
  honestly re-derived, ownership-boundary-tied lock-in proxy, not just
  the old tier-count one.
- **Access matters a great deal.** Confirmed and sharpened: best-architecture
  success rises from ~3% (1 satellite) to ~31% (24 satellites, 8 planes,
  4 terminals) and had not saturated when the sweep stopped.

## Every ASSUMED value driving this headline

Unchanged from `docs/V2_VS_V3.md` except: real Walker-delta configuration
parameters (`experiments/e12_access_sweep.py::SAT_CONFIGS`, planes and
phasing factors), the feasibility-floor's best-case rate and tier-byte
proxy (Progressive's tier table), and the 30% informative-cell threshold
(`INFORMATIVE_THRESHOLD`), all ASSUMED and documented in-code.
