"""Static architecture implementations A0-A6.

Each class exposes two interfaces:

- `run(...)`: single-contact-window evaluation. Bytes are always capped to
  the window's capacity; if the required product doesn't fit, the metric
  fields for the product that didn't arrive are censored (float('nan')) and
  `completed` is False, rather than reporting a delivery that didn't happen.
- `tiers(scene_bytes, ...)`: an ordered list of (ProductTier, bytes,
  processing_time_s) the architecture would deliver given unlimited contact
  time, used by `leo_edge.simulation.simulate_multi_contact` to carry
  undelivered bytes forward across a real sequence of contact windows.

Sizing ratios (0.3 / 0.02 / 0.1 and the Progressive tier byte targets) are
design assumptions, not measurements. See config/product_sizing.yaml and
docs/ASSUMPTIONS.md.
"""

from .architecture import (
    A0_GROUND_ONLY,
    A1_COMPRESSED_FULL,
    A2_QUICKLOOK_FIRST,
    A3_ROI_FIRST,
    A4_PROGRESSIVE,
    A5_CONTACT_AWARE,
    A6_THREAD_AWARE_PRIORITY,
)
from .metrics import contact_utilization as _contact_utilization
from .products import Fidelity, ProductTier, TIER_FIDELITY

PROCESSING_POWER_W = 15
RADIO_POWER_W = 25

COMPRESSED_FULL_FRACTION = 0.3
QUICKLOOK_SIZE_FRACTION = 0.02
QUICKLOOK_TIME_FRACTION = 0.1
ROI_SIZE_FRACTION = 0.1
PROGRESSIVE_METADATA_BYTES = 20 * 1024
PROGRESSIVE_THUMBNAIL_BYTES = int(0.5 * 1024 * 1024)
PROGRESSIVE_QUICKLOOK_BYTES = 10 * 1024 * 1024
PROGRESSIVE_ROI_BYTES = 50 * 1024 * 1024
CONTACT_AWARE_MARGIN_ALPHA = 0.2

_RAW_FIDELITY = Fidelity(lossy=False, resolution_class="full_res")


def _transmit_time_bytes(bytes_count, rate_bps):
    if rate_bps <= 0:
        return float("inf")
    return bytes_count * 8 / rate_bps


def _finalize_metrics(
    scene_bytes,
    contact_capacity_bytes,
    rate_bps,
    tfup_s,
    tcp_s,
    bytes_transmitted,
    processing_energy_j,
    tx_energy_j,
    completed,
    fidelity,
):
    """Compute standard metric fields for a single-window architecture run."""
    contact_duration_s = (
        contact_capacity_bytes * 8 / rate_bps if rate_bps > 0 else float("inf")
    )
    utilization = _contact_utilization(bytes_transmitted, contact_capacity_bytes)
    storage_peak_bytes = int(scene_bytes)
    deadline_met = bool(completed) and tcp_s <= contact_duration_s + 1e-9
    product_completeness = (
        min(1.0, bytes_transmitted / scene_bytes) if scene_bytes > 0 else 0.0
    )
    return {
        "tfup_s": tfup_s,
        "tcp_s": tcp_s,
        "contact_utilization": utilization,
        "processing_energy_j": processing_energy_j,
        "tx_energy_j": tx_energy_j,
        "storage_peak_bytes": storage_peak_bytes,
        "deadline_met": deadline_met,
        "product_completeness": product_completeness,
        "bytes_transmitted": bytes_transmitted,
        "completed": completed,
        "fidelity_lossy": fidelity.lossy,
        "fidelity_resolution_class": fidelity.resolution_class,
    }


class GroundOnly:
    """A0_GROUND_ONLY: no onboard processing, transmit raw scene if it fits.

    Raw imagery has no usable partial product: a truncated raw file isn't a
    viewable image, so a truncated delivery is censored, not scored as a
    smaller success.
    """

    ARCH_ID = A0_GROUND_ONLY
    # Part of the original A0-A5 candidate set defined before any evaluation
    # results existed (docs/DECISION_LOG.md ADR-014 explains why A6 below is
    # different: it was proposed after seeing v2 results).
    PROVENANCE = "original_candidate_set"
    CONDITIONAL_LOGIC = False  # always the same fixed behavior, no per-request branching

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        bytes_transmitted = min(scene_bytes, contact_capacity_bytes)
        completed = bytes_transmitted >= scene_bytes
        tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
        tfup_s = tx_time if completed else float("nan")
        tcp_s = tfup_s
        tx_energy_j = tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, 0.0, tx_energy_j,
            completed, _RAW_FIDELITY,
        )

    def tiers(self, scene_bytes):
        return [(ProductTier.P4_FULL, float(scene_bytes), 0.0)]


