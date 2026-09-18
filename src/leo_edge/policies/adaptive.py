"""Adaptive policy."""

class AdaptivePolicy:
    """Select policy adaptively based on contact capacity."""

    def choose(self, scene, spacecraft_state, contact):
        """Return adaptive policy name.
        
        Args:
            scene: dict with keys bytes, compressed_bytes, quicklook_bytes, roi_bytes
            spacecraft_state: dict with available_processing_energy
            contact: dict with capacity info
        Returns:
            str: policy name
        """
        capacity = contact.get("capacity_bytes", 0)
        compressed_size = scene.get("compressed_bytes", 0)
        quicklook_size = scene.get("quicklook_bytes", 0)
        
        if compressed_size <= capacity * 0.8:
            return "compressed_full"
        if quicklook_size <= capacity * 0.8:
            return "quicklook_roi"
        return "progressive_minimum"
