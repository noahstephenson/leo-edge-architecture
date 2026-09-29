"""Mission-thread evaluation with same-pass delivery and satellite identity.

Collection completes at closest approach during an area-of-interest pass.
Only the collecting satellite carries the scene, using the remaining part
of any open contact and later contacts with a terminal. The access schedule
comes from individually propagated synthetic satellites.
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
from leo_edge.products import TIER_FIDELITY
from leo_edge.stats import wilson_ci, paired_bootstrap_diff_ci, kaplan_meier_curve

SCENE_BYTES = 1_000_000_000  # 1 GB notional area-of-interest scene
PROCESSING_TIME_S = 20.0
HORIZON_S = 168 * 3600.0  # matches the 1-week access-window generation
EPOCH = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
ALTITUDE_KM = 550.0
INCLINATION_DEG = 97.4
MIN_ELEVATION_DEG = 10.0

# Ground-terminal and collection-area coordinates are synthetic.
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
    # Compute times and capabilities are notional sensitivity assumptions.
    # Both classes can derive a smaller product from a received full scene;
    # the manpack requires more time. Neither can recover missing scene area.
    "VEHICLE_MOUNTED": {"rate_bps": 50_000_000, "derivation_time_s": 5.0,
                        "derivable_tiers": tuple(ProductTier)[:-1]},
    "DISMOUNTED_MANPACK": {"rate_bps": 5_000_000, "derivation_time_s": 30.0,
                            "derivable_tiers": tuple(ProductTier)[:-1]},
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
    ADR-019/ADR-020). total_sats=1/planes=1 gives a single-satellite case."""
    tles = generate_walker_delta_tles(total_sats, planes, phasing_factor, ALTITUDE_KM, INCLINATION_DEG)
    aoi_raw = per_satellite_access_windows(tles, AOI_LAT, AOI_LON, MIN_ELEVATION_DEG, HORIZON_S / 3600.0)
    downlink_raw = per_satellite_access_windows(tles, GROUND_LAT, GROUND_LON, MIN_ELEVATION_DEG, HORIZON_S / 3600.0)
    aoi_by_sat = {sat_id: _offset_windows(w) for sat_id, w in aoi_raw.items()}
    downlink_by_sat = {sat_id: _offset_windows(w) for sat_id, w in downlink_raw.items()}
    return aoi_by_sat, downlink_by_sat


def tier_sufficient(needed_tier, delivered_tier, terminal=None):
    """Whether the received product can satisfy a need at this terminal.

    A crop never implies whole-scene coverage. P4 supports derivation only
    when the terminal has the function and the source has full-scene fidelity.
    This tests structural eligibility; elapsed derivation and deadline are
    checked when the delivered product is evaluated.
    """
    if delivered_tier == needed_tier:
        return True
    terminal = terminal or TERMINAL_CLASSES["VEHICLE_MOUNTED"]
    return (
        delivered_tier == ProductTier.P4_FULL
        and needed_tier in terminal.get("derivable_tiers", ())
        and terminal.get("derivation_time_s") is not None
        and TIER_FIDELITY[delivered_tier].resolution_class == "full_res"
    )


def get_needed_completion(result, needed_tier, terminal=None):
    terminal = terminal or TERMINAL_CLASSES["VEHICLE_MOUNTED"]
    candidates = []
    for tier_val, completion_s in result.tier_completion_s.items():
        try:
            delivered_tier_enum = ProductTier(tier_val)
        except ValueError:
            continue
        if tier_sufficient(needed_tier, delivered_tier_enum, terminal):
            derivation_s = (terminal["derivation_time_s"]
                            if delivered_tier_enum != needed_tier else 0.0)
            candidates.append((completion_s + derivation_s, delivered_tier_enum))
    if needed_tier == ProductTier.P4_FULL and result.completed:
        candidates.append((result.tcp_s, ProductTier.P4_FULL))
    return min(candidates, key=lambda item: item[0]) if candidates else (None, None)


def architecture_capable(architecture, needed_tier, scene_bytes, processing_time_s, terminal=None):
    """True if architecture can produce a tier sufficient for needed_tier."""
    try:
        tiers = architecture.tiers(scene_bytes, processing_time_s=processing_time_s)
    except TypeError:
        tiers = architecture.tiers(scene_bytes)
    return any(tier_sufficient(needed_tier, tier, terminal) for tier, _bytes, _proc in tiers)


