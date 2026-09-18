"""Tests for metrics_arch module."""

def test_architecture_complexity():
    from leo_edge.metrics_arch import architecture_complexity
    arch = {"blocks": ["A", "B", "C"], "interfaces": [("A","B"), ("B","C")]}
    assert architecture_complexity(arch) == 5

def test_interface_count():
    from leo_edge.metrics_arch import interface_count
    arch = {"interfaces": [("A","B"), ("B","C"), ("C","A")]}
    assert interface_count(arch) == 3

def test_coupling():
    from leo_edge.metrics_arch import coupling
    arch = {"blocks": ["A", "B", "C"], "interfaces": [("A","B"), ("B","C")]}
    c = coupling(arch)
    # degrees: A=1, B=2, C=1 => avg = 4/3
    assert abs(c - 4/3) < 1e-9

def test_swap_allocation():
    from leo_edge.metrics_arch import swap_allocation_per_block
    swap = {
        "proc": {"mass_kg": 1.0, "power_w": 5.0, "volume_l": 0.5},
        "radio": {"mass_kg": 1.0, "power_w": 5.0, "volume_l": 0.5},
    }
    res = swap_allocation_per_block(swap)
    assert res["_totals"]["mass_kg"] == 2.0
    assert abs(res["proc"]["mass_frac"] - 0.5) < 1e-9
    assert abs(res["radio"]["power_frac"] - 0.5) < 1e-9

def test_sweep_processor_power():
    from leo_edge.metrics_arch import sweep_processor_power
    powers = [10.0, 20.0, 40.0]
    results = sweep_processor_power(powers, base_energy_j=1000.0, contact_window_s=100.0, lead_time_s=0.0)
    # processing_time = 100, 50, 25
    assert len(results) == 3
    p, alpha, tfup = results[0]
    assert p == 10.0
    assert abs(tfup - 100.0) < 1e-9
    # alpha = 1 - 100/100 = 0
    assert abs(alpha - 0.0) < 1e-9
    p2, alpha2, tfup2 = results[2]
    assert abs(tfup2 - 25.0) < 1e-9
    assert abs(alpha2 - 0.75) < 1e-9
