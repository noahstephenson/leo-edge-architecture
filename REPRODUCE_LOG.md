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

## Last full run: 2026-09-18 (post-rework, post-cleanup, post-A6)

This run followed, in order: a cleanup pass that deleted `results/frozen/v1/`,
`paper/`, and `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` (`docs/DECISION_LOG.md`
ADR-011) and removed genuinely dead code (`src/leo_edge/mission.py`, ADR-012);
a fix for `e02_image_benchmark_tiles.py` mutating its own checked-in input
data (ADR-013); and the addition of A6 (`ThreadAwarePriority`, ADR-014), a
mission-thread-aware prioritization architecture that closes
`docs/ALLOCATION_SPACE.md`'s biggest originally-uncovered gap.

Two real bugs were caught during this run, both before being left
uncaught in a commit:

1. The cleanup pass's file deletion caught a bug this log's earlier
   version had missed: `figures/scripts/fig02_sensitivity_tornado.py`,
   `fig03_progressive_timeline.py`, and `fig06_contact_distribution.py`
   still pointed at the now-deleted `results/frozen/v1/`, which would have
   made `make figures` fail on a truly clean clone.
2. Wiring A6 into `experiments/e11_mission_thread_success.py` caught a
   naming bug in the same change (never committed): the refactor
   initially wrote the A-prefixed factory key (e.g. `"A0_GROUND_ONLY"`)
   into the CSV `architecture` column instead of the class name
   (`"GroundOnly"`) that `e03_results.csv` and `scripts/trade_study.py`
   expect, which would have silently zeroed out the `mission_thread_success`
   and `resilience` criteria for every architecture in every future trade-
   study run. Fixed before committing; see ADR-014 for the full story,
   including a related pre-existing gap it surfaced: `ContactAware` (A5)
   had never been included in `e03_static_architectures.py`'s sweep, so its
   "latency" criterion in every trade-study run up to this one was a silent
   fallback value, not a measurement. Both `ContactAware` and `ThreadAwarePriority`
   are now in that sweep.

Fixed and re-verified end to end below.

### Test suite

```bash
uv sync
uv run pytest
```

Result: **SUCCESS**, 81 passed (up from 36 pre-rework: 45 new tests added
for architecture correctness, multi-contact delivery, mission-thread
logic, and A6's reordering behavior).

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

Outputs written to `results/raw/` and promoted into `results/frozen/v2/`.
The original v1 results have been deleted from the working tree
(`docs/DECISION_LOG.md` ADR-011); `docs/V1_VS_V2.md` documents what they
showed and what changed. `e09`/`e10` write directly to
`results/frozen/v2/`, a structural quirk noted but not fixed in this pass
(`docs/DECISION_LOG.md` ADR-008's scope).

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

`experiments/e02_image_benchmark_tiles.py` previously re-downloaded and
overwrote `data/imagery/tiles/*.jpg` on every run regardless of whether a
tile already existed, silently mutating checked-in input data (confirmed
in an earlier session: running it changed `tile_001.jpg` from 910,705 to
630,392 bytes). Fixed this pass: `download_tile()` now reuses an existing
tile file instead of re-fetching it. Verified by hashing `tile_001.jpg`
before and after a run (`b2d8cbc4...` both times) and diffing the output
CSVs: `compressed_bytes`/`quicklook_bytes`/`roi_bytes`/`psnr`/`ssim` are
now byte-for-byte identical across runs, only the timing columns
(`comp_time_s`, `ql_time_s`, `roi_time_s`) vary, which is expected since
those are real wall-clock measurements. The script still falls back to a
deterministic synthetic tile on first run if a tile doesn't exist yet and
the network download fails or times out.
`experiments/e11_mission_thread_success.py` is a Monte Carlo experiment
seeded at 0, deterministic given the checked-in code; every other
experiment and figure is fully deterministic.
