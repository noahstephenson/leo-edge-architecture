# Architecture evidence figures

The [principal comparison](current/mt2_selected_deadline.png) uses one requesting dismounted terminal under nominal conditions. Its three panels retain sparse and larger constellations. The [all-miss counterexample](current/mt2_counterexample.png) uses a nominal vehicle link and four pooled sites with zero forwarding delay. The [sensitivity figure](current/mt2_sensitivity.png) shows the separate one-terminal corridor sample. Cases were selected to illustrate preparation differences and a shared timing limit, not to select a universal winner.

The [summary](../results/current/summary.csv) and [sensitivity summary](../results/current/sensitivity_summary.csv) supply the numerical values. The [manifest](current/manifest.json) records source and output hashes. Generate with `uv run --frozen python figures/scripts/fig_mt2_deadline.py`, then verify with the same command plus `--check`. Use `--evidence` and `--output` for scratch regeneration. The [independent verification command](../scripts/verify_reproduction.py) regenerates both evidence and figures before comparing them.

Points show sampled deadline fractions with 95% Wilson intervals. The sensitivity matrix is a compact result display, not a reliability estimate. The [model views](../docs/reference/VIEWS.md) explain the architecture.
