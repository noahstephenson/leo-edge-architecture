"""Experiment 12: Access/revisit sweep -- the v3 core experiment.

v2 and v3's shared finding is that access (contact frequency), not
processing architecture, dominates mission-thread success at the
single-satellite/single-terminal baseline. This experiment makes access
the independent variable: sweep satellite count and Army ground-terminal
count, and re-run the Part-1-fixed mission-thread evaluation at each
access level, extending orbit/constellation.py's phase-offset machinery
(not duplicating it -- base access windows are computed once per site via
real SGP4, then cheaply time-shifted for additional satellites) for the
satellite dimension, and unioning access windows across terminal sites for
the terminal dimension.

Scope reduction for tractability (documented, not silent, per
docs/DECISION_LOG.md): this sweep still evaluates all 7 architectures and
all 4 mission threads at every one of the 18 (satellite, terminal) cells,
but with 2 conditions (NOMINAL and COMBINED_DEGRADED, the nominal and
worst-case bookends) instead of e11's 5, and fewer trials per cell than
e11's single-access-level run, since this sweep spans 18 cells instead of
1. MT-4's cadence evaluation additionally samples a bounded, evenly-spaced
subset of AOI passes per trial rather than walking every pass, since pass
count scales with satellite count (up to ~900 passes/week at 32
satellites) and walking all of them at every trial would make the highest
access levels intractable.

Known modeling limitation, discovered while validating this experiment
(docs/DECISION_LOG.md): phase-shifting one orbital plane (the same
approach orbit/constellation.py already used for e09) spreads satellites
within a single plane, not across multiple planes. A single plane's
ground track still only crosses a given site's visibility circle during
specific parts of its precession cycle, so many satellites in one plane
produce clustered bursts of closely-spaced passes separated by long gaps,
not evenly-spaced revisits. Total contact-duration coverage still rises
monotonically and substantially with satellite count (confirmed: 1.5% of
the week at 1 satellite to ~27% at 32, single terminal), but tight
latency-tolerance mission threads can still fail even at high total
coverage if they land in one of the remaining long gaps. This is a real
property of single-plane phasing, not a bug, and it's exactly why success
rates in this sweep don't scale as cleanly with satellite count as total
coverage duration does. A true global-revisit constellation (multiple
orbital planes) would need more than phase-shifting one plane, which is
out of scope for extending, not duplicating, orbit/constellation.py's
existing machinery.
"""

import csv
import math
import random
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))

from e11_mission_thread_success import (  # noqa: E402
    ARCHITECTURE_FACTORIES, TERMINAL_CLASSES, HORIZON_S, EPOCH, AOI_LAT, AOI_LON,
    evaluate_single_request, evaluate_cadence, draw_request_context,
)
from leo_edge.mission_threads import MISSION_THREADS  # noqa: E402
from leo_edge.orbit.access import generate_access_windows  # noqa: E402
from leo_edge.stats import wilson_ci, paired_bootstrap_diff_ci  # noqa: E402

SAT_COUNTS = [1, 2, 4, 8, 16, 32]
TERMINAL_COUNTS = [1, 2, 4]

# 4 notional Army ground-terminal sites, documented ASSUMED coordinates,
# spread in latitude/longitude so they're genuinely different SGP4 ground
# tracks, not the same point relabeled as "more terminals."
TERMINAL_SITES = [(40.0, 0.0), (35.0, 20.0), (50.0, -10.0), (30.0, 40.0)]

CONDITIONS_SWEPT = {
    "NOMINAL": {"interference_derate": 1.0, "contact_denial_frac": 0.0, "tasking_delay_s": 60},
    "COMBINED_DEGRADED": {"interference_derate": 0.5, "contact_denial_frac": 0.3, "tasking_delay_s": 180},
}

N_TRIALS = 80
N_TRIALS_CADENCE = 10
MAX_CADENCE_PASSES = 40
SEED = 0

# Notional relative cost proxy for the cost-tradeoff figure. ASSUMED, not a
# real acquisition cost estimate: represents "one more satellite of
# constellation access" as more expensive than "one more ground terminal
# site," which is more expensive than "requiring one more onboard
# processing tier from the provider" (a software/interface requirement,
# not new hardware). Every number here is a relative unit, not a dollar
# figure, and is stated exactly this plainly in docs/ACQUISITION_IMPLICATIONS.md.
RELATIVE_COST_PER_SATELLITE = 10.0
RELATIVE_COST_PER_TERMINAL = 3.0
RELATIVE_COST_PER_PROCESSING_TIER = 1.0


def _windows_since_epoch(lat, lon):
    access = generate_access_windows(
        ground_lat=lat, ground_lon=lon, min_elevation_deg=10.0,
        altitude_km=550.0, inclination_deg=97.4, duration_hours=168.0,
    )
    out = []
    for w in access:
        start = datetime.fromisoformat(w["start"].replace("Z", "+00:00"))
        offset_s = (start - EPOCH).total_seconds()
        out.append((offset_s, float(w["duration_s"])))
    return sorted(out, key=lambda p: p[0])


