"""fig19_access_sweep_by_thread.py - Mission-thread success rate vs. access
level (satellite count), one panel per mission thread, with Wilson 95% CI
bands, from experiments/e12_access_sweep.py's output.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v4" / "e12_access_sweep.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig19.png"

THREADS = [
    "MT1_TIME_SENSITIVE_CUEING",
    "MT2_ROUTE_RECON_FIRST",
    "MT3_BATTLE_DAMAGE_ASSESSMENT",
    "MT4_PERSISTENT_MONITORING",
]


def load_data():
    return pd.read_csv(DATA_PATH)


def main():
    df = load_data()
    # Single-terminal slice: the cleanest single axis (satellite count) for
    # this figure; the sat x terminal interaction is fig20's heatmap.
    df = df[df["terminals"] == 1]
    # SAT_CONFIGS includes single-plane comparison points at some of the
    # same satellite counts as a multi-plane Walker config (e.g. 4 sats:
    # 1-plane and 4-plane both exist). This figure shows the main
    # multi-plane Walker sweep, so keep only the highest-plane-count row
    # per satellite count; the single-plane comparison is a separate,
    # smaller point made in docs/V3_VS_V4.md, not this line chart.
    df = df.sort_values("planes").groupby(["satellites", "architecture", "thread"], as_index=False).tail(1)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True)
    axes = axes.flatten()

    for ax, thread in zip(axes, THREADS):
        sub = df[df["thread"] == thread]
        for arch in sorted(sub["architecture"].unique()):
            arch_sub = sub[sub["architecture"] == arch].sort_values("satellites")
            if arch_sub["success_rate"].sum() == 0:
                continue  # skip architectures with zero success everywhere on this thread, decluttering the plot
            ax.plot(arch_sub["satellites"], arch_sub["success_rate"], marker="o", label=arch, linewidth=1.5)
            ax.fill_between(
                arch_sub["satellites"], arch_sub["success_rate_ci_lower"], arch_sub["success_rate_ci_upper"],
                alpha=0.15,
            )
        ax.set_xscale("log", base=2)
        ax.set_xticks(sorted(df["satellites"].unique()))
        ax.set_xticklabels(sorted(df["satellites"].unique()))
        ax.set_title(thread, fontsize=10)
        ax.set_xlabel("Satellites (single ground terminal)")
        ax.set_ylabel("Mission-thread success rate")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

    plt.suptitle("Mission-thread success vs. access level, by thread (single terminal, e12)", fontsize=13)
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
