"""Meaning of selected evidence outcomes and supporting analyses."""
from dataclasses import replace
import pytest
from e11_mission_thread_success import (
    evaluate_single_request, get_needed_completion, MISSION_THREADS,
    TERMINAL_CLASSES, CONDITIONS, usable_downlink_same_satellite,
)
from e13_mbse_evidence import _single_rows, _cadence_rows
from leo_edge.architectures import GroundOnly, ThreadAwarePriority
from leo_edge.configuration import DEFAULT_SIZING
from leo_edge.products import ProductTier
from leo_edge.simulation import simulate_multi_contact
from scripts.generate_model_views import load_model, render, paper_diagrams, ROOT


def evaluation(collection=(60, 'sat'), windows=(), terminal=None):
    terminal = terminal or TERMINAL_CLASSES['DISMOUNTED_MANPACK']
    ctx = dict(request_time_s=0, collection=collection, downlink_windows=windows,
               denial_rolls=[1.0] * len(windows), prior_reference_roll=0)
    return evaluate_single_request(lambda _: GroundOnly(), 'MT2_ROUTE_RECON_FIRST',
        MISSION_THREADS['MT2_ROUTE_RECON_FIRST'], 'DISMOUNTED_MANPACK', terminal,
        'NOMINAL', CONDITIONS['NOMINAL'], ctx, 0)


def test_outcomes_distinguish_missing_collection_and_incomplete_transfer():
    absent = evaluation(collection=None)
    assert absent['outcome'] == 'no_collection' and absent['full_scene_latency_s'] is None
    partial = evaluation(windows=[(60, 1, 60)])
    assert partial['outcome'] == 'incomplete_transfer'
    assert partial['bytes_transmitted'] == 625000


def test_terminal_derivation_and_exact_deadline():
    terminal = {**TERMINAL_CLASSES['DISMOUNTED_MANPACK'], 'rate_bps': 8_000_000_000}
    result = evaluation(collection=(869, 'sat'), windows=[(869, 10, 869)], terminal=terminal)
    assert result['collection_delay_s'] == 869
    assert result['product_arrival_time_s'] == 870
    assert result['terminal_processing_time_s'] == 30
    assert result['final_availability_time_s'] == 900
    assert result['success'] and result['outcome'] == 'timely_sufficient'
    assert result['full_scene_deadline_met']
    late = evaluation(collection=(870, 'sat'), windows=[(870, 10, 870)], terminal=terminal)
    assert late['outcome'] == 'late_availability' and not late['success']


def test_inadequate_terminal_fidelity_is_separate():
    terminal = dict(rate_bps=8_000_000_000, derivable_tiers=(), derivation_time_s=None)
    result = evaluation(windows=[(60, 10, 60)], terminal=terminal)
    assert result['outcome'] == 'insufficient_fidelity'
    assert result['full_scene_latency_s'] == 61


def test_full_receipt_precedes_end_of_candidate_sequence():
    sizing = replace(DEFAULT_SIZING, metadata_bytes=1, thumbnail_bytes=1)
    arch = ThreadAwarePriority(ProductTier.P4_FULL, sizing=sizing)
    result = simulate_multi_contact(arch, 1000, [(0, 1001)], 8, 0)
    assert not result.completed
    assert get_needed_completion(result, ProductTier.P4_FULL)[0] == 1001


def test_isolated_access_observation_has_no_capacity():
    assert usable_downlink_same_satellite(0, [(10, 0, 10)], [1], 0) == []


def test_receiver_semantics_pairing_and_seeded_replay():
    aoi = {'sat': [(0, 200, 100)]}
    links = {'sat': [(100, 1000, 100)]}
    first = _single_rows((1, 1, 0), 1, aoi, links, 2, 1, 7)
    repeated = _single_rows((1, 1, 0), 1, aoi, links, 2, 1, 7)
    # JSON handles the censored NaNs deterministically.
    import json
    assert json.dumps(first, sort_keys=True) == json.dumps(repeated, sort_keys=True)
    assert {r['receiver_semantics'] for r in first} == {'requesting_terminal'}
    pooled = _single_rows((1, 1, 0), 4, aoi, links, 2, 1, 7)
    assert {r['receiver_semantics'] for r in pooled} == {'pooled_connected_receiver_zero_forwarding_delay'}
    cadence = _cadence_rows((1, 1, 0), 1, aoi, links, 1, 7)
    assert {r['mode'] for r in cadence} == {'independent_opportunities'}


def test_manuscript_diagrams_follow_catalog():
    manuscript = (ROOT / 'paper/manuscript_draft.md').read_text(encoding='utf-8')
    assert paper_diagrams(manuscript, render(load_model())['VIEWS.md']) == manuscript
