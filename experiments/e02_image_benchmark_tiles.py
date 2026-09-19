"""Experiment e02 image benchmark run with 30 tiles."""
from __future__ import annotations

import io
import os
import random
import urllib.request
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
from PIL import Image

from leo_edge.imagery.benchmark import ImageBenchmark

RESULT_DIR = Path("results/frozen")
DATA_DIR = Path("data/imagery/tiles")
RESULT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

BENCH = ImageBenchmark()

def download_tile(tile_id: str, url: str, dest: Path) -> Path:
    if dest.exists():
        # Tiles are checked-in input data, not scratch output: once a tile
        # exists, reuse it rather than re-fetching and overwriting it. A
        # prior version of this function always re-downloaded and
        # overwrote dest on every run, silently mutating checked-in
        # data/imagery/tiles/*.jpg with whatever picsum.photos returned
        # that moment (confirmed: tile_001.jpg changed from 910,705 to
        # 630,392 bytes between two runs). See docs/DECISION_LOG.md.
        return dest
    try:
        # Try download with short timeout
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read()
        # Save
        dest.write_bytes(data)
        return dest
    except Exception:
        # Fallback to synthetic 4K
        return generate_synthetic_tile(tile_id, dest)

def generate_synthetic_tile(tile_id: str, dest: Path) -> Path:
    # Deterministic 4096x4096 gradient with stable seed from tile_id
    import hashlib
    digest = hashlib.md5(tile_id.encode()).hexdigest()
    seed = int(digest[:8], 16)
    random.seed(seed)
    np.random.seed(seed)
    w, h = 4096, 4096
    # Create blocky noise efficiently with NumPy
    block = 64
    blocks_y = h // block
    blocks_x = w // block
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for by in range(blocks_y):
        for bx in range(blocks_x):
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            y0 = by * block
            x0 = bx * block
            arr[y0:y0+block, x0:x0+block] = [r, g, b]
    img = Image.fromarray(arr, mode="RGB")
    img.save(dest, format="JPEG", quality=95)
    return dest

def compute_psnr(img1: Image.Image, img2: Image.Image) -> float:
    a = np.array(img1, dtype=np.float32)
    b = np.array(img2, dtype=np.float32)
    mse = np.mean((a - b) ** 2)
    if mse == 0:
        return float("inf")
    PIXEL_MAX = 255.0
    return 20 * np.log10(PIXEL_MAX / np.sqrt(mse))

def compute_ssim(img1: Image.Image, img2: Image.Image) -> float:
    a = np.array(img1, dtype=np.float32)
    b = np.array(img2, dtype=np.float32)
    mu_x = a.mean()
    mu_y = b.mean()
    sigma_x = a.std()
    sigma_y = b.std()
    sigma_xy = ((a - mu_x) * (b - mu_y)).mean()
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    num = (2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2)
    den = (mu_x ** 2 + mu_y ** 2 + C1) * (sigma_x ** 2 + sigma_y ** 2 + C2)
    return float(num / den) if den != 0 else 0.0

def benchmark_tile(tile_id: str, image_path: Path) -> Dict:
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    bands = len(img.getbands())
    raw_bytes = w * h * bands

    # Compression quality 85
    comp_res = BENCH.benchmark_compression(str(image_path), qualities=[85])
    comp_bytes = comp_res[0]["output_bytes"]
    comp_time_s = comp_res[0]["runtime_ms"] / 1000.0

    # Quicklook scale 0.25
    ql_res = BENCH.benchmark_quicklook(str(image_path), scales=[0.25])
    ql_bytes = ql_res[0]["output_bytes"]
    ql_time_s = ql_res[0]["runtime_ms"] / 1000.0

    # ROI fraction 0.25
    roi_res = BENCH.benchmark_roi(str(image_path), fractions=[0.25])
    roi_bytes = roi_res[0]["output_bytes"]
    roi_time_s = roi_res[0]["runtime_ms"] / 1000.0

    # PSNR/SSIM for compression quality 85
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, subsampling=0)
    buf.seek(0)
    comp_img = Image.open(buf).convert("RGB")
    # Resize comp_img to original size if needed
    if comp_img.size != img.size:
        comp_img = comp_img.resize(img.size, Image.LANCZOS)
    psnr = compute_psnr(img, comp_img)
    ssim = compute_ssim(img, comp_img)

    return {
        "tile_id": tile_id,
        "raw_bytes": raw_bytes,
        "compressed_bytes": comp_bytes,
        "quicklook_bytes": ql_bytes,
        "roi_bytes": roi_bytes,
        "comp_time_s": comp_time_s,
        "ql_time_s": ql_time_s,
        "roi_time_s": roi_time_s,
        "psnr": psnr,
        "ssim": ssim,
        "width": w,
        "height": h,
    }

def main():
    tile_ids = [f"tile_{i:03d}" for i in range(1, 31)]
    rows: List[Dict] = []

    for i, tile_id in enumerate(tile_ids, 1):
        dest = DATA_DIR / f"{tile_id}.jpg"
        # Public sample imagery source; falls back to a synthetic tile if unreachable
        url = f"https://picsum.photos/4096/4096?random={i}"
        image_path = download_tile(tile_id, url, dest)
        row = benchmark_tile(tile_id, image_path)
        rows.append(row)
        print(f"Processed {tile_id}: raw={row['raw_bytes']:,} bytes")

    # Save aggregate CSV
    df = pd.DataFrame(rows)
    out_csv = RESULT_DIR / "image_benchmark.csv"
    df[["tile_id","raw_bytes","compressed_bytes","quicklook_bytes","roi_bytes",
        "comp_time_s","ql_time_s","roi_time_s","psnr","ssim"]].to_csv(out_csv, index=False)
    print(f"Saved aggregate CSV to {out_csv}")

    # Normalized MB/pixel summary
    pixels = df["width"] * df["height"]
    # Convert bytes to MB (1 MB = 1e6 bytes) then per pixel
    norm = pd.DataFrame({
        "tile_id": df["tile_id"],
        "raw_mb_per_pixel": df["raw_bytes"] / pixels / 1e6,
        "compressed_mb_per_pixel": df["compressed_bytes"] / pixels / 1e6,
        "quicklook_mb_per_pixel": df["quicklook_bytes"] / pixels / 1e6,
        "roi_mb_per_pixel": df["roi_bytes"] / pixels / 1e6,
    })
    norm_csv = RESULT_DIR / "image_benchmark_normalized.csv"
    norm.to_csv(norm_csv, index=False)
    print(f"Saved normalized summary to {norm_csv}")

if __name__ == "__main__":
    main()
