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


def generate_constellation_contacts(
    ground_lat: float,
    ground_lon: float,
    min_elevation_deg: float,
    altitude_km: float,
    inclination_deg: float,
    duration_hours: float,
    num_sats: int = 3,
) -> List[Dict]:
    """Generate contact windows for a Walker-like constellation with phase offsets.

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
