"""Asserts src/leo_edge/mission_threads.py matches docs/MISSION_THREADS.md.

Values below are hand-transcribed from docs/MISSION_THREADS.md's tables,
independently of src/leo_edge/mission_threads.py, so this test actually
catches drift between the doc and the code rather than comparing the
module to itself. If you change one, change the other and this test.
"""

from leo_edge.mission_threads import MISSION_THREADS
from leo_edge.products import ProductTier

# Transcribed from docs/MISSION_THREADS.md's "First-needed product" and
# "Latency tolerance (first product)" rows.
DOC_STATED = {
    "MT1_TIME_SENSITIVE_CUEING": {
        "needed_tier": ProductTier.P2_QUICKLOOK,
        "latency_tolerance_s": 2 * 60,
    },
    "MT2_ROUTE_RECON_FIRST": {
        "needed_tier": ProductTier.P3_ROI,
        "latency_tolerance_s": 15 * 60,
    },
    "MT3_BATTLE_DAMAGE_ASSESSMENT": {
        "needed_tier": ProductTier.P3_ROI,  # documented proxy for the change product
        "latency_tolerance_s": 10 * 60,
        "no_reference_latency_tolerance_s": 15 * 60,  # degrades to MT-2's tolerance
    },
    "MT4_PERSISTENT_MONITORING": {
        "needed_tier": ProductTier.P1_THUMBNAIL,
        "latency_tolerance_s": 5 * 60,
    },
}


def test_all_doc_threads_are_modeled():
    assert set(DOC_STATED.keys()) == set(MISSION_THREADS.keys())


def test_needed_tier_matches_doc():
    for thread_key, doc_spec in DOC_STATED.items():
        assert MISSION_THREADS[thread_key]["needed_tier"] == doc_spec["needed_tier"], thread_key


def test_latency_tolerance_matches_doc():
    for thread_key, doc_spec in DOC_STATED.items():
        assert MISSION_THREADS[thread_key]["latency_tolerance_s"] == doc_spec["latency_tolerance_s"], thread_key


def test_mt3_no_reference_tolerance_matches_doc():
    assert (
        MISSION_THREADS["MT3_BATTLE_DAMAGE_ASSESSMENT"]["no_reference_latency_tolerance_s"]
        == DOC_STATED["MT3_BATTLE_DAMAGE_ASSESSMENT"]["no_reference_latency_tolerance_s"]
    )


def test_mt4_is_cadence_based_not_single_request():
    """docs/MISSION_THREADS.md defines MT-4's tolerance as measured from
    each collection pass, not from the original request; the code must
    flag it for the cadence-based evaluator, not the single-request one."""
    assert MISSION_THREADS["MT4_PERSISTENT_MONITORING"]["cadence"] is True
    for thread_key in ("MT1_TIME_SENSITIVE_CUEING", "MT2_ROUTE_RECON_FIRST", "MT3_BATTLE_DAMAGE_ASSESSMENT"):
        assert MISSION_THREADS[thread_key]["cadence"] is False
