"""Structural checks for the GitHub-readable conceptual system model."""

from __future__ import annotations

from copy import deepcopy

from scripts.generate_model_views import DESTINATION, render, validate_mermaid
from scripts.validate_model import ROOT, load_model, validate


def test_catalog_has_complete_primary_traces_and_allocations() -> None:
    assert validate(load_model()) == []


def test_catalog_preserves_the_original_research_question() -> None:
    question = next(line.removeprefix("> ") for line in (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
                    if line.startswith("> How should imagery functions"))
    assert load_model()["model"]["research_question"] == question


def test_dangling_trace_is_rejected() -> None:
    model = deepcopy(load_model())
    model["relationships"][0]["target"] = "MT-UNKNOWN"
    assert any("unknown target MT-UNKNOWN" in error for error in validate(model))


def test_incomplete_alternative_is_rejected() -> None:
    model = deepcopy(load_model())
    model["alternatives"][4]["transmission_order"].remove("P3_ROI")
    assert any("transmission order must cover" in error for error in validate(model))


def test_alternative_without_execution_mode_is_rejected() -> None:
    model = deepcopy(load_model())
    del model["alternatives"][0]["mode_overrides"]["F-08"]
    assert any("must specify valid F-04/F-05/F-08" in error for error in validate(model))


def test_unsubstantiated_claim_is_rejected() -> None:
    model = deepcopy(load_model())
    model["claims"][0]["evidence"] = []
    assert any("claim needs evidence" in error for error in validate(model))


def test_unquoted_comma_artifact_is_rejected() -> None:
    model = deepcopy(load_model())
    model["assumptions"][0]["not a measured value"] = None
    assert any("unexpected fields" in error for error in validate(model))


def test_generated_views_are_current_and_mermaid_subset_is_valid() -> None:
    generated = render(load_model())
    for filename, content in generated.items():
        assert (ROOT / DESTINATION / filename).read_text(encoding="utf-8") == content
    assert validate_mermaid(generated["VIEWS.md"]) == []


def test_semantic_view_edits_change_generated_diagrams() -> None:
    baseline = load_model()
    original = render(baseline)["VIEWS.md"]
    for section, edit in (
        ("use_case_view", lambda item: item["use_cases"][0].update(label="Submit imagery request")),
        ("sequence_view", lambda item: item["steps"][0].update(label="New request label")),
        ("product_state_view", lambda item: item["transitions"][1].update(guard="new access guard")),
        ("parametric_view", lambda item: item["nodes"][0].update(label="new lead-time label")),
    ):
        changed = deepcopy(baseline)
        edit(changed[section])
        assert render(changed)["VIEWS.md"] != original


def test_use_case_view_keeps_actor_external_and_associations_explicit() -> None:
    model = load_model()
    diagram = render(model)["VIEWS.md"]
    assert "Soldier (external actor)" in diagram
    assert 'subgraph use_case_subject ["Imagery delivery system"]' in diagram
    assert 'n_UC_REQUEST(["Request imagery"])' in diagram
    assert 'n_UC_RECEIVE(["Receive product or delivery status"])' in diagram
    assert "n_E_USER ---|association| n_UC_REQUEST" in diagram
    assert "n_E_USER ---|association| n_UC_RECEIVE" in diagram
    changed = deepcopy(model)
    changed["use_case_view"]["associations"].pop()
    assert any("every service must have one actor association" in error for error in validate(changed))


def test_terminal_capabilities_match_simulation() -> None:
    from experiments.e11_mission_thread_success import TERMINAL_CLASSES

    terminals = load_model()["terminal_classes"]
    assert {item["code_key"] for item in terminals} == set(TERMINAL_CLASSES)
    for item in terminals:
        implementation = TERMINAL_CLASSES[item["code_key"]]
        assert item["rate_bps"] == implementation["rate_bps"]
        assert item["derivation_time_s"] == implementation["derivation_time_s"]
        assert set(item["derivable_products"]) == {tier.value for tier in implementation["derivable_tiers"]}
        assert item["can_derive_full_scene"] == bool(implementation["derivable_tiers"])


def test_primary_sizing_and_terminal_assumptions_match_inputs() -> None:
    import yaml

    model = load_model()
    assumptions = {item["id"]: item["value"] for item in model["assumptions"] if "value" in item}
    with (ROOT / "src" / "leo_edge" / "product_sizing.yaml").open(encoding="utf-8") as handle:
        sizing = yaml.safe_load(handle)
    assert assumptions["ASM-PROC-002"]["compressed_full_fraction"] == sizing["compressed_full"]["size_fraction"]
    assert assumptions["ASM-PROC-003"]["quicklook_fraction"] == sizing["quicklook"]["size_fraction"]
    assert assumptions["ASM-PROC-004"]["roi_fraction"] == sizing["roi"]["size_fraction"]
    for key in ("metadata_bytes", "thumbnail_bytes"):
        assert assumptions["ASM-PROC-005"][key] == sizing["progressive"][key]
    terminals = {item["id"]: item for item in model["terminal_classes"]}
    for assumption_id, terminal_id in (("ASM-TERM-001", "TC-VEHICLE"), ("ASM-TERM-002", "TC-DISMOUNTED")):
        assert assumptions[assumption_id]["rate_bps"] == terminals[terminal_id]["rate_bps"]
        assert assumptions[assumption_id]["derivation_time_s"] == terminals[terminal_id]["derivation_time_s"]


def test_mermaid_subset_rejects_invalid_edge_and_unclosed_sequence() -> None:
    assert validate_mermaid("```mermaid\nflowchart LR\n    a -> b\n```")
    assert validate_mermaid("```mermaid\nsequenceDiagram\n    loop Contact\n```")


def test_mermaid_guards_are_quoted_and_semicolons_are_encoded() -> None:
    assert validate_mermaid('```mermaid\nflowchart TB\n    a -->|[eligible]| b\n```')
    assert not validate_mermaid('```mermaid\nflowchart TB\n    a -->|"[eligible]"| b\n```')
    generated = render(load_model())["VIEWS.md"]
    assert "provider transfer#59;" in generated
    assert "interrupted#59;" in generated
    assert "no<br/>change product" in generated


def test_composition_rejects_cycles_and_multiple_owners() -> None:
    for source, target, expected in (
        ("E-SATELLITE", "E-SYSTEM", "composition cycle"),
        ("E-TERMINAL", "E-SATELLITE", "multiple owners"),
    ):
        model = deepcopy(load_model())
        model["relationships"].append(dict(id="T-BAD", type="contains", source=source, target=target, status="modeled"))
        assert any(expected in error for error in validate(model))


def test_relationship_traces_agree_with_allocations_and_interfaces() -> None:
    for identifier, target, expected in (
        ("T-054", "E-TERMINAL", "allocation trace disagrees"),
        ("T-059", "E-PROVIDER", "exchange trace disagrees"),
    ):
        model = deepcopy(load_model())
        next(item for item in model["relationships"] if item["id"] == identifier)["target"] = target
        assert any(expected in error for error in validate(model))


def test_candidate_cannot_satisfy_a_study_evaluation_obligation() -> None:
    model = deepcopy(load_model())
    next(item for item in model["relationships"] if item["id"] == "T-061")["type"] = "satisfies"
    assert any("cannot satisfy a study evaluation obligation" in error for error in validate(model))


def test_activity_alternatives_require_control_nodes() -> None:
    model = deepcopy(load_model())
    model["logical_flow"].append({"from": "F-07", "to": "F-09", "guard": "direct"})
    assert any("explicit decision or merge" in error for error in validate(model))


def test_sequence_else_must_belong_to_alt_and_interfaces_match() -> None:
    model = deepcopy(load_model())
    next(item for item in model["sequence_view"]["steps"] if item["kind"] == "alt")["kind"] = "loop"
    assert any("else requires an open alt" in error for error in validate(model))
    model = deepcopy(load_model())
    next(item for item in model["sequence_view"]["steps"] if item.get("reference") == "I-DOWNLINK")["from"] = "P"
    assert any("message endpoints disagree" in error for error in validate(model))


def test_sequence_credits_receipt_inside_loop_and_signals_are_solid() -> None:
    model = load_model()
    stack = []
    for step in model["sequence_view"]["steps"]:
        if step["kind"] in {"alt", "opt", "loop"}:
            stack.append(step["kind"])
        elif step["kind"] == "end":
            stack.pop()
        elif step.get("reference") == "F-08":
            assert "loop" in stack
    rendered = render(model)["VIEWS.md"]
    assert "S-)T: Send product bytes" in rendered
    assert "T->>T: Derive requested view" in rendered
    assert "S-->>T" not in rendered


def test_lifecycle_choices_require_guards_and_bindings_require_constraints() -> None:
    model = deepcopy(load_model())
    next(item for item in model["product_state_view"]["transitions"] if item["from"] == "AssessReceipt").pop("guard")
    assert any("choice branches require guards" in error for error in validate(model))
    model = deepcopy(load_model())
    model["parametric_view"]["dependencies"][0]["to"] = "lead"
    assert any("binding must connect a value" in error for error in validate(model))
