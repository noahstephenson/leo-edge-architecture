"""Experiment 07: Compare the adaptive policy against the best static architecture.

Uses the real AdaptivePolicy.choose(), which now returns an actual
architecture class, instead of a label that was mapped to Progressive as an
approximation of two different architectures.
"""

import csv
from pathlib import Path

from leo_edge.architectures import GroundOnly, CompressedFull, QuicklookFirst, RoiFirst, Progressive
from leo_edge.simulation import run_static_architecture
from leo_edge.policies.adaptive import AdaptivePolicy

STATIC_CANDIDATES = [GroundOnly, CompressedFull, QuicklookFirst, RoiFirst, Progressive]


def tfup_for_arch(arch_class, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
    res = run_static_architecture(
        arch_class, scene_bytes, contact_capacity_bytes / (rate_bps / 8), rate_bps, processing_time_s
    )
    return res.tfup_s, res.completed


def main():
    scene_bytes = 1e9
    rate_bps = 10e6
    processing_time_s = 30.0

    capacities = [int(50e6 * i) for i in range(1, 25)]

    policy = AdaptivePolicy()
    scene = {
        "bytes": scene_bytes,
        "compressed_bytes": int(scene_bytes * 0.3),
        "quicklook_bytes": int(scene_bytes * 0.02),
        "roi_bytes": int(scene_bytes * 0.1),
    }
    spacecraft_state = {"available_processing_energy": 1e6}

    rows = []
    for cap in capacities:
        static_results = {
            arch.__name__: tfup_for_arch(arch, scene_bytes, cap, rate_bps, processing_time_s)
            for arch in STATIC_CANDIDATES
        }
        completed_static = {
            name: tfup for name, (tfup, completed) in static_results.items() if completed
        }
        best_static_name, best_static_tfup = (
            min(completed_static.items(), key=lambda kv: kv[1])
            if completed_static
            else (None, float("nan"))
        )

        contact = {"capacity_bytes": cap}
        chosen_class = policy.choose(scene, spacecraft_state, contact)
        adaptive_tfup, adaptive_completed = static_results[chosen_class.__name__]

        rows.append({
            "capacity_bytes": cap,
            "adaptive_arch_name": chosen_class.__name__,
            "adaptive_tfup_s": adaptive_tfup,
            "adaptive_completed": adaptive_completed,
            "best_static_arch_name": best_static_name,
            "best_static_tfup_s": best_static_tfup,
        })

    print("Adaptive vs best static (sample)")
    for r in rows[:10]:
        print(r)

    out_path = Path("results/raw/e07_adaptive_policy.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
