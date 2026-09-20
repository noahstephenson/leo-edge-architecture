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

`uv run pytest`: 105 passed. `experiments/e11_mission_thread_success.py`
(~30s) and `experiments/e12_access_sweep.py` (~1h; 7 Walker configs up to
24 satellites/8 planes) run clean; outputs promoted to `results/frozen/v4/`
(e01-e10 and monte_carlo carried forward unchanged from v3 -- no v4 change
touches their code paths, though `orbit/access.py` was vectorized and is
covered by the existing access tests). `scripts/trade_study.py` and
`figures/scripts/fig19-21` regenerated from v4. Two e12 attempts were lost
before this one: one killed by host memory pressure (32-sat config; now
capped at 24 with incremental CSV writes), one discarded for a TLE column
bug (ADR-024). e12 is not in `make experiments` (use `make access_sweep`).
Older frozen results (`v2/`, `v3/`) were later deleted (git history has them). A follow-up docs pass also
ported e09 to a real Walker constellation (e09/e10 now write to `v4/`),
re-ran every figure script and the dashboard smoke test (HTTP 200), and
added `tests/test_docs_consistency.py`. `uv run pytest`: 105 passed.

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
