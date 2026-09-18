"""Experiment 02: Image processing benchmark on synthetic image."""

import csv
from pathlib import Path

from leo_edge.imagery.benchmark import ImageBenchmark


def save_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    bench = ImageBenchmark()

    comp = bench.benchmark_compression(qualities=[95, 85, 75])
    quick = bench.benchmark_quicklook(scales=[0.25, 0.1])
    roi = bench.benchmark_roi(fractions=[0.05, 0.25, 0.5])

    print("Compression benchmark")
    for r in comp:
        print(r)
    print("\nQuicklook benchmark")
    for r in quick:
        print(r)
    print("\nROI benchmark")
    for r in roi:
        print(r)

    save_csv(Path("results/raw/e02_compression.csv"), comp, ["quality", "output_bytes", "runtime_ms", "compression_ratio"])
    save_csv(Path("results/raw/e02_quicklook.csv"), quick, ["scale", "output_bytes", "runtime_ms", "output_size"])
    save_csv(Path("results/raw/e02_roi.csv"), roi, ["fraction", "output_bytes", "runtime_ms", "crop_size"])

    print("\nSaved CSVs to results/raw/")


if __name__ == "__main__":
    main()
