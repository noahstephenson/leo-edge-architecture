"""Image processing benchmark stubs."""

from typing import Dict


def process_image(scene_bytes: int, pipeline: str) -> Dict[str, float]:
    """Process image bytes with named pipeline.

    Returns dict with output_bytes and processing_time_s.
    Pipeline names are illustrative; factors are simple constants.
    """
    pipeline = pipeline.lower()
    # Simple compression / resize factors
    factors = {
        "raw": (1.0, 0.0),
        "quicklook": (0.05, 0.5),
        "thumbnail": (0.01, 0.1),
        "roi": (0.3, 1.2),
        "compress": (0.4, 0.8),
    }
    factor, time_per_mb = factors.get(pipeline, (0.5, 1.0))
    # Processing time scales with input size (MB)
    size_mb = max(scene_bytes, 1) / (1024 * 1024)
    processing_time_s = time_per_mb * size_mb
    output_bytes = int(scene_bytes * factor)
    return {"output_bytes": output_bytes, "processing_time_s": processing_time_s}