def _orbital_period_s(altitude_km=550.0):
    mu = 398600.4418
    r_earth = 6378.137
    a = r_earth + altitude_km
    return 2 * math.pi * math.sqrt(a ** 3 / mu)


def _phase_shift_windows(base_windows, sat_count, horizon_s):
    """Cheaply extend base (single-satellite) windows to sat_count
    satellites by time-shifting copies -- same approach as
    orbit/constellation.py's generate_constellation_contacts -- instead of
    a second SGP4 propagation per satellite."""
    period_s = _orbital_period_s()
    offset_s = period_s / sat_count
    out = []
    for i in range(sat_count):
        shift = i * offset_s
        for start_s, dur_s in base_windows:
            shifted_start = start_s + shift
            if shifted_start <= horizon_s:
                out.append((shifted_start, dur_s))
    return sorted(out, key=lambda p: p[0])


def _merge_windows(windows):
    """Union overlapping windows into a minimal non-overlapping set: the
    terminal can only use one contact at a time regardless of how many
    satellites/sites are simultaneously visible (a single logical delivery
    pipe, not parallel radios -- a stated, documented simplification)."""
    if not windows:
        return []
    windows = sorted(windows, key=lambda w: w[0])
    merged = [[windows[0][0], windows[0][1]]]
    for start, dur in windows[1:]:
        end = start + dur
        last_start, last_dur = merged[-1]
        last_end = last_start + last_dur
        if start <= last_end:
            merged[-1][1] = max(last_end, end) - last_start
        else:
            merged.append([start, dur])
    return [(s, d) for s, d in merged]


def _evenly_spaced_sample(items, max_n):
    if len(items) <= max_n:
        return items
    stride = len(items) / max_n
    return [items[int(i * stride)] for i in range(max_n)]


def build_downlink_windows(base_by_site, sat_count, terminal_count):
    sites = TERMINAL_SITES[:terminal_count]
    all_windows = []
    for site in sites:
        all_windows.extend(_phase_shift_windows(base_by_site[site], sat_count, HORIZON_S))
    return _merge_windows(all_windows)


def build_aoi_windows(base_aoi, sat_count):
    return _merge_windows(_phase_shift_windows(base_aoi, sat_count, HORIZON_S))


def run_cell(sat_count, terminal_count, downlink_windows, aoi_windows, rng):
    single_rows = []
    single_request_threads = {k: v for k, v in MISSION_THREADS.items() if not v["cadence"]}
    for thread_key, thread in single_request_threads.items():
        for terminal_key, terminal in TERMINAL_CLASSES.items():
            for condition_key, condition in CONDITIONS_SWEPT.items():
                for trial_idx in range(N_TRIALS):
                    ctx = draw_request_context(rng, downlink_windows)
                    for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                        row = evaluate_single_request(
                            factory, thread_key, thread, terminal_key, terminal,
                            condition_key, condition, ctx, trial_idx, downlink_windows, aoi_windows,
                        )
                        row["satellites"] = sat_count
                        row["terminals"] = terminal_count
                        single_rows.append(row)

    cadence_rows = []
    thread = MISSION_THREADS["MT4_PERSISTENT_MONITORING"]
    sampled_aoi = _evenly_spaced_sample(aoi_windows, MAX_CADENCE_PASSES)
    for terminal_key, terminal in TERMINAL_CLASSES.items():
        for condition_key, condition in CONDITIONS_SWEPT.items():
            for trial_idx in range(N_TRIALS_CADENCE):
                denial_rolls = [rng.random() for _ in downlink_windows]
                for arch_name, factory in ARCHITECTURE_FACTORIES.items():
                    row = evaluate_cadence(
                        factory, thread, terminal_key, terminal, condition_key, condition,
                        denial_rolls, trial_idx, downlink_windows, sampled_aoi,
                    )
                    row["satellites"] = sat_count
                    row["terminals"] = terminal_count
                    cadence_rows.append(row)

    return single_rows, cadence_rows


def summarize_cell(single_rows, cadence_rows, sat_count, terminal_count):
    """Per (architecture, satellites, terminals) success rate pooling all
    threads/terminal-classes/conditions in this cell, plus each thread
    separately (needed for the per-thread sweep figure)."""
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
            "satellites": sat_count, "terminals": terminal_count, "architecture": arch, "thread": thread,
            "n_trials": n, "successes": s, "success_rate": rate,
            "success_rate_ci_lower": lo, "success_rate_ci_upper": hi,
        })
    return out