class CompressedFull:
    """A1_COMPRESSED_FULL: process then transmit one compressed product."""

    ARCH_ID = A1_COMPRESSED_FULL
    PROVENANCE = "original_candidate_set"
    CONDITIONAL_LOGIC = False

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        compressed_bytes = int(scene_bytes * COMPRESSED_FULL_FRACTION)
        bytes_transmitted = min(compressed_bytes, contact_capacity_bytes)
        completed = bytes_transmitted >= compressed_bytes
        tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
        total_time = processing_time_s + tx_time
        tfup_s = total_time if completed else float("nan")
        tcp_s = tfup_s
        processing_energy_j = processing_time_s * PROCESSING_POWER_W
        tx_energy_j = tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, processing_energy_j, tx_energy_j,
            completed, TIER_FIDELITY[ProductTier.P4_FULL],
        )

    def tiers(self, scene_bytes):
        compressed_bytes = float(int(scene_bytes * COMPRESSED_FULL_FRACTION))
        return [(ProductTier.P4_FULL, compressed_bytes, 20.0)]


class QuicklookFirst:
    """A2_QUICKLOOK_FIRST: quicklook first, then the full scene if capacity allows."""

    ARCH_ID = A2_QUICKLOOK_FIRST
    PROVENANCE = "original_candidate_set"
    CONDITIONAL_LOGIC = False

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        quicklook_bytes = int(scene_bytes * QUICKLOOK_SIZE_FRACTION)
        quicklook_proc = processing_time_s * QUICKLOOK_TIME_FRACTION

        ql_delivered = min(quicklook_bytes, contact_capacity_bytes)
        ql_complete = ql_delivered >= quicklook_bytes
        ql_tx = _transmit_time_bytes(ql_delivered, rate_bps)
        bytes_transmitted = ql_delivered
        tx_time_total = ql_tx

        if not ql_complete:
            tfup_s = float("nan")
            tcp_s = float("nan")
            completed = False
            fidelity = TIER_FIDELITY[ProductTier.P2_QUICKLOOK]
        else:
            tfup_s = quicklook_proc + ql_tx
            remaining_capacity = max(contact_capacity_bytes - quicklook_bytes, 0)
            full_delivered = min(remaining_capacity, scene_bytes)
            completed = full_delivered >= scene_bytes
            bytes_transmitted += full_delivered
            if completed:
                full_tx = _transmit_time_bytes(scene_bytes, rate_bps)
                tx_time_total += full_tx
                tcp_s = quicklook_proc + ql_tx + full_tx
                fidelity = TIER_FIDELITY[ProductTier.P4_FULL]
            else:
                tcp_s = float("nan")
                fidelity = TIER_FIDELITY[ProductTier.P2_QUICKLOOK]

        processing_energy_j = quicklook_proc * PROCESSING_POWER_W
        tx_energy_j = tx_time_total * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, processing_energy_j, tx_energy_j,
            completed, fidelity,
        )

    def tiers(self, scene_bytes, processing_time_s=20.0):
        quicklook_bytes = float(int(scene_bytes * QUICKLOOK_SIZE_FRACTION))
        quicklook_proc = processing_time_s * QUICKLOOK_TIME_FRACTION
        return [
            (ProductTier.P2_QUICKLOOK, quicklook_bytes, quicklook_proc),
            (ProductTier.P4_FULL, float(scene_bytes), 0.0),
        ]


