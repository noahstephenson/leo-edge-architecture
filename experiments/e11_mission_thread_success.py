"""Experiment 11: Mission-thread success under terminal class and contested conditions.

Evaluates each architecture (A0-A6) against each mission thread
(docs/MISSION_THREADS.md), each terminal class, and each degradation
condition, over real SGP4 contact windows with the tasking-path delay
added to total latency (time measured from user need, not capture). Success
is a boolean: did the thread's first-needed product tier arrive within its
latency tolerance. Aggregated into a success rate per condition with a
bootstrap confidence interval, using the same approach as
scripts/compute_confidence_intervals.py.

This is the evidence results/frozen/v2/mission_thread_success.csv that
docs/TRADE_STUDY.md's mission-thread-success criterion is built from.
"""

import csv
import random
from pathlib import Path
from datetime import datetime, timezone

from leo_edge.architectures import (
    GroundOnly,
    CompressedFull,
    QuicklookFirst,
    RoiFirst,
    Progressive,
    ContactAware,
    ThreadAwarePriority,
)
from leo_edge.orbit.access import generate_access_windows
from leo_edge.simulation import contact_windows_from_access_windows, simulate_multi_contact
from leo_edge.products import ProductTier

SCENE_BYTES = 1_000_000_000  # 1 GB notional area-of-interest scene
PROCESSING_TIME_S = 20.0

# Each factory takes the active mission thread's spec and returns a fresh
# architecture instance. A6 needs the thread's needed_tier at construction
# time (its whole point is reordering around it); the others ignore it.
ARCHITECTURE_FACTORIES = {
    "A0_GROUND_ONLY": lambda thread: GroundOnly(),
    "A1_COMPRESSED_FULL": lambda thread: CompressedFull(),
    "A2_QUICKLOOK_FIRST": lambda thread: QuicklookFirst(),
    "A3_ROI_FIRST": lambda thread: RoiFirst(),
    "A4_PROGRESSIVE": lambda thread: Progressive(),
    "A5_CONTACT_AWARE": lambda thread: ContactAware(),
    "A6_THREAD_AWARE_PRIORITY": lambda thread: ThreadAwarePriority(priority_tier=thread["needed_tier"]),
}

# MT-1/MT-2/MT-4 first-needed tiers and latency tolerances from
# docs/MISSION_THREADS.md. MT-3 (change detection) is not modeled here: no
# architecture implements a stored-prior-reference / difference product
# (docs/ALLOCATION_SPACE.md's uncovered-regions list), so MT-3 is left out
# rather than faked.
MISSION_THREADS = {
    "MT1_TIME_SENSITIVE_CUEING": {"needed_tier": ProductTier.P2_QUICKLOOK, "latency_tolerance_s": 120},
    "MT2_ROUTE_RECON_FIRST": {"needed_tier": ProductTier.P3_ROI, "latency_tolerance_s": 900},
    "MT4_PERSISTENT_MONITORING": {"needed_tier": ProductTier.P1_THUMBNAIL, "latency_tolerance_s": 300},
}

TERMINAL_CLASSES = {
    "VEHICLE_MOUNTED": {"rate_bps": 50_000_000},
    "DISMOUNTED_MANPACK": {"rate_bps": 5_000_000},
}

# docs/MISSION_THREADS.md contested/DDIL and tasking-path parameters.
CONDITIONS = {
    "NOMINAL": {"interference_derate": 1.0, "contact_denial_frac": 0.0, "tasking_delay_s": 60},
    "INTERFERENCE": {"interference_derate": 0.5, "contact_denial_frac": 0.0, "tasking_delay_s": 60},
    "CONTACT_DENIAL": {"interference_derate": 1.0, "contact_denial_frac": 0.3, "tasking_delay_s": 60},
    "REACHBACK_LOST": {"interference_derate": 1.0, "contact_denial_frac": 0.0, "tasking_delay_s": 180},
    "COMBINED_DEGRADED": {"interference_derate": 0.5, "contact_denial_frac": 0.3, "tasking_delay_s": 180},
}

N_TRIALS = 200
SEED = 0


def _base_windows():
    access = generate_access_windows(
        ground_lat=40.0,
        ground_lon=0.0,
        min_elevation_deg=10.0,
        altitude_km=550.0,
        inclination_deg=97.4,
        duration_hours=168.0,
    )
    capture_time = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return contact_windows_from_access_windows(access, capture_time)


def _apply_condition(windows, condition, rng):
    kept = []
    for start_s, duration_s in windows:
        if rng.random() < condition["contact_denial_frac"]:
            continue
        kept.append((start_s, duration_s))
    return kept


def _tier_index_for(architecture, needed_tier, scene_bytes, processing_time_s):
    try:
        tiers = architecture.tiers(scene_bytes, processing_time_s=processing_time_s)
    except TypeError:
        tiers = architecture.tiers(scene_bytes)
    for i, (tier, _bytes, _proc) in enumerate(tiers):
        if tier == needed_tier:
            return True
    return False


