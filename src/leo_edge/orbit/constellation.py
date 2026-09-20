"""Constellation contact generation with phase offsets."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from .access import generate_access_windows


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def _format_iso(dt: datetime) -> str:
    # Return ISO-8601 with Z
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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


def generate_constellation_contacts(
    ground_lat: float,
    ground_lon: float,
    min_elevation_deg: float,
    altitude_km: float,
    inclination_deg: float,
    duration_hours: float,
    num_sats: int = 3,
) -> List[Dict]:
    """DEPRECATED (docs/DECISION_LOG.md ADR-019): this approximates additional
    satellites by time-shifting copies of ONE satellite's real access
    windows by an orbital-period offset. That ignores Earth rotation and
    plane geometry: a phase-shifted copy in the same orbital plane does not
    have the ground track of a genuinely different satellite, let alone one
    in a different plane. It is not a constellation model.

    Kept only because `experiments/e09_constellation_handoff.py` still calls
    it and fixing e09 is out of scope for the v4 rework (which targets
    `experiments/e12_access_sweep.py`'s access/revisit sweep specifically);
    e09's handoff-timing results should be read with this limitation in
    mind. Do not use this for any new work -- use
    `generate_walker_delta_tles` + `per_satellite_access_windows` instead,
    which propagate every satellite independently with real SGP4.

    Args:
        ground_lat: Ground station latitude deg.
        ground_lon: Ground station longitude deg.
        min_elevation_deg: Minimum elevation deg.
        altitude_km: Circular orbit altitude km.
        inclination_deg: Inclination deg.
        duration_hours: Duration hours from fixed epoch.
        num_sats: Number of satellites with evenly spaced phase offsets.

    Returns:
        List of dicts with keys sat_id, start, end, duration_s, max_elevation_deg.
    """
    base_windows = generate_access_windows(
        ground_lat=ground_lat,
        ground_lon=ground_lon,
        min_elevation_deg=min_elevation_deg,
        altitude_km=altitude_km,
        inclination_deg=inclination_deg,
        duration_hours=duration_hours,
    )

    # Orbital period for circular orbit
    mu = 398600.4418  # km^3/s^2
    r_earth = 6378.137  # km
    a = r_earth + altitude_km
    period_s = 2 * math.pi * math.sqrt(a ** 3 / mu)
    offset_s = period_s / num_sats

    contacts: List[Dict] = []
    start_epoch = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_epoch = start_epoch + timedelta(hours=duration_hours)

    for i in range(num_sats):
        shift = timedelta(seconds=i * offset_s)
        sat_id = f"SAT{i+1}"
        for w in base_windows:
            w_start = _parse_iso(w["start"]) + shift
            w_end = _parse_iso(w["end"]) + shift
            # Clip to requested duration window
            if w_end < start_epoch or w_start > end_epoch:
                continue
            w_start_clipped = max(w_start, start_epoch)
            w_end_clipped = min(w_end, end_epoch)
            duration_s = (w_end_clipped - w_start_clipped).total_seconds()
            if duration_s <= 0:
                continue
            contacts.append({
                "sat_id": sat_id,
                "start": _format_iso(w_start_clipped),
                "end": _format_iso(w_end_clipped),
                "duration_s": float(duration_s),
                "max_elevation_deg": float(w["max_elevation_deg"]),
            })

    # Sort by start time
    contacts.sort(key=lambda c: c["start"])
    return contacts
