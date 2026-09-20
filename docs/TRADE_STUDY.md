# Trade Study

Multi-criteria evaluation of the seven candidate architectures
(`docs/ALLOCATION_SPACE.md`) against the stakeholder values in
`docs/STAKEHOLDERS.md`. Computed by `scripts/trade_study.py`, which writes
`results/frozen/v4/trade_study_scores.csv` and
`results/frozen/v4/trade_study_sensitivity.csv`. Re-run it after any
change to `results/frozen/v4/e03_results.csv` or
`results/frozen/v4/e11_mission_thread_trials.csv`.

**This document is about ranking the seven architectures against each
other. It is not the repository's headline result.** That's
`docs/ACQUISITION_IMPLICATIONS.md`'s access-sweep finding
(`experiments/e12_access_sweep.py`, `figures/fig20.png`). Read this
document as "which architecture would matter, on the occasions
architecture choice matters," not as "which architecture is good."

## Criteria, and how each is computed (v4: lock-in proxy fixed, `docs/DECISION_LOG.md` ADR-021)

Three criteria come directly from simulation; four are derived from real
architecture properties tied to `docs/INTERFACES.md`'s ownership boundary,
not hand-picked judgment numbers.

| Criterion | Type | Source and one-line derivation rule |
|---|---|---|
| Mission-thread success | Simulated | `e11_mission_thread_success.csv`, mean success rate across all threads/terminals/conditions |
| Latency | Simulated | Kaplan-Meier censored median over `e11_mission_thread_trials.csv`'s per-trial latency, censoring non-completions at the evaluation horizon (168h) instead of dropping them |
| Resilience | Simulated | `e11_mission_thread_success.csv`, mean success rate under degraded conditions only |
| Fidelity | Derived | Fraction of `e03_results.csv` rows delivered lossless (real `fidelity_lossy` field) |
| Space-segment processing burden | Derived | Real mean `processing_energy_j` from `e03_results.csv`: higher energy = more provider-side compute burden = worse |
| Terminal processing burden | Derived | Fraction of `e03_results.csv` rows with `processing_energy_j == 0`, i.e. raw/unprocessed delivery that pushes interpretation work onto the terminal = worse |
| Acquisition lock-in risk | Derived | Non-metadata tier count (named data-format interfaces in `docs/INTERFACES.md`) plus 2 (not 1) if the architecture has per-request conditional logic (`CONDITIONAL_LOGIC`), since a runtime decision is a non-standard interface in a way a fixed format spec isn't -- see ADR-021 |

Rankings are reported two ways: **SIMULATED_ONLY** (the three simulated
criteria only, renormalized to sum to 1.0) and **COMBINED** (all seven).
Every case where the two disagree on the top-ranked architecture is
reported explicitly below.

## Raw values

From `results/frozen/v4/trade_study_scores.csv`'s inputs (`scripts/trade_study.py`):

| Architecture | Mission-thread success | Resilience | Latency (KM median, s) | Fidelity (lossless frac.) | Space burden (mean J) | Terminal burden (raw frac.) | Lock-in score |
|---|---|---|---|---|---|---|---|
| GroundOnly | 0.000 | 0.000 | 604,800 (never) | 1.00 | 0 | 1.00 | 1 |
| CompressedFull | 0.000 | 0.000 | 604,800 (never) | 0.00 | 300 | 0.00 | 1 |
| QuicklookFirst | 0.000 | 0.000 | 604,800 (never) | 0.00 | 30 | 0.00 | 2 |
| RoiFirst | 0.012 | 0.009 | 35,587 | 0.00 | 300 | 0.00 | 2 |
| Progressive | 0.014 | 0.011 | 19,872 | 0.00 | 300 | 0.00 | 4 |
| ContactAware | 0.000 | 0.000 | 604,800 (never) | 0.33 | 200 | 0.33 | 3 |
| ThreadAwarePriority (A6) | 0.016 | 0.012 | 19,350 | 0.00 | 300 | 0.00 | 6 |

ContactAware's lock-in score rose from 2 (v3, tier count + 1 for
conditional logic) to 3 (v4, tier count + 2), and ThreadAwarePriority's
from 5 to 6, under the v4 ownership-boundary proxy (ADR-021); both remain
`CONDITIONAL_LOGIC = True`.

Mission-thread success roughly doubled to tripled across the tiered
architectures compared to v3's single-satellite baseline (v3: 0.078% tied
across RoiFirst/Progressive/ThreadAwarePriority; v4: 1.2%/1.4%/1.6%
respectively), driven entirely by the same-pass collect-and-downlink fix
(`docs/DECISION_LOG.md` ADR-020) -- not by any change to the architectures
themselves.

## Mission-thread success at the single-satellite baseline: real separation, not a tie

Unlike v3, where the top three architectures tied EXACTLY (7 vs. 7 vs. 7
successes out of 9,000 paired trials), v4's baseline shows genuine,
statistically significant separation
(`results/frozen/v4/e11_significance_tests.csv`,
`src/leo_edge/stats.py::paired_bootstrap_diff_ci`):

| Comparison | Result |
|---|---|
| ThreadAwarePriority vs. Progressive | 142 vs. 129 of 9,000, **significant** (diff +0.14pp) |
| Progressive vs. RoiFirst | 129 vs. 109 of 9,000, **significant** |
| ThreadAwarePriority vs. RoiFirst | 142 vs. 109 of 9,000, **significant** |
| Progressive vs. QuicklookFirst | 129 vs. 2 of 9,000, **significant** |

GroundOnly, CompressedFull, and ContactAware remain at exactly 0
successes: structurally incapable of ever producing an early tier,
unchanged from v3.

