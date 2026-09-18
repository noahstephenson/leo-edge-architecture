# Public Release

This repository is public source and unclassified. It uses only public/synthetic imagery, generic ground-terminal locations, and synthetic mission requests. It contains no real Army tactical collection plans, no classified data rates, and no real operational terminal locations.

## What's in the public release

- The full `src/leo_edge/` library.
- All experiment scripts (`experiments/`) and their frozen output (`results/frozen/v1/`).
- All figure-generation scripts and the figures themselves (`figures/`).
- The paper manuscript and hand-calculation validation (`paper/`).
- The architecture and operational documentation (`docs/`, `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md`).

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
