"""fig06_contact_distribution.py - Histogram of LEO contact window durations."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v1" / "e01_access_windows.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "fig06.png"

def load_durations():
    df = pd.read_csv(DATA_FILE)
    if "duration_s" not in df.columns:
        raise KeyError("duration_s column missing in access windows CSV")
    return df["duration_s"].values

def main():
    durations = load_durations()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(durations, bins=20, edgecolor="black")
    ax.set_xlabel("Contact Window Duration (s)")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of LEO Contact Window Durations")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
