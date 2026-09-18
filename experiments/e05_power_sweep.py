"""Experiment 05: Sweep processing power and compute energy break-even."""

import csv
from pathlib import Path


def main():
    D_r = 1e9
    D_p = 3e8
    T_proc = 20.0

    powers = list(range(5, 31, 5))  # 5 to 30 W

    rows = []
    for p in powers:
        processing_energy_j = p * T_proc
        # break-even transmission energy per byte: E_p < 8*e_t*(D_r - D_p)
        # => e_t* = E_p / (8*(D_r - D_p))
        e_t_star = processing_energy_j / (8 * (D_r - D_p))
        rows.append({
            "processing_power_w": p,
            "processing_energy_j": processing_energy_j,
            "e_t_break_even_j_per_byte": e_t_star,
        })
        print(f"Power {p} W -> E_p={processing_energy_j:.1f} J, e_t*={e_t_star:.3e} J/B")

    out_path = Path("results/raw/e05_power_sweep.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["processing_power_w", "processing_energy_j", "e_t_break_even_j_per_byte"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
