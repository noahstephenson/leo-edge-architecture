"""leo_edge package."""

import random
import numpy as np

# Ensure deterministic seeds for experiments
random.seed(0)
np.random.seed(0)

from .analysis import break_even_rate, latency_processed, latency_raw, energy_favorable
from .architectures import GroundOnly, CompressedFull, QuicklookFirst, RoiFirst, Progressive

__all__ = [
    "break_even_rate",
    "latency_processed",
    "latency_raw",
    "energy_favorable",
    "GroundOnly",
    "CompressedFull",
    "QuicklookFirst",
    "RoiFirst",
    "Progressive",
]
