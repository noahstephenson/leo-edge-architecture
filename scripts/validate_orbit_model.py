"""Orbit validation: compare Skyfield TLE-based access windows to synthetic generator."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from leo_edge.orbit.access import generate_access_windows

# Parameters
ALTITUDES = [500, 600, 700]  # km
INCLINATIONS = [45, 55, 97]  # deg
GROUND_LATS = [35, 45, 55]  # deg
GROUND_LON = 0.0  # fixed for validation
MIN_ELEVATION = 10.0  # deg
DURATION_HOURS = 24.0


def build_tle(altitude_km: float, inclination_deg: float) -> tuple[str, str]:
    """Build synthetic TLE for circular orbit matching generate_access_windows."""
    mu = 398600.4418  # km^3/s^2
    r_earth = 6378.137  # km
    a = r_earth + altitude_km
    n_rad_per_s = math.sqrt(mu / a ** 3)
    mean_motion_rev_per_day = n_rad_per_s * 86400.0 / (2.0 * math.pi)

    line1 = "1 00001U 00001A   20001.00000000  .00000000  00000-0  00000-0 0  9999"
    incl_str = f"{inclination_deg:8.4f}"
    mean_motion_str = f"{mean_motion_rev_per_day:11.8f}"
    line2 = f"2 00001 {incl_str}  0.0000 0000000  0.0000  0.0000 {mean_motion_str}  00000"
    return line1, line2


def main():
    rows = []
    for alt in ALTITUDES:
        for inc in INCLINATIONS:
            for lat in GROUND_LATS:
                # Synthetic generator via parameters
                windows_synth = generate_access_windows(
                    ground_lat=lat,
                    ground_lon=GROUND_LON,
                    min_elevation_deg=MIN_ELEVATION,
                    altitude_km=alt,
                    inclination_deg=inc,
                    duration_hours=DURATION_HOURS,
                )
                # Explicit TLE
                tle = build_tle(alt, inc)
                windows_tle = generate_access_windows(
                    ground_lat=lat,
                    ground_lon=GROUND_LON,
                    min_elevation_deg=MIN_ELEVATION,
                    altitude_km=alt,  # ignored when tle provided
                    inclination_deg=inc,
                    duration_hours=DURATION_HOURS,
                    tle_lines=tle,
                )

                count_synth = len(windows_synth)
                count_tle = len(windows_tle)
                diff = count_tle - count_synth

                total_dur_synth = sum(w["duration_s"] for w in windows_synth)
                total_dur_tle = sum(w["duration_s"] for w in windows_tle)

                rows.append({
                    "altitude_km": alt,
                    "inclination_deg": inc,
                    "ground_lat_deg": lat,
                    "ground_lon_deg": GROUND_LON,
                    "windows_synthetic": count_synth,
                    "windows_tle": count_tle,
                    "count_diff": diff,
                    "total_duration_s_synthetic": total_dur_synth,
                    "total_duration_s_tle": total_dur_tle,
                    "duration_diff_s": total_dur_tle - total_dur_synth,
                })

    out_path = Path("results/frozen/orbit_validation.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        fieldnames = [
            "altitude_km",
            "inclination_deg",
            "ground_lat_deg",
            "ground_lon_deg",
            "windows_synthetic",
            "windows_tle",
            "count_diff",
            "total_duration_s_synthetic",
            "total_duration_s_tle",
            "duration_diff_s",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Print summary
    mismatches = [r for r in rows if r["count_diff"] != 0 or abs(r["duration_diff_s"]) > 1e-6]
    print(f"Validated {len(rows)} combos, mismatches: {len(mismatches)}")
    print(f"Saved summary to {out_path}")


if __name__ == "__main__":
    main()
