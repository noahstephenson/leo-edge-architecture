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
