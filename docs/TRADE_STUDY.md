# Trade Study

Multi-criteria evaluation of the seven candidate architectures
(`docs/ALLOCATION_SPACE.md`) against the stakeholder values in
`docs/STAKEHOLDERS.md`. Computed by `scripts/trade_study.py`, which writes
`results/frozen/v3/trade_study_scores.csv` and
`results/frozen/v3/trade_study_sensitivity.csv`. Re-run it after any
change to `results/frozen/v3/e03_results.csv` or
`results/frozen/v3/e11_mission_thread_trials.csv`.

**This document is about ranking the seven architectures against each
other. It is not the repository's headline result.** That's
`docs/ACQUISITION_IMPLICATIONS.md`'s access-sweep finding
(`experiments/e12_access_sweep.py`, `figures/fig20.png`): across the 18
access levels tested, 17 show no statistically significant difference
between any pair of architectures at all. Read this document as "which
architecture would matter, on the rare occasions architecture choice
matters," not as "which architecture is good."

## Criteria, and how each is computed (v3 fix, `docs/DECISION_LOG.md` ADR-017)

Three criteria come directly from simulation; four are derived from real
architecture properties, not hand-picked judgment numbers.

| Criterion | Type | Source and one-line derivation rule |
|---|---|---|
| Mission-thread success | Simulated | `e11_mission_thread_success.csv`, mean success rate across all threads/terminals/conditions |
| Latency | Simulated | Kaplan-Meier censored median over `e11_mission_thread_trials.csv`'s per-trial latency, censoring non-completions at the evaluation horizon (168h) instead of dropping them |
| Resilience | Simulated | `e11_mission_thread_success.csv`, mean success rate under the degraded condition only |
| Fidelity | Derived | Fraction of `e03_results.csv` rows delivered lossless (real `fidelity_lossy` field) |
| Space-segment processing burden | Derived | Real mean `processing_energy_j` from `e03_results.csv`: higher energy = more provider-side compute burden = worse |
| Terminal processing burden | Derived | Fraction of `e03_results.csv` rows with `processing_energy_j == 0`, i.e. raw/unprocessed delivery that pushes interpretation work onto the terminal = worse |
| Acquisition lock-in risk | Derived | Each architecture's real tier count (`.tiers()`) plus 1 if it has per-request conditional logic (`CONDITIONAL_LOGIC`): more distinct provider-side functions = more to specify in a contract = worse |

v2's version of this table had a `terminal_swap_burden` criterion that
scored GroundOnly best (1.0): backwards, since GroundOnly does zero
onboard processing and pushes all interpretation work onto the Army
terminal. Fixed in v3 by splitting it into the two correctly-signed
burden criteria above. v2's fidelity and lock-in-risk were also
hand-picked numbers; both are now derived from code.

Rankings are reported two ways: **SIMULATED_ONLY** (the three simulated
criteria only, renormalized to sum to 1.0) and **COMBINED** (all seven).
Every case where the two disagree on the top-ranked architecture is
reported explicitly below, since that disagreement is exactly where
judgment-derived criteria are doing the work, not simulation.

## Raw values

From `results/frozen/v3/trade_study_scores.csv`'s inputs (`scripts/trade_study.py`):

| Architecture | Mission-thread success | Resilience | Latency (KM median, s) | Fidelity (lossless frac.) | Space burden (mean J) | Terminal burden (raw frac.) | Lock-in functions |
|---|---|---|---|---|---|---|---|
| GroundOnly | 0.000 | 0.000 | 604,800 (never) | 1.00 | 0 | 1.00 | 1 |
| CompressedFull | 0.000 | 0.000 | 604,800 (never) | 0.00 | 300 | 0.00 | 1 |
| QuicklookFirst | 0.000 | 0.000 | 604,800 (never) | 0.00 | 30 | 0.00 | 2 |
| RoiFirst | 0.001 | 0.001 | 45,679 | 0.00 | 300 | 0.00 | 2 |
| Progressive | 0.001 | 0.001 | 30,966 | 0.00 | 300 | 0.00 | 4 |
| ContactAware | 0.000 | 0.000 | 604,800 (never) | 0.33 | 200 | 0.33 | 2 |
| ThreadAwarePriority (A6) | 0.001 | 0.001 | 30,963 | 0.00 | 300 | 0.00 | 5 |

**A latency of 604,800 seconds (the full evaluation horizon) means the
Kaplan-Meier median is undefined: more than half of that architecture's
trials never completed at all.** That's true for four of the seven
architectures at this single-satellite/single-terminal baseline. Real
completion, when it happens, takes on the order of 30,000-46,000 seconds
(8.5-12.7 hours) from the original request, dominated by waiting for both
the AOI collection pass and the downlink pass (`docs/MODEL_REFERENCE.md`),
not by anything architecture-specific.

## Mission-thread success at the single-satellite baseline: near zero for everyone

At the single-satellite/single-terminal baseline (the same access level
v2 evaluated), mean mission-thread success rate is **0.078% for
Progressive, RoiFirst, and ThreadAwarePriority, tied exactly**, and 0%
for the other four architectures. Tested directly with a paired bootstrap
on the underlying trial data (`experiments/e11_mission_thread_success.py`'s
`overall_pairwise_significance`, `results/frozen/v3/e11_significance_tests.csv`):
Progressive vs. ThreadAwarePriority (the task's own example, generalized
to v3 data) shows **7 successes vs. 7 successes out of 9,000 paired
trials, a difference of exactly zero, not significant**. The pairs that
*are* statistically significant are exactly the "structurally incapable"
architectures (GroundOnly, CompressedFull, ContactAware, QuicklookFirst,
all 0 successes) against the three that can ever succeed (Progressive,
RoiFirst, ThreadAwarePriority, 7 successes each) -- i.e. tiering matters,
significantly; which specific tiered architecture is used does not, at
this access level.