MT-4 (persistent monitoring) still scores 0% for every architecture at
this baseline: even the tiered architectures never sustain the required
cadence (no 2-consecutive-miss gap) across a full week at one satellite.

## Scored results by stakeholder weight profile

From `results/frozen/v4/trade_study_scores.csv`, `WITH_A6` architecture set:

| Profile | SIMULATED_ONLY top (normalized score) | COMBINED top | COMBINED full order |
|---|---|---|---|
| TACTICAL_USER_LEANING | ThreadAwarePriority (1.000, vs. Progressive 0.943) | **RoiFirst** (0.676) | RoiFirst, Progressive, ThreadAwarePriority, GroundOnly, QuicklookFirst, ContactAware, CompressedFull |
| ACQUISITION_LEANING | ThreadAwarePriority (1.000, vs. Progressive 0.936) | **RoiFirst** (0.678) | RoiFirst, Progressive, GroundOnly, ThreadAwarePriority, CompressedFull, QuicklookFirst, ContactAware |
| TERMINAL_OPERATOR_LEANING | ThreadAwarePriority (1.000, vs. Progressive 0.934) | **RoiFirst** (0.700) | RoiFirst, Progressive, ThreadAwarePriority, QuicklookFirst, CompressedFull, ContactAware, GroundOnly |
| BALANCED | ThreadAwarePriority (1.000, vs. Progressive 0.943) | **RoiFirst** (0.611) | RoiFirst, Progressive, ThreadAwarePriority, GroundOnly, QuicklookFirst, ContactAware, CompressedFull |

**`SIMULATED_ONLY` and `COMBINED` disagree on the top architecture in
every single profile, exactly as in v3.** Unlike v3 -- where
ThreadAwarePriority's `SIMULATED_ONLY` edge over Progressive was a
rounding-level artifact of two statistically tied architectures -- v4's
`SIMULATED_ONLY` edge (1.000 vs. 0.943 or lower) reflects a real,
statistically significant mission-thread-success and latency advantage
(see the baseline table above). `RoiFirst` still wins the `COMBINED` view
every time, because its smaller tier count (2, vs. Progressive's 4 and
ThreadAwarePriority's 4+2=6 under the new lock-in proxy) gives it a real
advantage on `acquisition_lock_in_risk` that outweighs its real but
smaller latency disadvantage (35,587s vs. ~19,400-19,900s KM median).

**This flip is not an artifact of the lock-in proxy.** `docs/DECISION_LOG.md`
ADR-021 replaced the bare tier-count proxy with one explicitly tied to
`docs/INTERFACES.md`'s ownership boundary (named data-format interfaces
plus a doubled weight for runtime conditional logic), and RoiFirst still
wins `COMBINED` in every profile -- its `COMBINED` gap over
ThreadAwarePriority is now *wider* than under the old proxy, since A6's
score got worse (6, up from 5) while RoiFirst's stayed the same (2).

## Weight-sensitivity: where rankings flip

`scripts/trade_study.py`'s sensitivity sweep (`trade_study_sensitivity.csv`,
COMBINED view, WITH_A6 set) varies each criterion's weight by up to
+/-0.30 around each profile's baseline. Real rank flips found:

- **Acquisition lock-in risk**, swept under every profile: the top
  architecture moves among GroundOnly, Progressive, RoiFirst, and
  ThreadAwarePriority depending on profile.
- **Fidelity**, swept under ACQUISITION_LEANING and BALANCED: flips
  between GroundOnly and RoiFirst -- GroundOnly is the only architecture
  that ever delivers a lossless product, despite never succeeding a
  mission thread at all. Under TACTICAL_USER_LEANING and
  TERMINAL_OPERATOR_LEANING, it flips between GroundOnly and
  ThreadAwarePriority instead.
- **Mission-thread success and resilience**, newly appearing as
  sensitivity flip points in v4 (not in v3, where these three
  architectures were tied): under BALANCED and TERMINAL_OPERATOR_LEANING,
  sweeping either criterion's weight moves the top architecture among
  Progressive, RoiFirst, and ThreadAwarePriority -- a direct consequence
  of the real separation the same-pass fix produced.
- **Space-segment processing burden**, swept under ACQUISITION_LEANING,
  BALANCED, and TERMINAL_OPERATOR_LEANING: flips between GroundOnly (or
  QuicklookFirst) and RoiFirst/ThreadAwarePriority, since GroundOnly does
  zero onboard processing.

No sweep ever brought CompressedFull or ContactAware to the top of any
profile.

## Resilience: still no graceful degradation

Nominal and degraded success rates remain close together for every
architecture at the single-satellite baseline (e.g. ThreadAwarePriority:
1.6% mean success, 1.2% mean resilience-under-degraded -- a real but
small gap, not the collapse-to-zero v3 showed at this access level). See
`docs/ACQUISITION_IMPLICATIONS.md` for whether this pattern holds across
the real Walker sweep.

## What this trade study does not show

It does not show that RoiFirst, Progressive, or ThreadAwarePriority are
good enough in an absolute sense: a 1.2-1.6% mission-thread success rate
at the single-satellite baseline is still not a working system. It also
does not show that RoiFirst is operationally "the best architecture": the
`COMBINED` ranking that favors it is driven by a real, code-derived
lock-in-risk advantage, not a mission-thread-success advantage --
ThreadAwarePriority and Progressive both beat it there, with statistical
significance. See `docs/ACQUISITION_IMPLICATIONS.md` for the real headline
(access, not architecture, dominates until a real access threshold is
crossed) and `docs/V3_VS_V4.md` for the full accounting of what changed
from v3.
