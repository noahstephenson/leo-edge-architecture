.PHONY: reproduce test experiments figures trade_study paper

reproduce: test experiments figures trade_study
	@echo "Reproduce complete"

test:
	uv sync
	uv run pytest

experiments:
	uv sync
	@echo "Running experiments..."
	for f in experiments/*.py; do \
		echo "Running $$f"; \
		uv run python $$f; \
	done

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

paper: experiments figures
	uv sync
	@echo "Generating LaTeX tables..."
	uv run python scripts/generate_latex_tables.py
	@echo "Building paper with latexmk..."
	cd paper && latexmk -pdf ieee_template.tex
