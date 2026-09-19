# Data Dictionary

## Primary metrics

These are the fields computed by `src/leo_edge/metrics.py` and reported in every experiment's output CSV.

| Field | Meaning | Unit |
|---|---|---|
| `tfup_s` | Time to first useful product: how long after image capture the first usable product reaches the user. `NaN` when no usable product was delivered (see `completed`), never a fabricated number. | seconds |
| `tcp_s` | Time to complete product: how long after capture the full-resolution product reaches the user. `NaN` when the full product never arrived, rather than being set equal to `tfup_s`. | seconds |
| `completed` | Whether the full product (the tier `tcp_s` describes) actually finished delivering. False means `tcp_s` is `NaN`, not zero and not equal to `tfup_s`. | true/false |
| `contact_utilization` | Fraction of the contact window's downlink capacity actually used | 0 to 1, clamped |
| `processing_energy_j` | Energy spent on onboard processing | joules |
| `tx_energy_j` | Energy spent on radio transmission | joules |
| `storage_peak_bytes` | Peak onboard storage used during the scenario | bytes |
| `deadline_met` | Whether the product was delivered, and delivered within the contact window | true/false |
| `product_completeness` | Fraction of the full scene actually delivered | 0 to 1 |
| `fidelity_lossy` | Whether the delivered product discards information relative to the raw scene | true/false |
| `fidelity_resolution_class` | Coarse label for what the delivered product actually shows: `metadata`, `coarse`, `reduced`, `roi_full_res`, or `full_res`. Two architectures with the same `tfup_s` are not necessarily comparable unless this field also matches. | string |

## Product tiers

See `docs/CONOPS.md` for what each tier (P0 through P4) means operationally. In code, they're defined in `src/leo_edge/products.py`'s `ProductTier` enum.

## Architecture IDs

| ID | What it does |
|---|---|
| A0_GROUND_ONLY | No onboard processing, transmit raw |
| A1_COMPRESSED_FULL | Compress onboard, then transmit the compressed full scene |
| A2_QUICKLOOK_FIRST | Send a small quicklook first, then the full scene if capacity allows |
| A3_ROI_FIRST | Send a region-of-interest crop first, then the full scene if capacity allows |
| A4_PROGRESSIVE | Send metadata, thumbnail, quicklook, ROI, and full scene in that order, as capacity allows |
| A5_CONTACT_AWARE | Rule-based: process onboard only if it will finish with enough margin before contact ends, otherwise fall back to raw |

Implemented in `src/leo_edge/architectures.py`.

## Product metadata fields

Each generated product is described by:

```yaml
scene_id:
product_tier:
generation_time:
original_size_bytes:
product_size_bytes:
roi_fraction:
compression:
quality_setting:
deadline:
priority:
```

## Real image tile manifest

The 30 real image tiles in `data/imagery/tiles/` are described by the manifest schema in `data/imagery/README.md` (id, source, path, width, height, bands, size in bytes, acquisition time, license).

## Result CSV files

`results/frozen/v3/` holds one CSV per experiment (e.g. `e03_results.csv` has one row per architecture x downlink-rate combination) plus one CSV per figure that computes its own derived data (e.g. `fig04_data.csv`). Column names match the metric names above plus the experiment's swept parameters (`rate_bps`, `contact_duration_s`, `architecture_name`, and so on).
