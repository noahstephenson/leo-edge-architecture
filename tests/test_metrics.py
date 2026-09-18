"""Tests for metrics module."""

def test_tfup_exists():
    from leo_edge.metrics import tfup_s
    assert callable(tfup_s)

def test_tcp_exists():
    from leo_edge.metrics import tcp_s
    assert callable(tcp_s)

def test_contact_utilization_exists():
    from leo_edge.metrics import contact_utilization
    assert callable(contact_utilization)
