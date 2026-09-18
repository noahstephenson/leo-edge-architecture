"""Experiment 07: Compare adaptive policy vs best static architecture."""

import csv
from pathlib import Path

from leo_edge.architectures import GroundOnly, CompressedFull, Progressive
from leo_edge.simulation import run_static_architecture
from leo_edge.policies.adaptive import AdaptivePolicy


def tfup_for_arch(ArchClass, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
    res = run_static_architecture(ArchClass, scene_bytes, contact_capacity_bytes / (rate_bps/8), rate_bps, processing_time_s)
    return res.tfup_s


def main():
    scene_bytes = 1e9
    rate_bps = 10e6
    processing_time_s = 30.0

    # capacities from 50 MB to 1.2 GB
    capacities = [int(50e6 * i) for i in range(1, 25)]

    policy = AdaptivePolicy()
    # scene info for policy
    scene = {
        "bytes": scene_bytes,
        "compressed_bytes": int(scene_bytes * 0.3),
        "quicklook_bytes": int(scene_bytes * 0.02),
        "roi_bytes": int(scene_bytes * 0.1),
    }
    spacecraft_state = {"available_processing_energy": 1e6}
    
    rows = []
    for cap in capacities:
        contact_duration_s = cap / (rate_bps/8)
        # static architectures
        tfup_ground = tfup_for_arch(GroundOnly, scene_bytes, cap, rate_bps, processing_time_s)
        tfup_compressed = tfup_for_arch(CompressedFull, scene_bytes, cap, rate_bps, processing_time_s)
        tfup_prog = tfup_for_arch(Progressive, scene_bytes, cap, rate_bps, processing_time_s)
        
        best_static_tfup = min(tfup_ground, tfup_compressed, tfup_prog)
        # adaptive choice
        contact = {"capacity_bytes": cap}
        choice = policy.choose(scene, spacecraft_state, contact)
        # map choice to architecture
        if choice == "compressed_full":
            adaptive_tfup = tfup_compressed
            arch_name = "CompressedFull"
        elif choice == "quicklook_roi":
            # approximate with Progressive
            adaptive_tfup = tfup_prog
            arch_name = "Progressive"
        else:
            adaptive_tfup = tfup_prog
            arch_name = "Progressive"

        rows.append({
            "capacity_bytes": cap,
            "adaptive_tfup_s": adaptive_tfup,
            "best_static_tfup_s": best_static_tfup,
            "chosen_policy": choice,
            "arch_name": arch_name,
        })

    print("Adaptive vs best static (sample)")
    for r in rows[:10]:
        print(r)

    out_path = Path("results/raw/e07_adaptive_policy.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["capacity_bytes", "adaptive_tfup_s", "best_static_tfup_s", "chosen_policy", "arch_name"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
