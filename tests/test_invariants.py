"""Tests for scientific invariants."""

def test_metrics_importable():
    import leo_edge.metrics
    assert leo_edge.metrics is not None

def test_no_negative_energy():
    from leo_edge.metrics import processing_energy_j
    e = processing_energy_j(10.0, 5.0)
    assert e >= 0
