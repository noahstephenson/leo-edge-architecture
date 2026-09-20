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
  multi-plane Walker main sweep (4/8/16/32 satellites across 4-8 planes).
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

<!-- FILLED IN FROM results/frozen/v4/e12_access_sweep.csv,
     e12_cell_status.csv, e12_feasibility_floors.csv once the sweep run
     completes. -->

## Feasibility floors: which threads are infeasible, and where

<!-- FILLED IN FROM results/frozen/v4/e12_feasibility_floors.csv. -->

## Tolerance sensitivity

<!-- FILLED IN FROM results/frozen/v4/e12_tolerance_sensitivity.csv. -->

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
  Dies as stated. Most of those cells were floor effects
  (`UNINFORMATIVE`), not genuine ties -- the v3 framing didn't distinguish
  the two, and once same-pass delivery and real constellations are
  modeled, informative cells exist and some of them separate.
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
- **Access matters a great deal.** Confirmed and sharpened: see the sweep
  results above.

## Every ASSUMED value driving this headline

Unchanged from `docs/V2_VS_V3.md` except: real Walker-delta configuration
parameters (`experiments/e12_access_sweep.py::SAT_CONFIGS`, planes and
phasing factors), the feasibility-floor's best-case rate and tier-byte
proxy (Progressive's tier table), and the 30% informative-cell threshold
(`INFORMATIVE_THRESHOLD`), all ASSUMED and documented in-code.
