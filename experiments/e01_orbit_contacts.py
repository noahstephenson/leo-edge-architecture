"""Experiment 01: Generate LEO access windows and save CSV."""

import csv
from pathlib import Path

from leo_edge.orbit.access import generate_access_windows


def main():
    ground_lat = 35.0
    ground_lon = -106.0
    min_elevation_deg = 10.0
    altitude_km = 500.0
    inclination_deg = 97.6
    duration_hours = 168.0  # one week, enough passes for a real distribution

    windows = generate_access_windows(
        ground_lat=ground_lat,
        ground_lon=ground_lon,
        min_elevation_deg=min_elevation_deg,
        altitude_km=altitude_km,
        inclination_deg=inclination_deg,
        duration_hours=duration_hours,
    )

    num_windows = len(windows)
    total_duration = sum(w["duration_s"] for w in windows)

    print(f"Access windows: {num_windows}")
    print(f"Total contact duration: {total_duration:.1f} s ({total_duration/60:.1f} min)")

    out_path = Path("results/raw/e01_access_windows.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["start", "end", "duration_s", "max_elevation_deg"])
        writer.writeheader()
        for w in windows:
            writer.writerow(w)

    print(f"Saved CSV to {out_path}")


if __name__ == "__main__":
    main()
