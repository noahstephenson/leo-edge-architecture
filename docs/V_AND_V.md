# Verification and Validation

## Invariants the model enforces

| Area | Invariant | How it's enforced |
|---|---|---|
| Orbit | No contact below the elevation mask | `orbit/access.py` only records a window while elevation is above `min_elevation_deg` |
| Link | Zero downlink rate delivers zero bytes | `architectures.py`'s `_transmit_time_bytes()` returns infinite time at zero rate, so no bytes are scheduled |
| Storage | Storage occupancy can never go negative or over capacity | `storage.py`'s `MassMemory.store()` raises `ValueError` on overflow; `free()` clamps at zero |
| Power | Battery state of charge never goes negative or over capacity | `power.py`'s `PowerSystem.update()` clamps `soc` to `[0, capacity_wh]` and pauses processing on brownout |
| Metrics | `tfup_s`, `tcp_s`, `processing_energy_j`, `tx_energy_j` are never negative | `metrics.py` clamps each with `max(0.0, ...)` |
| Metrics | `contact_utilization` and `product_completeness` stay in `[0, 1]` | `metrics.py` clamps both with `min(1.0, ...)` |
| Queue | Transmitted bytes never exceed contact capacity | `scheduler.py`'s `ProductScheduler.simulate_step()` only transmits when `size_bytes <= contact_capacity_bytes` |

## Unit tests

`tests/` covers the metrics functions, the link/contact-capacity math, storage and power invariants, the scheduler, the queue, and the static architecture classes. Run them with `uv run pytest`.

## Hand-calculation check

`paper/hand_calc_break_even.md` works a small example by hand (raw scene 1 GB, compressed to 0.3 GB, 20 s processing time) and compares the analytical break-even downlink rate against the simulated crossover point from `e03_static_architectures.py`'s output. The two agree in direction; the gap in magnitude is explained by contact-window and queueing effects the closed-form formula doesn't capture. That reconciliation is the real validation step, not just running the formula once.

## Benchmark reproducibility

The image-processing numbers in `results/frozen/v1/e02_*.csv` come from actually running Pillow's JPEG encoder, resize, and crop operations, timed with `time.perf_counter_ns()`, not from an assumed compression ratio. Anyone can rerun `experiments/e02_image_benchmark.py` and get comparable numbers on their own machine; absolute runtimes will differ by hardware, but the relative shape (compression cheaper than quicklook resize, ROI crop cheapest) should hold.

## What "measured" vs. "assumed" means here

`docs/ASSUMPTIONS.md` lists every numeric assumption in the model along with whether it's measured, computed from a real physical model, or a design assumption. The regime map in `figures/fig04.png` should be read with that distinction in mind: the crossover points are real outputs of the model, but the model's power and compression-ratio inputs are reasonable assumptions for a COTS smallsat, not measurements from a flown spacecraft.
