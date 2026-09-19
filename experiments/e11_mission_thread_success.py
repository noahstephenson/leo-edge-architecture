"""Experiment 11 (v3): Mission-thread success with paired trials, a real
collection-opportunity model, cadence-based MT-4, and A6 reported
separately from the original A0-A5 candidate set.

Fixes applied vs. v2 (docs/DECISION_LOG.md has the full ADRs):
- Paired trials: one shared (request_time_s, contact-denial draw) per
  trial index, reused across every architecture, so architecture
  comparisons are paired, not independently-sampled.
- Collection timing: a request must wait for the next real imaging pass
  over a notional AOI location (a second SGP4 access-window computation,
  not the ground terminal) before any downlink window can be used.
  v2 treated collection as instantaneous at request time.
- MT-3 (battle damage assessment) restored, modeled as needing a
  P3_ROI-sized change/difference product, gated on a per-trial
  prior-reference-availability draw.
- MT-4 fixed to match docs/MISSION_THREADS.md: cadence is evaluated per
  actual collection pass across the whole horizon (2+ consecutive misses
  = failure), not as a single request/response like MT-1/MT-2/MT-3.
- "Never produces the needed tier" (structural_incapacity) is recorded
  separately from "produced it too slowly" in every row.

This is the evidence results/frozen/v3/e11_mission_thread_success.csv that
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
from leo_edge.simulation import simulate_multi_contact
from leo_edge.mission_threads import MISSION_THREADS
from leo_edge.products import ProductTier
from leo_edge.stats import wilson_ci, paired_bootstrap_diff_ci

SCENE_BYTES = 1_000_000_000  # 1 GB notional area-of-interest scene
PROCESSING_TIME_S = 20.0
HORIZON_S = 168 * 3600.0  # matches the 1-week access-window generation
EPOCH = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

# Ground terminal location (downlink) is unchanged from v2. The AOI
# (imaging target) location is new in v3: a distinct point representing a
# tactical objective the terminal supports but isn't co-located with,
# offset 5 degrees in latitude and longitude from the terminal. This is a
# notional, documented choice (docs/DECISION_LOG.md), not a real geodesy
# claim; it's enough to make collection and downlink genuinely separate
# SGP4 passes instead of the same event.
GROUND_LAT, GROUND_LON = 40.0, 0.0
AOI_LAT, AOI_LON = 45.0, 5.0

# Probability a usable prior reference image exists for MT-3's change
# detection at request time. ASSUMED; see docs/MISSION_THREADS.md's MT-3
# dependency note and docs/DECISION_LOG.md.
PRIOR_REFERENCE_PROB = 0.5

ARCHITECTURE_FACTORIES = {
    "A0_GROUND_ONLY": lambda thread: GroundOnly(),
    "A1_COMPRESSED_FULL": lambda thread: CompressedFull(),
    "A2_QUICKLOOK_FIRST": lambda thread: QuicklookFirst(),
    "A3_ROI_FIRST": lambda thread: RoiFirst(),
    "A4_PROGRESSIVE": lambda thread: Progressive(),
    "A5_CONTACT_AWARE": lambda thread: ContactAware(),
    "A6_THREAD_AWARE_PRIORITY": lambda thread: ThreadAwarePriority(priority_tier=thread["needed_tier"]),
}

TERMINAL_CLASSES = {
    "VEHICLE_MOUNTED": {"rate_bps": 50_000_000},
    "DISMOUNTED_MANPACK": {"rate_bps": 5_000_000},
}

CONDITIONS = {
    "NOMINAL": {"interference_derate": 1.0, "contact_denial_frac": 0.0, "tasking_delay_s": 60},
    "INTERFERENCE": {"interference_derate": 0.5, "contact_denial_frac": 0.0, "tasking_delay_s": 60},
    "CONTACT_DENIAL": {"interference_derate": 1.0, "contact_denial_frac": 0.3, "tasking_delay_s": 60},
    "REACHBACK_LOST": {"interference_derate": 1.0, "contact_denial_frac": 0.0, "tasking_delay_s": 180},
    "COMBINED_DEGRADED": {"interference_derate": 0.5, "contact_denial_frac": 0.3, "tasking_delay_s": 180},
}

N_TRIALS = 300          # single-request threads (MT-1/2/3)
N_TRIALS_CADENCE = 30   # MT-4: each "trial" walks every pass in the whole horizon
SEED = 0


def _windows_since_epoch(ground_lat, ground_lon):
    access = generate_access_windows(
        ground_lat=ground_lat,
        ground_lon=ground_lon,
        min_elevation_deg=10.0,
        altitude_km=550.0,
        inclination_deg=97.4,
        duration_hours=168.0,
    )
    out = []
    for w in access:
        start = datetime.fromisoformat(w["start"].replace("Z", "+00:00"))
        offset_s = (start - EPOCH).total_seconds()
        out.append((offset_s, float(w["duration_s"])))
    return sorted(out, key=lambda pair: pair[0])


def _tier_index_for(architecture, needed_tier, scene_bytes, processing_time_s):
    try:
        tiers = architecture.tiers(scene_bytes, processing_time_s=processing_time_s)
    except TypeError:
        tiers = architecture.tiers(scene_bytes)
    return any(tier == needed_tier for tier, _bytes, _proc in tiers)


def _collection_complete_s(request_time_s, tasking_delay_s, aoi_windows):
    """First AOI overflight at/after tasking completes; collection finishes
    at the end of that pass. None if no AOI pass exists before the horizon
    ends (the request effectively times out)."""
    earliest = request_time_s + tasking_delay_s
    for start_s, dur_s in aoi_windows:
        if start_s >= earliest:
            return start_s + dur_s
    return None


def _usable_downlink(base_time_s, downlink_windows, denial_rolls, contact_denial_frac):
    usable = []
    for (start_s, dur_s), denial_roll in zip(downlink_windows, denial_rolls):
        if start_s < base_time_s:
            continue
        if denial_roll < contact_denial_frac:
            continue
        usable.append((start_s - base_time_s, dur_s))
    return usable


def draw_request_context(rng, downlink_windows):
    """One shared draw per trial, reused across every architecture so
    comparisons are paired, not independently sampled."""
    return {
        "request_time_s": rng.uniform(0.0, HORIZON_S - 3600.0),
        "denial_rolls": [rng.random() for _ in downlink_windows],
        "prior_reference_roll": rng.random(),
    }


def evaluate_single_request(factory, thread_key, thread, terminal_key, terminal, condition_key, condition,
                             ctx, trial_idx, downlink_windows, aoi_windows):
    architecture = factory(thread)
    arch_name = type(architecture).__name__
    architecture_supports_tier = _tier_index_for(architecture, thread["needed_tier"], SCENE_BYTES, PROCESSING_TIME_S)
    rate_bps = terminal["rate_bps"] * condition["interference_derate"]

    collection_complete_s = _collection_complete_s(
        ctx["request_time_s"], condition["tasking_delay_s"], aoi_windows
    )

    if thread_key == "MT3_BATTLE_DAMAGE_ASSESSMENT":
        has_reference = ctx["prior_reference_roll"] < PRIOR_REFERENCE_PROB
        tolerance_s = thread["latency_tolerance_s"] if has_reference else thread["no_reference_latency_tolerance_s"]
    else:
        has_reference = None
        tolerance_s = thread["latency_tolerance_s"]

    if collection_complete_s is None:
        return {
            "architecture": arch_name, "thread": thread_key, "terminal_class": terminal_key,
            "condition": condition_key, "trial_idx": trial_idx,
            "latency_s": float("nan"), "produced_tier": False,
            "structural_incapacity": not architecture_supports_tier,
            "success": False, "has_prior_reference": has_reference,
        }

    usable = _usable_downlink(
        collection_complete_s, downlink_windows, ctx["denial_rolls"], condition["contact_denial_frac"]
    )
    result = simulate_multi_contact(architecture, SCENE_BYTES, usable, rate_bps, PROCESSING_TIME_S)

    needed_tier_time_s = result.tier_completion_s.get(thread["needed_tier"].value)
    if needed_tier_time_s is None and thread["needed_tier"] == ProductTier.P4_FULL and result.completed:
        needed_tier_time_s = result.tcp_s

    if needed_tier_time_s is None:
        latency_s = float("nan")
        produced_tier = False
    else:
        # Total latency from the ORIGINAL request: wait for the AOI pass,
        # plus however long delivery took after collection completed.
        latency_s = (collection_complete_s - ctx["request_time_s"]) + needed_tier_time_s
        produced_tier = True

    structural_incapacity = not architecture_supports_tier
    success = (not structural_incapacity) and produced_tier and latency_s <= tolerance_s

    return {
        "architecture": arch_name, "thread": thread_key, "terminal_class": terminal_key,
        "condition": condition_key, "trial_idx": trial_idx,
        "latency_s": latency_s, "produced_tier": produced_tier,
        "structural_incapacity": structural_incapacity,
        "success": success, "has_prior_reference": has_reference,
    }


def evaluate_cadence(factory, thread, terminal_key, terminal, condition_key, condition,
                      denial_rolls, trial_idx, downlink_windows, aoi_windows):
    """MT-4: walk every real collection pass across the horizon; success
    requires never missing the per-pass tolerance twice in a row."""
    architecture = factory(thread)
    arch_name = type(architecture).__name__
    architecture_supports_tier = _tier_index_for(architecture, thread["needed_tier"], SCENE_BYTES, PROCESSING_TIME_S)
    rate_bps = terminal["rate_bps"] * condition["interference_derate"]

    if not architecture_supports_tier:
        return {
            "architecture": arch_name, "thread": "MT4_PERSISTENT_MONITORING",
            "terminal_class": terminal_key, "condition": condition_key, "trial_idx": trial_idx,
            "total_passes": 0, "passes_met": 0, "cadence_rate": 0.0,
            "structural_incapacity": True, "success": False,
        }

    misses_in_a_row = 0
    total_passes = 0
    passes_met = 0
    cadence_failed = False

    for pass_start_s, pass_dur_s in aoi_windows:
        collection_complete_s = pass_start_s + pass_dur_s
        usable = _usable_downlink(
            collection_complete_s, downlink_windows, denial_rolls, condition["contact_denial_frac"]
        )
        result = simulate_multi_contact(architecture, SCENE_BYTES, usable, rate_bps, PROCESSING_TIME_S)
        tier_time_s = result.tier_completion_s.get(thread["needed_tier"].value)
        total_passes += 1
        met = tier_time_s is not None and tier_time_s <= thread["latency_tolerance_s"]
        if met:
            passes_met += 1
            misses_in_a_row = 0
        else:
            misses_in_a_row += 1
            if misses_in_a_row >= 2:
                cadence_failed = True

    success = total_passes > 0 and not cadence_failed
    cadence_rate = passes_met / total_passes if total_passes else 0.0

    return {
        "architecture": arch_name, "thread": "MT4_PERSISTENT_MONITORING",
        "terminal_class": terminal_key, "condition": condition_key, "trial_idx": trial_idx,
        "total_passes": total_passes, "passes_met": passes_met, "cadence_rate": cadence_rate,
        "structural_incapacity": False, "success": success,
    }


def run_single_request_threads(rng, downlink_windows, aoi_windows):
    rows = []
    single_request_threads = {k: v for k, v in MISSION_THREADS.items() if not v["cadence"]}
    for thread_key, thread in single_request_threads.items():
        for terminal_key, terminal in TERMINAL_CLASSES.items():
            for condition_key, condition in CONDITIONS.items():
                for trial_idx in range(N_TRIALS):
                    ctx = draw_request_context(rng, downlink_windows)
                    for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                        rows.append(evaluate_single_request(
                            factory, thread_key, thread, terminal_key, terminal,
                            condition_key, condition, ctx, trial_idx, downlink_windows, aoi_windows,
                        ))
    return rows


def run_cadence_thread(rng, downlink_windows, aoi_windows):
    rows = []
    thread = MISSION_THREADS["MT4_PERSISTENT_MONITORING"]
    for terminal_key, terminal in TERMINAL_CLASSES.items():
        for condition_key, condition in CONDITIONS.items():
            for trial_idx in range(N_TRIALS_CADENCE):
                denial_rolls = [rng.random() for _ in downlink_windows]
                for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                    rows.append(evaluate_cadence(
                        factory, thread, terminal_key, terminal, condition_key, condition,
                        denial_rolls, trial_idx, downlink_windows, aoi_windows,
                    ))
    return rows


def summarize_single_request(rows):
    summary = {}
    for row in rows:
        key = (row["architecture"], row["thread"], row["terminal_class"], row["condition"])
        summary.setdefault(key, {"success": [], "structural_incapacity": []})
        summary[key]["success"].append(1 if row["success"] else 0)
        summary[key]["structural_incapacity"].append(1 if row["structural_incapacity"] else 0)

    out = []
    for (arch, thread, terminal, condition), vals in sorted(summary.items()):
        n = len(vals["success"])
        successes = sum(vals["success"])
        rate = successes / n
        lo, hi = wilson_ci(successes, n)
        structural_rate = sum(vals["structural_incapacity"]) / n
        out.append({
            "architecture": arch, "thread": thread, "terminal_class": terminal, "condition": condition,
            "n_trials": n, "successes": successes, "success_rate": rate,
            "success_rate_ci_lower": lo, "success_rate_ci_upper": hi,
            "structural_incapacity_rate": structural_rate,
        })
    return out


def summarize_cadence(rows):
    summary = {}
    for row in rows:
        key = (row["architecture"], row["terminal_class"], row["condition"])
        summary.setdefault(key, {"success": [], "structural_incapacity": [], "cadence_rate": []})
        summary[key]["success"].append(1 if row["success"] else 0)
        summary[key]["structural_incapacity"].append(1 if row["structural_incapacity"] else 0)
        summary[key]["cadence_rate"].append(row["cadence_rate"])

    out = []
    for (arch, terminal, condition), vals in sorted(summary.items()):
        n = len(vals["success"])
        successes = sum(vals["success"])
        rate = successes / n
        lo, hi = wilson_ci(successes, n)
        out.append({
            "architecture": arch, "thread": "MT4_PERSISTENT_MONITORING",
            "terminal_class": terminal, "condition": condition,
            "n_trials": n, "successes": successes, "success_rate": rate,
            "success_rate_ci_lower": lo, "success_rate_ci_upper": hi,
            "structural_incapacity_rate": sum(vals["structural_incapacity"]) / n,
            "mean_cadence_rate": sum(vals["cadence_rate"]) / n,
        })
    return out


def overall_pairwise_significance(all_rows):
    """Paired comparison of every architecture pair, aggregated across all
    single-request trials (paired within trial_idx per cell, then pooled).
    This is what docs/TRADE_STUDY.md's ranking should be checked against,
    and specifically answers the "A6 vs Progressive, tested not ranked"
    requirement."""
    by_arch = {}
    # Build (thread, terminal, condition, trial_idx) -> {arch: success} so
    # we only compare trials that are genuinely paired (same cell, same
    # trial index means same draw).
    by_cell_trial = {}
    for row in all_rows:
        cell_trial = (row["thread"], row["terminal_class"], row["condition"], row["trial_idx"])
        by_cell_trial.setdefault(cell_trial, {})[row["architecture"]] = 1 if row["success"] else 0

    arch_names = sorted({row["architecture"] for row in all_rows})
    paired_series = {a: [] for a in arch_names}
    for cell_trial, outcomes in sorted(by_cell_trial.items()):
        if len(outcomes) != len(arch_names):
            continue  # incomplete cell (shouldn't happen), skip for safety
        for a in arch_names:
            paired_series[a].append(outcomes[a])

    results = []
    for i, a in enumerate(arch_names):
        for b in arch_names[i + 1:]:
            diff, lo, hi, significant = paired_bootstrap_diff_ci(paired_series[a], paired_series[b], seed=SEED)
            n = len(paired_series[a])
            results.append({
                "architecture_a": a, "architecture_b": b, "n_paired_trials": n,
                "successes_a": sum(paired_series[a]), "successes_b": sum(paired_series[b]),
                "diff_a_minus_b": diff, "diff_ci_lower": lo, "diff_ci_upper": hi,
                "significant": significant,
            })
    return results


def main():
    rng = random.Random(SEED)
    downlink_windows = _windows_since_epoch(GROUND_LAT, GROUND_LON)
    aoi_windows = _windows_since_epoch(AOI_LAT, AOI_LON)
    print(f"Downlink windows (1 week): {len(downlink_windows)}")
    print(f"AOI overflight windows (1 week): {len(aoi_windows)}")

    single_rows = run_single_request_threads(rng, downlink_windows, aoi_windows)
    cadence_rows = run_cadence_thread(rng, downlink_windows, aoi_windows)

    trial_out = Path("results/raw/e11_mission_thread_trials.csv")
    trial_out.parent.mkdir(parents=True, exist_ok=True)
    with trial_out.open("w", newline="") as f:
        fieldnames = ["architecture", "thread", "terminal_class", "condition", "trial_idx",
                      "latency_s", "produced_tier", "structural_incapacity", "success", "has_prior_reference"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(single_rows)

    cadence_trial_out = Path("results/raw/e11_cadence_trials.csv")
    with cadence_trial_out.open("w", newline="") as f:
        fieldnames = ["architecture", "thread", "terminal_class", "condition", "trial_idx",
                      "total_passes", "passes_met", "cadence_rate", "structural_incapacity", "success"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cadence_rows)

    # MT-1/2/3 (single-request) and MT-4 (cadence) track different fields
    # (cadence has no latency_s or per-request success in the same sense),
    # so they get separate summary files rather than a lossy merged schema.
    summary_rows = summarize_single_request(single_rows)
    summary_out = Path("results/raw/e11_mission_thread_success.csv")
    with summary_out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    cadence_summary_rows = summarize_cadence(cadence_rows)
    cadence_summary_out = Path("results/raw/e11_cadence_success.csv")
    with cadence_summary_out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(cadence_summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(cadence_summary_rows)

    sig_rows = overall_pairwise_significance(single_rows)
    sig_out = Path("results/raw/e11_significance_tests.csv")
    with sig_out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(sig_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sig_rows)

    print(f"\nSaved {len(single_rows)} single-request trial rows to {trial_out}")
    print(f"Saved {len(cadence_rows)} cadence trial rows to {cadence_trial_out}")
    print(f"Saved {len(summary_rows)} summary rows to {summary_out}")
    print(f"Saved {len(cadence_summary_rows)} cadence summary rows to {cadence_summary_out}")
    print(f"Saved {len(sig_rows)} pairwise significance rows to {sig_out}")

    print("\nOverall significant pairwise differences (95% CI excludes 0):")
    for r in sig_rows:
        if r["significant"]:
            print(f"  {r['architecture_a']:20s} vs {r['architecture_b']:20s}: "
                  f"diff={r['diff_a_minus_b']:+.4f} [{r['diff_ci_lower']:+.4f}, {r['diff_ci_upper']:+.4f}] "
                  f"({r['successes_a']} vs {r['successes_b']} of {r['n_paired_trials']})")

    a6_vs_prog = [r for r in sig_rows
                  if {r["architecture_a"], r["architecture_b"]} == {"ThreadAwarePriority", "Progressive"}]
    if a6_vs_prog:
        r = a6_vs_prog[0]
        print(f"\nA6 (ThreadAwarePriority) vs Progressive, explicitly: "
              f"{r['successes_a' if r['architecture_a']=='ThreadAwarePriority' else 'successes_b']} vs "
              f"{r['successes_b' if r['architecture_a']=='ThreadAwarePriority' else 'successes_a']} "
              f"of {r['n_paired_trials']} paired trials, significant={r['significant']}")


if __name__ == "__main__":
    main()