def cell_pairwise_significance(single_rows, cadence_rows, sat_count, terminal_count):
    """Paired comparison of every architecture pair, pooling all
    threads/terminal-classes/conditions in this cell (paired within
    (thread, terminal_class, condition, trial_idx))."""
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
        return None, []

    results = []
    for i, a in enumerate(arch_names):
        for b in arch_names[i + 1:]:
            diff, lo, hi, significant = paired_bootstrap_diff_ci(
                paired_series[a], paired_series[b], n_resamples=1000, seed=SEED,
            )
            results.append({
                "satellites": sat_count, "terminals": terminal_count,
                "architecture_a": a, "architecture_b": b, "n_paired_trials": n,
                "diff_a_minus_b": diff, "significant": significant,
            })

    # Best statistically-distinguishable architecture: the one with the
    # highest overall rate in this cell that beats every other
    # architecture's rate by a significant margin; "no significant
    # difference" if no single architecture clears that bar.
    rates = {a: sum(paired_series[a]) / n for a in arch_names}
    ranked = sorted(arch_names, key=lambda a: rates[a], reverse=True)
    best = ranked[0]
    beats_all = True
    for other in ranked[1:]:
        match = [r for r in results if {r["architecture_a"], r["architecture_b"]} == {best, other}]
        if not match or not match[0]["significant"]:
            beats_all = False
            break
    best_significant = best if beats_all and rates[best] > 0 else "NO_SIGNIFICANT_DIFFERENCE"

    return best_significant, results


def cost_tradeoff_row(sat_count, terminal_count, max_tiers_used, success_rate):
    relative_cost = (
        RELATIVE_COST_PER_SATELLITE * sat_count
        + RELATIVE_COST_PER_TERMINAL * terminal_count
        + RELATIVE_COST_PER_PROCESSING_TIER * max_tiers_used
    )
    return {
        "satellites": sat_count, "terminals": terminal_count, "processing_tiers": max_tiers_used,
        "relative_cost": relative_cost, "success_rate": success_rate,
    }


def main():
    rng = random.Random(SEED)

    print("Computing base access windows (real SGP4, once per site)...")
    base_by_site = {site: _windows_since_epoch(*site) for site in TERMINAL_SITES}
    base_aoi = _windows_since_epoch(AOI_LAT, AOI_LON)
    for site, windows in base_by_site.items():
        print(f"  terminal site {site}: {len(windows)} base windows")
    print(f"  AOI site ({AOI_LAT},{AOI_LON}): {len(base_aoi)} base windows")

    summary_rows = []
    best_arch_rows = []
    cost_rows = []
    all_sig_rows = []

    for sat_count in SAT_COUNTS:
        aoi_windows = build_aoi_windows(base_aoi, sat_count)
        for terminal_count in TERMINAL_COUNTS:
            downlink_windows = build_downlink_windows(base_by_site, sat_count, terminal_count)
            print(f"\n=== satellites={sat_count} terminals={terminal_count} "
                  f"(downlink windows: {len(downlink_windows)}, AOI windows: {len(aoi_windows)}) ===")

            single_rows, cadence_rows = run_cell(sat_count, terminal_count, downlink_windows, aoi_windows, rng)
            cell_summary = summarize_cell(single_rows, cadence_rows, sat_count, terminal_count)
            summary_rows.extend(cell_summary)

            best_arch, sig_rows = cell_pairwise_significance(single_rows, cadence_rows, sat_count, terminal_count)
            all_sig_rows.extend(sig_rows)
            best_arch_rows.append({"satellites": sat_count, "terminals": terminal_count, "best_architecture": best_arch})
            print(f"  Best statistically-distinguishable architecture: {best_arch}")

            overall_rate = sum(r["successes"] for r in cell_summary) / sum(r["n_trials"] for r in cell_summary)
            cost_rows.append(cost_tradeoff_row(sat_count, terminal_count, max_tiers_used=4, success_rate=overall_rate))

    out_dir = Path("results/raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "e12_access_sweep.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    with (out_dir / "e12_best_architecture_by_access.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(best_arch_rows[0].keys()))
        writer.writeheader()
        writer.writerows(best_arch_rows)

    with (out_dir / "e12_significance_by_cell.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_sig_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_sig_rows)

    with (out_dir / "e12_cost_tradeoff.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_rows[0].keys()))
        writer.writeheader()
        writer.writerows(cost_rows)

    print(f"\nSaved {len(summary_rows)} summary rows to {out_dir / 'e12_access_sweep.csv'}")
    print(f"Saved {len(best_arch_rows)} best-architecture rows to {out_dir / 'e12_best_architecture_by_access.csv'}")
    print(f"Saved {len(all_sig_rows)} significance rows to {out_dir / 'e12_significance_by_cell.csv'}")
    print(f"Saved {len(cost_rows)} cost-tradeoff rows to {out_dir / 'e12_cost_tradeoff.csv'}")


if __name__ == "__main__":
    main()
