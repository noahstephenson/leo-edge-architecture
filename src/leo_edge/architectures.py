"""Candidate product plans; single-contact calls use the shared transfer engine."""
from .architecture import (A0_GROUND_ONLY, A1_COMPRESSED_FULL, A2_QUICKLOOK_FIRST,
                           A3_ROI_FIRST, A4_PROGRESSIVE, A5_CONTACT_AWARE,
                           A6_THREAD_AWARE_PRIORITY)
from .configuration import DEFAULT_SIZING
from .products import ProductTier

PROCESSING_POWER_W = DEFAULT_SIZING.processing_power_w
RADIO_POWER_W = DEFAULT_SIZING.radio_power_w
COMPRESSED_FULL_FRACTION = DEFAULT_SIZING.compressed_fraction
QUICKLOOK_SIZE_FRACTION = DEFAULT_SIZING.quicklook_fraction
QUICKLOOK_TIME_FRACTION = DEFAULT_SIZING.quicklook_time_fraction
ROI_SIZE_FRACTION = DEFAULT_SIZING.roi_fraction
PROGRESSIVE_METADATA_BYTES = DEFAULT_SIZING.metadata_bytes
PROGRESSIVE_THUMBNAIL_BYTES = DEFAULT_SIZING.thumbnail_bytes
# Legacy aliases at the documented 1 GB scene; plans scale with scene size.
PROGRESSIVE_QUICKLOOK_BYTES = int(DEFAULT_SIZING.scene_bytes * DEFAULT_SIZING.quicklook_fraction)
PROGRESSIVE_ROI_BYTES = int(DEFAULT_SIZING.scene_bytes * DEFAULT_SIZING.roi_fraction)
CONTACT_AWARE_MARGIN_ALPHA = DEFAULT_SIZING.margin_alpha

class Candidate:
    PROVENANCE = "original_candidate_set"
    CONDITIONAL_LOGIC = False

    def __init__(self, sizing=DEFAULT_SIZING):
        self.sizing = sizing

    def run(self, scene_bytes, contact_capacity_bytes, rate_bps, processing_time_s):
        """Compatibility adapter, with no separate byte or time accounting."""
        from .simulation import single_contact_metrics
        return single_contact_metrics(self, scene_bytes, contact_capacity_bytes,
                                      rate_bps, processing_time_s)

class GroundOnly(Candidate):
    """Raw full scene; a capable terminal derives its needed view."""
    ARCH_ID = A0_GROUND_ONLY

    def tiers(self, scene_bytes, processing_time_s=DEFAULT_SIZING.nominal_processing_time_s, **kwargs):
        return [(ProductTier.P4_FULL, float(scene_bytes), 0.0)]

class CompressedFull(Candidate):
    ARCH_ID = A1_COMPRESSED_FULL

    def tiers(self, scene_bytes, processing_time_s=DEFAULT_SIZING.nominal_processing_time_s, **kwargs):
        return [(ProductTier.P4_FULL, max(1, int(scene_bytes * self.sizing.compressed_fraction)), processing_time_s)]

class QuicklookFirst(Candidate):
    ARCH_ID = A2_QUICKLOOK_FIRST

    def tiers(self, scene_bytes, processing_time_s=DEFAULT_SIZING.nominal_processing_time_s, **kwargs):
        return [(ProductTier.P2_QUICKLOOK, max(1, int(scene_bytes * self.sizing.quicklook_fraction)),
                 processing_time_s * self.sizing.quicklook_time_fraction),
                (ProductTier.P4_FULL, float(scene_bytes), 0.0)]

class RoiFirst(Candidate):
    ARCH_ID = A3_ROI_FIRST

    def tiers(self, scene_bytes, processing_time_s=DEFAULT_SIZING.nominal_processing_time_s, **kwargs):
        return [(ProductTier.P3_ROI, max(1, int(scene_bytes * self.sizing.roi_fraction)), processing_time_s),
                (ProductTier.P4_FULL, float(scene_bytes), 0.0)]

