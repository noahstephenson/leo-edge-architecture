"""Experiment 09: Constellation handoff and queue carry over."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt

from leo_edge.orbit.access import generate_access_windows
from leo_edge.orbit.constellation import generate_constellation_contacts


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def _in_windows(t: datetime, windows: list[dict]) -> bool:
    for w in windows:
        start = _parse_iso(w["start"])
        end = _parse_iso(w["end"])
        if start <= t <= end:
            return True
    return False


def _in_constellation(t: datetime, contacts: list[dict]) -> bool:
    for c in contacts:
        start = _parse_iso(c["start"])
        end = _parse_iso(c["end"])
        if start <= t <= end:
            return True
    return False


def main():
    ground_lat = 35.0
    ground_lon = -106.0
    min_elevation_deg = 10.0
    altitude_km = 500.0
    inclination_deg = 97.6
    duration_hours = 24.0

    # Generate contacts
    single_windows = generate_access_windows(
        ground_lat=ground_lat,
        ground_lon=ground_lon,
        min_elevation_deg=min_elevation_deg,
        altitude_km=altitude_km,
        inclination_deg=inclination_deg,
        duration_hours=duration_hours,
    )

    constellation_contacts = generate_constellation_contacts(
        ground_lat=ground_lat,
        ground_lon=ground_lon,
        min_elevation_deg=min_elevation_deg,
        altitude_km=altitude_km,
        inclination_deg=inclination_deg,
        duration_hours=duration_hours,
        num_sats=3,
    )

    # Simulation parameters
    start_epoch = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_epoch = start_epoch + timedelta(hours=duration_hours)
    step_s = 30
    total_steps = int((end_epoch - start_epoch).total_seconds() // step_s) + 1

    gen_rate_bps = 4 * 1024 * 1024  # 4 Mbps -> bytes/s
    downlink_rate_bps = 20 * 1024 * 1024  # 20 Mbps

    gen_rate_bps_per_s = gen_rate_bps / 8
    downlink_rate_bps_per_s = downlink_rate_bps / 8

    # Prepare output
    out_dir = Path("results/frozen/v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "e09_constellation.csv"
    fig_path = Path("figures/fig15_constellation_coverage.png")
    fig_path.parent.mkdir(parents=True, exist_ok=True)

    times_iso = []
    single_contact = []
    constellation_contact = []
    single_queue = []
    constellation_queue = []

    q_single = 0.0
    q_const = 0.0

    # For plotting
    plot_times = []
    single_series = []
    const_series = []

    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_iso",
            "single_in_contact",
            "constellation_in_contact",
            "single_queue_bytes",
            "constellation_queue_bytes",
            "handoff_sat_id",
        ])

        prev_sat = None
        for i in range(total_steps):
            t = start_epoch + timedelta(seconds=i * step_s)
            t_iso = t.isoformat().replace("+00:00", "Z")

            in_single = _in_windows(t, single_windows)
            in_const = _in_constellation(t, constellation_contacts)

            # Determine current sat for handoff tracking
            cur_sat = None
            for c in constellation_contacts:
                s = _parse_iso(c["start"])
                e = _parse_iso(c["end"])
                if s <= t <= e:
                    cur_sat = c["sat_id"]
                    break
            handoff = ""
            if cur_sat and cur_sat != prev_sat and prev_sat is not None:
                handoff = f"{prev_sat}->{cur_sat}"
            prev_sat = cur_sat if cur_sat else prev_sat

            # Queue update
            dt = step_s
            # generation
            q_single += gen_rate_bps_per_s * dt
            q_const += gen_rate_bps_per_s * dt

            if in_single:
                drain = min(q_single, downlink_rate_bps_per_s * dt)
                q_single -= drain
            if in_const:
                drain = min(q_const, downlink_rate_bps_per_s * dt)
                q_const -= drain

            times_iso.append(t_iso)
            single_contact.append(int(in_single))
            constellation_contact.append(int(in_const))
            single_queue.append(q_single)
            constellation_queue.append(q_const)

            writer.writerow([t_iso, int(in_single), int(in_const), f"{q_single:.0f}", f"{q_const:.0f}", handoff])

            plot_times.append(t)
            single_series.append(int(in_single))
            const_series.append(int(in_const))

    # Summary stats
    single_cov = sum(single_contact) / len(single_contact)
    const_cov = sum(constellation_contact) / len(constellation_contact)
    print(f"Single sat coverage fraction: {single_cov:.3f}")
    print(f"Constellation coverage fraction: {const_cov:.3f}")
    print(f"CSV saved to {csv_path}")

    # Plot
    plt.figure(figsize=(12, 5))
    # Convert times to seconds since start for x-axis
    x = [(t - start_epoch).total_seconds() / 3600 for t in plot_times]
    plt.step(x, single_series, where="post", label="Single SAT coverage", linewidth=1.5)
    plt.step(x, const_series, where="post", label="3-SAT constellation coverage", linewidth=1.5)
    plt.xlabel("Hours from start")
    plt.ylabel("In contact (0/1)")
    plt.title("Continuous coverage: single satellite vs 3-sat constellation")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()
    print(f"Figure saved to {fig_path}")


if __name__ == "__main__":
    main()