HORIZON_S = 168 * 3600.0  # matches the 1-week access-window generation


def run_trial(factory, thread_key, terminal_key, condition_key, rng, base_windows):
    thread = MISSION_THREADS[thread_key]
    terminal = TERMINAL_CLASSES[terminal_key]
    condition = CONDITIONS[condition_key]

    rate_bps = terminal["rate_bps"] * condition["interference_derate"]
    tasking_delay_s = condition["tasking_delay_s"]

    architecture = factory(thread)
    # Use the class name (e.g. "GroundOnly"), not the A-prefixed factory
    # key, so this matches e03_results.csv's architecture_name column and
    # scripts/trade_study.py's ARCHITECTURES list. Using the A-prefixed
    # key here was tried and caught during this same change (before ever
    # being committed): it would have silently never matched e03/
    # trade_study.py, making mission_thread_success and resilience always
    # fall back to 0 for every architecture.
    arch_name = type(architecture).__name__
    architecture_supports_tier = _tier_index_for(architecture, thread["needed_tier"], SCENE_BYTES, PROCESSING_TIME_S)

    # The user's request can land at any point in the week's contact
    # schedule; the clock starts at request time, not at a fixed epoch.
    # Collection can't begin, and so no contact window is usable, until
    # tasking has completed (request time + tasking delay).
    request_time_s = rng.uniform(0.0, HORIZON_S - 3600.0)
    earliest_usable_s = request_time_s + tasking_delay_s
    usable = [
        (start_s - request_time_s, dur)
        for start_s, dur in base_windows
        if start_s >= earliest_usable_s
    ]
    usable = _apply_condition(usable, condition, rng)

    result = simulate_multi_contact(architecture, SCENE_BYTES, usable, rate_bps, PROCESSING_TIME_S)

    needed_tier_time_s = result.tier_completion_s.get(thread["needed_tier"].value)
    if needed_tier_time_s is None and thread["needed_tier"] == ProductTier.P4_FULL and result.completed:
        needed_tier_time_s = result.tcp_s

    if needed_tier_time_s is None:
        success = False
        latency_s = float("nan")
    else:
        # needed_tier_time_s is already measured from request_time_s, so it
        # already includes both the tasking delay and the wait for the
        # first usable contact.
        latency_s = needed_tier_time_s
        success = architecture_supports_tier and latency_s <= thread["latency_tolerance_s"]

    return {
        "architecture": arch_name,
        "thread": thread_key,
        "terminal_class": terminal_key,
        "condition": condition_key,
        "latency_s": latency_s,
        "success": success,
    }


def bootstrap_ci(successes, n_resamples=2000, seed=SEED):
    n = len(successes)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    rate = sum(successes) / n
    means = []
    for _ in range(n_resamples):
        sample = [rng.choice(successes) for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * n_resamples)]
    hi = means[min(int(0.975 * n_resamples), n_resamples - 1)]
    return rate, lo, hi


def main():
    rng = random.Random(SEED)
    base_windows = _base_windows()
    print(f"Base contact windows (1 week, before degradation): {len(base_windows)}")

    rows = []
    for factory_id, factory in ARCHITECTURE_FACTORIES.items():
        for thread_key in MISSION_THREADS:
            for terminal_key in TERMINAL_CLASSES:
                for condition_key in CONDITIONS:
                    for _ in range(N_TRIALS):
                        rows.append(run_trial(factory, thread_key, terminal_key, condition_key, rng, base_windows))

    trial_out = Path("results/raw/e11_mission_thread_trials.csv")
    trial_out.parent.mkdir(parents=True, exist_ok=True)
    with trial_out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["architecture", "thread", "terminal_class", "condition", "latency_s", "success"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {}
    for row in rows:
        key = (row["architecture"], row["thread"], row["terminal_class"], row["condition"])
        summary.setdefault(key, []).append(1 if row["success"] else 0)

    summary_rows = []
    for (arch, thread, terminal, condition), successes in sorted(summary.items()):
        rate, lo, hi = bootstrap_ci(successes)
        summary_rows.append({
            "architecture": arch,
            "thread": thread,
            "terminal_class": terminal,
            "condition": condition,
            "n_trials": len(successes),
            "success_rate": rate,
            "success_rate_ci_lower": lo,
            "success_rate_ci_upper": hi,
        })

    summary_out = Path("results/raw/e11_mission_thread_success.csv")
    with summary_out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Saved {len(rows)} trial rows to {trial_out}")
    print(f"Saved {len(summary_rows)} summary rows to {summary_out}")
    print()
    print("Nominal condition, vehicle-mounted terminal, sample:")
    for r in summary_rows:
        if r["condition"] == "NOMINAL" and r["terminal_class"] == "VEHICLE_MOUNTED":
            print(f"  {r['architecture']:20s} {r['thread']:28s} success_rate={r['success_rate']:.2f} "
                  f"[{r['success_rate_ci_lower']:.2f}, {r['success_rate_ci_upper']:.2f}]")


if __name__ == "__main__":
    main()
