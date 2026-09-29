# Current figure

The [deadline comparison](current/mt2_selected_deadline.png) shows one selected
synthetic scenario. The numerical source is
[`results/current/summary.csv`](../results/current/summary.csv); the figure's
[`manifest.json`](current/manifest.json) records source and output hashes.

Generate and check it from the repository root:

```powershell
uv run python figures/scripts/fig_mt2_deadline.py
uv run python figures/scripts/fig_mt2_deadline.py --check
```

The plot covers one case. The [model views](../docs/reference/VIEWS.md)
document the architecture and its traceability.
