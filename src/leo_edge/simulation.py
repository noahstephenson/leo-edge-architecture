"""Simulation engine integrating orbit access, architecture policies, and metrics."""

from dataclasses import dataclass, field
from math import isfinite
from inspect import signature, Parameter
from .configuration import DEFAULT_SIZING
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
    bytes_transmitted: float
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
        bytes_transmitted=float(out.get("bytes_transmitted", 0)),
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
    tier_completion_s: dict
    bytes_transmitted: float = 0.0
    product_progress: dict = field(default_factory=dict)
    processing_time_used_s: float = 0.0
    transmission_time_used_s: float = 0.0
    contact_capacity_bytes: float = 0.0

    @property
    def contact_utilization(self):
        return self.bytes_transmitted / self.contact_capacity_bytes if self.contact_capacity_bytes else 0.0


def _parse_iso(ts: str) -> datetime:
    # Skyfield emits ISO-8601 with a trailing "Z"; datetime.fromisoformat
    # before 3.11 doesn't accept that, so normalize it explicitly.
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def contact_windows_from_access_windows(
    access_windows: List[dict], capture_time: datetime
) -> List[Tuple[float, float]]:
    """Convert `orbit.access.generate_access_windows` output into
    (window_start_s, duration_s) pairs relative to `capture_time`. A contact
    already open at capture is clipped to its remaining duration so a
    same-pass delivery remains possible.
    """
    out = []
    for w in access_windows:
        start = _parse_iso(w["start"])
        offset_s = (start - capture_time).total_seconds()
        end_offset_s = offset_s + float(w["duration_s"])
        if end_offset_s <= 0:
            continue
        usable_start_s = max(0.0, offset_s)
        out.append((usable_start_s, end_offset_s - usable_start_s))
    return sorted(out, key=lambda pair: pair[0])


