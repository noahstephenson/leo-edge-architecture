"""Analytical break-even models for processing placement decisions."""

from __future__ import annotations


def break_even_rate(D_r: float, D_p: float, T_proc: float) -> float:
    """Return break-even downlink rate R* = (D_r - D_p) / T_proc.

    Args:
        D_r: Raw data size in bytes.
        D_p: Processed data size in bytes.
        T_proc: Processing time in seconds.

    Returns:
        Break-even rate in bytes per second.
    """
    if T_proc <= 0:
        raise ValueError("T_proc must be > 0")
    return (D_r - D_p) / T_proc


def latency_processed(T_proc: float, D_p: float, R: float) -> float:
    """Latency when processing onboard then downlinking.

    Args:
        T_proc: Processing time in seconds.
        D_p: Processed data size in bytes.
        R: Downlink rate in bytes per second.

    Returns:
        Total latency in seconds.
    """
    if R <= 0:
        raise ValueError("R must be > 0")
    return T_proc + D_p / R


def latency_raw(D_r: float, R: float) -> float:
    """Latency when downlinking raw data.

    Args:
        D_r: Raw data size in bytes.
        R: Downlink rate in bytes per second.

    Returns:
        Transmission latency in seconds.
    """
    if R <= 0:
        raise ValueError("R must be > 0")
    return D_r / R


def energy_favorable(E_p: float, e_t: float, D_r: float, D_p: float) -> bool:
    """Check if onboard processing saves energy.

    Energy saved condition: E_p < 8 * e_t * (D_r - D_p)
    where e_t is energy per byte transmitted.

    Args:
        E_p: Processing energy in joules.
        e_t: Transmission energy per byte in joules/byte.
        D_r: Raw data size in bytes.
        D_p: Processed data size in bytes.

    Returns:
        True if processing is energetically favorable.
    """
    return E_p < 8 * e_t * (D_r - D_p)


if __name__ == "__main__":
    # Example values
    D_r = 1e9
    D_p = 3e8
    T_proc = 20
    R = 25e6

    R_star = break_even_rate(D_r, D_p, T_proc)
    t_processed = latency_processed(T_proc, D_p, R)
    t_raw = latency_raw(D_r, R)

    print(f"Break-even rate R* = {R_star:.2e} B/s")
    print(f"Latency processed = {t_processed:.2f} s")
    print(f"Latency raw = {t_raw:.2f} s")
    print(f"Processing favorable? {t_processed < t_raw}")

    # Simple unit tests
    assert abs(break_even_rate(1e9, 3e8, 20) - 35_000_000) < 1e-6
    assert abs(latency_processed(20, 3e8, 25e6) - 32.0) < 1e-6
    assert abs(latency_raw(1e9, 25e6) - 40.0) < 1e-6
    assert energy_favorable(10, 0.001, 1e9, 3e8) is True
    print("All simple tests passed.")
