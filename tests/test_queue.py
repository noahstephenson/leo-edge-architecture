"""Tests for queues module."""

def test_queues_module_imports():
    import leo_edge.queues as queues
    assert queues is not None

def test_queues_module_has_name():
    import leo_edge.queues
    assert leo_edge.queues.__name__ == "leo_edge.queues"
