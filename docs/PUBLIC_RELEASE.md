# Public Release

This repository is public source and unclassified. It uses only public/synthetic imagery, generic ground-terminal locations, and synthetic mission requests. It contains no real Army tactical collection plans, no classified data rates, and no real operational terminal locations. Everything operational is notional and unofficial; nothing here represents an Army requirement, program, or acquisition decision.

## What's in the public release

- The full `src/leo_edge/` library.
- All experiment scripts (`experiments/`) and their frozen output (`results/frozen/v3/`).
- All figure-generation scripts and the figures themselves (`figures/`).
- The trade study script (`scripts/trade_study.py`) and its output.
- The hand-calculation validation (`docs/HAND_CALC_BREAK_EVEN.md`).
- The full architecture and operational documentation (`docs/`).

## Built on open source

The project relies on established open-source tools rather than writing orbital mechanics or benchmarking infrastructure from scratch:

- **Skyfield** for orbit propagation and ground-station access windows.
- **Pillow** for the real image-processing benchmark (compression, resize, crop).
- **pandas / matplotlib / numpy** for data handling and figures.

None of these libraries are themselves a claimed contribution of this project; they're the plumbing the actual research question (processing placement under intermittent contact) is built on top of.

## License

MIT. See `LICENSE`.

## Reproducing this release

```bash
uv sync
uv run pytest
make experiments
make figures
```

Everything regenerates from a clean clone. See `REPRODUCE_LOG.md` for the actual run log.
