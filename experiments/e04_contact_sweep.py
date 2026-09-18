"""Experiment 04: Sweep contact duration for GroundOnly vs Progressive."""

import csv
from pathlib import Path

from leo_edge.architectures import GroundOnly, Progressive
from leo_edge.simulation import run_static_architecture


def main():
    scene_bytes = 1e9  # 1 GB raw
    rate_bps = 10e6  # 10 Mbps
    processing_time_s = 30.0

    durations = list(range(120, 601, 60))  # 120 to 600 s

    rows = []
    for dur in durations:
        for ArchClass, name in [(GroundOnly, "A0_GROUND_ONLY"), (Progressive, "A4_PROGRESSIVE")]:
            res = run_static_architecture(
                arch_class=ArchClass,
                scene_bytes=scene_bytes,
                contact_duration_s=dur,
                rate_bps=rate_bps,
                processing_time_s=processing_time_s,
            )
            rows.append({
                "contact_duration_s": dur,
                "architecture": name,
                "tfup_s": res.tfup_s,
                "tcp_s": res.tcp_s,
                "bytes_transmitted": res.bytes_transmitted,
                "contact_utilization": res.contact_utilization,
                "processing_energy_j": res.processing_energy_j,
                "tx_energy_j": res.tx_energy_j,
            })

    print("Contact sweep results (first 6 rows)")
    for r in rows[:6]:
        print(r)

    out_path = Path("results/raw/e04_contact_sweep.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "contact_duration_s", "architecture", "tfup_s", "tcp_s",
            "bytes_transmitted", "contact_utilization", "processing_energy_j", "tx_energy_j"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
