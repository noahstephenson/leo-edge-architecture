"""Static architecture implementations A0-A6."""

PROCESSING_POWER_W = 15
RADIO_POWER_W = 25


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
):
    """Compute standard metric fields for architecture outputs."""
    contact_duration_s = (
        contact_capacity_bytes * 8 / rate_bps if rate_bps > 0 else float("inf")
    )
    contact_utilization = (
        bytes_transmitted / contact_capacity_bytes if contact_capacity_bytes > 0 else 0.0
    )
    storage_peak_bytes = int(scene_bytes)
    # Simple deadline heuristic: delivery within contact window + processing
    deadline_met = tcp_s <= contact_duration_s + 1e-9
    product_completeness = (
        min(1.0, bytes_transmitted / scene_bytes) if scene_bytes > 0 else 0.0
    )
    return {
        "tfup_s": tfup_s,
        "tcp_s": tcp_s,
        "contact_utilization": contact_utilization,
        "processing_energy_j": processing_energy_j,
        "tx_energy_j": tx_energy_j,
        "storage_peak_bytes": storage_peak_bytes,
        "deadline_met": deadline_met,
        "product_completeness": product_completeness,
        "bytes_transmitted": bytes_transmitted,
    }


class GroundOnly:
    """A0_GROUND_ONLY: no processing, transmit raw if fits."""

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        bytes_transmitted = min(scene_bytes, contact_capacity_bytes)
        tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
        tfup_s = tx_time
        tcp_s = tx_time
        processing_energy_j = 0.0
        tx_energy_j = tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes,
            contact_capacity_bytes,
            rate_bps,
            tfup_s,
            tcp_s,
            bytes_transmitted,
            processing_energy_j,
            tx_energy_j,
        )


class CompressedFull:
    """A1_COMPRESSED_FULL: process then transmit compressed."""

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        compressed_bytes = int(scene_bytes * 0.3)
        bytes_transmitted = min(compressed_bytes, contact_capacity_bytes)
        tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
        total_time = processing_time_s + tx_time
        processing_energy_j = processing_time_s * PROCESSING_POWER_W
        tx_energy_j = tx_time * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes,
            contact_capacity_bytes,
            rate_bps,
            total_time,
            total_time,
            bytes_transmitted,
            processing_energy_j,
            tx_energy_j,
        )


class QuicklookFirst:
    """A2_QUICKLOOK_FIRST: quicklook then full if capacity allows."""

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        quicklook_bytes = int(scene_bytes * 0.02)
        quicklook_proc = processing_time_s * 0.1
        quicklook_tx = _transmit_time_bytes(quicklook_bytes, rate_bps)
        tfup_s = quicklook_proc + quicklook_tx

        bytes_transmitted = quicklook_bytes
        tx_time_total = quicklook_tx

        remaining_capacity = contact_capacity_bytes - quicklook_bytes
        if remaining_capacity >= scene_bytes:
            full_tx = _transmit_time_bytes(scene_bytes, rate_bps)
            bytes_transmitted += scene_bytes
            tx_time_total += full_tx
            tcp_s = quicklook_proc + quicklook_tx + full_tx
        else:
            tcp_s = tfup_s

        processing_energy_j = quicklook_proc * PROCESSING_POWER_W
        tx_energy_j = tx_time_total * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes,
            contact_capacity_bytes,
            rate_bps,
            tfup_s,
            tcp_s,
            bytes_transmitted,
            processing_energy_j,
            tx_energy_j,
        )


class RoiFirst:
    """A3_ROI_FIRST: ROI then full if capacity allows."""

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        roi_bytes = int(scene_bytes * 0.1)
        roi_proc = processing_time_s  # ROI generation time
        roi_tx = _transmit_time_bytes(roi_bytes, rate_bps)
        tfup_s = roi_proc + roi_tx

        bytes_transmitted = roi_bytes
        tx_time_total = roi_tx

        remaining_capacity = contact_capacity_bytes - roi_bytes
        if remaining_capacity >= scene_bytes:
            full_tx = _transmit_time_bytes(scene_bytes, rate_bps)
            bytes_transmitted += scene_bytes
            tx_time_total += full_tx
            tcp_s = roi_proc + roi_tx + full_tx
        else:
            tcp_s = tfup_s

        processing_energy_j = roi_proc * PROCESSING_POWER_W
        tx_energy_j = tx_time_total * RADIO_POWER_W
        return _finalize_metrics(
            scene_bytes,
            contact_capacity_bytes,
            rate_bps,
            tfup_s,
            tcp_s,
            bytes_transmitted,
            processing_energy_j,
            tx_energy_j,
        )


