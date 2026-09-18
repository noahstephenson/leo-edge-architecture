#!/usr/bin/env bash
set -euo pipefail

echo "Running experiments..."
uv sync
for f in experiments/*.py; do
  echo "Running $f"
  uv run python "$f"
done

echo "Generating figures..."
for f in figures/scripts/*.py; do
  echo "Generating $f"
  uv run python "$f"
done

echo "Generating LaTeX tables..."
uv run python scripts/generate_latex_tables.py

echo "Building paper with latexmk..."
cd paper
latexmk -pdf ieee_template.tex
