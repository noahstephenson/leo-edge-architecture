"""Experiment 08: Uncertainty in contact capacity."""

import csv
import random
from pathlib import Path

from leo_edge.architectures import GroundOnly, Progressive
from leo_edge.simulation import run_static_architecture


def main():
    random.seed(0)
    scene_bytes = 1e9
    rate_bps = 10e6
    processing_time_s = 30.0
    nominal_duration_s = 300.0
    nominal_capacity_bytes = (rate_bps / 8) * nominal_duration_s

    n_runs = 100
    sigma_frac = 0.10  # 10% std dev

    rows = []
    for i in range(n_runs):
        error = random.gauss(0, sigma_frac)
        capacity = max(0.0, nominal_capacity_bytes * (1 + error))
        duration = capacity / (rate_bps / 8)
        
        res_g = run_static_architecture(GroundOnly, scene_bytes, duration, rate_bps, processing_time_s)
        res_p = run_static_architecture(Progressive, scene_bytes, duration, rate_bps, processing_time_s)
        
        rows.append({
            "run_id": i,
            "capacity_bytes": capacity,
            "capacity_error_frac": error,
            "tfup_ground_s": res_g.tfup_s,
            "tfup_progressive_s": res_p.tfup_s,
            "tcp_ground_s": res_g.tcp_s,
            "tcp_progressive_s": res_p.tcp_s,
        })

    tfup_g_vals = [r["tfup_ground_s"] for r in rows]
    tfup_p_vals = [r["tfup_progressive_s"] for r in rows]
    mean_g = sum(tfup_g_vals) / n_runs
    mean_p = sum(tfup_p_vals) / n_runs
    import math
    std_g = math.sqrt(sum((v-mean_g)**2 for v in tfup_g_vals)/n_runs)
    std_p = math.sqrt(sum((v-mean_p)**2 for v in tfup_p_vals)/n_runs)

    print(f"Nominal capacity: {nominal_capacity_bytes/1e6:.1f} MB")
    print(f"GroundOnly TFUP: mean={mean_g:.1f}s std={std_g:.1f}s")
    print(f"Progressive TFUP: mean={mean_p:.1f}s std={std_p:.1f}s")

    out_path = Path("results/raw/e08_uncertainty.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "run_id", "capacity_bytes", "capacity_error_frac",
            "tfup_ground_s", "tfup_progressive_s", "tcp_ground_s", "tcp_progressive_s"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
