# Experiments Summary - v1 Frozen Results

Generated: 2026-09-18

## Overview
Experiments e00_sanity.py through e10_storage_wear.py executed with PYTHONPATH=src. CSV outputs copied to `results/frozen/v1/`. Config files baseline.yaml and orbits.yaml archived.

## e00_sanity.py - Analytical Model Sanity Check
Analytical break-even examples printed:
- Example 1: D_r=1e9 B, D_p=3e8 B, T_proc=20s → R* = 3.50e7 B/s. At R=4.20e7 B/s, processed=27.1s, raw=23.8s, favorable=False
- Example 2: D_r=2e9 B, D_p=5e8 B, T_proc=30s → R* = 5.00e7 B/s. At R=6.00e7 B/s, processed=38.3s, raw=33.3s, favorable=False
- Example 3: D_r=5e8 B, D_p=1e8 B, T_proc=10s → R* = 4.00e7 B/s. At R=4.80e7 B/s, processed=12.1s, raw=10.4s, favorable=False

## e01_orbit_contacts.py - LEO Access Windows
CSV: e01_access_windows.csv
- Duration modeled: 168 hours (one week)
- Num windows: 21
- Total contact duration: 6810.0 s (113.5 min)
- Window durations range from about 30 s to 420 s, concentrated in the 150-420 s band

## e02_image_benchmark.py - Image Processing Benchmark
CSV: e02_compression.csv, e02_quicklook.csv, e02_roi.csv
Compression:
- quality 95 → output_bytes 813681, runtime_ms 125.1, ratio 0.0647
- quality 85 → output_bytes 500119, runtime_ms 23.4, ratio 0.0397
- quality 75 → output_bytes 378985, runtime_ms 26.2, ratio 0.0301

Quicklook:
- scale 0.25 → output_bytes 41043, runtime_ms 180.2, output_size (512,512)
- scale 0.1 → output_bytes 16000, runtime_ms 159.6, output_size (204,204)

ROI:
- fraction 0.05 → output_bytes 19083, runtime_ms 4.1, crop_size (457,457)
- fraction 0.25 → output_bytes 71331, runtime_ms 14.8, crop_size (1024,1024)
- fraction 0.5 → output_bytes 190510, runtime_ms 22.5, crop_size (1448,1448)

## e03_static_architectures.py - Rate Sweep
CSV: e03_results.csv, 30 rows (5 architectures × 6 rates)
Scene 1e9 B, contact 300 s, processing 20 s
Key TFUP samples:
- GroundOnly @ 100 Mbps: TFUP 80.0 s, TCP 80.0 s
- CompressedFull @ 100 Mbps: TFUP 44.0 s, TCP 44.0 s
- QuicklookFirst @ 100 Mbps: TFUP 3.6 s, TCP 83.6 s
- Progressive @ 1 Mbps: TFUP 20.2 s, TCP 108.2 s
Progressive achieves ~20 s TFUP across rates due to quicklook-first delivery.

## e04_contact_sweep.py - Contact Duration Sweep
CSV: e04_contact_sweep.csv, 18 rows
Scene 1e9 B, rate 10 Mbps, processing 30 s
Durations 120-600 s step 60 s
- GroundOnly TFUP = contact_duration_s, utilization 1.0
- Progressive TFUP ≈ 30.0 s constant, TCP ≈ 80.8 s
Example 120 s: GroundOnly TFUP 120.0 s, Progressive TFUP 30.02 s, Progressive utilization 0.42

## e05_power_sweep.py - Processing Power Break-even
CSV: e05_power_sweep.csv
D_r=1e9 B, D_p=3e8 B, T_proc=20 s
Power vs energy break-even transmission energy per byte e_t*:
- 5 W → E_p 100.0 J, e_t* 1.786e-08 J/B
- 15 W → E_p 300.0 J, e_t* 5.357e-08 J/B
- 30 W → E_p 600.0 J, e_t* 1.071e-07 J/B

## e06_queue_stress.py - Queue Stress
CSV: e06_queue_stress.csv, 24 events
Scenes per day 20, scene 500 MB, arrivals every 4320 s
Contacts 4/day × 300 s @10 Mbps = 375 MB per contact
- Max backlog: 8500.0 MB
- Final backlog: 8500.0 MB
Indicates backlog growth under given arrival/contact assumptions.

## e07_adaptive_policy.py - Adaptive vs Static
CSV: e07_adaptive_policy.csv, 24 capacities
Scene 1e9 B, rate 10 Mbps, processing 30 s
Capacities 50 MB to 1.2 GB
Sample:
- 50 MB capacity: adaptive TFUP 30.02 s, best static TFUP 30.02 s, policy quicklook_roi
- 400 MB capacity: adaptive TFUP 270.0 s, best static TFUP 30.02 s, policy compressed_full
Policy switches from Progressive-like to CompressedFull at higher capacities.

## e08_uncertainty.py - Contact Capacity Uncertainty
CSV: e08_uncertainty.csv, 100 runs
Nominal capacity 375.0 MB, σ=10%
- GroundOnly TFUP: mean 297.5 s, std 31.9 s
- Progressive TFUP: mean 30.0 s, std 0.0 s
Progressive TFUP insensitive to capacity variation; GroundOnly varies with contact.

## e09_constellation_handoff.py - Constellation Coverage
CSV: e09_constellation.csv, 2881 rows (30 s steps over 24 h)
Compares queue backlog for a single satellite versus a 3-satellite constellation with phased contacts.
- Max single-satellite queue: 42.9 GB
- Max constellation queue: 38.3 GB (lower peak backlog from more frequent contact opportunities)
- 9 satellite handoffs recorded over the window

## e10_storage_wear.py - Flash Storage Wear
CSV: e10_storage_wear.csv, 720 rows (hourly over 30 days)
- 31 brownout events recorded (battery SOC dropped below threshold, processing paused)
- Final wear fraction after 30 days: 0.11% of rated endurance consumed
- Final storage health: 99.9%, flash wear is not a near-term concern at this duty cycle

## Files in results/frozen/v1/
Manifest with sizes and SHA256 generated in manifest.txt. Configs archived: baseline.yaml, orbits.yaml.

## Notes
- All CSV outputs from results/raw copied to frozen/v1 for reproducibility.
- experiments/e02_image_benchmark_run.py was renamed to experiments/e02_image_benchmark_tiles.py; it benchmarks the 30 real image tiles in data/imagery/tiles/, separate from e02_image_benchmark.py's single synthetic image benchmark.
