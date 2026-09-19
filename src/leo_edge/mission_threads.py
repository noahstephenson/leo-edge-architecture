"""Mission thread definitions: single source of truth for tier/tolerance
parameters, so experiments/e11_mission_thread_success.py, app/dashboard.py,
and tests/test_mission_thread_consistency.py can't silently drift apart
from docs/MISSION_THREADS.md. If you change a value here, update
docs/MISSION_THREADS.md's table in the same commit, and vice versa.

Every field is ASSUMED (docs/MISSION_THREADS.md's header note); none of
this is a sourced Army requirement.
"""

from .products import ProductTier

# MT-3 (battle damage assessment) has no dedicated product type in
# src/leo_edge/products.py; its change/difference product is modeled as
# equivalent in size and processing cost to a P3_ROI tier (a stated proxy,
# not a claim that a change product and an ROI crop are the same thing).
# See docs/DECISION_LOG.md for the ADR.
MISSION_THREADS = {
    "MT1_TIME_SENSITIVE_CUEING": {
        "needed_tier": ProductTier.P2_QUICKLOOK,
        "latency_tolerance_s": 120,
        "cadence": False,
    },
    "MT2_ROUTE_RECON_FIRST": {
        "needed_tier": ProductTier.P3_ROI,
        "latency_tolerance_s": 900,
        "cadence": False,
    },
    "MT3_BATTLE_DAMAGE_ASSESSMENT": {
        "needed_tier": ProductTier.P3_ROI,  # change-product size/processing proxy
        "latency_tolerance_s": 600,  # 10 minutes, with a prior reference available
        "no_reference_latency_tolerance_s": 900,  # degrades to MT-2's 15-minute tolerance
        "cadence": False,
    },
    "MT4_PERSISTENT_MONITORING": {
        "needed_tier": ProductTier.P1_THUMBNAIL,
        "latency_tolerance_s": 300,  # measured from each collection pass, not from request
        "cadence": True,
    },
}
