"""Experiment 12 (v4): Access/revisit sweep over REAL Walker-delta
constellations.

v3's version of this sweep approximated additional satellites by
time-shifting one satellite's access windows (`_phase_shift_windows`,
deleted here). That ignores Earth rotation and orbital-plane geometry
entirely and is retracted as a constellation model
(docs/DECISION_LOG.md ADR-019). This version sweeps real Walker-delta
constellations (`orbit/constellation.py::generate_walker_delta_tles`),
each satellite individually propagated with SGP4, including single-plane
configurations kept in the sweep for direct comparison against the
multi-plane Walker configurations that are the actual main sweep.

Same-pass collect-and-downlink and per-satellite collection/downlink
tracking (v4 item 2, docs/DECISION_LOG.md ADR-020) apply here exactly as
in `e11_mission_thread_success.py`, whose functions this module imports
and reuses rather than duplicating.

New in v4 (see docs/REWORK_PLAN_V4.md):
- Feasibility floors per mission thread per configuration: a structural
  floor (processing + minimal transmit time at the best rate, ignoring
  access entirely -- true regardless of constellation size) and a
  revisit-aware floor (adds a typical AOI-wait term from this
  configuration's real collection-event gaps). A thread whose structural
  floor already exceeds tolerance is flagged infeasible at ANY
  configuration, not averaged in as an ordinary zero.
- A tolerance sensitivity sweep (0.5x/1x/2x/4x) at the single-satellite
  baseline and the largest swept configuration.
- Architecture-difference significance testing restricted to
  INFORMATIVE cells (best architecture's success > 30%); every cell is
  labeled UNINFORMATIVE (floor effect), SEPARATES (significant
  difference among informative cells), or TIES (informative, no
  significant difference) -- the three-way distinction item 4 requires,
  replacing v3's single "no significant difference" bucket that
  conflated floor effects with real ties.

Scope reduction for tractability, documented rather than silent
(docs/DECISION_LOG.md): real per-satellite SGP4 propagation is much more
expensive than v3's time-shift approximation, so this sweep uses fewer
trials per cell than v3's already-reduced count, and the KM-curve /
tolerance-sensitivity analyses run only at the baseline and the largest
swept configuration rather than at every cell.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from e11_mission_thread_success import (  # noqa: E402
    ARCHITECTURE_FACTORIES, TERMINAL_CLASSES, HORIZON_S, EPOCH,
    AOI_LAT, AOI_LON, GROUND_LAT, GROUND_LON, ALTITUDE_KM, INCLINATION_DEG, MIN_ELEVATION_DEG,
    SCENE_BYTES, PROCESSING_TIME_S,
    evaluate_single_request, evaluate_cadence, draw_trial_context,
    next_collection_event, all_collection_events, usable_downlink_same_satellite,
    _offset_windows,
)
from leo_edge.architectures import Progressive
from leo_edge.mission_threads import MISSION_THREADS
from leo_edge.orbit.constellation import generate_walker_delta_tles, per_satellite_access_windows
from leo_edge.stats import wilson_ci, paired_bootstrap_diff_ci, kaplan_meier_curve

# Walker-delta configurations (total_sats, planes, phasing_factor). Single-
# plane configs (planes=1) are kept for direct comparison; the multi-plane
# Walker configs are the main sweep, per the v4 task's explicit instruction.
SAT_CONFIGS = [
    (1, 1, 0),    # baseline
    (2, 1, 0),    # single-plane comparison
    (4, 1, 0),    # single-plane comparison
    (4, 4, 1),    # Walker-delta 4/4/1
    (8, 4, 1),    # Walker-delta 8/4/1
    (16, 4, 1),   # Walker-delta 16/4/1
    (32, 8, 1),   # Walker-delta 32/8/1
]
TERMINAL_COUNTS = [1, 2, 4]

TERMINAL_SITES = [(40.0, 0.0), (35.0, 20.0), (50.0, -10.0), (30.0, 40.0)]

CONDITIONS_SWEPT = {
    "NOMINAL": {"interference_derate": 1.0, "contact_denial_frac": 0.0, "tasking_delay_s": 60},
    "COMBINED_DEGRADED": {"interference_derate": 0.5, "contact_denial_frac": 0.3, "tasking_delay_s": 180},
}

N_TRIALS = 40
N_TRIALS_CADENCE = 6
MAX_CADENCE_EVENTS = 40
SEED = 0
INFORMATIVE_THRESHOLD = 0.30  # best architecture's success rate must exceed this to test differences

RELATIVE_COST_PER_SATELLITE = 10.0
RELATIVE_COST_PER_TERMINAL = 3.0
RELATIVE_COST_PER_PROCESSING_TIER = 1.0

_PROGRESSIVE_TIER_BYTES = dict((tier, size) for tier, size in Progressive()._tier_sizes(SCENE_BYTES))


def build_config_windows(total_sats, planes, phasing_factor):
    """Real per-satellite AOI windows and, per terminal site, real
    per-satellite downlink windows, for one Walker configuration. Terminal
    sites are propagated separately (not merged yet) so different
    TERMINAL_COUNTS can reuse the same propagation without recomputing."""
    tles = generate_walker_delta_tles(total_sats, planes, phasing_factor, ALTITUDE_KM, INCLINATION_DEG)
    duration_hours = HORIZON_S / 3600.0

    aoi_raw = per_satellite_access_windows(tles, AOI_LAT, AOI_LON, MIN_ELEVATION_DEG, duration_hours)
    aoi_by_sat = {sat_id: _offset_windows(w) for sat_id, w in aoi_raw.items()}

    downlink_by_site_by_sat = {}
    for site in TERMINAL_SITES:
        raw = per_satellite_access_windows(tles, site[0], site[1], MIN_ELEVATION_DEG, duration_hours)
        downlink_by_site_by_sat[site] = {sat_id: _offset_windows(w) for sat_id, w in raw.items()}

    return aoi_by_sat, downlink_by_site_by_sat


def _merge_pairs(triples):
    """Union overlapping (start_s, dur_s, peak_s) windows for one satellite
    seen from multiple terminal sites into a minimal non-overlapping set
    (one logical delivery pipe, docs/DECISION_LOG.md, unchanged from v3)."""
    if not triples:
        return []
    triples = sorted(triples, key=lambda w: w[0])
    merged = [[triples[0][0], triples[0][1]]]
    for start, dur, _peak in triples[1:]:
        end = start + dur
        last_start, last_dur = merged[-1]
        last_end = last_start + last_dur
        if start <= last_end:
            merged[-1][1] = max(last_end, end) - last_start
        else:
            merged.append([start, dur])
    return [(s, d, s + d / 2.0) for s, d in merged]


def build_downlink_windows_by_sat(downlink_by_site_by_sat, terminal_count):
    selected_sites = TERMINAL_SITES[:terminal_count]
    sat_ids = set()
    for site in selected_sites:
        sat_ids.update(downlink_by_site_by_sat[site].keys())
    out = {}
    for sat_id in sat_ids:
        combined = []
        for site in selected_sites:
            combined.extend(downlink_by_site_by_sat[site].get(sat_id, []))
        out[sat_id] = _merge_pairs(combined)
    return out


def run_cell(sat_count, planes, terminal_count, aoi_by_sat, downlink_by_sat, rng):
    single_rows = []
    single_request_threads = {k: v for k, v in MISSION_THREADS.items() if not v["cadence"]}
    for thread_key, thread in single_request_threads.items():
        for terminal_key, terminal in TERMINAL_CLASSES.items():
            for condition_key, condition in CONDITIONS_SWEPT.items():
                for trial_idx in range(N_TRIALS):
                    ctx = draw_trial_context(rng, condition, aoi_by_sat, downlink_by_sat)
                    for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                        row = evaluate_single_request(
                            factory, thread_key, thread, terminal_key, terminal,
                            condition_key, condition, ctx, trial_idx,
                        )
                        row["satellites"] = sat_count
                        row["planes"] = planes
                        row["terminals"] = terminal_count
                        single_rows.append(row)

    cadence_rows = []
    thread = MISSION_THREADS["MT4_PERSISTENT_MONITORING"]
    all_events = all_collection_events(aoi_by_sat)
    sampled_events = (
        all_events if len(all_events) <= MAX_CADENCE_EVENTS
        else [all_events[int(i * len(all_events) / MAX_CADENCE_EVENTS)] for i in range(MAX_CADENCE_EVENTS)]
    )
    for terminal_key, terminal in TERMINAL_CLASSES.items():
        for condition_key, condition in CONDITIONS_SWEPT.items():
            for trial_idx in range(N_TRIALS_CADENCE):
                denial_rolls_by_sat = {
                    sat_id: [rng.random() for _ in windows] for sat_id, windows in downlink_by_sat.items()
                }
                for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                    row = evaluate_cadence(
                        factory, thread, terminal_key, terminal, condition_key, condition,
                        sampled_events, downlink_by_sat, denial_rolls_by_sat, trial_idx,
                    )
                    row["satellites"] = sat_count
                    row["planes"] = planes
                    row["terminals"] = terminal_count
                    cadence_rows.append(row)

    return single_rows, cadence_rows


def summarize_cell(single_rows, cadence_rows, sat_count, planes, terminal_count):
    out = []
    by_arch_thread = {}
    for row in single_rows:
        key = (row["architecture"], row["thread"])
        by_arch_thread.setdefault(key, []).append(1 if row["success"] else 0)
    for row in cadence_rows:
        key = (row["architecture"], row["thread"])
        by_arch_thread.setdefault(key, []).append(1 if row["success"] else 0)

    for (arch, thread), successes in sorted(by_arch_thread.items()):
        n = len(successes)
        s = sum(successes)
        rate = s / n
        lo, hi = wilson_ci(s, n)
        out.append({
            "satellites": sat_count, "planes": planes, "terminals": terminal_count,
            "architecture": arch, "thread": thread,
            "n_trials": n, "successes": s, "success_rate": rate,
            "success_rate_ci_lower": lo, "success_rate_ci_upper": hi,
        })
    return out


def cell_pairwise_significance(single_rows, cadence_rows, sat_count, planes, terminal_count):
    """Paired comparison of every architecture pair, but ONLY when the best
    architecture's overall success rate in this cell exceeds
    INFORMATIVE_THRESHOLD (v4 item 4): testing whether two ~0%-success
    architectures "differ significantly" is not a meaningful statement, so
    those cells are labeled UNINFORMATIVE instead of tested."""
    by_cell_trial = {}
    for row in single_rows:
        key = (row["thread"], row["terminal_class"], row["condition"], row["trial_idx"])
        by_cell_trial.setdefault(key, {})[row["architecture"]] = 1 if row["success"] else 0
    for row in cadence_rows:
        key = (row["thread"], row["terminal_class"], row["condition"], row["trial_idx"])
        by_cell_trial.setdefault(key, {})[row["architecture"]] = 1 if row["success"] else 0

    arch_names = sorted({row["architecture"] for row in single_rows})
    paired_series = {a: [] for a in arch_names}
    for _key, outcomes in sorted(by_cell_trial.items()):
        if len(outcomes) != len(arch_names):
            continue
        for a in arch_names:
            paired_series[a].append(outcomes[a])

    n = len(paired_series[arch_names[0]]) if arch_names else 0
    if n == 0:
        return "UNINFORMATIVE", None, []

    rates = {a: sum(paired_series[a]) / n for a in arch_names}
    best_rate = max(rates.values())

    if best_rate <= INFORMATIVE_THRESHOLD:
        return "UNINFORMATIVE", None, []

    results = []
    for i, a in enumerate(arch_names):
        for b in arch_names[i + 1:]:
            diff, lo, hi, significant = paired_bootstrap_diff_ci(
                paired_series[a], paired_series[b], n_resamples=1000, seed=SEED,
            )
            results.append({
                "satellites": sat_count, "planes": planes, "terminals": terminal_count,
                "architecture_a": a, "architecture_b": b, "n_paired_trials": n,
                "diff_a_minus_b": diff, "significant": significant,
            })

    ranked = sorted(arch_names, key=lambda a: rates[a], reverse=True)
    best = ranked[0]
    beats_all = True
    for other in ranked[1:]:
        match = [r for r in results if {r["architecture_a"], r["architecture_b"]} == {best, other}]
        if not match or not match[0]["significant"]:
            beats_all = False
            break

    if beats_all:
        return "SEPARATES", best, results
    return "TIES", "NO_SIGNIFICANT_DIFFERENCE", results


def compute_feasibility_floor(thread, best_rate_bps=TERMINAL_CLASSES["VEHICLE_MOUNTED"]["rate_bps"]):
    """Structural floor: minimum tasking delay + processing + minimal
    transmit time for the needed tier at the best available rate, IGNORING
    access entirely (as if the AOI were always instantly overhead). This is
    a hard lower bound independent of constellation size -- if a thread's
    tolerance is below this, no amount of access density can ever save it.
    Tier byte sizes come from Progressive's real tier table (shared by
    ThreadAwarePriority), the smallest documented estimate available for a
    given tier in this codebase."""
    tier_bytes = _PROGRESSIVE_TIER_BYTES[thread["needed_tier"]]
    transmit_s = tier_bytes * 8 / best_rate_bps
    min_tasking_delay_s = min(c["tasking_delay_s"] for c in CONDITIONS_SWEPT.values())
    return min_tasking_delay_s + PROCESSING_TIME_S + transmit_s


def compute_revisit_gap_stats(aoi_by_sat):
    events = all_collection_events(aoi_by_sat)
    if len(events) < 2:
        return {"median_gap_s": float("nan"), "max_gap_s": float("nan"), "n_events": len(events)}
    peaks = sorted(peak_s for peak_s, _sat_id in events)
    gaps = [b - a for a, b in zip(peaks, peaks[1:])]
    gaps.sort()
    median_gap_s = gaps[len(gaps) // 2]
    return {"median_gap_s": median_gap_s, "max_gap_s": max(gaps), "n_events": len(events)}


def feasibility_rows_for_config(sat_count, planes, aoi_by_sat):
    gap_stats = compute_revisit_gap_stats(aoi_by_sat)
    rows = []
    for thread_key, thread in MISSION_THREADS.items():
        tolerance_s = thread["latency_tolerance_s"]
        structural_floor_s = compute_feasibility_floor(thread)
        revisit_floor_s = structural_floor_s + gap_stats["median_gap_s"] / 2.0
        if structural_floor_s > tolerance_s:
            status = "INFEASIBLE_STRUCTURAL"  # impossible at ANY access level
        elif revisit_floor_s > tolerance_s:
            status = "INFEASIBLE_AT_THIS_ACCESS"
        else:
            status = "FEASIBLE"
        rows.append({
            "satellites": sat_count, "planes": planes, "thread": thread_key, "tolerance_s": tolerance_s,
            "structural_floor_s": structural_floor_s, "revisit_floor_s": revisit_floor_s,
            "median_revisit_gap_s": gap_stats["median_gap_s"], "max_revisit_gap_s": gap_stats["max_gap_s"],
            "n_aoi_events": gap_stats["n_events"], "status": status,
        })
    return rows


def km_summary_rows(single_rows, sat_count, planes, terminal_count):
    """Per-architecture KM survival curve summary (quartile crossing
    times), v4 item 3's "report latency distributions" requirement, without
    dumping a full curve per cell (see module docstring's scope note)."""
    by_arch = {}
    for row in single_rows:
        by_arch.setdefault(row["architecture"], []).append(row)

    out = []
    for arch, rows in sorted(by_arch.items()):
        times = [r["latency_s"] if r["produced_tier"] else HORIZON_S for r in rows]
        censored = [not r["produced_tier"] for r in rows]
        curve = kaplan_meier_curve(times, censored, HORIZON_S)
        q = {}
        for target in (0.75, 0.5, 0.25):
            q[target] = next((t for t, s in curve if s <= target), float("nan"))
        out.append({
            "satellites": sat_count, "planes": planes, "terminals": terminal_count, "architecture": arch,
            "time_to_25pct_failed_s": q[0.75], "time_to_50pct_failed_s": q[0.5],
            "time_to_75pct_failed_s": q[0.25], "final_survival": curve[-1][1],
        })
    return out


def tolerance_sensitivity_rows(single_rows, sat_count, planes, terminal_count, multipliers=(0.5, 1.0, 2.0, 4.0)):
    """At this configuration, how does success rate change if each
    thread's tolerance were scaled by `multipliers`? Shows whether
    conclusions depend on the specific assumed tolerance values."""
    by_thread = {}
    for row in single_rows:
        by_thread.setdefault(row["thread"], []).append(row)

    out = []
    for thread_key, rows in sorted(by_thread.items()):
        base_tolerance_s = MISSION_THREADS[thread_key]["latency_tolerance_s"]
        for mult in multipliers:
            scaled_tolerance_s = base_tolerance_s * mult
            successes = sum(
                1 for r in rows
                if not r["structural_incapacity"] and r["produced_tier"] and r["latency_s"] <= scaled_tolerance_s
            )
            n = len(rows)
            out.append({
                "satellites": sat_count, "planes": planes, "terminals": terminal_count, "thread": thread_key,
                "tolerance_multiplier": mult, "tolerance_s": scaled_tolerance_s,
                "n_trials": n, "successes": successes, "success_rate": successes / n if n else float("nan"),
            })
    return out


def cost_tradeoff_row(sat_count, planes, terminal_count, max_tiers_used, success_rate):
    relative_cost = (
        RELATIVE_COST_PER_SATELLITE * sat_count
        + RELATIVE_COST_PER_TERMINAL * terminal_count
        + RELATIVE_COST_PER_PROCESSING_TIER * max_tiers_used
    )
    return {
        "satellites": sat_count, "planes": planes, "terminals": terminal_count, "processing_tiers": max_tiers_used,
        "relative_cost": relative_cost, "success_rate": success_rate,
    }


def main():
    rng = __import__("random").Random(SEED)

    summary_rows, cell_status_rows, all_sig_rows, cost_rows = [], [], [], []
    feasibility_rows, km_rows, tolerance_rows = [], [], []

    for total_sats, planes, phasing_factor in SAT_CONFIGS:
        print(f"\n=== Walker config: {total_sats} sats / {planes} planes / F={phasing_factor} ===")
        aoi_by_sat, downlink_by_site_by_sat = build_config_windows(total_sats, planes, phasing_factor)
        print(f"  {len(aoi_by_sat)} satellites propagated; "
              f"AOI events: {sum(len(w) for w in aoi_by_sat.values())}")

        feasibility_rows.extend(feasibility_rows_for_config(total_sats, planes, aoi_by_sat))

        is_largest = (total_sats, planes, phasing_factor) == SAT_CONFIGS[-1]
        is_baseline = (total_sats, planes, phasing_factor) == SAT_CONFIGS[0]

        for terminal_count in TERMINAL_COUNTS:
            downlink_by_sat = build_downlink_windows_by_sat(downlink_by_site_by_sat, terminal_count)
            print(f"  terminals={terminal_count}: {sum(len(w) for w in downlink_by_sat.values())} downlink windows")

            single_rows, cadence_rows = run_cell(total_sats, planes, terminal_count, aoi_by_sat, downlink_by_sat, rng)
            cell_summary = summarize_cell(single_rows, cadence_rows, total_sats, planes, terminal_count)
            summary_rows.extend(cell_summary)

            status, best_or_reason, sig_rows = cell_pairwise_significance(
                single_rows, cadence_rows, total_sats, planes, terminal_count
            )
            all_sig_rows.extend(sig_rows)
            cell_status_rows.append({
                "satellites": total_sats, "planes": planes, "terminals": terminal_count,
                "status": status, "best_architecture_or_reason": best_or_reason,
            })
            print(f"  Cell status: {status} ({best_or_reason})")

            overall_rate = sum(r["successes"] for r in cell_summary) / sum(r["n_trials"] for r in cell_summary)
            cost_rows.append(cost_tradeoff_row(total_sats, planes, terminal_count, max_tiers_used=4, success_rate=overall_rate))

            if is_baseline or is_largest:
                km_rows.extend(km_summary_rows(single_rows, total_sats, planes, terminal_count))
                if terminal_count == 1:
                    tolerance_rows.extend(tolerance_sensitivity_rows(single_rows, total_sats, planes, terminal_count))

    out_dir = Path("results/raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    def _write(name, rows):
        if not rows:
            return
        with (out_dir / name).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {len(rows)} rows to {out_dir / name}")

    _write("e12_access_sweep.csv", summary_rows)
    _write("e12_cell_status.csv", cell_status_rows)
    _write("e12_significance_by_cell.csv", all_sig_rows)
    _write("e12_cost_tradeoff.csv", cost_rows)
    _write("e12_feasibility_floors.csv", feasibility_rows)
    _write("e12_km_summary.csv", km_rows)
    _write("e12_tolerance_sensitivity.csv", tolerance_rows)

    print("\nCell status counts:")
    from collections import Counter
    print(Counter(r["status"] for r in cell_status_rows))

    print("\nStructurally infeasible threads (tolerance below the floor at ANY access level):")
    seen = set()
    for r in feasibility_rows:
        if r["status"] == "INFEASIBLE_STRUCTURAL" and r["thread"] not in seen:
            seen.add(r["thread"])
            print(f"  {r['thread']}: tolerance={r['tolerance_s']}s, structural floor={r['structural_floor_s']:.1f}s")


if __name__ == "__main__":
    main()
