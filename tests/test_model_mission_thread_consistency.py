"""Keep the conceptual scenario catalog and executable thread settings aligned.

The stable MT IDs are mapped to legacy Python keys for historical result
compatibility. The catalog is the source of record for product, deadline,
and clock origin; this test fails if the experiment constants drift.
"""

from pathlib import Path

import yaml

from leo_edge.mission_threads import MISSION_THREADS


MODEL_PATH = Path(__file__).resolve().parents[1] / "model" / "architecture.yaml"
LEGACY_KEYS = {
    "MT-1": "MT1_TIME_SENSITIVE_CUEING",
    "MT-2": "MT2_ROUTE_RECON_FIRST",
    "MT-3": "MT3_BATTLE_DAMAGE_ASSESSMENT",
    "MT-4": "MT4_PERSISTENT_MONITORING",
}


def test_executable_thread_settings_match_model_catalog() -> None:
    model = yaml.safe_load(MODEL_PATH.read_text(encoding="utf-8"))
    scenarios = {scenario["id"]: scenario for scenario in model["scenarios"]}

    assert set(scenarios) == set(LEGACY_KEYS)
    assert set(MISSION_THREADS) == set(LEGACY_KEYS.values())

    for model_id, code_key in LEGACY_KEYS.items():
        catalog = scenarios[model_id]
        executable = MISSION_THREADS[code_key]
        assert executable["needed_tier"].value == catalog["needed_product"], model_id
        assert executable["latency_tolerance_s"] == catalog["deadline_s"], model_id
        expected_clock = "collection" if executable["cadence"] else "request"
        assert expected_clock == catalog["deadline_origin"], model_id
