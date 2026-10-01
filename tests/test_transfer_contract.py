"""Hand cases for the single authoritative transfer contract."""
from dataclasses import replace
import math
import pytest
from leo_edge.architectures import ARCHITECTURE_REGISTRY, CompressedFull, GroundOnly, Progressive
from leo_edge.configuration import DEFAULT_SIZING
from leo_edge.simulation import simulate_multi_contact


def test_processing_consumes_contact_and_completeness_uses_encoded_bytes():
    partial = CompressedFull().run(1000, 300, 8, 20)
    assert not partial["completed"]
    assert partial["bytes_transmitted"] == 280
    assert partial["product_completeness"] == pytest.approx(280 / 300)
    assert partial["processing_energy_j"] == 20 * DEFAULT_SIZING.processing_power_w
    assert partial["tx_energy_j"] == 280 * DEFAULT_SIZING.radio_power_w
    complete = CompressedFull().run(1000, 320, 8, 20)
    assert complete["tcp_s"] == 320
    assert complete["product_completeness"] == 1
    assert complete["deadline_met"]


def test_processing_hidden_in_gap_and_excess_processing():
    hidden = simulate_multi_contact(CompressedFull(), 1000, [(20, 300)], 8, 20)
    assert hidden.tcp_s == 320
    assert hidden.processing_time_used_s == 20
    blocked = simulate_multi_contact(CompressedFull(), 1000, [(0, 10)], 8, 20)
    assert blocked.bytes_transmitted == 0 and not blocked.completed
    assert blocked.processing_time_used_s == 10


@pytest.mark.parametrize("candidate", ARCHITECTURE_REGISTRY.values())
def test_single_contact_is_multi_contact(candidate):
    arch = candidate()
    single = arch.run(1_000_000_000, 300 * 5_000_000 / 8, 5_000_000, 20)
    multi = simulate_multi_contact(arch, 1_000_000_000, [(0, 300)], 5_000_000, 20)
    assert single["bytes_transmitted"] == multi.bytes_transmitted
    assert single["product_progress"] == multi.product_progress
    assert single["completed"] == multi.completed
    assert single["tcp_s"] == multi.tcp_s or math.isnan(single["tcp_s"]) and math.isnan(multi.tcp_s)


@pytest.mark.parametrize("windows", [[(1, 5), (2, 5)], [(5, 1), (0, 1)], [(0, -1)], [(float('nan'), 1)]])
def test_invalid_contacts_rejected(windows):
    with pytest.raises(ValueError):
        simulate_multi_contact(GroundOnly(), 10, windows, 8)


@pytest.mark.parametrize("rate", [0, -1, float('nan'), float('inf')])
def test_invalid_rate_rejected(rate):
    with pytest.raises(ValueError):
        simulate_multi_contact(GroundOnly(), 10, [], rate)


def test_empty_contacts_and_interrupted_byte_conservation():
    assert not simulate_multi_contact(GroundOnly(), 10, [], 8).completed
    result = simulate_multi_contact(GroundOnly(), 10, [(0, 4), (10, 6)], 8)
    assert result.tcp_s == 16 and result.bytes_transmitted == 10
    assert result.product_progress['P4_FULL']['completeness'] == 1
    assert result.contact_utilization == 1


def test_injected_configuration_controls_execution():
    sizing = replace(DEFAULT_SIZING, roi_fraction=0.1, quicklook_fraction=0.04)
    tiers = Progressive(sizing=sizing).tiers(1000)
    assert dict((tier.value, size) for tier, size, _ in tiers)['P3_ROI'] == 100
    assert dict((tier.value, size) for tier, size, _ in tiers)['P2_QUICKLOOK'] == 40
    with pytest.raises(ValueError):
        replace(sizing, roi_fraction=2)