MT-4 (persistent monitoring, evaluated separately via the cadence walk,
`docs/DECISION_LOG.md` ADR-015) scores exactly 0% for every architecture
at this baseline: even the architectures capable of an early tier never
sustain the required cadence (no 2-consecutive-miss gap) across a full
week at one satellite.

## Scored results by stakeholder weight profile

From `results/frozen/v3/trade_study_scores.csv` (four profiles from
`docs/STAKEHOLDERS.md`'s value conflicts, plus a balanced/equal-weight
baseline), `WITH_A6` architecture set:

| Profile | SIMULATED_ONLY top (normalized score) | COMBINED top | COMBINED full order |
|---|---|---|---|
| TACTICAL_USER_LEANING | ThreadAwarePriority (1.000, vs. Progressive 0.99999) | **RoiFirst** | RoiFirst, Progressive, ThreadAwarePriority, GroundOnly, ContactAware, QuicklookFirst, CompressedFull |
| ACQUISITION_LEANING | ThreadAwarePriority (1.000, vs. Progressive 0.99999) | **RoiFirst** | RoiFirst, Progressive, GroundOnly, ThreadAwarePriority, CompressedFull, QuicklookFirst, ContactAware |
| TERMINAL_OPERATOR_LEANING | ThreadAwarePriority (1.000, vs. Progressive 0.99999) | **RoiFirst** | RoiFirst, Progressive, ThreadAwarePriority, QuicklookFirst, CompressedFull, ContactAware, GroundOnly |
| BALANCED | ThreadAwarePriority (1.000, vs. Progressive 0.99999) | **RoiFirst** | RoiFirst, Progressive, ThreadAwarePriority, GroundOnly, QuicklookFirst, ContactAware, CompressedFull |

**`SIMULATED_ONLY` and `COMBINED` disagree on the top architecture in
every single profile.** ThreadAwarePriority's SIMULATED_ONLY edge over
Progressive is a rounding-level artifact of the Kaplan-Meier latency
median (30,963s vs. 30,966s) -- not a real difference: tested directly,
the two are tied exactly on the underlying paired trial counts (7
successes each, out of 9,000 paired trials, `results/frozen/v3/e11_significance_tests.csv`,
not significant). `RoiFirst` wins the `COMBINED` view every time, because
its smaller tier count (2, vs. Progressive's 4 and ThreadAwarePriority's
5) gives it a real, code-derived advantage on `acquisition_lock_in_risk`
even though all three are tied exactly on mission-thread success and
resilience (7 successes each, out of 9,000 paired trials, no significant
pairwise difference between any of the three -- `results/frozen/v3/e11_significance_tests.csv`).
RoiFirst's only real, measured disadvantage among the three is a slower
Kaplan-Meier median time-to-product when it does succeed (45,679s vs.
~30,965s), which is what drags its SIMULATED_ONLY score below the
Progressive/ThreadAwarePriority pair, not a lower success rate. This is
exactly the kind of flip item 2 of the v3 rework asked to be surfaced
explicitly rather than hidden inside one blended score: **the COMBINED
"winner" is a function of the derived acquisition_lock_in_risk criterion
outweighing a real but small latency difference, on top of a genuine,
statistically confirmed tie on whether these three architectures succeed
at all.**

## Weight-sensitivity: where rankings flip

`scripts/trade_study.py`'s sensitivity sweep (`trade_study_sensitivity.csv`,
COMBINED view, WITH_A6 set) varies each criterion's weight by up to
+/-0.30 around each profile's baseline. Real rank flips found:

- **Acquisition lock-in risk**, swept under every profile: the top
  architecture moves among GroundOnly, RoiFirst, and ThreadAwarePriority.
- **Fidelity**, swept under every profile: flips between GroundOnly and
  RoiFirst -- GroundOnly is the only architecture that ever delivers a
  lossless product (raw bytes), which matters once fidelity is weighted
  heavily, despite GroundOnly never succeeding a mission thread at all.
- **Space-segment processing burden**, swept under ACQUISITION_LEANING,
  BALANCED, and TERMINAL_OPERATOR_LEANING: flips between GroundOnly (or
  QuicklookFirst) and RoiFirst, for the same reason -- GroundOnly does
  zero onboard processing.
- **Terminal SWaP burden**: no longer produces a GroundOnly-favoring flip
  (the v2 inversion bug is fixed); GroundOnly now correctly scores worst,
  not best, on this criterion.

No sweep ever brought CompressedFull, ContactAware, or QuicklookFirst to
the top of any profile.

## Resilience: no graceful degradation, at any access level tested

None of the seven architectures degrade gracefully in the sense of "still
succeeds under contested conditions when it couldn't under nominal ones."
At the single-satellite baseline, nominal and degraded success rates are
both effectively zero for every architecture (there is no room to degrade
further). The access sweep (`docs/ACQUISITION_IMPLICATIONS.md`) confirms
this pattern holds at every access level tested, not just the baseline:
degraded conditions never produce a graceful-vs-catastrophic split between
architectures.

## What this trade study does not show

It does not show that RoiFirst, Progressive, or ThreadAwarePriority are
good enough in an absolute sense -- a 0.078% mission-thread success rate
at the baseline access level is not a system that works. It also does not
show that RoiFirst is operationally "the best architecture": the
`COMBINED` ranking that favors it is driven entirely by a derived
lock-in-risk criterion counting provider-side functions, not by any
measured performance advantage, since the three top architectures are
tied on every simulated criterion. See `docs/ACQUISITION_IMPLICATIONS.md`
for the actual headline finding (access density, not architecture,
dominates) and `docs/V2_VS_V3.md` for the full accounting of what changed
from v2.
