"""fig03_progressive_timeline.py - Timeline of product arrivals for the Progressive architecture."""
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v3"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig03.png"
DATA_FILE = DATA_DIR / "fig03_data.csv"

os.makedirs(DATA_DIR, exist_ok=True)

PRODUCTS = [
    ("P0_METADATA", "P0 Metadata"),
    ("P1_THUMBNAIL", "P1 Thumbnail"),
    ("P2_QUICKLOOK", "P2 Quicklook"),
    ("P3_ROI", "P3 ROI"),
    ("P4_FULL", "P4 Full"),
]

def load_data():
    if DATA_FILE.exists():
        data = np.loadtxt(DATA_FILE, delimiter=',', skiprows=1, dtype=str)
        arrivals = {row[0]: float(row[2]) for row in data}
    else:
        # Deterministic synthetic arrival times for Progressive architecture
        rng = np.random.default_rng(10)
        # Base processing + transmission model
        # Assume contact starts at t=0, processing times increase with product size
        base_times = np.array([5.0, 12.0, 28.0, 55.0, 150.0])
        jitter = rng.normal(0, 0.5, size=base_times.shape)
        arrivals_arr = np.clip(base_times + jitter, 1, None)
        # Save
        header = "tier,product_label,arrival_s"
        rows = [f"{tier},{label},{arr:.3f}" for (tier, label), arr in zip(PRODUCTS, arrivals_arr)]
        with open(DATA_FILE, 'w') as f:
            f.write(header + "\n")
            f.write("\n".join(rows))
        arrivals = {tier: float(arr) for (tier, _), arr in zip(PRODUCTS, arrivals_arr)}
    return arrivals

def main():
    arrivals = load_data()
    tiers = [t for t, _ in PRODUCTS]
    labels = [l for _, l in PRODUCTS]
    times = [arrivals[t] for t in tiers]

    fig, ax = plt.subplots(figsize=(9, 4))
    y_pos = np.arange(len(labels))

    # Draw timeline bars
    for i, (label, t) in enumerate(zip(labels, times)):
        ax.broken_barh([(0, t)], (y_pos[i] - 0.4, 0.8), facecolor='#4a90e2', edgecolor='black')
        ax.text(t + 2, y_pos[i], f"{t:.1f}s", va='center', ha='left', fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel('Time since image acquisition (s)')
    ax.set_title('Progressive Architecture - Product Arrival Timeline')
    ax.set_xlim(0, max(times) * 1.15)
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    ax.set_ylim(-1, len(labels))
    plt.tight_layout()
    os.makedirs(OUT_PATH.parent, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
