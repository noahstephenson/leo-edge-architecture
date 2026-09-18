"""Architecture definitions."""

from dataclasses import dataclass
from typing import Final

# Architecture IDs
A0_GROUND_ONLY: Final = "A0_GROUND_ONLY"
A1_COMPRESSED_FULL: Final = "A1_COMPRESSED_FULL"
A2_QUICKLOOK_FIRST: Final = "A2_QUICKLOOK_FIRST"
A3_ROI_FIRST: Final = "A3_ROI_FIRST"
A4_PROGRESSIVE: Final = "A4_PROGRESSIVE"
A5_CONTACT_AWARE: Final = "A5_CONTACT_AWARE"


@dataclass
class Architecture:
    """Simple architecture descriptor."""
    name: str
    description: str
