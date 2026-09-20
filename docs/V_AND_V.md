# Verification and Validation

## Invariants the model enforces

| Area | Invariant | How it's enforced |
|---|---|---|
| Orbit | No contact below the elevation mask | `orbit/access.py` only records a window while elevation is above `min_elevation_deg` |
| Link | Zero downlink rate delivers zero bytes | `architectures.py`'s `_transmit_time_bytes()` returns infinite time at zero rate, so no bytes are scheduled |
| Storage | Storage occupancy can never go negative or over capacity | `storage.py`'s `MassMemory.store()` raises `ValueError` on overflow; `free()` clamps at zero |
| Power | Battery state of charge never goes negative or over capacity | `power.py`'s `PowerSystem.update()` clamps `soc` to `[0, capacity_wh]` and pauses processing on brownout |
| Metrics | `tfup_s`, `tcp_s`, `processing_energy_j`, `tx_energy_j` are never negative | `metrics.py` clamps each with `max(0.0, ...)` |
| Metrics | `contact_utilization` and `product_completeness` stay in `[0, 1]` | `architectures.py`'s `_finalize_metrics()` calls the single clamped `metrics.contact_utilization()` (`docs/DECISION_LOG.md` ADR-008; v1 had three divergent, mostly-unclamped implementations) |
| Delivery | Transmitted bytes never exceed contact capacity | Every architecture caps `bytes_transmitted` at assignment (ADR-008); regression-tested directly in `tests/test_architectures.py::test_never_exceeds_contact_capacity`, not just enforced structurally |
| Delivery | A product that doesn't finish is censored, never reported as complete | `completed=False`, `tfup_s`/`tcp_s = NaN` when a tier doesn't fully deliver; `tests/test_architectures.py::test_censored_when_capacity_too_small` and `test_tcp_never_equals_tfup_for_truncated_tiered_delivery` |

## Unit tests

`tests/` (105 tests) covers the metrics functions, the link/contact-capacity math, storage and power invariants, the queue, and the static and multi-contact architecture logic directly (`tests/test_architectures.py`, `tests/test_simulation.py`), not just existence/import smoke tests. Run them with `uv run pytest`.

## Orbit model cross-check

`scripts/validate_orbit_model.py` compares access windows generated from a synthetic circular-orbit TLE against windows generated from an explicit TLE with the same orbital elements, across a grid of altitudes, inclinations, and ground-station latitudes, and reports any mismatch in window count or total duration. It's a standalone script, not a pytest test (it writes a comparison CSV to `results/frozen/orbit_validation.csv` for inspection), so it isn't run automatically by `uv run pytest` or `make reproduce`; run it directly when changing `orbit/access.py`.

## Hand-calculation check

`docs/HAND_CALC_BREAK_EVEN.md` works a small example by hand (raw scene 1 GB, compressed to 0.3 GB, 20 s processing time) and compares the analytical break-even downlink rate against the simulated crossover point from `e03_static_architectures.py`'s output. The two agree in direction; the gap in magnitude is explained by contact-window limits and the fact that below the break-even rate, the simulation shows raw downlink not merely losing but frequently failing to complete at all within one window. That reconciliation is the real validation step, not just running the formula once.

## Benchmark reproducibility

The image-processing numbers in `results/frozen/v4/e02_*.csv` and `results/frozen/image_benchmark*.csv` come from actually running Pillow's JPEG encoder, resize, and crop operations, timed with `time.perf_counter_ns()`, not from an assumed compression ratio. Anyone can rerun `experiments/e02_image_benchmark.py` and get comparable numbers on their own machine; absolute runtimes will differ by hardware, but the relative shape (compression cheaper than quicklook resize, ROI crop cheapest) should hold.

## What "measured" vs. "assumed" means here

`docs/ASSUMPTIONS.md` lists every numeric assumption in the model along with whether it's measured, computed from a real physical model, or a design assumption. The regime map in `figures/fig04.png` should be read with that distinction in mind: the crossover points are real outputs of the model, but the model's power and compression-ratio inputs are reasonable assumptions for a COTS smallsat, not measurements from a flown spacecraft.
