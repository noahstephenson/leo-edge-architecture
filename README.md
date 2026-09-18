# LEO Edge Architecture

A reproducible systems-architecture study: under intermittent LEO contact and spacecraft power/size/weight constraints, when should a small satellite process imagery onboard instead of sending it raw for a ground terminal to process?

![OV-1: Army COTS LEO direct-to-edge imagery concept](docs/figures/ov1_concept.png)

## The system

A small COTS-heavy satellite in low Earth orbit images an area, optionally processes the result onboard, and downlinks directly to a local ground terminal during the next contact window, no centralized ground station required. The question this project answers is what to do on the satellite before that downlink: send the raw scene and let the ground terminal do all the work, or spend onboard compute time shrinking the product first.

See `docs/ARCHITECTURE.md` for the block diagram and state machine, `docs/ARCHITECTURE_VIEWS.md` for the full 4+1 view set, and `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` for the operational concept the OV-1 graphic above comes from.

## Six architectures, one regime map

We compare six delivery architectures (raw, compressed, quicklook-first, ROI-first, progressive, and a contact-aware adaptive policy) across a grid of downlink rates and contact durations, using processing and compression numbers measured from real image benchmarks rather than assumed constants.

![Best architecture by rate and contact duration](figures/fig04.png)

Quicklook-first delivery wins across most of the grid. Compressed full-scene delivery only wins once the link is fast enough that transmission is cheap and onboard processing delay stops paying for itself. The fully staged progressive architecture wins only at the lowest rate and longest contact durations, where even a small early product beats waiting for anything bigger. The full result, with real numbers, is in `paper/manuscript.md`.

## Quick start

```bash
uv sync
uv run pytest
make experiments
make figures
```

Every experiment writes its output to `results/`, and every figure regenerates from that output. See `REPRODUCE_LOG.md` for a real run log and `Makefile` for the individual targets.

## Repository map

| Path | What's there |
|---|---|
| `src/leo_edge/` | The architecture, orbit, imagery, and metrics model |
| `experiments/` | Twelve scripts, `e00` through `e10`, each answering one question about the model |
| `results/frozen/v1/` | Frozen CSV output from those experiments |
| `figures/` | Six figures generated from that output, see `figures/README.md` |
| `docs/` | Requirements, assumptions, decisions, architecture views, validation |
| `paper/` | The manuscript and a hand-calculation check of the core timing model |
| `app/dashboard.py` | A Streamlit dashboard for exploring the architectures interactively |

## License

Public source, unclassified, MIT licensed. See `LICENSE`.
