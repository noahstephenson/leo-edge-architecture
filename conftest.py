"""Makes experiments/ importable from tests/, the same way
experiments/e12_access_sweep.py already imports from e11_mission_thread_success
(sys.path.insert), so tests can exercise experiment functions directly
instead of duplicating their logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "experiments"))