class RoiFirst:
    """A3_ROI_FIRST: region-of-interest crop first, then the full scene."""

    ARCH_ID = A3_ROI_FIRST
    PROVENANCE = "original_candidate_set"
    CONDITIONAL_LOGIC = False

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        roi_bytes = int(scene_bytes * ROI_SIZE_FRACTION)
        roi_proc = processing_time_s

        roi_delivered = min(roi_bytes, contact_capacity_bytes)
        roi_complete = roi_delivered >= roi_bytes
        roi_tx = _transmit_time_bytes(roi_delivered, rate_bps)
        bytes_transmitted = roi_delivered
        tx_time_total = roi_tx

        if not roi_complete:
            tfup_s = float("nan")
            tcp_s = float("nan")
            completed = False
            fidelity = TIER_FIDELITY[ProductTier.P3_ROI]
        else:
            tfup_s = roi_proc + roi_tx
            remaining_capacity = max(contact_capacity_bytes - roi_bytes, 0)
            full_delivered = min(remaining_capacity, scene_bytes)
            completed = full_delivered >= scene_bytes
            bytes_transmitted += full_delivered
            if completed:
                full_tx = _transmit_time_bytes(scene_bytes, rate_bps)
                tx_time_total += full_tx
                tcp_s = roi_proc + roi_tx + full_tx
                fidelity = TIER_FIDELITY[ProductTier.P4_FULL]
            else:
                tcp_s = float("nan")
                fidelity = TIER_FIDELITY[ProductTier.P3_ROI]

        processing_energy_j = roi_proc * PROCESSING_POWER_W
        tx_energy_j = tx_time_total * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, processing_energy_j, tx_energy_j,
            completed, fidelity,
        )

    def tiers(self, scene_bytes, processing_time_s=20.0):
        roi_bytes = float(int(scene_bytes * ROI_SIZE_FRACTION))
        return [
            (ProductTier.P3_ROI, roi_bytes, processing_time_s),
            (ProductTier.P4_FULL, float(scene_bytes), 0.0),
        ]


class Progressive:
    """A4_PROGRESSIVE: metadata, thumbnail, quicklook, ROI, full, in priority order."""

    ARCH_ID = A4_PROGRESSIVE
    PROVENANCE = "original_candidate_set"
    CONDITIONAL_LOGIC = False

    def _tier_sizes(self, scene_bytes):
        return [
            (ProductTier.P0_METADATA, PROGRESSIVE_METADATA_BYTES),
            (ProductTier.P1_THUMBNAIL, PROGRESSIVE_THUMBNAIL_BYTES),
            (ProductTier.P2_QUICKLOOK, PROGRESSIVE_QUICKLOOK_BYTES),
            (ProductTier.P3_ROI, PROGRESSIVE_ROI_BYTES),
            (ProductTier.P4_FULL, scene_bytes),
        ]

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        tier_sizes = self._tier_sizes(scene_bytes)

        remaining = contact_capacity_bytes
        bytes_transmitted = 0
        total_tx_time = 0.0
        first_tx_time = None
        last_tier_delivered = None
        completed = False

        for tier, size in tier_sizes:
            if size > remaining:
                # Priority order is monotonically increasing in size, so
                # once one tier doesn't fit, no later tier will either.
                break
            tx_time = _transmit_time_bytes(size, rate_bps)
            if first_tx_time is None:
                first_tx_time = tx_time
            total_tx_time += tx_time
            bytes_transmitted += size
            remaining -= size
            last_tier_delivered = tier
            if tier == ProductTier.P4_FULL:
                completed = True

        if last_tier_delivered is None:
            tfup_s = float("nan")
            tcp_s = float("nan")
            fidelity = TIER_FIDELITY[ProductTier.P0_METADATA]
        else:
            tfup_s = processing_time_s + first_tx_time
            tcp_s = (processing_time_s + total_tx_time) if completed else float("nan")
            fidelity = TIER_FIDELITY[last_tier_delivered]

        processing_energy_j = processing_time_s * PROCESSING_POWER_W
        tx_energy_j = total_tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, processing_energy_j, tx_energy_j,
            completed, fidelity,
        )

    def tiers(self, scene_bytes, processing_time_s=20.0):
        tier_sizes = self._tier_sizes(scene_bytes)
        out = []
        for i, (tier, size) in enumerate(tier_sizes):
            proc = processing_time_s if i == 0 else 0.0
            out.append((tier, float(size), proc))
        return out


