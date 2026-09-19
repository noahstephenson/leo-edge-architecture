"""fig20_access_heatmap.py - Best statistically-distinguishable architecture
over (satellites x terminals), from experiments/e12_access_sweep.py's
pairwise-significance output. Cells with no architecture that beats every
other by a significant margin are labeled "no significant difference"
rather than an arbitrary pick.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

DATA_PATH = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v3" / "e12_best_architecture_by_access.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig20.png"

NO_SIG_LABEL = "NO_SIGNIFICANT_DIFFERENCE"


def main():
    df = pd.read_csv(DATA_PATH)
    pivot = df.pivot(index="terminals", columns="satellites", values="best_architecture")

    labels = sorted(set(pivot.values.ravel()))
    codes = {label: i for i, label in enumerate(labels)}
    code_matrix = pivot.map(lambda label: codes[label]).astype(int)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    cmap = plt.get_cmap("tab10")
    im = ax.imshow(code_matrix.values, aspect="auto", cmap=cmap, vmin=0, vmax=max(len(labels) - 1, 1), origin="lower")

    for i in range(code_matrix.shape[0]):
        for j in range(code_matrix.shape[1]):
            label = pivot.iloc[i, j]
            text = "no sig.\ndiff." if label == NO_SIG_LABEL else label.replace("ThreadAwarePriority", "A6\n(proposed)")
            ax.text(j, i, text, ha="center", va="center", fontsize=8)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Satellites")
    ax.set_ylabel("Army ground terminals")
    ax.set_title(
        "Best statistically-distinguishable architecture by access level\n"
        "(paired bootstrap, 95% CI; A6 is a proposed post-v2 design, not part of the original candidate set)"
    )
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
