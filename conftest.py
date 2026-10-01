"""Expose experiment evaluators to tests without duplicating their logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "experiments"))

# Independent clean-checkout verification may leave copied suites in scratch.
collect_ignore = ["results/reproduced"]
