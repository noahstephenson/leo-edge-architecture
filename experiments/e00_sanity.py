"""Experiment 00: Sanity check analytical model break-even examples."""

from leo_edge.analysis import break_even_rate, latency_processed, latency_raw


def main():
    examples = [
        (1e9, 3e8, 20),
        (2e9, 5e8, 30),
        (5e8, 1e8, 10),
    ]
    print("Analytical model break-even examples")
    print("-" * 60)
    for D_r, D_p, T_proc in examples:
        R_star = break_even_rate(D_r, D_p, T_proc)
        R = R_star * 1.2  # pick rate above break-even
        t_proc = latency_processed(T_proc, D_p, R)
        t_raw = latency_raw(D_r, R)
        print(f"D_r={D_r:.0e} B, D_p={D_p:.0e} B, T_proc={T_proc}s")
        print(f"  Break-even rate R* = {R_star:.2e} B/s")
        print(f"  At R = {R:.2e} B/s: processed={t_proc:.1f}s, raw={t_raw:.1f}s, favorable={t_proc < t_raw}")
        print()
    print("Sanity check complete.")


if __name__ == "__main__":
    main()
