"""Tests for power module."""

def test_power_module_imports():
    import leo_edge.power as power
    assert power is not None

def test_power_module_has_name():
    import leo_edge.power
    assert leo_edge.power.__name__ == "leo_edge.power"
