"""Tests for processing module."""

def test_processing_module_imports():
    import leo_edge.processing as processing
    assert processing is not None

def test_processing_module_has_name():
    import leo_edge.processing
    assert leo_edge.processing.__name__ == "leo_edge.processing"
