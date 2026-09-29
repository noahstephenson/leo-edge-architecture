# Public release scope

This repository uses public or synthetic imagery, synthetic requests, and generic terminal locations. It contains no real Army tactical collection plan, classified workflow, or operational terminal location. All mission cases and performance thresholds are notional and unofficial.

The release includes the [structured conceptual model](../model/), [generated views](reference/VIEWS.md), [analysis code](../src/leo_edge/), [current evidence](../results/current/), and [manuscript draft](../paper/manuscript_draft.md). Scripts generate the figures and result files from recorded inputs. The study contributes a traceable architecture and examines delivery under intermittent contact using those tools.

To verify the model and selected evidence from a clean clone:

```bash
uv sync
uv run python scripts/validate_model.py
uv run python scripts/generate_model_views.py --check
uv run pytest
uv run python experiments/e13_mbse_evidence.py --check
```

The repository is licensed under [MIT](../LICENSE).
