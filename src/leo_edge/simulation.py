"""Simple simulation engine integrating orbit access, architecture policies, and metrics."""

from dataclasses import dataclass
from typing import List, Type

from .architectures import (
    GroundOnly,
    CompressedFull,
    QuicklookFirst,
    RoiFirst,
    Progressive,
)


@dataclass
class SimulationResult:
    """Result of a single static architecture run."""

    architecture_name: str
    tfup_s: float
    tcp_s: float
    bytes_transmitted: int
    processing_energy_j: float
    tx_energy_j: float
    contact_utilization: float


def run_static_architecture(
    arch_class: Type,
    scene_bytes: float,
    contact_duration_s: float,
    rate_bps: float,
    processing_time_s: float,
) -> SimulationResult:
    """Run a static architecture for a single contact.

    Args:
        arch_class: Architecture class with a run method.
        scene_bytes: Size of the raw scene in bytes.
        contact_duration_s: Duration of the contact window in seconds.
        rate_bps: Downlink rate in bits per second.
        processing_time_s: Nominal processing time in seconds.

    Returns:
        SimulationResult with computed metrics.
    """
    contact_capacity_bytes = (rate_bps / 8.0) * contact_duration_s
    arch = arch_class()
    out = arch.run(scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s)

    bytes_transmitted = int(out.get("bytes_transmitted", 0))
    contact_utilization = (
        bytes_transmitted / contact_capacity_bytes
        if contact_capacity_bytes > 0
        else 0.0
    )

    return SimulationResult(
        architecture_name=arch_class.__name__,
        tfup_s=float(out.get("tfup_s", 0.0)),
        tcp_s=float(out.get("tcp_s", 0.0)),
        bytes_transmitted=bytes_transmitted,
        processing_energy_j=float(out.get("processing_energy_j", 0.0)),
        tx_energy_j=float(out.get("tx_energy_j", 0.0)),
        contact_utilization=float(contact_utilization),
    )


def sweep_rate(
    arch_classes: List[Type],
    scene_bytes: float,
    contact_duration_s: float,
    rates_bps: List[float],
    processing_time_s: float,
) -> List[SimulationResult]:
    """Sweep downlink rates for multiple architectures.

    Args:
        arch_classes: List of architecture classes to evaluate.
        scene_bytes: Size of the raw scene in bytes.
        contact_duration_s: Contact window duration in seconds.
        rates_bps: List of downlink rates in bits per second.
        processing_time_s: Nominal processing time in seconds.

    Returns:
        List of SimulationResult for each architecture and rate combination.
    """
    results: List[SimulationResult] = []
    for arch_class in arch_classes:
        for rate in rates_bps:
            res = run_static_architecture(
                arch_class,
                scene_bytes,
                contact_duration_s,
                rate,
                processing_time_s,
            )
            results.append(res)
    return results
