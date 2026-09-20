"""Walker-delta constellation generation: one real SGP4-propagated TLE per satellite."""

from __future__ import annotations

from typing import List, Dict

from .access import generate_access_windows


def _build_synthetic_tle(altitude_km: float, inclination_deg: float, raan_deg: float, mean_anomaly_deg: float):
    """Build a synthetic circular-orbit TLE at given RAAN/mean-anomaly.

    Same construction as `orbit.access.generate_access_windows`'s default
    synthetic-TLE path (fixed 2020-01-01 epoch, zero eccentricity, zero
    argument of perigee), except RAAN and mean anomaly are real per-satellite
    parameters instead of both hardcoded to zero. This is what makes each
    Walker-constellation satellite an independently, correctly propagated
    orbit instead of a time-shifted copy of one ground track.
    """
    import math

    mu = 398600.4418
    r_earth = 6378.137
    a = r_earth + altitude_km
    n_rad_per_s = math.sqrt(mu / a ** 3)
    mean_motion_rev_per_day = n_rad_per_s * 86400.0 / (2.0 * math.pi)

    line1 = "1 00001U 00001A   20001.00000000  .00000000  00000-0  00000-0 0  9999"
    # Exact fixed-width TLE columns: SGP4 parses by column position, so a
    # missing separator silently mis-reads a field (an earlier version
    # dropped the space before mean anomaly and every satellite parsed as
    # mean anomaly 0, co-locating all satellites in a plane).
    line2 = (
        f"2 00001 {inclination_deg:8.4f} {raan_deg % 360.0:8.4f} 0000000 "
        f"{0.0:8.4f} {mean_anomaly_deg % 360.0:8.4f} {mean_motion_rev_per_day:11.8f}    10"
    )
    return line1, line2


def generate_walker_delta_tles(
    total_sats: int,
    planes: int,
    phasing_factor: int,
    altitude_km: float,
    inclination_deg: float,
) -> List[Dict]:
    """Generate one TLE per satellite of a Walker-delta constellation
    (T/P/F notation: total_sats/planes/phasing_factor), each individually
    propagable with SGP4.

    Unlike `generate_constellation_contacts` below, this does not
    approximate additional satellites by time-shifting one satellite's
    ground track; each satellite gets its own RAAN (spread evenly across
    `planes`) and mean anomaly (spread evenly within its plane, offset
    between planes by `phasing_factor`), so a satellite in a different
    plane genuinely has a different ground track, not a phase-delayed copy
    of the same one. See docs/DECISION_LOG.md ADR-019.

    Returns a list of dicts: {"sat_id": str, "line1": str, "line2": str}.
    """
    if total_sats % planes != 0:
        raise ValueError(f"total_sats ({total_sats}) must be divisible by planes ({planes})")
    sats_per_plane = total_sats // planes

    out = []
    for p in range(planes):
        raan_deg = p * 360.0 / planes
        for s in range(sats_per_plane):
            mean_anomaly_deg = (
                s * 360.0 / sats_per_plane
                + p * phasing_factor * 360.0 / total_sats
            )
            line1, line2 = _build_synthetic_tle(altitude_km, inclination_deg, raan_deg, mean_anomaly_deg)
            out.append({"sat_id": f"P{p}S{s}", "line1": line1, "line2": line2})
    return out


def per_satellite_access_windows(
    tles: List[Dict],
    ground_lat: float,
    ground_lon: float,
    min_elevation_deg: float,
    duration_hours: float,
) -> Dict[str, List[Dict]]:
    """Propagate every satellite in `tles` (from `generate_walker_delta_tles`)
    individually against one ground point via real SGP4, and return each
    satellite's own access windows (each with "peak", the time of closest
    approach within the window, from `orbit.access.generate_access_windows`).

    This is the real per-satellite propagation item 1 of the v4 rework
    requires in place of `generate_constellation_contacts`'s time-shifted
    copies. It's O(len(tles)) SGP4 propagations, made tractable by
    `access.generate_access_windows`'s vectorized elevation scan
    (docs/DECISION_LOG.md ADR-019); callers that sweep many constellation
    sizes should still cache results per (tle, ground point) pair rather
    than recomputing, since the same base satellite geometry recurs across
    a sweep's terminal/AOI ground points but not across different total
    satellite counts.
    """
    out = {}
    for tle in tles:
        windows = generate_access_windows(
            ground_lat=ground_lat,
            ground_lon=ground_lon,
            min_elevation_deg=min_elevation_deg,
            altitude_km=0.0,
            inclination_deg=0.0,
            duration_hours=duration_hours,
            tle_lines=(tle["line1"], tle["line2"]),
        )
        out[tle["sat_id"]] = windows
    return out
