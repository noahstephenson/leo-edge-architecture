# Reproduce Log

## How to reproduce

```bash
uv sync
uv run pytest
make experiments
make figures
```

Or all at once with `make reproduce`, which runs `test`, `experiments`, and `figures` in order.

## Last full run: 2026-09-18

### Test suite

```bash
uv sync
uv run pytest
```

Result: **SUCCESS**, 36 passed.

### Experiments

```bash
for f in experiments/*.py; do uv run python $f; done
```

Result: **SUCCESS**, all 12 scripts ran clean:

- experiments/e00_sanity.py
- experiments/e01_orbit_contacts.py
- experiments/e02_image_benchmark.py
- experiments/e02_image_benchmark_tiles.py
- experiments/e03_static_architectures.py
- experiments/e04_contact_sweep.py
- experiments/e05_power_sweep.py
- experiments/e06_queue_stress.py
- experiments/e07_adaptive_policy.py
- experiments/e08_uncertainty.py
- experiments/e09_constellation_handoff.py
- experiments/e10_storage_wear.py

Outputs written to `results/raw/` and `results/frozen/`. See `results/frozen/v1/experiments_summary.md` for what each one produced.

### Figures

```bash
for f in figures/scripts/*.py; do uv run python $f; done
```

Result: **SUCCESS**, all 7 scripts ran clean:

- figures/scripts/fig01_system_architecture.py
- figures/scripts/fig02_sensitivity_tornado.py
- figures/scripts/fig03_progressive_timeline.py
- figures/scripts/fig04_regime_heatmap.py
- figures/scripts/fig05_pareto_frontier.py
- figures/scripts/fig06_contact_distribution.py
- figures/scripts/fig_infographic_pdf.py

`fig15_constellation_coverage.png` and `fig16_storage_health.png` are generated inline by `e09_constellation_handoff.py` and `e10_storage_wear.py` respectively, as part of the experiments step above, not the figures step. See `figures/README.md` for the full figure list and data sources.

### Full reproduce

`make reproduce` (test + experiments + figures in sequence): **SUCCESS**.

## Notes

`experiments/e02_image_benchmark_tiles.py` downloads sample imagery over the network and falls back to a deterministic synthetic tile if the download fails or times out, so its exact runtime and byte counts can vary slightly between runs and machines; every other experiment and figure is fully deterministic given the checked-in code and configuration.
