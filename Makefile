.PHONY: reproduce test model_check model_views selected_evidence rebuild_selected_evidence current_figure

reproduce: test selected_evidence current_figure
	@echo "Reproduce complete"

selected_evidence:
	uv run python experiments/e13_mbse_evidence.py --check

# Writes a separate local copy; the committed current evidence is not overwritten.
# Choose another --output path if results/reproduced/current already exists.
rebuild_selected_evidence:
	uv run python experiments/e13_mbse_evidence.py --output results/reproduced/current

current_figure: selected_evidence
	uv run python figures/scripts/fig_mt2_deadline.py
	uv run python figures/scripts/fig_mt2_deadline.py --check

model_check:
	uv run python scripts/validate_model.py
	uv run python scripts/generate_model_views.py --check
	uv run python scripts/check_reading_path.py

model_views:
	uv run python scripts/validate_model.py
	uv run python scripts/generate_model_views.py

test: model_check
	uv run pytest