class Progressive:
    """A4_PROGRESSIVE: metadata, thumbnail, quicklook, roi, full in order."""

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        metadata_bytes = 20 * 1024
        thumbnail_bytes = int(0.5 * 1024 * 1024)
        quicklook_bytes = int(10 * 1024 * 1024)
        roi_bytes = int(50 * 1024 * 1024)
        full_bytes = scene_bytes

        products = [
            metadata_bytes,
            thumbnail_bytes,
            quicklook_bytes,
            roi_bytes,
            full_bytes,
        ]

        remaining = contact_capacity_bytes
        bytes_transmitted = 0
        total_tx_time = 0.0
        first_tx_time = None

        for size in products:
            if size > remaining:
                # skip product that does not fit
                continue
            tx_time = _transmit_time_bytes(size, rate_bps)
            if first_tx_time is None:
                first_tx_time = tx_time
            total_tx_time += tx_time
            bytes_transmitted += size
            remaining -= size

        first_tx_time = first_tx_time or 0.0
        tfup_s = processing_time_s + first_tx_time
        tcp_s = processing_time_s + total_tx_time

        processing_energy_j = processing_time_s * PROCESSING_POWER_W
        tx_energy_j = total_tx_time * RADIO_POWER_W

        return _finalize_metrics(
            scene_bytes,
            contact_capacity_bytes,
            rate_bps,
            tfup_s,
            tcp_s,
            bytes_transmitted,
            processing_energy_j,
            tx_energy_j,
        )


class ContactAware:
    """A5_CONTACT_AWARE: rule-based policy using contact margin α and predicted contact time.

    If processor fault or insufficient margin, falls back to raw transmit.
    Otherwise processes compressed full when processing fits within margin.
    """

    def __init__(self, alpha=0.2, processor_fault=False):
        self.alpha = alpha
        self.processor_fault = processor_fault

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        # Graceful fallback on processor fault
        if self.processor_fault or rate_bps <= 0:
            bytes_transmitted = min(scene_bytes, contact_capacity_bytes)
            tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
            tfup_s = tx_time
            tcp_s = tx_time
            processing_energy_j = 0.0
            tx_energy_j = tx_time * RADIO_POWER_W
            return _finalize_metrics(
                scene_bytes,
                contact_capacity_bytes,
                rate_bps,
                tfup_s,
                tcp_s,
                bytes_transmitted,
                processing_energy_j,
                tx_energy_j,
            )

        contact_duration_s = (
            contact_capacity_bytes * 8 / rate_bps if rate_bps > 0 else float("inf")
        )
        # Rule: need processing to finish with margin α before contact ends
        # and enough time left to transmit compressed product
        compressed_bytes = int(scene_bytes * 0.3)
        compressed_tx = _transmit_time_bytes(compressed_bytes, rate_bps)

        # Margin check
        if processing_time_s <= (1.0 - self.alpha) * contact_duration_s and (
            processing_time_s + compressed_tx <= contact_duration_s
        ):
            # Process onboard
            bytes_transmitted = min(compressed_bytes, contact_capacity_bytes)
            tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
            tfup_s = processing_time_s + tx_time
            tcp_s = tfup_s
            processing_energy_j = processing_time_s * PROCESSING_POWER_W
            tx_energy_j = tx_time * RADIO_POWER_W
        else:
            # Fallback to raw transmit
            bytes_transmitted = min(scene_bytes, contact_capacity_bytes)
            tx_time = _transmit_time_bytes(bytes_transmitted, rate_bps)
            tfup_s = tx_time
            tcp_s = tx_time
            processing_energy_j = 0.0
            tx_energy_j = tx_time * RADIO_POWER_W

        return _finalize_metrics(
            scene_bytes,
            contact_capacity_bytes,
            rate_bps,
            tfup_s,
            tcp_s,
            bytes_transmitted,
            processing_energy_j,
            tx_energy_j,
        )
