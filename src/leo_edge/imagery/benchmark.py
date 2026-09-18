"""Image processing benchmark for LEO edge architecture."""

from __future__ import annotations

# Measured hardware benchmark config (updated by scripts/import_hardware_benchmark.py)
# Values are seconds per MB
MEASURED_CONFIG = {
    "compression_s_per_mb": 0.006897892777777776,
    "quicklook_s_per_mb": 0.015342352222222222,
    "roi_s_per_mb": 0.0009992768749999999,
    "source_csv": "C:/Users/noahh/OneDrive - West Point/leo-edge-architecture/results/frozen/image_benchmark.csv",
    "updated_at": "2026-09-18T21:20:20.687564Z",
}

import io
import time
from typing import List, Dict, Optional

from PIL import Image


class ImageBenchmark:
    """Benchmark image compression, quicklook and ROI operations."""

    def _load_image(self, image_path: Optional[str]) -> Image.Image:
        if image_path:
            return Image.open(image_path).convert("RGB")
        # synthetic 2048x2048 RGB
        img = Image.new("RGB", (2048, 2048))
        # simple gradient for non-trivial data
        pixels = img.load()
        for y in range(2048):
            for x in range(2048):
                pixels[x, y] = (x % 256, y % 256, (x + y) % 256)
        return img

    def _image_raw_bytes(self, img: Image.Image) -> int:
        # approximate raw RGB bytes
        w, h = img.size
        bands = len(img.getbands())
        return w * h * bands

    def benchmark_compression(
        self, image_path: Optional[str] = None, qualities: List[int] = [95, 85, 75]
    ) -> List[Dict]:
        img = self._load_image(image_path)
        raw_bytes = self._image_raw_bytes(img)
        results = []
        for q in qualities:
            buf = io.BytesIO()
            start = time.perf_counter_ns()
            img.save(buf, format="JPEG", quality=q, subsampling=0)
            end = time.perf_counter_ns()
            out_bytes = len(buf.getvalue())
            results.append({
                "quality": q,
                "output_bytes": out_bytes,
                "runtime_ms": (end - start) / 1_000_000,
                "compression_ratio": out_bytes / max(raw_bytes, 1),
            })
        return results

    def benchmark_quicklook(
        self, image_path: Optional[str] = None, scales: List[float] = [0.25, 0.1]
    ) -> List[Dict]:
        img = self._load_image(image_path)
        results = []
        for s in scales:
            w, h = img.size
            new_size = (max(1, int(w * s)), max(1, int(h * s)))
            start = time.perf_counter_ns()
            small = img.resize(new_size, Image.LANCZOS)
            buf = io.BytesIO()
            small.save(buf, format="JPEG", quality=85)
            end = time.perf_counter_ns()
            results.append({
                "scale": s,
                "output_bytes": len(buf.getvalue()),
                "runtime_ms": (end - start) / 1_000_000,
                "output_size": new_size,
            })
        return results

    def benchmark_roi(
        self, image_path: Optional[str] = None, fractions: List[float] = [0.05, 0.25, 0.5]
    ) -> List[Dict]:
        img = self._load_image(image_path)
        w, h = img.size
        results = []
        for f in fractions:
            # central crop with area fraction f
            scale = max(0.01, f ** 0.5)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            left = (w - new_w) // 2
            upper = (h - new_h) // 2
            right = left + new_w
            lower = upper + new_h
            roi = img.crop((left, upper, right, lower))
            buf = io.BytesIO()
            start = time.perf_counter_ns()
            roi.save(buf, format="JPEG", quality=85)
            end = time.perf_counter_ns()
            results.append({
                "fraction": f,
                "output_bytes": len(buf.getvalue()),
                "runtime_ms": (end - start) / 1_000_000,
                "crop_size": (new_w, new_h),
            })
        return results
