"""Adaptive policy: selects a real architecture class based on contact capacity."""

from ..architectures import CompressedFull, Progressive, QuicklookFirst, RoiFirst


class AdaptivePolicy:
    """Pick an architecture class from how much of the contact capacity a
    scene's compressed, ROI, and quicklook products would each use.

    This is a simple margin-based rule matching A5_CONTACT_AWARE's intent
    (send the richest product that fits with margin to spare), extended
    here to choose among the real architecture classes instead of returning
    a label that had no corresponding implementation. See
    docs/ALLOCATION_SPACE.md for how A5 fits the broader allocation space.
    """

    def __init__(self, margin: float = 0.8):
        self.margin = margin

    def choose(self, scene, spacecraft_state, contact):
        """Return the architecture class this policy would run.

        Args:
            scene: dict with keys bytes, compressed_bytes, quicklook_bytes, roi_bytes
            spacecraft_state: dict with available_processing_energy (unused
                by this rule today; kept in the signature so a future
                power-aware rule doesn't need to change every caller)
            contact: dict with capacity_bytes

        Returns:
            An architecture class from leo_edge.architectures.
        """
        capacity = contact.get("capacity_bytes", 0)
        compressed_size = scene.get("compressed_bytes", 0)
        roi_size = scene.get("roi_bytes", 0)
        quicklook_size = scene.get("quicklook_bytes", 0)

        if compressed_size <= capacity * self.margin:
            return CompressedFull
        if roi_size <= capacity * self.margin:
            return RoiFirst
        if quicklook_size <= capacity * self.margin:
            return QuicklookFirst
        return Progressive
