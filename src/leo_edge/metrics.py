"""Metric calculations."""

from typing import List


def tfup_s(collection_time: float, first_use_time: float) -> float:
    """Time from collection to first use."""
    return max(0.0, first_use_time - collection_time)


def tcp_s(collection_time: float, complete_time: float) -> float:
    """Time to complete product delivery."""
    return max(0.0, complete_time - collection_time)


def contact_utilization(used_bytes: int, capacity_bytes: int) -> float:
    """Fraction of contact capacity used."""
    if capacity_bytes <= 0:
        return 0.0
    return min(1.0, used_bytes / capacity_bytes)


def processing_energy_j(power_w: float, duration_s: float) -> float:
    """Energy for processing."""
    return max(0.0, power_w * duration_s)


def tx_energy_j(power_w: float, duration_s: float) -> float:
    """Energy for transmission."""
    return max(0.0, power_w * duration_s)


def storage_peak_bytes(sizes: List[int]) -> int:
    """Peak storage usage."""
    return max(sizes) if sizes else 0


def deadline_met(deadline: float, delivery_time: float) -> bool:
    """Check if delivery meets deadline."""
    return delivery_time <= deadline


def product_completeness(completeness: float) -> float:
    """Normalize completeness to 0-1."""
    return max(0.0, min(1.0, completeness))
