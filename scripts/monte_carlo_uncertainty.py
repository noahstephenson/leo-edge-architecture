"""Monte Carlo uncertainty simulation for LEO edge architectures.

Runs 10k simulations varying contact prediction error, processor jitter,
and compression variance. Fixed seed 0 for reproducibility.

Saves results to results/frozen/v3/monte_carlo.csv and generates
figures/monte_carlo_distribution.png.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from leo_edge.architectures import (
    GroundOnly,
    CompressedFull,
    QuicklookFirst,
    RoiFirst,
    Progressive,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "frozen" / "v3"
FIGURES_DIR = REPO_ROOT / "figures"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = RESULTS_DIR / "monte_carlo.csv"
OUTPUT_FIG = FIGURES_DIR / "monte_carlo_distribution.png"

# Nominal baseline parameters
SCENE_BYTES = 1e9  # 1 GB
RATE_BPS = 10e6  # 10 Mbps
NOMINAL_DURATION_S = 300.0
NOMINAL_PROCESSING_S = 30.0

ARCHITECTURES = [
    ("A0_GROUND_ONLY", GroundOnly),
    ("A1_COMPRESSED_FULL", CompressedFull),
    ("A2_QUICKLOOK_FIRST", QuicklookFirst),
    ("A3_ROI_FIRST", RoiFirst),
    ("A4_PROGRESSIVE", Progressive),
]

N_RUNS = 10_000
SEED = 0

# Uncertainty parameters
SIGMA_CONTACT = 0.10  # 10% contact prediction error
SIGMA_PROC = 0.05     # 5% processor jitter
SIGMA_COMP = 0.05     # 5% compression variance

def run_simulation(rng):
    rows = []
    # Sample all noise for this run
    contact_err = rng.normal(0.0, SIGMA_CONTACT)
    proc_jitter = rng.normal(0.0, SIGMA_PROC)
    comp_var = rng.normal(0.0, SIGMA_COMP)

    contact_duration = max(1.0, NOMINAL_DURATION_S * (1.0 + contact_err))
    # Processor jitter also modulated by compression variance for processing architectures
    base_processing = max(1.0, NOMINAL_PROCESSING_S * (1.0 + proc_jitter))

    for arch_name, arch_cls in ARCHITECTURES:
        # Apply compression variance as additional processing time perturbation
        # for architectures that perform processing
        processing_time = base_processing
        if arch_name != "A0_GROUND_ONLY":
            processing_time *= (1.0 + 0.5 * comp_var)

        arch = arch_cls()
        # Contact capacity in bytes
        contact_capacity_bytes = (RATE_BPS / 8.0) * contact_duration
        out = arch.run(SCENE_BYTES, contact_capacity_bytes, RATE_BPS, processing_time)

        rows.append({
            "run_id": int(rng.integers(0, 1_000_000_000)),  # overwritten with the real run index below
            "architecture": arch_name,
            "tfup_s": float(out.get("tfup_s", np.nan)),
            "tcp_s": float(out.get("tcp_s", np.nan)),
            "contact_error": contact_err,
            "proc_jitter": proc_jitter,
            "comp_var": comp_var,
        })
    return rows

def main():
    rng = np.random.default_rng(SEED)
    all_rows = []
    for i in range(N_RUNS):
        contact_err = rng.normal(0.0, SIGMA_CONTACT)
        proc_jitter = rng.normal(0.0, SIGMA_PROC)
        comp_var = rng.normal(0.0, SIGMA_COMP)

        contact_duration = max(1.0, NOMINAL_DURATION_S * (1.0 + contact_err))
        base_processing = max(1.0, NOMINAL_PROCESSING_S * (1.0 + proc_jitter))

        for arch_name, arch_cls in ARCHITECTURES:
            processing_time = base_processing
            if arch_name != "A0_GROUND_ONLY":
                processing_time *= (1.0 + 0.5 * comp_var)

            arch = arch_cls()
            contact_capacity_bytes = (RATE_BPS / 8.0) * contact_duration
            out = arch.run(SCENE_BYTES, contact_capacity_bytes, RATE_BPS, processing_time)

            all_rows.append({
                "run_id": i,
                "architecture": arch_name,
                "tfup_s": float(out.get("tfup_s", np.nan)),
                "tcp_s": float(out.get("tcp_s", np.nan)),
                "completed": bool(out.get("completed", False)),
                "contact_error": float(contact_err),
                "proc_jitter": float(proc_jitter),
                "comp_var": float(comp_var),
            })

    df = pd.DataFrame(all_rows)
    # Save CSV with required columns plus diagnostics
    df_out = df[["run_id", "architecture", "tfup_s", "tcp_s", "completed"]]
    df_out.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df_out)} rows to {OUTPUT_CSV}")
    completion_rates = df.groupby("architecture")["completed"].mean()
    print("Completion rate per architecture:")
    print(completion_rates.to_string())

    # Figure: distribution of TFUP and TCP per architecture, censored
    # (uncompleted) runs excluded since NaN has no place on a boxplot.
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)

    arch_names = [a[0] for a in ARCHITECTURES]

    def _nonempty_series(metric):
        names, data = [], []
        for name in arch_names:
            vals = df[(df["architecture"] == name) & df[metric].notna()][metric].values
            if len(vals) > 0:
                names.append(name)
                data.append(vals)
            else:
                print(f"Monte Carlo: {name} had zero completed runs for {metric}, excluded from boxplot")
        return names, data

    tfup_names, tfup_data = _nonempty_series("tfup_s")
    tcp_names, tcp_data = _nonempty_series("tcp_s")

    bp0 = axes[0].boxplot(tfup_data, showfliers=False)
    axes[0].set_xticks(range(1, len(tfup_names) + 1))
    axes[0].set_xticklabels(tfup_names, rotation=45)
    axes[0].set_title("TFUP Distribution (Monte Carlo, completed runs only)")
    axes[0].set_ylabel("TFUP [s]")

    bp1 = axes[1].boxplot(tcp_data, showfliers=False)
    axes[1].set_xticks(range(1, len(tcp_names) + 1))
    axes[1].set_xticklabels(tcp_names, rotation=45)
    axes[1].set_title("TCP Distribution (Monte Carlo, completed runs only)")
    axes[1].set_ylabel("TCP [s]")

    plt.tight_layout()
    plt.savefig(OUTPUT_FIG, dpi=150)
    plt.close()
    print(f"Saved figure to {OUTPUT_FIG}")

if __name__ == "__main__":
    main()
