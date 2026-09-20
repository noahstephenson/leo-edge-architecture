"""fig20_access_heatmap.py - Best statistically-distinguishable architecture
over (satellites x terminals), from experiments/e12_access_sweep.py's
pairwise-significance output (results/frozen/v4/e12_cell_status.csv).

v4 fix (docs/DECISION_LOG.md ADR-022): v3 labeled every cell that failed to
separate architectures "no significant difference," collapsing two very
different situations into one label -- a cell where nothing worked (a
floor effect, testing is uninformative) and a cell where architectures
were genuinely tested and tied. This version greys out UNINFORMATIVE cells
(best architecture's success <= 30%) distinctly from TIES (informative,
tested, no significant difference) and SEPARATES (a real winner).
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

DATA_PATH = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v4" / "e12_cell_status.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig20.png"


def main():
    df = pd.read_csv(DATA_PATH)
    # Keep only the highest-plane-count row per satellite count (main
    # multi-plane Walker sweep; see fig19 same filter
    # for the single-plane comparison points this drops from the heatmap).
    df = df.sort_values("planes").groupby(["satellites", "terminals"], as_index=False).tail(1)
    pivot_status = df.pivot(index="terminals", columns="satellites", values="status")
    pivot_label = df.pivot(index="terminals", columns="satellites", values="best_architecture_or_reason")

    status_codes = {"UNINFORMATIVE": 0, "TIES": 1, "SEPARATES": 2}
    code_matrix = pivot_status.map(lambda s: status_codes[s]).astype(int)
    cmap = ListedColormap(["#d9d9d9", "#ffd699", "#7fc97f"])  # grey / amber / green

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.imshow(code_matrix.values, aspect="auto", cmap=cmap, vmin=0, vmax=2, origin="lower")

    for i in range(code_matrix.shape[0]):
        for j in range(code_matrix.shape[1]):
            status = pivot_status.iloc[i, j]
            label = pivot_label.iloc[i, j]
            if status == "UNINFORMATIVE":
                text = "uninformative\n(floor effect)"
            elif status == "TIES":
                text = "tested, tied\n(no sig. diff.)"
            else:
                text = str(label).replace("ThreadAwarePriority", "A6\n(proposed)")
            ax.text(j, i, text, ha="center", va="center", fontsize=7.5)

    ax.set_xticks(range(len(pivot_status.columns)))
    ax.set_xticklabels(pivot_status.columns)
    ax.set_yticks(range(len(pivot_status.index)))
    ax.set_yticklabels(pivot_status.index)
    ax.set_xlabel("Satellites (main Walker-delta sweep)")
    ax.set_ylabel("Army ground terminals")
    ax.set_title(
        "Architecture comparison outcome by access level (paired bootstrap, 95% CI)\n"
        "grey = uninformative (best success <= 30%); amber = tested, tied; green = real winner"
    )
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