class ThreadAwarePriority(Progressive):
    """A6_THREAD_AWARE_PRIORITY: like Progressive, but the mission thread's
    specific first-needed tier is prioritized immediately after metadata,
    instead of always sending tiers in the fixed P0-P4 order regardless of
    which thread is being served.

    This is the "mission-thread-aware prioritization" axis
    docs/ALLOCATION_SPACE.md names as uncovered by A0-A5: none of them
    reorder based on which mission thread (docs/MISSION_THREADS.md) is
    active. A3_ROI_FIRST, for example, always sends the ROI crop first even
    when the active thread needs a quicklook, not an ROI. This class picks
    a priority tier at construction time and reorders around it.

    Unlike Progressive, tier sizes here are NOT monotonically increasing in
    priority order (a big priority tier can be followed by a smaller
    deprioritized one), so `run()` cannot break out of the loop the moment
    one tier doesn't fit; it must keep trying every remaining tier.

    `fidelity_resolution_class` reports the last tier delivered in
    transmission order, same as Progressive. Since a smaller,
    lower-priority tier can still fit and transmit after the priority
    tier, this can understate the best fidelity actually delivered (e.g.
    the priority ROI tier arrived, then a small thumbnail arrived after
    it, and the fidelity field reports "coarse" even though the richer ROI
    is also in hand). For mission-thread evaluation, use
    `simulation.simulate_multi_contact`'s per-tier `tier_completion_s`
    instead of this field, which is exactly what
    `experiments/e11_mission_thread_success.py` does.
    """

    ARCH_ID = A6_THREAD_AWARE_PRIORITY
    # Proposed after seeing v2's mission-thread-success results (which
    # showed tiered architectures winning and named mission-thread-aware
    # prioritization as the biggest uncovered allocation-space region);
    # not part of the original A0-A5 candidate set defined before any
    # evaluation. Reported separately in docs/TRADE_STUDY.md and
    # experiments/e11_mission_thread_success.py's output for this reason,
    # per docs/DECISION_LOG.md.
    PROVENANCE = "proposed_post_v2"
    CONDITIONAL_LOGIC = True  # priority tier is chosen per request, not fixed

    def __init__(self, priority_tier=ProductTier.P2_QUICKLOOK):
        self.priority_tier = priority_tier

    def _tier_sizes(self, scene_bytes):
        base = super()._tier_sizes(scene_bytes)
        metadata = [t for t in base if t[0] == ProductTier.P0_METADATA]
        priority = [t for t in base if t[0] == self.priority_tier]
        rest = [t for t in base if t[0] not in (ProductTier.P0_METADATA, self.priority_tier)]
        return metadata + priority + rest

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        tier_sizes = self._tier_sizes(scene_bytes)

        remaining = contact_capacity_bytes
        bytes_transmitted = 0
        total_tx_time = 0.0
        first_tx_time = None
        last_tier_delivered = None
        completed = False

        for tier, size in tier_sizes:
            if size > remaining:
                # Sizes aren't monotonic in this priority order, so a
                # later, smaller tier may still fit even if this one
                # didn't; keep checking instead of breaking.
                continue
            tx_time = _transmit_time_bytes(size, rate_bps)
            if first_tx_time is None:
                first_tx_time = tx_time
            total_tx_time += tx_time
            bytes_transmitted += size
            remaining -= size
            last_tier_delivered = tier
            if tier == ProductTier.P4_FULL:
                completed = True

        if last_tier_delivered is None:
            tfup_s = float("nan")
            tcp_s = float("nan")
            fidelity = TIER_FIDELITY[ProductTier.P0_METADATA]
        else:
            tfup_s = processing_time_s + first_tx_time
            tcp_s = (processing_time_s + total_tx_time) if completed else float("nan")
            fidelity = TIER_FIDELITY[last_tier_delivered]

        processing_energy_j = processing_time_s * PROCESSING_POWER_W
        tx_energy_j = total_tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, processing_energy_j, tx_energy_j,
            completed, fidelity,
        )


