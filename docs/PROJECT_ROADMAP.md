# Project Roadmap

What's actually built, and how the pieces connect.

## The chain

Every piece of this repo traces the same path: operational need, architecture, requirements, model, experiment, figure, paper claim.

1. **Operational need**: `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` and `docs/CONOPS.md` describe who needs what and why.
2. **Architecture**: `docs/ARCHITECTURE.md` and `docs/ARCHITECTURE_VIEWS.md` describe the system in block diagrams, sequence diagrams, and a 4+1 view set.
3. **Requirements**: `docs/REQUIREMENTS.md` and `docs/INTERFACES.md` pin down what the system must do and how its pieces talk to each other.
4. **Model**: `src/leo_edge/` implements the architectures, product tiers, power, storage, link, and orbit models described above.
5. **Experiment**: `experiments/e00` through `e10` run that model under different conditions and write CSVs to `results/frozen/v1/`.
6. **Figure**: `figures/scripts/` turn those CSVs into the six figures in `figures/`.
7. **Paper claim**: `paper/manuscript.md` states the actual result, backed by the actual numbers in those CSVs.

## Status

The model, the test suite, all 12 experiments, and all 6 figures run clean from a fresh clone (`uv sync && uv run pytest && make experiments && make figures`). The paper states the real headline result: which architecture wins where, across downlink rate and contact duration, shown in `figures/fig04.png`.

## What's intentionally out of scope

Target recognition, tracking, weapon cueing, classified workflows, real Army tactical collection plans, and detailed orbital-warfare scenarios. This is a systems-architecture study using public/synthetic imagery and generic ground-terminal geometry. See `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` section 2.2 for the full list.
