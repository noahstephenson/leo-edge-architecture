"""Tests for link module."""

def test_contact_window_exists():
    from leo_edge.link import ContactWindow
    cw = ContactWindow(start=0, stop=1, duration_s=1, max_elevation_deg=10)
    assert hasattr(cw, "start")
    assert hasattr(cw, "duration_s")

def test_contact_capacity_method():
    from leo_edge.link import ContactWindow
    cw = ContactWindow(start=0, stop=10, duration_s=10, max_elevation_deg=30)
    assert hasattr(cw, "contact_capacity_bytes")

def test_rate_monotonic_with_elevation():
    from leo_edge.link import rate_bps
    base = 1e6
    rates = [rate_bps(e, base) for e in [0, 10, 30, 60, 90]]
    # Rate should be non-decreasing with elevation up to 90 deg
    for i in range(len(rates)-1):
        assert rates[i] <= rates[i+1] + 1e-9
    # Zero elevation gives zero rate
    assert rate_bps(0, base) == 0.0
    # Negative elevation gives zero
    assert rate_bps(-10, base) == 0.0

def test_margin_reduces_effective_contact_time():
    from leo_edge.link import sweep_contact_margin
    alphas = [0.0, 0.1, 0.2, 0.3]
    durations = sweep_contact_margin(alpha_values=alphas, duration_s=100.0)
    assert len(durations) == len(alphas)
    # Effective time should decrease with increasing margin
    for i in range(len(durations)-1):
        assert durations[i] >= durations[i+1]
    # No margin gives original duration
    assert durations[0] == 100.0
    # Margin reduces time
    assert durations[-1] < durations[0]
