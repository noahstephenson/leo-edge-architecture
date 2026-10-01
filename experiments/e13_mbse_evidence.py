"""Selected evidence cases for the conceptual architecture study.

Run from the repository root with ``uv run python experiments/e13_mbse_evidence.py``.
The 48-hour horizon and sample counts are stated in the output configuration.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

import skyfield.api  # noqa: F401 -- fail visibly if orbit propagation is unavailable

from e11_mission_thread_success import (
    ALTITUDE_KM, AOI_LAT, AOI_LON, ARCHITECTURE_FACTORIES, CONDITIONS,
    EPOCH, INCLINATION_DEG, MIN_ELEVATION_DEG, PRIOR_REFERENCE_PROB,
    PROCESSING_TIME_S, SCENE_BYTES, TERMINAL_CLASSES,
    _offset_windows, all_collection_events, evaluate_cadence,
    evaluate_single_request, next_collection_event,
)
from leo_edge.architectures import COMPRESSED_FULL_FRACTION
from leo_edge.mission_threads import MISSION_THREADS
from leo_edge.orbit.constellation import (
    generate_walker_delta_tles, per_satellite_access_windows,
)
from leo_edge.stats import wilson_ci


WALKER_CONFIGS = ((1, 1, 0), (8, 4, 1), (24, 8, 1))
TERMINAL_SITES = ((40.0, 0.0), (35.0, 20.0), (50.0, -10.0), (30.0, 40.0))
SITE_COUNTS = (1, 4)
CONDITION_IDS = ("NOMINAL", "COMBINED_DEGRADED")
SOURCE_PATHS = (
    "experiments/e13_mbse_evidence.py",
    "experiments/e11_mission_thread_success.py",
    "src/leo_edge/architectures.py",
    "src/leo_edge/simulation.py",
    "src/leo_edge/products.py",
    "src/leo_edge/mission_threads.py",
    "src/leo_edge/orbit/access.py",
    "src/leo_edge/orbit/constellation.py",
    "src/leo_edge/stats.py",
    "src/leo_edge/product_sizing.yaml",
    "src/leo_edge/configuration.py",
    "experiments/evidence_analysis.py",
    "results/history/pre-completion-2026-09-30/single_request_trials.csv",
    "model/system.yaml",
    "model/architecture.yaml",
    "model/assurance.yaml",
    "model/traceability.yaml",
    ".python-version",
    "pyproject.toml",
    "uv.lock",
)
HASH_METHOD = "SHA-256 of UTF-8 text with CRLF/CR normalized to LF"


def _sha256(path: Path) -> str:
    """Hash UTF-8 text with canonical LF endings across Git checkouts.

    Git may check out these Python, YAML, CSV, and JSON files with CRLF on
    Windows. Normalizing line endings preserves the content audit while
    allowing a clean clone on another platform to verify the same freeze.
    """
    canonical = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(canonical).hexdigest()


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _merged_windows(site_windows: list[list[tuple[float, float, float]]]):
    """Union overlapping site opportunities into one logical link per sat."""
    intervals = sorted((start, start + duration)
                       for windows in site_windows for start, duration, _ in windows)
    merged: list[list[float]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end - start, (start + end) / 2.0) for start, end in merged]


def _access_for_config(config: tuple[int, int, int], hours: float,
                       step_seconds=30.0, start_offset_s=0.0, aoi_shift=0.0,
                       single_site_only=False):
    total, planes, phasing = config
    tles = generate_walker_delta_tles(total, planes, phasing, ALTITUDE_KM, INCLINATION_DEG)
    aoi_raw = per_satellite_access_windows(tles, AOI_LAT + aoi_shift, AOI_LON + aoi_shift,
                                           MIN_ELEVATION_DEG, hours, step_seconds, start_offset_s)
    def offsets(windows):
        return [(start - start_offset_s, duration, peak - start_offset_s)
                for start, duration, peak in _offset_windows(windows)]
    aoi = {sat: offsets(windows) for sat, windows in aoi_raw.items()}
    sites = []
    for lat, lon in TERMINAL_SITES[:1] if single_site_only else TERMINAL_SITES:
        raw = per_satellite_access_windows(tles, lat, lon,
                                           MIN_ELEVATION_DEG, hours, step_seconds, start_offset_s)
        sites.append({sat: offsets(windows)
                      for sat, windows in raw.items()})
    by_count = {}
    for count in (1,) if single_site_only else SITE_COUNTS:
        by_count[count] = {
            sat: _merged_windows([site[sat] for site in sites[:count]])
            for sat in aoi
        }
    return aoi, by_count


def _trial_context(rng: random.Random, condition: dict, aoi: dict,
                   downlink: dict, horizon_s: float):
    request_s = rng.uniform(0.0, max(0.0, horizon_s - 3600.0))
    prior_roll = rng.random()
    collection = next_collection_event(request_s + condition["tasking_delay_s"], aoi)
    if collection is None:
        return {"request_time_s": request_s, "prior_reference_roll": prior_roll,
                "collection": None, "downlink_windows": [], "denial_rolls": []}
    windows = downlink[collection[1]]
    return {"request_time_s": request_s, "prior_reference_roll": prior_roll,
            "collection": collection, "downlink_windows": windows,
            "denial_rolls": [rng.random() for _ in windows]}


def _single_rows(config, count, aoi, downlink, hours, trials, seed):
    total, planes, phasing = config
    rows = []
    threads = {key: value for key, value in MISSION_THREADS.items()
               if not value["cadence"]}
    for thread_id, thread in threads.items():
        for terminal_id, terminal in TERMINAL_CLASSES.items():
            for condition_id in CONDITION_IDS:
                condition = CONDITIONS[condition_id]
                # The same request, prior-reference draw, and contact denial
                # rolls are applied to every architecture in this cell.
                rng = random.Random(f"{seed}:{total}:{planes}:{phasing}:{count}:"
                                    f"{thread_id}:{terminal_id}:{condition_id}")
                for trial in range(trials):
                    context = _trial_context(rng, condition, aoi, downlink,
                                             hours * 3600.0)
                    context_sha256 = hashlib.sha256(
                        json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest()
                    for arch_id, factory in ARCHITECTURE_FACTORIES.items():
                        result = evaluate_single_request(
                            factory, thread_id, thread, terminal_id, terminal,
                            condition_id, condition, context, trial,
                        )
                        rows.append({
                            "walker": f"{total}/{planes}/{phasing}",
                            "terminal_sites": count, "terminal_class": terminal_id,
                            "condition": condition_id, "thread": thread_id,
                            "trial": trial, "architecture_id": arch_id,
                            "mode": "single_request",
                            "receiver_semantics": "requesting_terminal" if count == 1 else "pooled_connected_receiver_zero_forwarding_delay",
                            "paired_context_sha256": context_sha256,
                            "request_time_s": result["request_time_s"],
                            "collection_time_s": result["collection_time_s"],
                            "collecting_satellite": result["sat_id"],
                            "delivered_tier": result["delivered_tier"],
                            "product_arrival_time_s": result["product_arrival_time_s"],
                            "terminal_processing_time_s": result["terminal_processing_time_s"],
                            "final_availability_time_s": result["final_availability_time_s"],
                            "latency_s": result["latency_s"],
                            "has_prior_reference": result["has_prior_reference"],
                            "produced": result["produced_tier"],
                            "structural_incapacity": result["structural_incapacity"],
                            "success": result["success"],
                            **{key: result[key] for key in (
                                "collection_delay_s", "full_scene_arrival_time_s", "full_scene_latency_s",
                                "full_scene_deadline_met", "bytes_transmitted", "contact_utilization", "outcome")},
                            "product_progress_json": json.dumps(result["product_progress"], sort_keys=True),
                        })
    return rows


def _cadence_rows(config, count, aoi, downlink, trials, seed):
    total, planes, phasing = config
    rows = []
    thread = MISSION_THREADS["MT4_PERSISTENT_MONITORING"]
    events = all_collection_events(aoi)
    # Every collection event is retained: the MT-4 success rule depends on
    # consecutive missed passes, so dropping intermediate events changes it.
    for terminal_id, terminal in TERMINAL_CLASSES.items():
        for condition_id in CONDITION_IDS:
            condition = CONDITIONS[condition_id]
            rng = random.Random(f"{seed}:{total}:{planes}:{phasing}:{count}:"
                                f"MT4:{terminal_id}:{condition_id}")
            # Nominal cadence over this fixed geometry is deterministic;
            # repeating it would manufacture an apparent sample size. The
            # degraded condition samples independent denial rolls instead.
            n_draws = 1 if condition_id == "NOMINAL" else trials
            for trial in range(n_draws):
                denial_rolls = {
                    sat: [rng.random() for _ in windows]
                    for sat, windows in downlink.items()
                }
                context_sha256 = hashlib.sha256(
                    json.dumps({"events": events, "denial_rolls": denial_rolls},
                               sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                for arch_id, factory in ARCHITECTURE_FACTORIES.items():
                    result = evaluate_cadence(
                        factory, thread, terminal_id, terminal,
                        condition_id, condition, events, downlink,
                        denial_rolls, trial,
                    )
                    rows.append({
                        "walker": f"{total}/{planes}/{phasing}",
                        "terminal_sites": count, "terminal_class": terminal_id,
                        "condition": condition_id,
                        "thread": "MT4_PERSISTENT_MONITORING", "trial": trial,
                        "architecture_id": arch_id, "mode": "independent_opportunities",
                        "receiver_semantics": "requesting_terminal" if count == 1 else "pooled_connected_receiver_zero_forwarding_delay",
                        "paired_context_sha256": context_sha256,
                        "total_passes": result["total_passes"],
                        "passes_met": result["passes_met"],
                        "cadence_rate": result["cadence_rate"],
                        "structural_incapacity": result["structural_incapacity"],
                        "success": result["success"],
                    })
    return rows


def _summary(rows: list[dict]):
    groups = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in (
            "walker", "terminal_sites", "terminal_class", "condition",
            "thread", "architecture_id", "mode",
        ))
        groups[key].append(row)
    out = []
    for key, group in sorted(groups.items()):
        n = len(group)
        successes = sum(row["success"] for row in group)
        # One deterministic nominal cadence sequence is a scenario result,
        # not a Bernoulli sample from an uncertainty distribution.
        lower, upper = (("", "") if key[-1] == "independent_opportunities" and key[3] == "NOMINAL"
                        else wilson_ci(successes, n))
        out.append(dict(zip((
            "walker", "terminal_sites", "terminal_class", "condition",
            "thread", "architecture_id", "mode"), key),
            n_trials=n, successes=successes, success_rate=successes / n,
            ci95_lower=lower, ci95_upper=upper,
            no_usable_product_by_horizon=(sum(not row["produced"] for row in group)
                                          if key[-1] == "single_request" else ""),
            no_collection=(sum(row["collection_time_s"] is None for row in group)
                           if key[-1] == "single_request" else "")))
    return out


def _parametric_rows():
    rows = []
    raw = SCENE_BYTES
    processed = int(raw * COMPRESSED_FULL_FRACTION)
    for rate in (5_000_000, 50_000_000):
        for lead in (0.0, 30.0):
            exposed = max(0.0, PROCESSING_TIME_S - lead)
            saved = (raw - processed) * 8 / rate
            rows.append({
                "comparison": "A1 compressed full vs A0 raw full",
                "rate_bps": rate, "processing_lead_s": lead,
                "raw_bytes": raw, "processed_bytes": processed,
                "processing_time_s": PROCESSING_TIME_S,
                "exposed_processing_s": exposed,
                "transmission_time_saved_s": saved,
                "compressed_latency_advantage_s": saved - exposed,
                "caveat": "P4 full-scene products differ in lossy fidelity",
            })
    return rows


def _audit(single: list[dict], cadence: list[dict], trials: int,
           cadence_trials: int, access_counts: list[dict]):
    groups = defaultdict(list)
    for row in single + cadence:
        key = tuple(row[field] for field in (
            "walker", "terminal_sites", "terminal_class", "condition",
            "thread", "trial", "mode",
        ))
        groups[key].append(row)
    expected = set(ARCHITECTURE_FACTORIES)
    paired = all({r["architecture_id"] for r in group} == expected and
                 len(group) == len(expected) for group in groups.values())
    same_context = all(len({r["paired_context_sha256"] for r in group}) == 1
                       for group in groups.values())
    events_by_walker = {row["walker"]: row["aoi_events"] for row in access_counts}
    cadence_complete = all(row["total_passes"] == events_by_walker[row["walker"]]
                           for row in cadence)
    semantics = all(not r["success"] or
                    (r["produced"] and r["final_availability_time_s"] is not None)
                    for r in single)
    expected_single = len(WALKER_CONFIGS) * len(SITE_COUNTS) * len(TERMINAL_CLASSES) * len(CONDITION_IDS) * 3 * trials * len(expected)
    expected_cadence = len(WALKER_CONFIGS) * len(SITE_COUNTS) * len(TERMINAL_CLASSES) * (1 + cadence_trials) * len(expected)
    passed = (paired and same_context and cadence_complete and semantics
              and len(single) == expected_single and len(cadence) == expected_cadence)
    return {"passed": passed, "paired_trials_complete": paired,
            "paired_context_identical": same_context,
            "cadence_includes_all_collection_events": cadence_complete,
            "success_requires_available_product": semantics,
            "single_rows": len(single), "expected_single_rows": expected_single,
            "cadence_rows": len(cadence), "expected_cadence_rows": expected_cadence,
            "distinct_paired_trials": len(groups)}


def check_freeze(output: Path) -> None:
    """Check frozen bytes and current source without rerunning propagation."""
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing freeze manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("hash_method") != HASH_METHOD:
        raise RuntimeError("Evidence manifest has an unsupported hash method")
    repo = Path(__file__).resolve().parents[1]
    failures = []
    for relative, expected in manifest["source_sha256"].items():
        path = repo / relative
        if not path.is_file() or _sha256(path) != expected:
            failures.append(f"source changed: {relative}")
    for filename, expected in manifest["result_sha256"].items():
        path = output / filename
        if not path.is_file() or _sha256(path) != expected:
            failures.append(f"result changed: {filename}")
    if not manifest.get("audit_passed") or failures:
        raise RuntimeError("Evidence check failed: " + "; ".join(failures))
    from evidence_analysis import select
    claim_sources = {}
    for claim in json.loads((output / 'claims.json').read_text()):
        if claim['source'] not in claim_sources:
            with (output / claim['source']).open(newline='', encoding='utf-8') as stream:
                claim_sources[claim['source']] = list(csv.DictReader(stream))
        rows = claim_sources[claim['source']]
        group = select(rows, claim['filters'])
        count = (float(group[0][claim['column']]) if claim['aggregation'] == 'first_numeric'
                 else sum(row[claim['column']] == 'True' for row in group))
        if count != claim['numerator'] or len(group) != claim['denominator']:
            raise RuntimeError('Claim filter disagrees with rows: ' + claim['claim'])
    print(f"Evidence verified: {len(manifest['source_sha256'])} sources, "
          f"{len(manifest['result_sha256'])} result files", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/current"))
    parser.add_argument("--hours", type=float, default=48.0)
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--cadence-trials", type=int, default=6)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--check", action="store_true",
                        help="verify current source/result hashes without running cases")
    parser.add_argument("--replace", action="store_true",
                        help="explicitly replace an existing output directory")
    args = parser.parse_args()
    if args.check:
        check_freeze(args.output)
        return
    if args.hours <= 1 or args.trials < 1 or args.cadence_trials < 1:
        parser.error("hours must exceed one and trial counts must be positive")
    if args.output.exists() and any(args.output.iterdir()) and not args.replace:
        parser.error(f"output directory already contains files: {args.output}; "
                     "use --check to verify it or choose a new --output")
    args.output.mkdir(parents=True, exist_ok=True)

    single, cadence = [], []
    access_counts = []
    for config in WALKER_CONFIGS:
        print(f"Propagating Walker {config[0]}/{config[1]}/{config[2]} for {args.hours:g} h", flush=True)
        aoi, downlink_by_count = _access_for_config(config, args.hours)
        access_counts.append({"walker": f"{config[0]}/{config[1]}/{config[2]}",
                              "aoi_events": len(all_collection_events(aoi)),
                              "downlink_windows_one_site": sum(map(len, downlink_by_count[1].values())),
                              "downlink_windows_four_sites": sum(map(len, downlink_by_count[4].values()))})
        for count in SITE_COUNTS:
            downlink = downlink_by_count[count]
            single.extend(_single_rows(config, count, aoi, downlink,
                                       args.hours, args.trials, args.seed))
            cadence.extend(_cadence_rows(config, count, aoi, downlink,
                                         args.cadence_trials, args.seed))

    config_doc = {
        "receiver_semantics": {"1": "requesting_terminal", "4": "pooled_connected_receiver_zero_forwarding_delay"},
        "cadence_scope": "independent opportunities; no shared queue or capacity reservation",
        "collection_proxy": "peak elevation; no optical field of regard, illumination, clouds, or collection duration",
        "access_sampling_step_s": 30,
        "full_scene_receipt_deadline_s": 3600,
        "status": "selected synthetic evidence",
        "walker_t_p_f": WALKER_CONFIGS, "terminal_sites_lat_lon": TERMINAL_SITES,
        "terminal_site_counts": SITE_COUNTS, "terminal_classes": {
            key: {"rate_bps": value["rate_bps"],
                  "derivation_time_s": value["derivation_time_s"],
                  "derivable_tiers": [tier.value for tier in value["derivable_tiers"]]}
            for key, value in TERMINAL_CLASSES.items()},
        "conditions": {key: CONDITIONS[key] for key in CONDITION_IDS},
        "scene_bytes": SCENE_BYTES, "processing_time_s": PROCESSING_TIME_S,
        "prior_reference_probability": PRIOR_REFERENCE_PROB,
        "horizon_hours": args.hours, "single_request_trials_per_cell": args.trials,
        "cadence_trials_degraded_per_cell": args.cadence_trials,
        "cadence_trials_nominal_per_cell": 1,
        "cadence_event_policy": "all collection events in the evaluation horizon",
        "seed": args.seed,
        "orbit": {"epoch_utc": EPOCH.isoformat(), "altitude_km": ALTITUDE_KM,
                  "inclination_deg": INCLINATION_DEG,
                  "minimum_elevation_deg": MIN_ELEVATION_DEG,
                  "aoi_lat_lon": [AOI_LAT, AOI_LON]},
        "source_classification": {
            "orbital_access": "synthetic TLE plus SGP4 geometry; not measured access",
            "scene_product_rates_deadlines_compute": "sensitivity-only assumptions",
            "terminal_sites": "synthetic locations, not operational terminal locations",
            "mission_utility": "assumed tier sufficiency, not demonstrated capability",
            "imagery_benchmark": "optional synthetic benchmark is not calibrated into this analysis",
        },
        "scenario_labels": {
            "MT1_TIME_SENSITIVE_CUEING": "rapid area update (legacy key retained for file compatibility)",
            "MT2_ROUTE_RECON_FIRST": "route-area observation",
            "MT3_BATTLE_DAMAGE_ASSESSMENT": "generic change assessment (legacy key retained for file compatibility)",
            "MT4_PERSISTENT_MONITORING": "repeated area update",
        },
        "sample_limitations": "48-hour geometry; request times sampled within the first 47 hours; 24 draws paired across A0-A6 within each fixed Walker/site/thread/terminal/condition cell, with independent draws across Walker and site cells; nominal cadence is one deterministic full pass sequence, while degraded cadence has six denial draws. Wilson intervals describe sampled uncertainty only, not model uncertainty or operational validity",
        "reproduce_command": "uv run python experiments/e13_mbse_evidence.py --output results/reproduced/current",
        "freeze_check_command": "uv run python experiments/e13_mbse_evidence.py --check",
    }
    audit = _audit(single, cadence, args.trials, args.cadence_trials, access_counts)
    if not audit["passed"]:
        raise RuntimeError(f"Evidence audit failed: {audit}")
    _write_csv(args.output / "single_request_trials.csv", single)
    _write_csv(args.output / "cadence_trials.csv", cadence)
    _write_csv(args.output / "summary.csv", _summary(single + cadence))
    _write_csv(args.output / "parametric.csv", _parametric_rows())
    _write_csv(args.output / "access_counts.csv", access_counts)
    from evidence_analysis import additional_evidence
    additional_evidence(args.output, single, args.hours, args.trials, args.seed,
                        _access_for_config, _trial_context, _write_csv, _write_json)
    _write_json(args.output / "config.json", config_doc)
    _write_json(args.output / "audit.json", audit)
    repo = Path(__file__).resolve().parents[1]
    manifest = {
        "seed": args.seed,
        "hash_method": HASH_METHOD,
        "source_sha256": {path: _sha256(repo / path) for path in SOURCE_PATHS},
        "result_sha256": {path.name: _sha256(path) for path in sorted(args.output.iterdir())
                          if path.is_file() and path.name != "manifest.json"},
        "audit_passed": audit["passed"],
    }
    _write_json(args.output / "manifest.json", manifest)
    print(f"Evidence: {len(single)} single-request and {len(cadence)} cadence rows; audit passed", flush=True)


if __name__ == "__main__":
    main()
