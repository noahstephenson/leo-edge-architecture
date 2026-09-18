"""Tests for scheduler module."""

def test_scheduler_module_imports():
    import leo_edge.scheduler as scheduler
    assert scheduler is not None

def test_scheduler_module_has_name():
    import leo_edge.scheduler
    assert leo_edge.scheduler.__name__ == "leo_edge.scheduler"
