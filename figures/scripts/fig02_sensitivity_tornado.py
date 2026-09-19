"""fig02_sensitivity_tornado.py - Tornado sensitivity of TFUP to key parameters."""
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

OUT_PATH = Path(__file__).resolve().parents[1] / "fig02.png"
DATA_DIR = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v3"
DATA_FILE = DATA_DIR / "fig02_data.csv"

os.makedirs(DATA_DIR, exist_ok=True)

def tfup_model(power_w, alpha, compression_ratio, base_tfup=1200.0):
    # Simple analytic sensitivity model
    # Higher power reduces processing time -> reduces TFUP
    # Higher alpha (contact margin) increases TFUP
    # Higher compression reduces data -> reduces TFUP
    power_factor = (power_w / 15.0) ** -0.3
    alpha_factor = (1.0 + alpha / 0.2) ** 0.5
    comp_factor = (compression_ratio / 5.0) ** -0.4
    return base_tfup * power_factor * alpha_factor * comp_factor

def load_or_generate():
    if DATA_FILE.exists():
        data = np.loadtxt(DATA_FILE, delimiter=',', skiprows=1)
        params = data[:,0]
        low = data[:,1]
        high = data[:,2]
        baseline = float(data[0,3])
        return params, low, high, baseline
    param_names = np.array(['Processor Power (W)', 'Contact Margin Alpha', 'Compression Ratio'])
    baseline_vals = np.array([15.0, 0.2, 5.0])
    low_factor, high_factor = 0.8, 1.2
    baseline_tfup = tfup_model(*baseline_vals)
    lows = []
    highs = []
    for i in range(len(baseline_vals)):
        vals = baseline_vals.copy()
        vals[i] *= low_factor
        low_tfup = tfup_model(*vals)
        vals[i] = baseline_vals[i] * high_factor
        high_tfup = tfup_model(*vals)
        lows.append(low_tfup)
        highs.append(high_tfup)
    # Save for reproducibility
    np.savetxt(DATA_FILE, np.column_stack([np.arange(len(param_names)), lows, highs, np.full(len(param_names), baseline_tfup)]), delimiter=',', header='idx,low,high,baseline', comments='')
    return param_names, np.array(lows), np.array(highs), baseline_tfup

def main():
    param_names, lows, highs, baseline = load_or_generate()
    # Compute deviations from baseline
    low_dev = lows - baseline
    high_dev = highs - baseline
    # For tornado, sort by range magnitude
    ranges = high_dev - low_dev
    order = np.argsort(ranges)
    param_names = param_names[order]
    low_dev = low_dev[order]
    high_dev = high_dev[order]

    y_pos = np.arange(len(param_names))
    fig, ax = plt.subplots(figsize=(8,5))
    # Plot bars from low to high
    ax.barh(y_pos, high_dev - low_dev, left=low_dev, height=0.6)
    ax.axvline(0, color='k', linewidth=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(param_names)
    ax.set_xlabel('TFUP change from baseline (s)')
    ax.set_title('TFUP Sensitivity Tornado')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
