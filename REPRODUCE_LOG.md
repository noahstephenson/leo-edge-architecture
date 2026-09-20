# Reproduce Log

## How to reproduce

```bash
uv sync
uv run pytest
make experiments
make figures
make trade_study
uv run python experiments/e12_access_sweep.py
```

`make reproduce` runs the first four. The access sweep
(`experiments/e12_access_sweep.py`) isn't in the default `make
experiments` loop yet since it's slower than a single experiment
(~5 minutes; see the note below). See `README.md`'s Quick Start.

## Last full run: 2026-09-20 (v4: real constellations + same-pass delivery)

`uv run pytest`: 102 passed. `experiments/e11_mission_thread_success.py`
(~30s) and `experiments/e12_access_sweep.py` (~1h; 7 Walker configs up to
24 satellites/8 planes) run clean; outputs promoted to `results/frozen/v4/`
(e01-e10 and monte_carlo carried forward unchanged from v3 -- no v4 change
touches their code paths, though `orbit/access.py` was vectorized and is
covered by the existing access tests). `scripts/trade_study.py` and
`figures/scripts/fig19-21` regenerated from v4. Two e12 attempts were lost
before this one: one killed by host memory pressure (32-sat config; now
capped at 24 with incremental CSV writes), one discarded for a TLE column
bug (ADR-024). e12 is not in `make experiments`. `results/frozen/v3/` is
untouched. The dashboard and the other figure scripts were not re-run this
pass.

## Previous run: 2026-09-19 (v3: evaluation-engine fixes + access sweep)

This run followed the v3 rework (`docs/REWORK_PLAN_V3.md`,
`docs/DECISION_LOG.md` ADR-015 through ADR-018): paired trials, a real
collection-timing model, MT-3 restored and MT-4 fixed to be genuinely
cadence-based, structural incapacity tracked separately from slowness,
censoring-aware latency, a fixed (previously inverted) terminal-SWaP
criterion, architecture-derived trade-study criteria replacing hand-picked
numbers, and the new access/revisit sweep.

### Test suite

```bash
uv sync
uv run pytest
```

Result: **SUCCESS**, 96 passed (up from 81 pre-v3: 15 new tests for the
stats helpers, mission-thread consistency, A6 provenance/conditional-logic
flags).

### Experiments

```bash
for f in experiments/e00_sanity.py experiments/e01_orbit_contacts.py \
  experiments/e02_image_benchmark.py experiments/e03_static_architectures.py \
  experiments/e04_contact_sweep.py experiments/e05_power_sweep.py \
  experiments/e06_queue_stress.py experiments/e07_adaptive_policy.py \
  experiments/e08_uncertainty.py experiments/e09_constellation_handoff.py \
  experiments/e10_storage_wear.py; do uv run python $f; done
uv run python experiments/e11_mission_thread_success.py
uv run python experiments/e12_access_sweep.py
```

Result: **SUCCESS**, all 13 scripts ran clean. `e11` (~30s) reproduced
byte-identical significance results on a second run (same 7-vs-7 A6/
Progressive tie, same 12 significant pairs). `e12` (~4-5 minutes) was
re-run once for this log and separately interrupted mid-run by the host
environment's own memory-pressure management on a repeat verification
attempt (not a code issue; the original completed run's output was
already committed and verified before that interruption).

`experiments/e02_image_benchmark_tiles.py` was not re-run this session
(network-dependent, and its fix was already verified in the prior
session); its checked-in outputs are unchanged.

Outputs written to `results/raw/` and promoted into `results/frozen/v3/`.
`results/frozen/v2/` is left in place as the historical record
(`docs/V2_VS_V3.md`); `e01`, `e02_*` (synthetic), `e04`-`e10`, and
`monte_carlo.csv` were carried forward from v2 into v3 unchanged, since
none of the v3 fixes touch the code paths that produce them (confirmed by
inspection, not re-run, since re-running them would produce
bit-identical output given unchanged code and fixed seeds). `e09`/`e10`
still write directly to `results/frozen/v3/`, a structural quirk noted but
not fixed in this pass (unchanged from v2).

### Trade study

```bash
uv run python scripts/trade_study.py
```

Result: **SUCCESS**. Writes `results/frozen/v3/trade_study_scores.csv`
and `results/frozen/v3/trade_study_sensitivity.csv`. See
`docs/TRADE_STUDY.md` for the results, including the SIMULATED_ONLY vs.
COMBINED disagreement in every stakeholder profile.

### Figures

```bash
for f in figures/scripts/*.py; do uv run python $f; done
```

Result: **SUCCESS**, all 10 scripts ran clean (fig01-fig06,
fig19-fig21, fig_infographic_pdf). `fig19`-`fig21` are new this pass
(the access sweep visualizations). All figures were also opened and
visually reviewed, not just checked for a clean exit code.

`fig15_constellation_coverage.png` and `fig16_storage_health.png` are
generated inline by `e09_constellation_handoff.py` and
`e10_storage_wear.py`, part of the experiments step above, not the
figures step.

### Dashboard

```bash
uv run streamlit run app/dashboard.py
```

Result: **SUCCESS**. Smoke-tested headless (`--server.headless true`),
served HTTP 200 with no traceback in the server log, after the
`src/leo_edge/mission_threads.py` import refactor.

### Full reproduce

`make` itself isn't installed on the machine this log was run on; each
`make reproduce` step's underlying commands (shown above) were run
directly instead and all **SUCCEEDED**. `make reproduce` as a single
invocation was not itself executed in this environment; `make
trade_study` and the `e12` step still aren't part of `make experiments`'s
default loop (documented above), so `make reproduce` alone does not yet
regenerate the full v3 dataset even where `make` is available.

## Notes

`experiments/e11_mission_thread_success.py` and
`experiments/e12_access_sweep.py` are Monte Carlo experiments seeded at
0, deterministic given the checked-in code; every other experiment and
figure is fully deterministic except `e02_image_benchmark_tiles.py`
(network-dependent, falls back to a deterministic synthetic tile).

`e12_access_sweep.py` takes noticeably longer than the other experiments
(~4-5 minutes) because it evaluates 18 access levels x 7 architectures x
4 mission threads x 2 terminal classes x 2 conditions; this is by design
(`docs/DECISION_LOG.md` ADR-018 documents the tractability tradeoffs
already made to keep it in this range rather than e11's full 5-condition
sweep at every access level).
