"""Simulation engine integrating orbit access, architecture policies, and metrics."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Type

from .architectures import (
    GroundOnly,
    CompressedFull,
    QuicklookFirst,
    RoiFirst,
    Progressive,
)


@dataclass
class SimulationResult:
    """Result of a single static architecture run against one contact window.

    tfup_s/tcp_s are NaN when the corresponding product was not delivered
    within this one window; check `completed` before treating tcp_s as a
    real number.
    """

    architecture_name: str
    tfup_s: float
    tcp_s: float
    bytes_transmitted: int
    processing_energy_j: float
    tx_energy_j: float
    contact_utilization: float
    completed: bool
    fidelity_lossy: bool
    fidelity_resolution_class: str


def run_static_architecture(
    arch_class: Type,
    scene_bytes: float,
    contact_duration_s: float,
    rate_bps: float,
    processing_time_s: float,
) -> SimulationResult:
    """Run a static architecture for a single contact window.

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

    return SimulationResult(
        architecture_name=arch_class.__name__,
        tfup_s=float(out.get("tfup_s", float("nan"))),
        tcp_s=float(out.get("tcp_s", float("nan"))),
        bytes_transmitted=int(out.get("bytes_transmitted", 0)),
        processing_energy_j=float(out.get("processing_energy_j", 0.0)),
        tx_energy_j=float(out.get("tx_energy_j", 0.0)),
        contact_utilization=float(out.get("contact_utilization", 0.0)),
        completed=bool(out.get("completed", False)),
        fidelity_lossy=bool(out.get("fidelity_lossy", True)),
        fidelity_resolution_class=str(out.get("fidelity_resolution_class", "unknown")),
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


@dataclass
class MultiContactResult:
    """Result of delivering one architecture's product across a real
    sequence of contact windows, carrying undelivered bytes forward.
    """

    architecture_name: str
    tfup_s: float
    tcp_s: float
    completed: bool
    contacts_used: int


def _parse_iso(ts: str) -> datetime:
    # Skyfield emits ISO-8601 with a trailing "Z"; datetime.fromisoformat
    # before 3.11 doesn't accept that, so normalize it explicitly.
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def contact_windows_from_access_windows(
    access_windows: List[dict], capture_time: datetime
) -> List[Tuple[float, float]]:
    """Convert `orbit.access.generate_access_windows` output into
    (window_start_s, duration_s) pairs relative to `capture_time`, dropping
    any window that starts before capture (the product doesn't exist yet).
    """
    out = []
    for w in access_windows:
        start = _parse_iso(w["start"])
        offset_s = (start - capture_time).total_seconds()
        if offset_s < 0:
            continue
        out.append((offset_s, float(w["duration_s"])))
    return sorted(out, key=lambda pair: pair[0])


def simulate_multi_contact(
    architecture,
    scene_bytes: float,
    contact_windows_s: List[Tuple[float, float]],
    rate_bps: float,
    processing_time_s: float = 20.0,
) -> MultiContactResult:
    """Deliver an architecture's product tiers across a real sequence of
    contact windows, carrying undelivered bytes forward.

    Within each window, any processing time still owed on the tier in
    progress is spent first (processing overrun delays transmission, it
    never extends past the contact window silently); remaining window time
    is then spent transmitting toward the current tier's byte target. If a
    window's capacity runs out mid-tier, the remainder carries to the next
    window. A product that never finishes across all given windows is
    censored: tfup_s/tcp_s stay NaN and completed is False.

    Args:
        architecture: an architecture instance exposing
            `.tiers(scene_bytes, processing_time_s=...)`.
        scene_bytes: raw scene size in bytes.
        contact_windows_s: ordered list of (window_start_s, duration_s)
            relative to capture time, e.g. from
            `contact_windows_from_access_windows`.
        rate_bps: downlink rate in bits per second.
        processing_time_s: nominal full-scene processing time in seconds,
            passed through to the architecture's tier plan.

    Returns:
        MultiContactResult.
    """
    try:
        tiers = architecture.tiers(scene_bytes, processing_time_s=processing_time_s)
    except TypeError:
        tiers = architecture.tiers(scene_bytes)

    name = type(architecture).__name__
    if not tiers or rate_bps <= 0:
        return MultiContactResult(name, float("nan"), float("nan"), False, 0)

    delivered = [0.0] * len(tiers)
    tier_idx = 0
    proc_left_s = tiers[0][2]
    tfup_s = None
    tcp_s = None
    contacts_used = 0

    for window_start_s, duration_s in contact_windows_s:
        if tier_idx >= len(tiers):
            break
        contacts_used += 1
        t = 0.0
        while t < duration_s and tier_idx < len(tiers):
            if proc_left_s > 0:
                spend = min(proc_left_s, duration_s - t)
                proc_left_s -= spend
                t += spend
                continue
            tier, target_bytes, _tier_proc = tiers[tier_idx]
            remaining_time_s = duration_s - t
            if remaining_time_s <= 0:
                break
            capacity_bytes = (rate_bps / 8.0) * remaining_time_s
            need_bytes = target_bytes - delivered[tier_idx]
            take_bytes = min(need_bytes, capacity_bytes)
            take_time_s = take_bytes * 8 / rate_bps
            delivered[tier_idx] += take_bytes
            t += take_time_s
            if delivered[tier_idx] >= target_bytes - 1e-6:
                completion_s = window_start_s + t
                if tfup_s is None:
                    tfup_s = completion_s
                if tier_idx == len(tiers) - 1:
                    tcp_s = completion_s
                tier_idx += 1
                if tier_idx < len(tiers):
                    proc_left_s = tiers[tier_idx][2]
            else:
                break

    return MultiContactResult(
        architecture_name=name,
        tfup_s=tfup_s if tfup_s is not None else float("nan"),
        tcp_s=tcp_s if tcp_s is not None else float("nan"),
        completed=tcp_s is not None,
        contacts_used=contacts_used,
    )