def _tier_index_for(architecture, needed_tier, scene_bytes, processing_time_s):
    return architecture_capable(architecture, needed_tier, scene_bytes, processing_time_s)


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
    this is what allows same-pass delivery: a window doesn't
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
    architecture_capable_flag = architecture_capable(architecture, thread["needed_tier"], SCENE_BYTES, PROCESSING_TIME_S, terminal)
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
            "structural_incapacity": not architecture_capable_flag,
            "success": False, "has_prior_reference": has_reference,
            "request_time_s": ctx.get("request_time_s"),
            "collection_time_s": None,
            "sat_id": None,
            "delivered_tier": None,
            "terminal_derivation_required": None,
            "terminal_processing_time_s": None,
            "product_arrival_time_s": None,
            "final_availability_time_s": None,
        }

    collection_time_s, sat_id = ctx["collection"]
    request_time_s = ctx.get("request_time_s")
    usable = usable_downlink_same_satellite(
        collection_time_s, ctx["downlink_windows"], ctx["denial_rolls"], condition["contact_denial_frac"]
    )
    result = simulate_multi_contact(architecture, SCENE_BYTES, usable, rate_bps, PROCESSING_TIME_S)

    # Find a delivered tier that is sufficient for the needed tier, allowing terminal derivation from P4_FULL
    needed_completion, delivered_tier_found = get_needed_completion(result, thread["needed_tier"], terminal)

    if needed_completion is None:
        latency_s = float("nan")
        produced_tier = False
        delivered_tier = None
        terminal_derivation_required = None
        terminal_processing_time_s = None
        product_arrival_time_s = None
        final_availability_time_s = None
    else:
        latency_s = (collection_time_s - request_time_s) + needed_completion
        produced_tier = True
        delivered_tier = delivered_tier_found.name if delivered_tier_found else None
        terminal_derivation_required = delivered_tier_found == ProductTier.P4_FULL and delivered_tier_found != thread["needed_tier"]
        terminal_processing_time_s = terminal["derivation_time_s"] if terminal_derivation_required else 0.0
        product_arrival_time_s = collection_time_s + needed_completion - terminal_processing_time_s
        final_availability_time_s = collection_time_s + needed_completion

    structural_incapacity = not architecture_capable_flag
    success = (not structural_incapacity) and produced_tier and latency_s <= tolerance_s

    return {
        "architecture": arch_name, "thread": thread_key, "terminal_class": terminal_key,
        "condition": condition_key, "trial_idx": trial_idx,
        "latency_s": latency_s, "produced_tier": produced_tier,
        "structural_incapacity": structural_incapacity,
        "success": success, "has_prior_reference": has_reference,
        "request_time_s": request_time_s,
        "collection_time_s": collection_time_s,
        "sat_id": sat_id,
        "delivered_tier": delivered_tier,
        "terminal_derivation_required": terminal_derivation_required,
        "terminal_processing_time_s": terminal_processing_time_s,
        "product_arrival_time_s": product_arrival_time_s,
        "final_availability_time_s": final_availability_time_s,
    }


def evaluate_cadence(factory, thread, terminal_key, terminal, condition_key, condition,
                      collection_events, downlink_windows_by_sat, denial_rolls_by_sat, trial_idx):
    """MT-4: walk every real collection pass across the horizon (now across
    every satellite in the constellation, each pass handled by whichever
    satellite made it); success requires never missing the per-pass
    tolerance twice in a row."""
    architecture = factory(thread)
    arch_name = type(architecture).__name__
    architecture_capable_flag = architecture_capable(architecture, thread["needed_tier"], SCENE_BYTES, PROCESSING_TIME_S, terminal)
    rate_bps = terminal["rate_bps"] * condition["interference_derate"]

    if not architecture_capable_flag:
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
        completion, _ = get_needed_completion(result, thread["needed_tier"], terminal)
        total_passes += 1
        met = completion is not None and completion <= thread["latency_tolerance_s"]
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
                      "latency_s", "produced_tier", "structural_incapacity", "success", "has_prior_reference",
                      "request_time_s", "collection_time_s", "sat_id", "delivered_tier",
                      "terminal_derivation_required", "terminal_processing_time_s",
                      "product_arrival_time_s", "final_availability_time_s"]
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



if __name__ == "__main__":
    main()
