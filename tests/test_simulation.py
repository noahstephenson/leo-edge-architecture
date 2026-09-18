"""Tests for leo_edge.simulation, including multi-contact carry-forward."""

import math

from leo_edge.architectures import GroundOnly, QuicklookFirst
from leo_edge.simulation import (
    run_static_architecture,
    simulate_multi_contact,
    contact_windows_from_access_windows,
)


def test_run_static_architecture_reports_completed_field():
    res = run_static_architecture(GroundOnly, 1_000_000_000, 600, 100_000_000, 20)
    assert res.completed is True
    res_small = run_static_architecture(GroundOnly, 1_000_000_000, 10, 1_000_000, 20)
    assert res_small.completed is False
    assert math.isnan(res_small.tcp_s)


def test_multi_contact_carries_bytes_across_windows():
    """A scene that can't fit in one window should complete once enough
    windows have accumulated capacity, with tcp_s reflecting the true
    completion time, not the first window's time."""
    arch = GroundOnly()
    scene_bytes = 100_000_000  # 100 MB
    rate_bps = 1_000_000  # 1 Mbps -> 125,000 bytes/s
    # Each window alone holds 125,000 * 60 = 7.5 MB; need many windows.
    windows = [(i * 3600.0, 60.0) for i in range(20)]  # 20 hourly passes, 60s each
    result = simulate_multi_contact(arch, scene_bytes, windows, rate_bps)
    assert result.completed is True
    assert result.contacts_used > 1
    assert result.tcp_s > windows[0][1]  # took longer than a single window


def test_multi_contact_censors_when_horizon_runs_out():
    arch = GroundOnly()
    scene_bytes = 100_000_000_000  # 100 GB, won't fit in a short horizon
    rate_bps = 1_000_000
    windows = [(i * 3600.0, 60.0) for i in range(5)]
    result = simulate_multi_contact(arch, scene_bytes, windows, rate_bps)
    assert result.completed is False
    assert math.isnan(result.tcp_s)


def test_multi_contact_two_tier_architecture_completes_first_tier_before_full():
    arch = QuicklookFirst()
    scene_bytes = 1_000_000_000  # 1 GB, quicklook = 2% = 20 MB
    rate_bps = 5_000_000  # 5 Mbps -> 625,000 bytes/s
    windows = [(i * 3600.0, 300.0) for i in range(50)]
    result = simulate_multi_contact(arch, scene_bytes, windows, rate_bps, processing_time_s=20.0)
    # tfup (quicklook) should complete well before tcp (full scene)
    assert result.tfup_s < result.tcp_s or math.isnan(result.tcp_s)


def test_contact_windows_from_access_windows_drops_pre_capture():
    from datetime import datetime, timedelta, timezone

    capture = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    windows = [
        {"start": "2019-12-31T23:00:00Z", "end": "2019-12-31T23:05:00Z", "duration_s": 300.0},
        {"start": "2020-01-01T01:00:00Z", "end": "2020-01-01T01:05:00Z", "duration_s": 300.0},
    ]
    out = contact_windows_from_access_windows(windows, capture)
    assert len(out) == 1
    assert out[0][0] == timedelta(hours=1).total_seconds()
