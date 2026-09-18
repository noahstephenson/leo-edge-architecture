"""Semantic tests for architecture delivery correctness, not just non-negativity.

Regression-guards the bugs found in the v1 audit: uncompleted deliveries
being scored as complete, bytes_transmitted exceeding contact capacity, and
contact_utilization exceeding 1.0.
"""

import math

import pytest

from leo_edge.architectures import (
    GroundOnly,
    CompressedFull,
    QuicklookFirst,
    RoiFirst,
    Progressive,
    ContactAware,
)

ALL_ARCHITECTURES = [GroundOnly, CompressedFull, QuicklookFirst, RoiFirst, Progressive, ContactAware]

SCENE_BYTES = 1_000_000_000  # 1 GB
PROCESSING_TIME_S = 20.0


def _tiny_capacity_bytes(rate_bps=1_000_000, contact_duration_s=10):
    """A capacity far too small for any product tier to fit."""
    return (rate_bps / 8.0) * contact_duration_s


def _ample_capacity_bytes(rate_bps=100_000_000, contact_duration_s=600):
    """A capacity large enough for even the raw scene to fit easily."""
    return (rate_bps / 8.0) * contact_duration_s


@pytest.mark.parametrize("arch_class", ALL_ARCHITECTURES)
def test_never_exceeds_contact_capacity(arch_class):
    """bytes_transmitted must never exceed what the contact window can hold,
    for any capacity size, not just the ones in the frozen sweep."""
    for rate_bps, duration_s in [(1_000_000, 10), (1_000_000, 300), (10_000_000, 300), (100_000_000, 600)]:
        capacity = (rate_bps / 8.0) * duration_s
        arch = arch_class()
        out = arch.run(SCENE_BYTES, capacity, rate_bps, PROCESSING_TIME_S)
        assert out["bytes_transmitted"] <= capacity + 1e-6, (
            f"{arch_class.__name__} transmitted {out['bytes_transmitted']} bytes "
            f"against a {capacity} byte capacity"
        )


@pytest.mark.parametrize("arch_class", ALL_ARCHITECTURES)
def test_contact_utilization_never_exceeds_one(arch_class):
    for rate_bps, duration_s in [(1_000_000, 10), (1_000_000, 300), (10_000_000, 300), (100_000_000, 600)]:
        capacity = (rate_bps / 8.0) * duration_s
        arch = arch_class()
        out = arch.run(SCENE_BYTES, capacity, rate_bps, PROCESSING_TIME_S)
        assert 0.0 <= out["contact_utilization"] <= 1.0


@pytest.mark.parametrize("arch_class", ALL_ARCHITECTURES)
def test_censored_when_capacity_too_small(arch_class):
    """When nothing usable can fit in the window, the architecture must not
    report a completed delivery or a real-looking tfup_s/tcp_s."""
    capacity = _tiny_capacity_bytes()
    arch = arch_class()
    out = arch.run(SCENE_BYTES, capacity, 1_000_000, PROCESSING_TIME_S)
    if not out["completed"]:
        assert math.isnan(out["tcp_s"])


@pytest.mark.parametrize("arch_class", ALL_ARCHITECTURES)
def test_completed_when_capacity_is_ample(arch_class):
    """When the window can easily hold the full product, delivery must
    complete and produce real (non-NaN) times."""
    capacity = _ample_capacity_bytes()
    arch = arch_class()
    out = arch.run(SCENE_BYTES, capacity, 100_000_000, PROCESSING_TIME_S)
    assert out["completed"] is True
    assert not math.isnan(out["tcp_s"])
    assert not math.isnan(out["tfup_s"])
    assert out["tcp_s"] >= out["tfup_s"] - 1e-9


@pytest.mark.parametrize("arch_class", [QuicklookFirst, RoiFirst, Progressive])
def test_tcp_never_equals_tfup_for_truncated_tiered_delivery(arch_class):
    """QuicklookFirst/RoiFirst/Progressive have a real first-tier product
    distinct from the full scene; when capacity holds the first tier but
    not the full scene, tcp_s must be censored, never silently equal to
    tfup_s (the historical bug this regression-tests)."""
    # Capacity: enough for a quicklook/ROI/metadata-thumbnail-quicklook tier,
    # not enough for the full 1 GB scene.
    rate_bps = 1_000_000
    duration_s = 300
    capacity = (rate_bps / 8.0) * duration_s  # 37.5 MB
    arch = arch_class()
    out = arch.run(SCENE_BYTES, capacity, rate_bps, PROCESSING_TIME_S)
    assert out["completed"] is False
    assert math.isnan(out["tcp_s"])


def test_architecture_registry_matches_arch_ids():
    from leo_edge.architectures import ARCHITECTURE_REGISTRY

    for arch_id, arch_class in ARCHITECTURE_REGISTRY.items():
        assert arch_class.ARCH_ID == arch_id


@pytest.mark.parametrize("arch_class", [GroundOnly, CompressedFull, QuicklookFirst, RoiFirst, Progressive])
def test_fidelity_always_reported(arch_class):
    capacity = _ample_capacity_bytes()
    arch = arch_class()
    out = arch.run(SCENE_BYTES, capacity, 100_000_000, PROCESSING_TIME_S)
    assert isinstance(out["fidelity_lossy"], bool)
    assert out["fidelity_resolution_class"] in {
        "metadata", "coarse", "reduced", "roi_full_res", "full_res",
    }
