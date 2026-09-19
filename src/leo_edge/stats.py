"""Small, dependency-free statistics helpers shared by experiments/e11,
experiments/e12, and scripts/trade_study.py.

No scipy dependency; these are hand-rolled but standard techniques
(paired bootstrap, Kaplan-Meier), not novel statistics.
"""

import random
from typing import List, Optional, Sequence, Tuple


def paired_bootstrap_diff_ci(
    successes_a: Sequence[int],
    successes_b: Sequence[int],
    n_resamples: int = 2000,
    seed: int = 0,
) -> Tuple[float, float, float, bool]:
    """95% CI on the paired difference in success rate (a - b).

    successes_a/successes_b must be the same length and index-aligned:
    successes_a[i] and successes_b[i] come from the SAME trial i (same
    request time, same contact-denial draw), so this resamples trial
    indices, not individual outcomes, which is what makes the comparison
    paired rather than a naive two-sample test.

    Returns (point_diff, ci_lower, ci_upper, significant), where
    `significant` is True iff the 95% CI excludes 0.
    """
    n = len(successes_a)
    if n == 0 or n != len(successes_b):
        return float("nan"), float("nan"), float("nan"), False

    point_diff = (sum(successes_a) - sum(successes_b)) / n

    rng = random.Random(seed)
    diffs = []
    for _ in range(n_resamples):
        sample = [rng.randrange(n) for _ in range(n)]
        a_rate = sum(successes_a[i] for i in sample) / n
        b_rate = sum(successes_b[i] for i in sample) / n
        diffs.append(a_rate - b_rate)
    diffs.sort()
    lo = diffs[int(0.025 * n_resamples)]
    hi = diffs[min(int(0.975 * n_resamples), n_resamples - 1)]
    significant = lo > 0 or hi < 0
    return point_diff, lo, hi, significant


def wilson_ci(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for a single proportion; more stable than a
    normal approximation at small n or extreme rates (both common here,
    since most cells have success rates near 0)."""
    if n == 0:
        return float("nan"), float("nan")
    p = successes / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    margin = (z * ((p * (1 - p) / n + z ** 2 / (4 * n ** 2)) ** 0.5)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def kaplan_meier_median(
    times_s: Sequence[float],
    censored: Sequence[bool],
    horizon_s: float,
) -> float:
    """Kaplan-Meier-style median time-to-event, treating censored
    observations as "survived at least to horizon_s" rather than dropping
    them (which is what averaging over completed-only does, and silently
    overstates how fast the fast-but-frequently-incomplete architectures
    really are).

    times_s: observed completion time for each trial, or horizon_s for
        censored trials (any real time up to horizon_s is fine as the
        recorded "last known survived" point; horizon_s is a reasonable
        default when no partial-progress time is available).
    censored: True where the trial never completed (censored at times_s).

    Returns the smallest time at which the survival function first drops
    to <= 0.5, or NaN if the survival function never drops that low
    (median is undefined, i.e. most trials never completed).
    """
    n = len(times_s)
    if n == 0:
        return float("nan")

    events = sorted(zip(times_s, censored), key=lambda pair: pair[0])
    at_risk = n
    survival = 1.0
    for t, is_censored in events:
        if not is_censored:
            survival *= (at_risk - 1) / at_risk
        at_risk -= 1
        if survival <= 0.5:
            return t
    return float("nan")
