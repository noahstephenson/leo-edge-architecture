"""Skyfield-based contact window generator."""

from __future__ import annotations

from typing import List, Dict

# Optional import guard for environments without Skyfield
try:
    from skyfield.api import load, EarthSatellite
    from skyfield.toposlib import wgs84
    _SKYFIELD_AVAILABLE = True
except Exception:  # pragma: no cover
    _SKYFIELD_AVAILABLE = False


def generate_access_windows(
    ground_lat: float,
    ground_lon: float,
    min_elevation_deg: float,
    altitude_km: float,
    inclination_deg: float,
    duration_hours: float,
    tle_lines: tuple[str, str] | None = None,
) -> List[Dict]:
    """Generate satellite access windows for a ground station.

    Creates a deterministic synthetic circular LEO orbit with the given
    altitude and inclination, propagates it with Skyfield SGP4 via a
    synthetic TLE, and returns intervals where elevation >= min_elevation_deg.

    Optionally accepts explicit TLE lines to override synthetic generation.

    Args:
        ground_lat: Ground station latitude in degrees.
        ground_lon: Ground station longitude in degrees.
        min_elevation_deg: Minimum elevation for access in degrees.
        altitude_km: Circular orbit altitude above Earth surface in km.
        inclination_deg: Orbital inclination in degrees.
        duration_hours: Propagation duration in hours from fixed epoch.
        tle_lines: Optional (line1, line2) TLE strings. If provided, synthetic
            orbit parameters are ignored and the TLE is used directly.

    Returns:
        List of dicts with keys:
          - start: ISO-8601 UTC start time
          - end: ISO-8601 UTC end time
          - duration_s: window duration in seconds
          - max_elevation_deg: maximum elevation within window
          - peak: ISO-8601 UTC time of maximum elevation within the window
            (closest approach), used by v4's collection-timing model instead
            of window end (docs/DECISION_LOG.md ADR-019)
    """
    if not _SKYFIELD_AVAILABLE:
        # Skyfield isn't installed; no access windows can be generated
        return []

    import math
    from datetime import datetime, timedelta, timezone

    ts = load.timescale()
    # Deterministic start epoch
    start_dt = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(hours=duration_hours)

    # Sample every 30 seconds for a simple deterministic scan
    step_seconds = 30
    total_seconds = int((end_dt - start_dt).total_seconds())
    n_steps = max(1, total_seconds // step_seconds + 1)
    datetimes = [start_dt + timedelta(seconds=i * step_seconds) for i in range(n_steps)]
    times = ts.from_datetimes(datetimes)

    # Build synthetic TLE for circular orbit or use provided TLE
    if tle_lines is not None:
        line1, line2 = tle_lines
    else:
        mu = 398600.4418  # km^3/s^2
        r_earth = 6378.137  # km
        a = r_earth + altitude_km
        n_rad_per_s = math.sqrt(mu / a ** 3)
        mean_motion_rev_per_day = n_rad_per_s * 86400.0 / (2.0 * math.pi)

        # Fixed epoch for TLE: 2020-01-01
        line1 = "1 00001U 00001A   20001.00000000  .00000000  00000-0  00000-0 0  9999"
        incl_str = f"{inclination_deg:8.4f}"
        mean_motion_str = f"{mean_motion_rev_per_day:11.8f}"
        # Eccentricity zero, RAAN/arg/perigee/MNA zero for simplicity
        line2 = f"2 00001 {incl_str}  0.0000 0000000  0.0000  0.0000 {mean_motion_str}  00000"

    satellite = EarthSatellite(line1, line2, ts=ts)
    observer = wgs84.latlon(ground_lat, ground_lon)

    # Vectorized: compute all altitudes in one skyfield call instead of one
    # Python-level call per time step. Same geometry, same results, just
    # fast enough to make per-satellite propagation of a real multi-satellite
    # Walker constellation tractable (docs/DECISION_LOG.md ADR-019).
    topocentric = (satellite - observer).at(times)
    alt, _az, _distance = topocentric.altaz()
    elevations = alt.degrees

    def _mk_window(start_idx, end_idx, peak_idx, max_elev):
        start_time = times[start_idx]
        end_time = times[end_idx]
        peak_time = times[peak_idx]
        duration_s = (end_time.utc_datetime() - start_time.utc_datetime()).total_seconds()
        return {
            "start": start_time.utc_iso(),
            "end": end_time.utc_iso(),
            "peak": peak_time.utc_iso(),
            "duration_s": float(duration_s),
            "max_elevation_deg": float(max_elev),
        }

    windows: List[Dict] = []
    in_window = False
    start_idx = 0
    peak_idx = 0
    max_elev = -90.0

    for i, elev in enumerate(elevations):
        if elev >= min_elevation_deg:
            if not in_window:
                in_window = True
                start_idx = i
                peak_idx = i
                max_elev = elev
            elif elev > max_elev:
                max_elev = elev
                peak_idx = i
        else:
            if in_window:
                windows.append(_mk_window(start_idx, i - 1, peak_idx, max_elev))
                in_window = False
                max_elev = -90.0

    if in_window:
        windows.append(_mk_window(start_idx, len(elevations) - 1, peak_idx, max_elev))

    return windows
