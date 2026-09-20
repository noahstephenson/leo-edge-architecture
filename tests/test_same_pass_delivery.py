"""v4 item 2: a downlink window that is already open when collection
completes must be usable for its remaining duration, not skipped just
because it started before collection did. This is what makes same-pass
collect-and-downlink possible -- the defining capability of direct-to-edge
that v3's `_usable_downlink` (start-time-gated) forbade entirely.
"""

from e11_mission_thread_success import usable_downlink_same_satellite


def test_same_pass_window_is_clipped_not_skipped():
    # Downlink window open [100, 400) (start_s=100, dur_s=300); collection
    # completes at t=250, mid-window. v3's rule would have skipped this
    # window entirely (start_s=100 < base_time_s=250); v4 must use its
    # remaining 150s (250 -> 400).
    downlink_windows = [(100.0, 300.0, 250.0)]  # (start_s, dur_s, peak_s)
    usable = usable_downlink_same_satellite(
        collection_time_s=250.0, downlink_windows=downlink_windows,
        denial_rolls=[1.0], contact_denial_frac=0.0,
    )
    assert usable == [(0.0, 150.0)]


def test_window_fully_before_collection_is_skipped():
    downlink_windows = [(100.0, 100.0, 150.0)]  # ends at 200, before collection at 250
    usable = usable_downlink_same_satellite(
        collection_time_s=250.0, downlink_windows=downlink_windows,
        denial_rolls=[1.0], contact_denial_frac=0.0,
    )
    assert usable == []


def test_window_fully_after_collection_is_used_whole():
    downlink_windows = [(300.0, 50.0, 320.0)]
    usable = usable_downlink_same_satellite(
        collection_time_s=250.0, downlink_windows=downlink_windows,
        denial_rolls=[1.0], contact_denial_frac=0.0,
    )
    assert usable == [(50.0, 50.0)]


def test_denied_window_is_excluded_regardless_of_timing():
    downlink_windows = [(100.0, 300.0, 250.0)]
    usable = usable_downlink_same_satellite(
        collection_time_s=250.0, downlink_windows=downlink_windows,
        denial_rolls=[0.0], contact_denial_frac=0.5,
    )
    assert usable == []
