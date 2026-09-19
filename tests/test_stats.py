"""Tests for src/leo_edge/stats.py's significance-testing helpers."""

import math

from leo_edge.stats import kaplan_meier_median, paired_bootstrap_diff_ci, wilson_ci


def test_paired_bootstrap_identical_arrays_never_significant():
    a = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0] * 20
    diff, lo, hi, significant = paired_bootstrap_diff_ci(a, a)
    assert diff == 0.0
    assert lo <= 0.0 <= hi
    assert significant is False


def test_paired_bootstrap_detects_large_real_difference():
    a = [1] * 180 + [0] * 20  # 90% success
    b = [1] * 20 + [0] * 180  # 10% success
    diff, lo, hi, significant = paired_bootstrap_diff_ci(a, b)
    assert diff > 0.5
    assert lo > 0
    assert significant is True


def test_paired_bootstrap_point_estimate_matches_raw_counts():
    """docs/DECISION_LOG.md/the v3 task cites 73 vs 69 successes out of
    6,000 paired trials as a gap that must be tested, not assumed
    significant either way. This checks the point estimate is exactly
    right; the actual significance call depends on how correlated real
    paired trials are (see test_paired_bootstrap_correlated_pairs_can_be_
    significant_at_small_gaps below), so it isn't hardcoded here."""
    n = 6000
    a = [1] * 73 + [0] * (n - 73)
    b = [1] * 69 + [0] * (n - 69)
    diff, lo, hi, significant = paired_bootstrap_diff_ci(a, b, seed=1)
    assert abs(diff - (73 - 69) / n) < 1e-9
    assert lo <= diff <= hi


def test_paired_bootstrap_independent_random_pairs_small_gap_not_significant():
    """When paired outcomes are only weakly correlated (close to
    independent), a 4-in-6000 gap should not clear significance -- this is
    the realistic case for architectures whose per-trial success barely
    depends on which architecture was used (e.g. both gated mostly by
    whether the request happened to land near a pass, not by the
    architecture itself)."""
    import random

    rng = random.Random(7)
    n = 6000
    a = [1 if rng.random() < 73 / n else 0 for _ in range(n)]
    b = [1 if rng.random() < 69 / n else 0 for _ in range(n)]
    diff, lo, hi, significant = paired_bootstrap_diff_ci(a, b, seed=1)
    assert significant is False


def test_wilson_ci_bounds_are_sane():
    lo, hi = wilson_ci(50, 100)
    assert 0.0 < lo < 0.5 < hi < 1.0
    lo0, hi0 = wilson_ci(0, 100)
    assert lo0 == 0.0
    assert hi0 < 0.1


def test_kaplan_meier_median_all_events_matches_plain_median():
    times = [10.0, 20.0, 30.0, 40.0, 50.0]
    censored = [False] * 5
    assert kaplan_meier_median(times, censored, horizon_s=1000.0) == 30.0


def test_kaplan_meier_median_undefined_when_majority_censored():
    times = [10.0, 1000.0, 1000.0, 1000.0, 1000.0]
    censored = [False, True, True, True, True]
    result = kaplan_meier_median(times, censored, horizon_s=1000.0)
    assert math.isnan(result)


def test_kaplan_meier_median_with_some_censoring():
    # 3 events at 10, 20, 30; 2 censored at 1000 (never completed).
    # Survival drops below 0.5 at the 30s event (3rd of 5 at risk).
    times = [10.0, 20.0, 30.0, 1000.0, 1000.0]
    censored = [False, False, False, True, True]
    result = kaplan_meier_median(times, censored, horizon_s=1000.0)
    assert result == 30.0
