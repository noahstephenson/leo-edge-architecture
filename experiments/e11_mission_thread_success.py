"""Experiment 11 (v4): Mission-thread success with same-pass delivery and
per-satellite collection/downlink tracking.

Fixes applied vs. v3 (docs/DECISION_LOG.md ADR-020 has the full ADR):
- Collection timing: a request's image is now collected at the AOI pass's
  time of closest approach ("peak", orbit/access.py), not at pass end. v3
  used pass end, which meant a request could never be delivered on the
  same orbital pass that collected it -- the defining capability of
  direct-to-edge.
- Downlink is now tracked per satellite. A request's image can only be
  downlinked by the SATELLITE THAT COLLECTED IT (no crosslink model here;
  see docs/DECISION_LOG.md if one is ever added as a separate, documented
  option), using any of that satellite's own downlink windows still open
  after collection -- including the remaining portion of the very pass
  that did the collection.
- All of this runs against real per-satellite SGP4 windows
  (orbit/constellation.py::generate_walker_delta_tles +
  per_satellite_access_windows), including at the single-satellite
  baseline (a trivial 1-satellite/1-plane Walker constellation), so e11
  and e12 now share one real orbital model end to end.

Everything else (paired trials, MT-3, cadence-based MT-4, structural
incapacity tracked separately from slowness) is unchanged from v3.
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
from leo_edge.orbit.constellation import generate_walker_delta_tles, per_satellite_access_windows
from leo_edge.simulation import simulate_multi_contact
from leo_edge.mission_threads import MISSION_THREADS
from leo_edge.products import ProductTier
from leo_edge.stats import wilson_ci, paired_bootstrap_diff_ci, kaplan_meier_curve

SCENE_BYTES = 1_000_000_000  # 1 GB notional area-of-interest scene
PROCESSING_TIME_S = 20.0
HORIZON_S = 168 * 3600.0  # matches the 1-week access-window generation
EPOCH = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
ALTITUDE_KM = 550.0
INCLINATION_DEG = 97.4
MIN_ELEVATION_DEG = 10.0

# Ground terminal (downlink) and AOI (imaging target) locations, unchanged
# from v3: a notional, documented offset (docs/DECISION_LOG.md), not a real
# geodesy claim.
GROUND_LAT, GROUND_LON = 40.0, 0.0
AOI_LAT, AOI_LON = 45.0, 5.0

# Probability a usable prior reference image exists for MT-3's change
# detection at request time. ASSUMED; see docs/MISSION_THREADS.md.
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
N_TRIALS_CADENCE = 30   # MT-4: each "trial" walks every real collection pass
SEED = 0


def _offset_windows(access_windows):
    """Convert generate_access_windows output to (start_s, dur_s, peak_s)
    triples, offset from EPOCH, sorted by start."""
    out = []
    for w in access_windows:
        start = datetime.fromisoformat(w["start"].replace("Z", "+00:00"))
        peak = datetime.fromisoformat(w["peak"].replace("Z", "+00:00"))
        start_s = (start - EPOCH).total_seconds()
        peak_s = (peak - EPOCH).total_seconds()
        out.append((start_s, float(w["duration_s"]), peak_s))
    return sorted(out, key=lambda triple: triple[0])


def build_per_satellite_windows(total_sats=1, planes=1, phasing_factor=0):
    """Build per-satellite AOI and downlink windows for a Walker-delta
    constellation, via real per-satellite SGP4 (docs/DECISION_LOG.md
    ADR-019/ADR-020). total_sats=1/planes=1 is the single-satellite
    baseline other v3 experiments compare against."""
    tles = generate_walker_delta_tles(total_sats, planes, phasing_factor, ALTITUDE_KM, INCLINATION_DEG)
    aoi_raw = per_satellite_access_windows(tles, AOI_LAT, AOI_LON, MIN_ELEVATION_DEG, HORIZON_S / 3600.0)
    downlink_raw = per_satellite_access_windows(tles, GROUND_LAT, GROUND_LON, MIN_ELEVATION_DEG, HORIZON_S / 3600.0)
    aoi_by_sat = {sat_id: _offset_windows(w) for sat_id, w in aoi_raw.items()}
    downlink_by_sat = {sat_id: _offset_windows(w) for sat_id, w in downlink_raw.items()}
    return aoi_by_sat, downlink_by_sat


def _tier_index_for(architecture, needed_tier, scene_bytes, processing_time_s):
    try:
        tiers = architecture.tiers(scene_bytes, processing_time_s=processing_time_s)
    except TypeError:
        tiers = architecture.tiers(scene_bytes)
    return any(tier == needed_tier for tier, _bytes, _proc in tiers)


def next_collection_event(earliest_s, aoi_windows_by_sat):
    """Earliest AOI overflight (by time of closest approach, "peak") across
    every satellite in the constellation, at/after `earliest_s`. Returns
    (peak_s, sat_id) or None if no such pass exists before the horizon.

    Whichever satellite gets there first collects the image -- this is a
    real property of the constellation, not an architecture choice, so
    every architecture in a paired trial shares the same collection event.
    """
    best = None
    for sat_id, windows in aoi_windows_by_sat.items():
        for _start_s, _dur_s, peak_s in windows:
            if peak_s >= earliest_s:
                if best is None or peak_s < best[0]:
                    best = (peak_s, sat_id)
                break  # windows sorted by start/peak; first qualifying is earliest for this sat
    return best


def all_collection_events(aoi_windows_by_sat):
    """Every AOI overflight across the whole constellation and horizon,
    sorted by time of closest approach. Used by MT-4's cadence walk."""
    events = []
    for sat_id, windows in aoi_windows_by_sat.items():
        for _start_s, _dur_s, peak_s in windows:
            events.append((peak_s, sat_id))
    return sorted(events)


