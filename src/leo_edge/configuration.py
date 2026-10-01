"""Validated notional product assumptions, available from installed wheels."""

from dataclasses import dataclass
from importlib.resources import files
from math import isfinite
import yaml


@dataclass(frozen=True)
class ProductSizing:
    compressed_fraction: float
    quicklook_fraction: float
    quicklook_time_fraction: float
    roi_fraction: float
    metadata_bytes: int
    thumbnail_bytes: int
    margin_alpha: float
    processing_power_w: float
    radio_power_w: float
    nominal_processing_time_s: float
    scene_bytes: int

    def __post_init__(self):
        for name, value in vars(self).items():
            if isinstance(value, bool) or not isfinite(value) or value < 0:
                raise ValueError(f"Invalid product assumption: {name}")
        for name in ("compressed_fraction", "quicklook_fraction", "roi_fraction"):
            if not 0 < getattr(self, name) <= 1:
                raise ValueError(f"Invalid size fraction: {name}")
        if not 0 <= self.margin_alpha < 1 or self.quicklook_time_fraction > 1:
            raise ValueError("Invalid processing fraction or contact margin")
        for name in ("metadata_bytes", "thumbnail_bytes"):
            if not isinstance(getattr(self, name), int) or getattr(self, name) <= 0:
                raise ValueError(f"Invalid fixed product size: {name}")
        if not isinstance(self.scene_bytes, int) or self.scene_bytes <= 0:
            raise ValueError("Nominal scene size must be a positive integer")


def load_sizing() -> ProductSizing:
    data = yaml.safe_load(files("leo_edge").joinpath("product_sizing.yaml").read_text())
    return ProductSizing(
        data["compressed_full"]["size_fraction"],
        data["quicklook"]["size_fraction"],
        data["quicklook"]["processing_time_fraction"],
        data["roi"]["size_fraction"],
        data["progressive"]["metadata_bytes"],
        data["progressive"]["thumbnail_bytes"],
        data["contact_aware"]["margin_alpha"],
        data["power"]["processing_power_w"], data["power"]["radio_power_w"],
        data["processing"]["nominal_time_s"], data["scene_bytes"],
    )


DEFAULT_SIZING = load_sizing()
