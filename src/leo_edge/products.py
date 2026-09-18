"""Product tier and product definitions."""

from dataclasses import dataclass
from enum import Enum


class ProductTier(str, Enum):
    """Product tier identifiers."""
    P0_METADATA = "P0_METADATA"
    P1_THUMBNAIL = "P1_THUMBNAIL"
    P2_QUICKLOOK = "P2_QUICKLOOK"
    P3_ROI = "P3_ROI"
    P4_FULL = "P4_FULL"


@dataclass(frozen=True)
class Fidelity:
    """Fidelity descriptor for a product tier.

    lossy: whether the tier discards image information relative to the raw
        scene (True for every tier except metadata).
    resolution_class: coarse label for what a viewer actually sees, used so
        results never compare tiers on delivery time alone without also
        stating what was delivered. Not a pixel count: "full_res" means the
        tier carries the scene at its native resolution (possibly cropped,
        as with an ROI), "coarse" and "reduced" mean downsampled.
    """
    lossy: bool
    resolution_class: str


# Fidelity is a property of the tier, not of any one architecture's encoding
# choice: two architectures that both deliver a quicklook are both delivering
# a coarse, lossy product, whatever compression they used to get there.
TIER_FIDELITY = {
    ProductTier.P0_METADATA: Fidelity(lossy=False, resolution_class="metadata"),
    ProductTier.P1_THUMBNAIL: Fidelity(lossy=True, resolution_class="coarse"),
    ProductTier.P2_QUICKLOOK: Fidelity(lossy=True, resolution_class="reduced"),
    ProductTier.P3_ROI: Fidelity(lossy=True, resolution_class="roi_full_res"),
    ProductTier.P4_FULL: Fidelity(lossy=True, resolution_class="full_res"),
}


@dataclass
class Product:
    """A generated product."""
    tier: str
    parent_scene: str
    bytes: int
    processing_time: float  # seconds
    energy_cost: float  # joules
    priority: int
    completeness: float  # 0-1

    @property
    def fidelity(self) -> Fidelity:
        return TIER_FIDELITY[ProductTier(self.tier)]