def simulate_multi_contact(
    architecture,
    scene_bytes: float,
    contact_windows_s: List[Tuple[float, float]],
    rate_bps: float,
    processing_time_s: float = DEFAULT_SIZING.nominal_processing_time_s,
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
    if not isfinite(scene_bytes) or scene_bytes <= 0 or not isfinite(rate_bps) or rate_bps <= 0:
        raise ValueError("Scene size and rate must be finite and positive")
    if not isfinite(processing_time_s) or processing_time_s < 0:
        raise ValueError("Processing time must be finite and nonnegative")
    previous_end = 0.0
    for start, duration in contact_windows_s:
        if not isfinite(start) or not isfinite(duration) or start < previous_end or duration <= 0:
            raise ValueError("Contacts must be finite, ordered, positive, and nonoverlapping")
        previous_end = start + duration
    first_start_s, first_duration_s = contact_windows_s[0] if contact_windows_s else (None, None)
    options = dict(processing_time_s=processing_time_s, rate_bps=rate_bps,
                   first_window_duration_s=first_duration_s, first_window_start_s=first_start_s)
    parameters = signature(architecture.tiers).parameters
    accepts_all = any(p.kind == Parameter.VAR_KEYWORD for p in parameters.values())
    tiers = architecture.tiers(scene_bytes, **{k: v for k, v in options.items() if accepts_all or k in parameters})

    name = type(architecture).__name__
    if not tiers or rate_bps <= 0:
        return MultiContactResult(name, float("nan"), float("nan"), False, 0, {})

    identifiers = [tier.value for tier, _, _ in tiers]
    if len(set(identifiers)) != len(identifiers) or any(
        not isfinite(size) or size <= 0 or not isfinite(proc) or proc < 0
        for _, size, proc in tiers
    ):
        raise ValueError("Products must be unique with positive sizes and nonnegative processing")
    delivered = [0.0] * len(tiers)
    tier_idx = 0
    proc_left_s = tiers[0][2]
    tfup_s = None
    tcp_s = None
    contacts_used = 0
    tier_completion_s = {}
    bytes_transmitted = 0.0
    processing_used_s = 0.0

    current_time = 0.0
    for window_start_s, duration_s in contact_windows_s:
        if tier_idx >= len(tiers):
            break
        contacts_used += 1
        # idle gap before window
        idle = max(0.0, window_start_s - current_time)
        if proc_left_s > 0 and idle > 0:
            spend = min(proc_left_s, idle)
            proc_left_s -= spend
            processing_used_s += spend
            current_time += spend
        current_time = window_start_s
        t = 0.0
        while t < duration_s and tier_idx < len(tiers):
            if proc_left_s > 0:
                spend = min(proc_left_s, duration_s - t)
                proc_left_s -= spend
                processing_used_s += spend
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
            bytes_transmitted += take_bytes
            t += take_time_s
            if delivered[tier_idx] >= target_bytes:
                completion_s = window_start_s + t
                tier_completion_s[tier.value] = completion_s
                if tfup_s is None:
                    tfup_s = completion_s
                if tier_idx == len(tiers) - 1:
                    tcp_s = completion_s
                tier_idx += 1
                if tier_idx < len(tiers):
                    proc_left_s = tiers[tier_idx][2]
            else:
                break
        current_time = window_start_s + duration_s

    return MultiContactResult(
        architecture_name=name,
        tfup_s=tfup_s if tfup_s is not None else float("nan"),
        tcp_s=tcp_s if tcp_s is not None else float("nan"),
        completed=tcp_s is not None,
        contacts_used=contacts_used,
        tier_completion_s=tier_completion_s,
        bytes_transmitted=bytes_transmitted,
        product_progress={tier.value: {
            "target_bytes": target, "received_bytes": delivered[i],
            "completeness": delivered[i] / target,
            "completion_time_s": tier_completion_s.get(tier.value),
        } for i, (tier, target, _) in enumerate(tiers)},
        processing_time_used_s=processing_used_s,
        transmission_time_used_s=bytes_transmitted * 8 / rate_bps,
        contact_capacity_bytes=sum(duration * rate_bps / 8 for _, duration in contact_windows_s),
    )


def single_contact_metrics(architecture, scene_bytes, capacity_bytes, rate_bps, processing_time_s):
    """Legacy dictionary interface backed by the same transfer accounting.

    Completeness refers to P4's encoded product, not bytes divided by raw
    scene size. Energy is bookkeeping at assumed constant powers. Peak
    storage is not evaluated.
    """
    from .products import ProductTier, TIER_FIDELITY
    if not isfinite(capacity_bytes) or capacity_bytes < 0 or not isfinite(rate_bps) or rate_bps <= 0:
        raise ValueError("Capacity must be nonnegative and rate positive")
    duration = capacity_bytes * 8 / rate_bps
    result = simulate_multi_contact(architecture, scene_bytes,
                                   [(0.0, duration)] if duration else [],
                                   rate_bps, processing_time_s)
    completed_tiers = list(result.tier_completion_s)
    tier = ProductTier(completed_tiers[-1]) if completed_tiers else None
    fidelity = TIER_FIDELITY[tier] if tier else None
    raw_full = tier == ProductTier.P4_FULL and result.product_progress[tier.value]["target_bytes"] == scene_bytes
    return {
        "tfup_s": result.tfup_s, "tcp_s": result.tcp_s,
        "bytes_transmitted": result.bytes_transmitted, "completed": result.completed,
        "contact_utilization": result.contact_utilization,
        "processing_energy_j": result.processing_time_used_s * architecture.sizing.processing_power_w,
        "tx_energy_j": result.transmission_time_used_s * architecture.sizing.radio_power_w,
        "storage_peak_bytes": None,
        "deadline_met": result.completed and result.tcp_s <= duration,
        "product_completeness": result.product_progress.get("P4_FULL", {}).get("completeness", 0.0),
        "product_progress": result.product_progress,
        "fidelity_lossy": False if raw_full else fidelity.lossy if fidelity else True,
        "fidelity_resolution_class": fidelity.resolution_class if fidelity else "unknown",
    }