def usable_downlink_same_satellite(collection_time_s, downlink_windows, denial_rolls, contact_denial_frac):
    """Downlink windows of the collecting satellite that are still open at
    or after collection completes, clipped to their remaining portion --
    this is what allows same-pass delivery (v4 item 2): a window doesn't
    have to START after collection, it only has to still be open (END
    after collection)."""
    usable = []
    for (start_s, dur_s, _peak_s), denial_roll in zip(downlink_windows, denial_rolls):
        end_s = start_s + dur_s
        if end_s <= collection_time_s:
            continue
        if denial_roll < contact_denial_frac:
            continue
        usable_start_s = max(start_s, collection_time_s)
        usable.append((usable_start_s - collection_time_s, end_s - usable_start_s))
    return usable


def draw_trial_context(rng, condition, aoi_windows_by_sat, downlink_windows_by_sat):
    """One shared draw per trial: request time, the resulting collection
    event (same for every architecture, since it depends only on the
    constellation and the condition's tasking delay), and the downlink
    denial rolls for whichever satellite ends up collecting -- drawn once
    per trial and reused across every architecture so comparisons stay
    paired."""
    request_time_s = rng.uniform(0.0, HORIZON_S - 3600.0)
    prior_reference_roll = rng.random()
    collection = next_collection_event(request_time_s + condition["tasking_delay_s"], aoi_windows_by_sat)
    if collection is None:
        return {
            "request_time_s": request_time_s, "prior_reference_roll": prior_reference_roll,
            "collection": None, "downlink_windows": [], "denial_rolls": [],
        }
    peak_s, sat_id = collection
    downlink_windows = downlink_windows_by_sat.get(sat_id, [])
    denial_rolls = [rng.random() for _ in downlink_windows]
    return {
        "request_time_s": request_time_s, "prior_reference_roll": prior_reference_roll,
        "collection": collection, "downlink_windows": downlink_windows, "denial_rolls": denial_rolls,
    }


