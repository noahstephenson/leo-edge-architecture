# Synthetic imagery example

The optional [benchmark](../../experiments/image_benchmark.py) generates a 2048 by 2048 RGB modular gradient. There is no downloaded image or external image license dependency. Earlier image files and unsupported benchmark tables have been removed because their provenance could not be established.

Run `uv run --frozen python experiments/image_benchmark.py` from the repository root. The report is written under ignored `results/reproduced/` and records repetitions, encoded sizes, operation times, Python/Pillow versions, and machine information. Input generation and loading are outside the timing boundary. Quicklook timing includes resize and encoding; crop timing includes cropping and encoding.

Pixels are deterministic. Wall-clock timings depend on hardware and software, and the gradient is not representative Earth-observation imagery. These timings neither calibrate the selected study nor establish radiometric quality, declared geographic coverage, or user utility.
