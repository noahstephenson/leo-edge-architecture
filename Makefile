.PHONY: reproduce test experiments access_sweep figures trade_study

reproduce: test experiments figures trade_study
	@echo "Reproduce complete"

test:
	uv sync
	uv run pytest

experiments:
	uv sync
	@echo "Running experiments..."
	for f in experiments/*.py; do \
		case $$f in *e12_access_sweep.py) continue;; esac; \
		echo "Running $$f"; \
		uv run python $$f; \
	done

# Real per-satellite SGP4 for up to 24 satellites; takes about an hour.
access_sweep:
	uv sync
	uv run python experiments/e12_access_sweep.py

figures:
	uv sync
	@echo "Generating figures..."
	for f in figures/scripts/*.py; do \
		echo "Generating $$f"; \
		uv run python $$f; \
	done

trade_study:
	uv sync
	@echo "Running trade study..."
	uv run python scripts/trade_study.py
