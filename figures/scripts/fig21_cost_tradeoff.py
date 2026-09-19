"""fig21_cost_tradeoff.py - Notional cost-vs-success-rate tradeoff curve
from experiments/e12_access_sweep.py's relative cost proxy. Every cost
number here is an ASSUMED relative unit, not a real dollar estimate; see
the module docstring in e12_access_sweep.py and docs/ACQUISITION_IMPLICATIONS.md.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v3" / "e12_cost_tradeoff.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig21.png"


def main():
    df = pd.read_csv(DATA_PATH).sort_values("relative_cost")

    fig, ax = plt.subplots(figsize=(9, 6))
    for terminals, group in df.groupby("terminals"):
        group = group.sort_values("relative_cost")
        ax.plot(group["relative_cost"], group["success_rate"], marker="o", label=f"{terminals} terminal(s)")

    ax.set_xlabel("Notional relative cost (ASSUMED units: satellites x10 + terminals x3 + processing tiers x1)")
    ax.set_ylabel("Overall mission-thread success rate (all threads/conditions pooled)")
    ax.set_title("Notional cost vs. mission-thread success rate (e12)\nASSUMED cost proxy, not a real acquisition cost estimate")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