class ContactAware:
    """A5_CONTACT_AWARE: rule-based policy using contact margin alpha.

    If there's a processor fault, or processing plus compressed transmit
    wouldn't finish inside the window with the required margin, it falls
    back to raw transmit. Otherwise it processes and sends the compressed
    product.
    """

    ARCH_ID = A5_CONTACT_AWARE
    PROVENANCE = "original_candidate_set"
    # True for architectures whose provider-side behavior branches at
    # request time (a margin check here, a priority-tier choice for A6)
    # rather than always following one fixed pipeline. Used by
    # scripts/trade_study.py to derive acquisition_lock_in_risk: a
    # conditional rule is an extra thing to specify and verify in a
    # multi-vendor contract, on top of however many product tiers the
    # architecture can produce.
    CONDITIONAL_LOGIC = True

    def __init__(self, alpha=CONTACT_AWARE_MARGIN_ALPHA, processor_fault=False):
        self.alpha = alpha
        self.processor_fault = processor_fault

    def _raw_fallback(self, scene_bytes, contact_capacity_bytes, rate_bps):
        bytes_transmitted = min(scene_bytes, contact_capacity_bytes)
        completed = bytes_transmitted >= scene_bytes
        tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
        tfup_s = tx_time if completed else float("nan")
        tcp_s = tfup_s
        tx_energy_j = tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, 0.0, tx_energy_j,
            completed, _RAW_FIDELITY,
        )

    def _margin_ok(self, contact_duration_s, compressed_tx, processing_time_s):
        return (
            processing_time_s <= (1.0 - self.alpha) * contact_duration_s
            and processing_time_s + compressed_tx <= contact_duration_s
        )

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        if self.processor_fault or rate_bps <= 0:
            return self._raw_fallback(scene_bytes, contact_capacity_bytes, rate_bps)

        contact_duration_s = contact_capacity_bytes * 8 / rate_bps
        compressed_bytes = int(scene_bytes * COMPRESSED_FULL_FRACTION)
        compressed_tx = _transmit_time_bytes(compressed_bytes, rate_bps)

        if not self._margin_ok(contact_duration_s, compressed_tx, processing_time_s):
            return self._raw_fallback(scene_bytes, contact_capacity_bytes, rate_bps)

        bytes_transmitted = min(compressed_bytes, contact_capacity_bytes)
        completed = bytes_transmitted >= compressed_bytes
        tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
        tfup_s = (processing_time_s + tx_time) if completed else float("nan")
        tcp_s = tfup_s
        processing_energy_j = processing_time_s * PROCESSING_POWER_W
        tx_energy_j = tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes, contact_capacity_bytes, rate_bps,
            tfup_s, tcp_s, bytes_transmitted, processing_energy_j, tx_energy_j,
            completed, TIER_FIDELITY[ProductTier.P4_FULL],
        )

    def tiers(self, scene_bytes, processing_time_s=20.0, rate_bps=None, first_window_duration_s=None):
        """Tier plan for multi-contact use.

        A5's choice is rule-based per window in `run()`. For a multi-contact
        delivery, we evaluate the margin rule once against the first contact
        window and commit to that choice for the whole delivery, since the
        policy has no mechanism to re-evaluate mid-delivery. This is a
        stated simplification, not a claim that a fielded A5 would behave
        this way across many windows; see docs/ASSUMPTIONS.md.
        """
        use_compressed = True
        if rate_bps and first_window_duration_s:
            contact_duration_s = first_window_duration_s
            compressed_bytes = int(scene_bytes * COMPRESSED_FULL_FRACTION)
            compressed_tx = _transmit_time_bytes(compressed_bytes, rate_bps)
            use_compressed = self._margin_ok(contact_duration_s, compressed_tx, processing_time_s)
        if use_compressed:
            compressed_bytes = float(int(scene_bytes * COMPRESSED_FULL_FRACTION))
            return [(ProductTier.P4_FULL, compressed_bytes, processing_time_s)]
        return [(ProductTier.P4_FULL, float(scene_bytes), 0.0)]


ARCHITECTURE_REGISTRY = {
    A0_GROUND_ONLY: GroundOnly,
    A1_COMPRESSED_FULL: CompressedFull,
    A2_QUICKLOOK_FIRST: QuicklookFirst,
    A3_ROI_FIRST: RoiFirst,
    A4_PROGRESSIVE: Progressive,
    A5_CONTACT_AWARE: ContactAware,
    A6_THREAD_AWARE_PRIORITY: ThreadAwarePriority,
}