class Progressive(Candidate):
    ARCH_ID = A4_PROGRESSIVE

    def _tier_sizes(self, scene_bytes):
        return [(ProductTier.P0_METADATA, self.sizing.metadata_bytes),
                (ProductTier.P1_THUMBNAIL, self.sizing.thumbnail_bytes),
                (ProductTier.P2_QUICKLOOK, max(1, int(scene_bytes * self.sizing.quicklook_fraction))),
                (ProductTier.P3_ROI, max(1, int(scene_bytes * self.sizing.roi_fraction))),
                (ProductTier.P4_FULL, scene_bytes)]

    def tiers(self, scene_bytes, processing_time_s=DEFAULT_SIZING.nominal_processing_time_s, **kwargs):
        return [(tier, float(size), processing_time_s if i == 0 else 0.0)
                for i, (tier, size) in enumerate(self._tier_sizes(scene_bytes))]

class ThreadAwarePriority(Progressive):
    """Metadata, requested product, then remaining catalog order.

    Partial products retain their place; large products are never skipped.
    This policy does not schedule competing requests.
    """
    ARCH_ID = A6_THREAD_AWARE_PRIORITY
    PROVENANCE = "proposed_post_v2"
    CONDITIONAL_LOGIC = True

    def __init__(self, priority_tier=ProductTier.P2_QUICKLOOK, sizing=DEFAULT_SIZING):
        super().__init__(sizing)
        self.priority_tier = ProductTier(priority_tier)

    def _tier_sizes(self, scene_bytes):
        base = super()._tier_sizes(scene_bytes)
        return ([item for item in base if item[0] == ProductTier.P0_METADATA]
                + [item for item in base if item[0] == self.priority_tier and item[0] != ProductTier.P0_METADATA]
                + [item for item in base if item[0] not in (ProductTier.P0_METADATA, self.priority_tier)])

class ContactAware(Candidate):
    """Choose raw or compressed once using the first contact's margin."""
    ARCH_ID = A5_CONTACT_AWARE
    CONDITIONAL_LOGIC = True

    def __init__(self, alpha=None, processor_fault=False, sizing=DEFAULT_SIZING):
        super().__init__(sizing)
        self.alpha = sizing.margin_alpha if alpha is None else alpha
        if not 0 <= self.alpha < 1:
            raise ValueError("Contact margin must lie in [0, 1)")
        self.processor_fault = processor_fault

    def _margin_ok(self, contact_duration_s, compressed_tx, processing_time_s):
        return (processing_time_s <= (1 - self.alpha) * contact_duration_s
                and processing_time_s + compressed_tx <= contact_duration_s)

    def tiers(self, scene_bytes, processing_time_s=DEFAULT_SIZING.nominal_processing_time_s, rate_bps=None,
              first_window_duration_s=None, first_window_start_s=None):
        size = max(1, int(scene_bytes * self.sizing.compressed_fraction))
        compressed = not self.processor_fault
        if compressed and rate_bps is not None and first_window_duration_s is not None:
            exposed = max(0.0, processing_time_s - (first_window_start_s or 0.0))
            compressed = self._margin_ok(first_window_duration_s, size * 8 / rate_bps, exposed)
        return [(ProductTier.P4_FULL, float(size if compressed else scene_bytes),
                 processing_time_s if compressed else 0.0)]

ARCHITECTURE_REGISTRY = {
    A0_GROUND_ONLY: GroundOnly, A1_COMPRESSED_FULL: CompressedFull,
    A2_QUICKLOOK_FIRST: QuicklookFirst, A3_ROI_FIRST: RoiFirst,
    A4_PROGRESSIVE: Progressive, A5_CONTACT_AWARE: ContactAware,
    A6_THREAD_AWARE_PRIORITY: ThreadAwarePriority,
}
