"""Hand-check tests for analytical break-even models."""

import pytest
from leo_edge.analysis import break_even_rate, latency_processed, latency_raw, energy_favorable


def test_break_even_rate_manual():
    # D_r=1e9, D_p=3e8, T_proc=20 => (700_000_000)/20 = 35_000_000
    D_r = 1e9
    D_p = 3e8
    T_proc = 20.0
    expected = 35_000_000.0
    assert break_even_rate(D_r, D_p, T_proc) == pytest.approx(expected)


def test_break_even_rate_simple_integer():
    # Simple manual calc: (100 - 20)/5 = 16
    assert break_even_rate(100, 20, 5) == pytest.approx(16.0)


def test_latency_processed_manual():
    # T_proc=20, D_p=3e8, R=25e6 => 20 + 12 = 32
    assert latency_processed(20, 3e8, 25e6) == pytest.approx(32.0)


def test_latency_raw_manual():
    # D_r=1e9, R=25e6 => 40
    assert latency_raw(1e9, 25e6) == pytest.approx(40.0)


def test_break_even_condition_matches_latency():
    # Verify T_proc < (D_r - D_p)/R  <=>  R < R*
    D_r = 1e9
    D_p = 3e8
    T_proc = 20.0
    R_star = break_even_rate(D_r, D_p, T_proc)

    # R below break-even => processing faster
    R_low = R_star * 0.8
    assert latency_processed(T_proc, D_p, R_low) < latency_raw(D_r, R_low)
    assert T_proc < (D_r - D_p) / R_low

    # R above break-even => raw faster
    R_high = R_star * 1.2
    assert latency_processed(T_proc, D_p, R_high) > latency_raw(D_r, R_high)
    assert not (T_proc < (D_r - D_p) / R_high)


def test_energy_favorable_true():
    # E_p < 8*e_t*(D_r - D_p)
    # Choose values where condition holds
    E_p = 10.0
    e_t = 0.001
    D_r = 1e9
    D_p = 3e8
    # RHS = 8 * 0.001 * 700e6 = 5_600_000
    assert energy_favorable(E_p, e_t, D_r, D_p) is True


def test_energy_favorable_false():
    E_p = 10_000_000.0
    e_t = 0.001
    D_r = 1e9
    D_p = 3e8
    assert energy_favorable(E_p, e_t, D_r, D_p) is False


def test_exposed_processing_time_logic():
    # Exposed processing time = max(0, T_proc - T_lead)
    # Verify latency comparison with lead time
    D_r = 1e9
    D_p = 3e8
    T_proc = 20.0
    R = 30e6
    T_lead = 10.0

    exposed = max(0.0, T_proc - T_lead)
    latency_with_lead = exposed + D_p / R
    latency_raw_val = D_r / R

    # With lead, effective processing time is reduced
    assert latency_with_lead < T_proc + D_p / R
    # Condition for favorable with exposed time: exposed < (D_r - D_p)/R
    if exposed < (D_r - D_p) / R:
        assert latency_with_lead < latency_raw_val
    else:
        assert latency_with_lead >= latency_raw_val

    # Edge case: lead >= proc => exposed = 0
    T_lead_big = 30.0
    exposed_zero = max(0.0, T_proc - T_lead_big)
    assert exposed_zero == 0.0
    assert 0.0 + D_p / R < latency_raw_val


def test_break_even_rate_raises_on_nonpositive_Tproc():
    with pytest.raises(ValueError):
        break_even_rate(1e9, 3e8, 0)
    with pytest.raises(ValueError):
        break_even_rate(1e9, 3e8, -5)


def test_latency_processed_raises_on_nonpositive_R():
    with pytest.raises(ValueError):
        latency_processed(10, 1e6, 0)
