"""fig05_pareto_frontier.py - Pareto frontier of processing energy vs TFUP, from real e03 sweep data."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v4" / "e03_results.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig05.png"

ARCH_MAP = {
    "GroundOnly": "A0_GROUND_ONLY",
    "CompressedFull": "A1_COMPRESSED_FULL",
    "QuicklookFirst": "A2_QUICKLOOK_FIRST",
    "RoiFirst": "A3_ROI_FIRST",
    "Progressive": "A4_PROGRESSIVE",
    "ContactAware": "A5_CONTACT_AWARE",
    "ThreadAwarePriority": "A6_THREAD_AWARE_PRIORITY",
}


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["architecture_id"] = df["architecture_name"].map(ARCH_MAP).fillna(df["architecture_name"])
    # Only completed deliveries have a real TFUP; a censored (NaN) point
    # can't be meaningfully placed on a Pareto frontier.
    n_before = len(df)
    df = df[df["completed"].astype(bool)].reset_index(drop=True)
    dropped = n_before - len(df)
    if dropped:
        print(f"fig05: dropped {dropped} uncompleted (censored) rows out of {n_before}")
    return df


def pareto_frontier(energy, tfup):
    # A point is Pareto-optimal if no other point is at least as good on both
    # axes and strictly better on one (minimizing both energy and TFUP).
    points = np.column_stack([energy, tfup])
    is_pareto = np.ones(len(points), dtype=bool)
    for i in range(len(points)):
        if is_pareto[i]:
            dominates = np.all(points <= points[i], axis=1) & np.any(points < points[i], axis=1)
            is_pareto[dominates] = False
    return is_pareto


def main():
    df = load_data()
    arch_ids = sorted(df["architecture_id"].unique())
    energy = df["processing_energy_j"].values
    tfup = df["tfup_s"].values

    fig, ax = plt.subplots(figsize=(8, 5))
    for arch in arch_ids:
        mask = df["architecture_id"] == arch
        ax.scatter(tfup[mask], energy[mask], label=arch, alpha=0.7, s=60)

    is_pareto = pareto_frontier(energy, tfup)
    ax.scatter(tfup[is_pareto], energy[is_pareto], facecolors='none', edgecolors='k',
               s=120, linewidths=1.5, label='Pareto optimal')

    ax.set_xlabel('TFUP (s)')
    ax.set_ylabel('Processing energy (J)')
    ax.set_title('Processing energy vs TFUP across the rate sweep')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
