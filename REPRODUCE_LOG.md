# Reproduce Log

## How to reproduce

```bash
uv sync
uv run pytest
make experiments
make figures
make trade_study
```

`make reproduce` runs `test`, `experiments` (which now includes
`e11_mission_thread_success.py`), `figures`, and `trade_study` in order.
See `README.md`'s Quick Start.

## Last full run: 2026-09-18 (post-rework)

### Test suite

```bash
uv sync
uv run pytest
```

Result: **SUCCESS**, 74 passed (up from 36 pre-rework: 38 new tests added
for architecture correctness, multi-contact delivery, and mission-thread
logic).

### Experiments

```bash
for f in experiments/*.py; do uv run python $f; done
```

Result: **SUCCESS**, all 13 scripts ran clean:

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
- experiments/e11_mission_thread_success.py (new this pass)

Outputs written to `results/raw/` and promoted into `results/frozen/v2/`
(`results/frozen/v1/` is untouched, kept as the historical pre-fix record;
see `docs/V1_VS_V2.md`). `e09`/`e10` write directly to
`results/frozen/v2/`, same structural quirk as v1
(`results/frozen/v1/experiments_summary.md`'s note, unchanged by this
pass).

### Trade study

```bash
uv run python scripts/trade_study.py
```

Result: **SUCCESS**. Writes `results/frozen/v2/trade_study_scores.csv` and
`results/frozen/v2/trade_study_sensitivity.csv`. See `docs/TRADE_STUDY.md`
for the results.

### Figures

```bash
for f in figures/scripts/*.py; do uv run python $f; done
```

Result: **SUCCESS**, all 7 scripts ran clean:

- figures/scripts/fig01_system_architecture.py
- figures/scripts/fig02_sensitivity_tornado.py
- figures/scripts/fig03_progressive_timeline.py
- figures/scripts/fig04_regime_heatmap.py (now shows "no completion" cells honestly, docs/DECISION_LOG.md ADR-008)
- figures/scripts/fig05_pareto_frontier.py (drops censored rows explicitly, printed at generation time)
- figures/scripts/fig06_contact_distribution.py
- figures/scripts/fig_infographic_pdf.py

`fig15_constellation_coverage.png` and `fig16_storage_health.png` are
generated inline by `e09_constellation_handoff.py` and
`e10_storage_wear.py`, part of the experiments step above, not the figures
step.

### Dashboard

```bash
uv run streamlit run app/dashboard.py
```

Result: **SUCCESS**. `streamlit` was missing from `pyproject.toml`'s
dependencies (a pre-existing gap, not introduced by this pass) and has
been added. Smoke-tested headless (`--server.headless true`), served
HTTP 200 with no traceback in the server log. New this pass: sidebar
controls for terminal class, contested condition, and mission thread
(`docs/MISSION_THREADS.md`), and a single-contact-window mission-thread
pass/fail table per architecture.

### Full reproduce

`make` itself isn't installed on the machine this log was run on; each
`make reproduce` step's underlying commands (shown above) were run
directly instead and all **SUCCEEDED**. The `Makefile` targets were
reviewed to confirm they invoke the same commands, but `make reproduce`
as a single invocation was not itself executed in this environment.

## Notes

`experiments/e02_image_benchmark_tiles.py` downloads sample imagery over
the network and falls back to a deterministic synthetic tile if the
download fails or times out, so its exact runtime and byte counts can vary
slightly between runs and machines. Running it also re-downloads and
overwrites `data/imagery/tiles/*.jpg` and
`results/frozen/image_benchmark*.csv` in place (confirmed this session:
running it changed `tile_001.jpg` from 910,705 to 630,392 bytes). Those
files were reverted to their committed versions after this run rather than
committing a network-dependent regeneration; this is a pre-existing
reproducibility wart in that script (it mutates its own checked-in input
data as a side effect), not something fixed in this pass.
`experiments/e11_mission_thread_success.py` is a Monte Carlo experiment
seeded at 0, deterministic given the checked-in code; every other
experiment and figure is fully deterministic.