def evaluate_single_request(factory, thread_key, thread, terminal_key, terminal, condition_key, condition,
                             ctx, trial_idx):
    architecture = factory(thread)
    arch_name = type(architecture).__name__
    architecture_supports_tier = _tier_index_for(architecture, thread["needed_tier"], SCENE_BYTES, PROCESSING_TIME_S)
    rate_bps = terminal["rate_bps"] * condition["interference_derate"]

    if thread_key == "MT3_BATTLE_DAMAGE_ASSESSMENT":
        has_reference = ctx["prior_reference_roll"] < PRIOR_REFERENCE_PROB
        tolerance_s = thread["latency_tolerance_s"] if has_reference else thread["no_reference_latency_tolerance_s"]
    else:
        has_reference = None
        tolerance_s = thread["latency_tolerance_s"]

    if ctx["collection"] is None:
        return {
            "architecture": arch_name, "thread": thread_key, "terminal_class": terminal_key,
            "condition": condition_key, "trial_idx": trial_idx,
            "latency_s": float("nan"), "produced_tier": False,
            "structural_incapacity": not architecture_supports_tier,
            "success": False, "has_prior_reference": has_reference,
        }

    collection_time_s, _sat_id = ctx["collection"]
    usable = usable_downlink_same_satellite(
        collection_time_s, ctx["downlink_windows"], ctx["denial_rolls"], condition["contact_denial_frac"]
    )
    result = simulate_multi_contact(architecture, SCENE_BYTES, usable, rate_bps, PROCESSING_TIME_S)

    needed_tier_time_s = result.tier_completion_s.get(thread["needed_tier"].value)
    if needed_tier_time_s is None and thread["needed_tier"] == ProductTier.P4_FULL and result.completed:
        needed_tier_time_s = result.tcp_s

    if needed_tier_time_s is None:
        latency_s = float("nan")
        produced_tier = False
    else:
        latency_s = (collection_time_s - ctx["request_time_s"]) + needed_tier_time_s
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
                      collection_events, downlink_windows_by_sat, denial_rolls_by_sat, trial_idx):
    """MT-4: walk every real collection pass across the horizon (now across
    every satellite in the constellation, each pass handled by whichever
    satellite made it); success requires never missing the per-pass
    tolerance twice in a row."""
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

    for collection_time_s, sat_id in collection_events:
        downlink_windows = downlink_windows_by_sat.get(sat_id, [])
        denial_rolls = denial_rolls_by_sat.get(sat_id, [])
        usable = usable_downlink_same_satellite(
            collection_time_s, downlink_windows, denial_rolls, condition["contact_denial_frac"]
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


def run_single_request_threads(rng, aoi_windows_by_sat, downlink_windows_by_sat):
    rows = []
    single_request_threads = {k: v for k, v in MISSION_THREADS.items() if not v["cadence"]}
    for thread_key, thread in single_request_threads.items():
        for terminal_key, terminal in TERMINAL_CLASSES.items():
            for condition_key, condition in CONDITIONS.items():
                for trial_idx in range(N_TRIALS):
                    ctx = draw_trial_context(rng, condition, aoi_windows_by_sat, downlink_windows_by_sat)
                    for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                        rows.append(evaluate_single_request(
                            factory, thread_key, thread, terminal_key, terminal,
                            condition_key, condition, ctx, trial_idx,
                        ))
    return rows


def run_cadence_thread(rng, aoi_windows_by_sat, downlink_windows_by_sat):
    rows = []
    thread = MISSION_THREADS["MT4_PERSISTENT_MONITORING"]
    collection_events = all_collection_events(aoi_windows_by_sat)
    for terminal_key, terminal in TERMINAL_CLASSES.items():
        for condition_key, condition in CONDITIONS.items():
            for trial_idx in range(N_TRIALS_CADENCE):
                denial_rolls_by_sat = {
                    sat_id: [rng.random() for _ in windows]
                    for sat_id, windows in downlink_windows_by_sat.items()
                }
                for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                    rows.append(evaluate_cadence(
                        factory, thread, terminal_key, terminal, condition_key, condition,
                        collection_events, downlink_windows_by_sat, denial_rolls_by_sat, trial_idx,
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
    by_cell_trial = {}
    for row in all_rows:
        cell_trial = (row["thread"], row["terminal_class"], row["condition"], row["trial_idx"])
        by_cell_trial.setdefault(cell_trial, {})[row["architecture"]] = 1 if row["success"] else 0

    arch_names = sorted({row["architecture"] for row in all_rows})
    paired_series = {a: [] for a in arch_names}
    for cell_trial, outcomes in sorted(by_cell_trial.items()):
        if len(outcomes) != len(arch_names):
            continue
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


def report_same_pass_effect(rng_seed=SEED):
    """Isolate and print how much the v4 same-pass/peak-time collection fix
    (vs. v3's wait-for-pass-end model) alone moves success and latency at
    the single-satellite baseline, as the v4 task requires. Runs a small,
    separate comparison rather than keeping two production code paths."""
    aoi_by_sat, downlink_by_sat = build_per_satellite_windows(total_sats=1, planes=1, phasing_factor=0)
    aoi_windows = next(iter(aoi_by_sat.values()))
    downlink_windows = next(iter(downlink_by_sat.values()))

    def v3_style_collection_complete(request_time_s, tasking_delay_s):
        earliest = request_time_s + tasking_delay_s
        for start_s, dur_s, _peak_s in aoi_windows:
            if start_s >= earliest:
                return start_s + dur_s
        return None

    def v3_style_usable_downlink(base_time_s, denial_rolls):
        usable = []
        for (start_s, dur_s, _peak_s), denial_roll in zip(downlink_windows, denial_rolls):
            if start_s < base_time_s or denial_roll < 0.0:
                continue
            usable.append((start_s - base_time_s, dur_s))
        return usable

    thread = MISSION_THREADS["MT1_TIME_SENSITIVE_CUEING"]
    terminal = TERMINAL_CLASSES["VEHICLE_MOUNTED"]
    condition = CONDITIONS["NOMINAL"]
    rng = random.Random(rng_seed)

    v3_successes, v4_successes = 0, 0
    v3_latencies, v4_latencies = [], []
    n = 500
    for _ in range(n):
        request_time_s = rng.uniform(0.0, HORIZON_S - 3600.0)
        # v3: collection at pass end, downlink windows must start after it.
        collection_end_s = v3_style_collection_complete(request_time_s, condition["tasking_delay_s"])
        if collection_end_s is not None:
            usable_v3 = v3_style_usable_downlink(collection_end_s, [1.0] * len(downlink_windows))
            arch = Progressive()
            result_v3 = simulate_multi_contact(arch, SCENE_BYTES, usable_v3, terminal["rate_bps"], PROCESSING_TIME_S)
            tier_time = result_v3.tier_completion_s.get(thread["needed_tier"].value)
            if tier_time is not None:
                latency = (collection_end_s - request_time_s) + tier_time
                v3_latencies.append(latency)
                if latency <= thread["latency_tolerance_s"]:
                    v3_successes += 1

        # v4: collection at peak (closest approach), same-satellite downlink
        # windows usable from their remaining portion after collection.
        collection = next_collection_event(request_time_s + condition["tasking_delay_s"], aoi_by_sat)
        if collection is not None:
            peak_s, sat_id = collection
            usable_v4 = usable_downlink_same_satellite(peak_s, downlink_by_sat[sat_id], [1.0] * len(downlink_windows), 0.0)
            arch = Progressive()
            result_v4 = simulate_multi_contact(arch, SCENE_BYTES, usable_v4, terminal["rate_bps"], PROCESSING_TIME_S)
            tier_time = result_v4.tier_completion_s.get(thread["needed_tier"].value)
            if tier_time is not None:
                latency = (peak_s - request_time_s) + tier_time
                v4_latencies.append(latency)
                if latency <= thread["latency_tolerance_s"]:
                    v4_successes += 1

    print(f"\nSame-pass-delivery isolation (Progressive, MT-1, VEHICLE_MOUNTED, NOMINAL, {n} trials, single satellite):")
    print(f"  v3 (collection at pass end): {v3_successes}/{n} successes, "
          f"mean latency (of trials that produced the tier) = "
          f"{sum(v3_latencies)/len(v3_latencies):.1f}s" if v3_latencies else "  v3: no trials produced the tier")
    print(f"  v4 (collection at closest approach, same-pass delivery allowed): {v4_successes}/{n} successes, "
          f"mean latency (of trials that produced the tier) = "
          f"{sum(v4_latencies)/len(v4_latencies):.1f}s" if v4_latencies else "  v4: no trials produced the tier")
    return {
        "v3_successes": v3_successes, "v4_successes": v4_successes, "n": n,
        "v3_mean_latency_s": (sum(v3_latencies) / len(v3_latencies)) if v3_latencies else float("nan"),
        "v4_mean_latency_s": (sum(v4_latencies) / len(v4_latencies)) if v4_latencies else float("nan"),
    }


def main():
    rng = random.Random(SEED)
    aoi_by_sat, downlink_by_sat = build_per_satellite_windows(total_sats=1, planes=1, phasing_factor=0)
    aoi_windows = next(iter(aoi_by_sat.values()))
    downlink_windows = next(iter(downlink_by_sat.values()))
    print(f"Downlink windows (1 week, single satellite): {len(downlink_windows)}")
    print(f"AOI overflight windows (1 week, single satellite): {len(aoi_windows)}")

    single_rows = run_single_request_threads(rng, aoi_by_sat, downlink_by_sat)
    cadence_rows = run_cadence_thread(rng, aoi_by_sat, downlink_by_sat)

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

    report_same_pass_effect()


if __name__ == "__main__":
    main()
