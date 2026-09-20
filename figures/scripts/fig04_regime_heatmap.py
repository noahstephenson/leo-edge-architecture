"""fig04_regime_heatmap.py - Regime heatmap of best architecture by rate and contact duration.

The frozen e03/e04 experiments each sweep one axis at a time (e03 sweeps rate
at a fixed 300 s contact, e04 sweeps contact duration at a fixed 10 Mbps),
so neither has the full rate x duration grid a regime map needs. This script
builds that grid directly from the same simulation code those experiments
use (leo_edge.simulation.run_static_architecture) and caches the result to
results/frozen/v4/fig04_data.csv for reproducibility.

tcp_s is NaN wherever an architecture didn't complete full delivery within
that single contact window (see architectures.py's `completed` flag); a
grid cell where every architecture is censored has no winner and is plotted
as "no completion" rather than picking an arbitrary NaN-adjacent value.
"""
from pathlib import Path
import sys

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from leo_edge.architectures import GroundOnly, CompressedFull, QuicklookFirst, RoiFirst, Progressive
from leo_edge.simulation import run_static_architecture

DATA_DIR = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v4"
DATA_FILE = DATA_DIR / "fig04_data.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig04.png"

SCENE_BYTES = 1_000_000_000
PROCESSING_TIME_S = 20
RATES_BPS = [1_000_000, 5_000_000, 10_000_000, 25_000_000, 50_000_000, 100_000_000]
DURATIONS_S = [120, 180, 240, 300, 420, 600]

ARCH_CLASSES = {
    "A0_GROUND_ONLY": GroundOnly,
    "A1_COMPRESSED_FULL": CompressedFull,
    "A2_QUICKLOOK_FIRST": QuicklookFirst,
    "A3_ROI_FIRST": RoiFirst,
    "A4_PROGRESSIVE": Progressive,
}

NO_COMPLETION_LABEL = "NO_COMPLETION"


def build_grid():
    rows = []
    for duration_s in DURATIONS_S:
        for rate_bps in RATES_BPS:
            for arch_id, arch_class in ARCH_CLASSES.items():
                result = run_static_architecture(
                    arch_class, SCENE_BYTES, duration_s, rate_bps, PROCESSING_TIME_S
                )
                rows.append({
                    "contact_duration_s": duration_s,
                    "rate_bps": rate_bps,
                    "architecture_id": arch_id,
                    "tcp_s": result.tcp_s,
                    "completed": result.completed,
                })
    df = pd.DataFrame(rows)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_FILE, index=False)
    return df


def load_data():
    if DATA_FILE.exists():
        return pd.read_csv(DATA_FILE)
    return build_grid()


def best_architecture(df):
    # Best = minimal time to complete product (tcp_s) among architectures
    # that actually completed delivery in that cell. Cells where nothing
    # completed get an explicit NO_COMPLETION label instead of an error or
    # an arbitrary pick among NaNs.
    completed = df[df["completed"].astype(bool)]
    winners = {}
    for (rate, dur), group in df.groupby(["rate_bps", "contact_duration_s"]):
        sub = completed[(completed["rate_bps"] == rate) & (completed["contact_duration_s"] == dur)]
        if sub.empty:
            winners[(rate, dur)] = NO_COMPLETION_LABEL
        else:
            winners[(rate, dur)] = sub.loc[sub["tcp_s"].idxmin(), "architecture_id"]
    out = pd.DataFrame(
        [{"rate_bps": r, "contact_duration_s": d, "architecture_id": a} for (r, d), a in winners.items()]
    )
    return out


def main():
    df = load_data()
    best = best_architecture(df)
    pivot = best.pivot(index="contact_duration_s", columns="rate_bps", values="architecture_id")

    arch_codes = {arch: i for i, arch in enumerate(sorted(set(pivot.values.ravel())))}
    code_matrix = pivot.map(lambda arch: arch_codes[arch]).astype(int)

    rate_labels = [f"{int(r / 1e6)} Mbps" for r in pivot.columns]
    duration_labels = [f"{int(d)} s" for d in pivot.index]

    plt.figure(figsize=(9, 6))
    cmap = plt.get_cmap("tab10")
    plt.imshow(code_matrix.values, aspect="auto", cmap=cmap, vmin=0, vmax=max(len(arch_codes) - 1, 1), origin="lower")

    for i in range(code_matrix.shape[0]):
        for j in range(code_matrix.shape[1]):
            arch = pivot.iloc[i, j]
            label = "no\ncompletion" if arch == NO_COMPLETION_LABEL else arch.replace("_", "\n", 1)
            plt.text(j, i, label, ha="center", va="center", fontsize=7)

    plt.xticks(ticks=np.arange(len(rate_labels)), labels=rate_labels, rotation=45, ha="right")
    plt.yticks(ticks=np.arange(len(duration_labels)), labels=duration_labels)
    plt.xlabel("Downlink rate")
    plt.ylabel("Contact duration")
    plt.title("Best architecture by rate and contact duration\n(minimum time to complete product, among those that completed)")
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
