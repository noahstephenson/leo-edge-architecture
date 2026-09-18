# Imagery Dataset Manifest

This directory holds public and synthetic imagery used for benchmarking LEO edge processing.

## Structure

- `data/imagery/` – root for dataset files
- `manifest.csv` – required dataset manifest
- `raw/` – original source images
- `processed/` – derived products (quicklook, ROI, compressed)

## Manifest Schema

`manifest.csv` must contain:

| Column | Description | Example |
|--------|-------------|---------|
| id | Unique image identifier | `landsat_2024_001` |
| source | Source label, e.g., `landsat`, `sentinel2`, `synthetic` | `synthetic` |
| path | Relative path to raw file from this directory | `raw/landsat_2024_001.tif` |
| width | Image width in pixels | 2048 |
| height | Image height in pixels | 2048 |
| bands | Number of spectral bands | 3 |
| size_bytes | File size on disk | 12582912 |
| acquisition_time | ISO-8601 timestamp | 2024-06-01T12:00:00Z |
| license | Public source license | `USGS EROS` |

## Usage Notes

- Only public civilian imagery is permitted.
- No operational collection plans or real terminal locations.
- Synthetic images are generated on demand by `ImageBenchmark` when no path is provided.
- Benchmark results are deterministic when seeded and must be reproducible from this manifest.

## Adding Data

1. Place raw files under `raw/`.
2. Append a row to `manifest.csv` with accurate metadata.
3. Do not commit large binary files; use external storage or references for paper runs.
