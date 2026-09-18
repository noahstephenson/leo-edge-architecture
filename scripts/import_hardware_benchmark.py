"""Import measured COTS hardware benchmark CSV and update benchmark config.

Reads measured timings for compression/quicklook/ROI, updates
src/leo_edge/imagery/benchmark.py MEASURED_CONFIG, and generates
figures/fig17_measured_vs_modeled.png comparing measured vs modeled times.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import pathlib
import re
from typing import Dict

import matplotlib.pyplot as plt


BENCHMARK_PY = pathlib.Path("src/leo_edge/imagery/benchmark.py")
FIGURES_DIR = pathlib.Path("figures")
OUTPUT_FIG = FIGURES_DIR / "fig17_measured_vs_modeled.png"

# Modeled times per MB from processing.py
MODELED_PER_MB = {
    "compression": 0.8,
    "quicklook": 0.5,
    "roi": 1.2,
}


def read_csv(path: pathlib.Path):
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return reader.fieldnames, rows


def compute_stats(fieldnames, rows):
    # Detect format
    has_raw = "raw_bytes" in fieldnames
    has_comp = "comp_time_s" in fieldnames
    has_ql = "ql_time_s" in fieldnames
    has_roi = "roi_time_s" in fieldnames

    # Standard format from image_benchmark.csv
    if has_raw and has_comp and has_ql and has_roi:
        comp_times = []
        ql_times = []
        roi_times = []
        sizes_mb = []
        for r in rows:
            try:
                raw = float(r["raw_bytes"])
                size_mb = raw / (1024 * 1024)
                sizes_mb.append(size_mb)
                comp_times.append(float(r["comp_time_s"]))
                ql_times.append(float(r["ql_time_s"]))
                roi_times.append(float(r["roi_time_s"]))
            except Exception:
                continue
        # seconds per MB
        comp_spm = [t / s for t, s in zip(comp_times, sizes_mb)]
        ql_spm = [t / s for t, s in zip(ql_times, sizes_mb)]
        roi_spm = [t / s for t, s in zip(roi_times, sizes_mb)]

        avg_comp = sum(comp_spm) / len(comp_spm) if comp_spm else None
        avg_ql = sum(ql_spm) / len(ql_spm) if ql_spm else None
        avg_roi = sum(roi_spm) / len(roi_spm) if roi_spm else None

        # For plotting measured vs modeled per tile
        modeled_comp = [s * MODELED_PER_MB["compression"] for s in sizes_mb]
        modeled_ql = [s * MODELED_PER_MB["quicklook"] for s in sizes_mb]
        modeled_roi = [s * MODELED_PER_MB["roi"] for s in sizes_mb]

        return {
            "avg_s_per_mb": {
                "compression": avg_comp,
                "quicklook": avg_ql,
                "roi": avg_roi,
            },
            "plot_data": {
                "sizes_mb": sizes_mb,
                "measured": {
                    "compression": comp_times,
                    "quicklook": ql_times,
                    "roi": roi_times,
                },
                "modeled": {
                    "compression": modeled_comp,
                    "quicklook": modeled_ql,
                    "roi": modeled_roi,
                },
            },
        }

    raise ValueError("Unsupported CSV format. Expected raw_bytes, comp_time_s, ql_time_s, roi_time_s.")


def update_benchmark_py(config: Dict):
    text = BENCHMARK_PY.read_text(encoding="utf-8")
    updated_at = datetime.datetime.utcnow().isoformat() + "Z"
    # Normalize path separators for Python string literal
    source_csv = config["source_csv"].replace("\\", "/")
    new_block = (
        "MEASURED_CONFIG = {\n"
        f'    "compression_s_per_mb": {config["avg_s_per_mb"]["compression"]},\n'
        f'    "quicklook_s_per_mb": {config["avg_s_per_mb"]["quicklook"]},\n'
        f'    "roi_s_per_mb": {config["avg_s_per_mb"]["roi"]},\n'
        f'    "source_csv": "{source_csv}",\n'
        f'    "updated_at": "{updated_at}",\n'
        "}"
    )
    # Replace the MEASURED_CONFIG block line by line
    lines = text.splitlines(keepends=True)
    out_lines = []
    in_block = False
    brace_count = 0
    for line in lines:
        if "MEASURED_CONFIG = {" in line:
            out_lines.append(new_block + "\n")
            in_block = True
            brace_count = 0
            # skip lines until closing brace of block
            continue
        if in_block:
            # skip until we have passed the original block
            # simple heuristic: skip lines that are part of dict
            if "}" in line:
                in_block = False
            continue
        out_lines.append(line)
    BENCHMARK_PY.write_text("".join(out_lines), encoding="utf-8")


def plot_comparison(data):
    sizes = data["sizes_mb"]
    measured = data["measured"]
    modeled = data["modeled"]

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    ops = ["compression", "quicklook", "roi"]
    titles = ["Compression", "Quicklook", "ROI"]

    for ax, op, title in zip(axes, ops, titles):
        m = measured[op]
        mod = modeled[op]
        ax.scatter(mod, m, alpha=0.7, s=40)
        # identity line
        lims = [
            min(min(m), min(mod)),
            max(max(m), max(mod)),
        ]
        ax.plot(lims, lims, "r--", linewidth=1, label="1:1")
        ax.set_xlabel("Modeled time (s)")
        ax.set_ylabel("Measured time (s)" if ax is axes[0] else "")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Measured vs Modeled Processing Times (COTS hardware)")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(OUTPUT_FIG, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Import hardware benchmark CSV")
    parser.add_argument(
        "--csv",
        type=str,
        default="results/frozen/image_benchmark.csv",
        help="Path to measured benchmark CSV",
    )
    args = parser.parse_args()

    csv_path = pathlib.Path(args.csv).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    fieldnames, rows = read_csv(csv_path)
    stats = compute_stats(fieldnames, rows)

    config = {
        "avg_s_per_mb": stats["avg_s_per_mb"],
        "source_csv": str(csv_path),
    }
    update_benchmark_py(config)
    plot_comparison(stats["plot_data"])

    print(f"Updated {BENCHMARK_PY}")
    print(f"Avg s/MB: compression={stats['avg_s_per_mb']['compression']:.4f}, "
          f"quicklook={stats['avg_s_per_mb']['quicklook']:.4f}, "
          f"roi={stats['avg_s_per_mb']['roi']:.4f}")
    print(f"Figure saved to {OUTPUT_FIG}")


if __name__ == "__main__":
    main()
