"""Static architectures experiment e03.

Sweeps downlink rates for static architectures and prints a table.
Saves results to results/raw/e03_results.csv
"""

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from leo_edge.simulation import sweep_rate
from leo_edge.architectures import (
    GroundOnly,
    CompressedFull,
    QuicklookFirst,
    RoiFirst,
    Progressive,
    ContactAware,
    ThreadAwarePriority,
)


def main():
    scene_bytes = 1e9
    contact_duration_s = 300
    processing_time_s = 20
    rates_bps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6]

    # ContactAware and ThreadAwarePriority were missing from this sweep
    # until now, which meant scripts/trade_study.py's "latency" criterion
    # for both silently fell back to the worst observed value instead of a
    # real measurement (docs/DECISION_LOG.md). Both take zero-arg
    # construction with their default parameters here (ContactAware's
    # default margin alpha; ThreadAwarePriority's default priority tier,
    # quicklook), since this sweep has no notion of an active mission
    # thread to prioritize around.
    arch_classes = [
        GroundOnly,
        CompressedFull,
        QuicklookFirst,
        RoiFirst,
        Progressive,
        ContactAware,
        ThreadAwarePriority,
    ]

    results = sweep_rate(
        arch_classes,
        scene_bytes,
        contact_duration_s,
        rates_bps,
        processing_time_s,
    )

    # Print table
    print(f"{'Architecture':20s} {'Rate_bps':>12s} {'TFUP_s':>10s} {'TCP_s':>10s}")
    print("-" * 56)
    idx = 0
    for arch_class in arch_classes:
        for rate in rates_bps:
            r = results[idx]
            print(f"{r.architecture_name:20s} {rate:12.0f} {r.tfup_s:10.2f} {r.tcp_s:10.2f}")
            idx += 1

    # Save CSV
    out_dir = Path("results") / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "e03_results.csv"

    fieldnames = [
        "architecture_name",
        "rate_bps",
        "scene_bytes",
        "contact_duration_s",
        "processing_time_s",
        "tfup_s",
        "tcp_s",
        "bytes_transmitted",
        "processing_energy_j",
        "tx_energy_j",
        "contact_utilization",
        "completed",
        "fidelity_lossy",
        "fidelity_resolution_class",
    ]

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        idx = 0
        for arch_class in arch_classes:
            for rate in rates_bps:
                r = results[idx]
                writer.writerow(
                    {
                        "architecture_name": r.architecture_name,
                        "rate_bps": rate,
                        "scene_bytes": scene_bytes,
                        "contact_duration_s": contact_duration_s,
                        "processing_time_s": processing_time_s,
                        "tfup_s": r.tfup_s,
                        "tcp_s": r.tcp_s,
                        "bytes_transmitted": r.bytes_transmitted,
                        "processing_energy_j": r.processing_energy_j,
                        "tx_energy_j": r.tx_energy_j,
                        "contact_utilization": r.contact_utilization,
                        "completed": r.completed,
                        "fidelity_lossy": r.fidelity_lossy,
                        "fidelity_resolution_class": r.fidelity_resolution_class,
                    }
                )
                idx += 1

    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
