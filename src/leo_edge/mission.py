"""Mission request definitions."""

from dataclasses import dataclass
from typing import Any


@dataclass
class MissionRequest:
    """A single collection request."""
    request_id: str
    collection_time: float  # seconds since epoch
    deadline: float  # seconds since epoch
    requested_product_tier: str
    roi_fraction: float  # 0-1
    priority_class: int
