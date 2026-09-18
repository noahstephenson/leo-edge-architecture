"""Link and contact window definitions."""

from dataclasses import dataclass
from typing import Final
import math


@dataclass
class ContactWindow:
    """A single ground contact window."""
    start: float  # seconds since epoch
    stop: float  # seconds since epoch
    duration_s: float
    max_elevation_deg: float

    def contact_capacity_bytes(self, rate_bps: float) -> int:
        """Capacity in bytes for given downlink rate."""
        if rate_bps <= 0 or self.duration_s <= 0:
            return 0
        bits = rate_bps * self.duration_s
        return int(bits // 8)


def rate_bps(elevation_deg: float, base_rate: float) -> float:
    """Elevation-dependent downlink rate."""
    # rate = base_rate * max(0, sin(elevation))
    factor = max(0.0, math.sin(math.radians(elevation_deg)))
    return base_rate * factor


def sweep_contact_margin(alpha_values=None, duration_s: float = 100.0):
    """Return effective contact durations with margin applied.
    
    Margin alpha reduces usable time: effective = duration_s * (1 - alpha).
    """
    if alpha_values is None:
        alpha_values = [0.0, 0.1, 0.2, 0.3]
    effective = []
    for alpha in alpha_values:
        # Ensure margin does not make duration negative
        eff = duration_s * max(0.0, 1.0 - alpha)
        effective.append(eff)
    return effective
