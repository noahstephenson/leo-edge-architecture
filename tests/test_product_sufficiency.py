"""Product coverage and terminal processing rules used by mission trials."""

import random

import pytest

from e11_mission_thread_success import (
    CONDITIONS,
    TERMINAL_CLASSES,
    draw_trial_context,
    evaluate_single_request,
    get_needed_completion,
    tier_sufficient,
)
from leo_edge.architectures import (
    CompressedFull, ContactAware, GroundOnly, ROI_SIZE_FRACTION,
    PROGRESSIVE_QUICKLOOK_BYTES,
)
from leo_edge.products import ProductTier
from leo_edge.simulation import MultiContactResult, simulate_multi_contact


def test_cropped_roi_cannot_substitute_for_whole_scene_quicklook():
    assert not tier_sufficient(ProductTier.P2_QUICKLOOK, ProductTier.P3_ROI)
    assert not tier_sufficient(ProductTier.P3_ROI, ProductTier.P2_QUICKLOOK)


def test_full_scene_derivation_requires_terminal_capability():
    full = ProductTier.P4_FULL
    quicklook = ProductTier.P2_QUICKLOOK
    assert tier_sufficient(quicklook, full, TERMINAL_CLASSES["VEHICLE_MOUNTED"])
    unable = {"derivable_tiers": (), "derivation_time_s": None}
    assert not tier_sufficient(quicklook, full, unable)


def test_full_scene_arrival_precedes_terminal_derivation():
    result = MultiContactResult("GroundOnly", 80.0, 80.0, True, 1,
                                {ProductTier.P4_FULL.value: 80.0})
    completion, delivered = get_needed_completion(
        result, ProductTier.P2_QUICKLOOK, TERMINAL_CLASSES["VEHICLE_MOUNTED"]
    )
    assert delivered == ProductTier.P4_FULL
    assert completion == pytest.approx(85.0)


def test_terminal_processing_can_change_deadline_result():
    context = {
        "request_time_s": 0.0,
        "prior_reference_roll": 0.0,
        "collection": (0.0, "SAT"),
        "downlink_windows": [(0.0, 100.0, 50.0)],
        "denial_rolls": [1.0],
    }
    thread = {"needed_tier": ProductTier.P2_QUICKLOOK,
              "latency_tolerance_s": 90.0}
    condition = CONDITIONS["NOMINAL"]
    fast = dict(TERMINAL_CLASSES["VEHICLE_MOUNTED"], rate_bps=100_000_000)
    slow = dict(TERMINAL_CLASSES["DISMOUNTED_MANPACK"], rate_bps=100_000_000)
    for terminal, expected_success, expected_time in (
        (fast, True, 85.0), (slow, False, 110.0)
    ):
        row = evaluate_single_request(
            lambda _thread: GroundOnly(), "MT1_TIME_SENSITIVE_CUEING", thread,
            "TEST", terminal, "NOMINAL", condition, context, 0,
        )
        assert row["success"] is expected_success
        assert row["product_arrival_time_s"] == pytest.approx(80.0)
        assert row["final_availability_time_s"] == pytest.approx(expected_time)
        assert row["terminal_derivation_required"] is True


def test_missing_prior_reference_uses_explicit_thread_tolerance():
    thread = {"needed_tier": ProductTier.P3_ROI,
              "latency_tolerance_s": 600.0,
              "no_reference_latency_tolerance_s": 900.0}
    base = {
        "request_time_s": 0.0,
        "collection": (700.0, "SAT"),
        "downlink_windows": [(700.0, 100.0, 750.0)],
        "denial_rolls": [1.0],
    }
    terminal = dict(TERMINAL_CLASSES["VEHICLE_MOUNTED"], rate_bps=100_000_000)
    outcomes = []
    for roll in (0.1, 0.9):
        row = evaluate_single_request(
            lambda _thread: GroundOnly(), "MT3_BATTLE_DAMAGE_ASSESSMENT", thread,
            "TEST", terminal, "NOMINAL", CONDITIONS["NOMINAL"],
            dict(base, prior_reference_roll=roll), 0,
        )
        outcomes.append((row["has_prior_reference"], row["success"]))
    assert outcomes == [(True, False), (False, True)]


def test_product_sizing_matches_documented_assumption():
    assert ROI_SIZE_FRACTION == 0.05
    assert PROGRESSIVE_QUICKLOOK_BYTES == 20_000_000


def test_contact_bytes_never_exceed_available_capacity():
    windows = [(0.0, 2.0), (10.0, 2.0)]
    rate_bps = 8_000_000
    result = simulate_multi_contact(GroundOnly(), 10_000_000, windows, rate_bps, 0)
    assert result.bytes_transmitted <= sum(duration * rate_bps / 8 for _, duration in windows)
    assert result.bytes_transmitted == pytest.approx(4_000_000)
    assert not result.completed


def test_contact_aware_rule_uses_first_contact_and_precontact_work():
    # 300 kB compressed product at 8 Mbps needs 0.3 s transmission. A
    # 2-second contact cannot absorb 20 s of processing; 30 s of lead can.
    short = simulate_multi_contact(ContactAware(), 1_000_000,
                                   [(0.0, 2.0)], 8_000_000, 20.0)
    prepared = simulate_multi_contact(ContactAware(), 1_000_000,
                                      [(30.0, 2.0)], 8_000_000, 20.0)
    assert short.bytes_transmitted == pytest.approx(1_000_000)
    assert prepared.bytes_transmitted == pytest.approx(300_000)
    assert prepared.completed


def test_compressed_full_respects_configured_processing_time():
    result = simulate_multi_contact(CompressedFull(), 1_000_000,
                                    [(0.0, 5.0)], 8_000_000, 3.0)
    assert result.completed
    assert result.tcp_s == pytest.approx(3.3)


def test_seeded_trial_context_is_reproducible():
    aoi = {"SAT": [(0.0, 100.0, 50.0), (500.0, 100.0, 550.0)]}
    downlink = {"SAT": [(0.0, 100.0, 50.0), (500.0, 100.0, 550.0)]}
    first = draw_trial_context(random.Random(23), CONDITIONS["COMBINED_DEGRADED"], aoi, downlink)
    second = draw_trial_context(random.Random(23), CONDITIONS["COMBINED_DEGRADED"], aoi, downlink)
    assert first == second
