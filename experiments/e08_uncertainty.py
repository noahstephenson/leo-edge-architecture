"""Experiment 08: Uncertainty in contact capacity.

Monte Carlo over contact-capacity noise. tfup_s/tcp_s are censored (NaN,
completed=False) whenever a product doesn't fit the noisy capacity for that
run, so aggregate statistics are computed only over completed runs, and the
completion rate itself is reported as a result, not hidden inside a mean.
"""

import csv
import math
import random
from pathlib import Path

from leo_edge.architectures import GroundOnly, Progressive
from leo_edge.simulation import run_static_architecture


def _mean_std(values):
    if not values:
        return float("nan"), float("nan")
    mean = sum(values) / len(values)
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    return mean, std


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
            "tfup_ground_completed": res_g.completed,
            "tfup_progressive_s": res_p.tfup_s,
            "tfup_progressive_completed": res_p.completed,
            "tcp_ground_s": res_g.tcp_s,
            "tcp_progressive_s": res_p.tcp_s,
        })

    tfup_g_vals = [r["tfup_ground_s"] for r in rows if r["tfup_ground_completed"]]
    tfup_p_vals = [r["tfup_progressive_s"] for r in rows if r["tfup_progressive_completed"]]
    mean_g, std_g = _mean_std(tfup_g_vals)
    mean_p, std_p = _mean_std(tfup_p_vals)
    rate_g = len(tfup_g_vals) / n_runs
    rate_p = len(tfup_p_vals) / n_runs

    print(f"Nominal capacity: {nominal_capacity_bytes/1e6:.1f} MB, scene: {scene_bytes/1e6:.0f} MB")
    print(f"GroundOnly: completion_rate={rate_g:.2f} TFUP mean={mean_g:.1f}s std={std_g:.1f}s (n={len(tfup_g_vals)})")
    print(f"Progressive: completion_rate={rate_p:.2f} TFUP mean={mean_p:.1f}s std={std_p:.1f}s (n={len(tfup_p_vals)})")

    out_path = Path("results/raw/e08_uncertainty.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
