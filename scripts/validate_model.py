"""Validate the small, versioned conceptual architecture catalog.

This validates model structure and trace completeness. It does not validate
operational performance or establish SysML conformance.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
FILES = ("system.yaml", "architecture.yaml", "assurance.yaml", "traceability.yaml")
COLLECTIONS = {
    "stakeholders": "stakeholder",
    "elements": "element",
    "views": "view",
    "scenarios": "scenario",
    "terminal_classes": "terminal_class",
    "functions": "function",
    "interfaces": "interface",
    "products": "product",
    "alternatives": "alternative",
    "needs": "need",
    "requirements": "requirement",
    "model_integrity_checks": "model_integrity_check",
    "measures": "measure",
    "assumptions": "assumption",
    "verification_cases": "verification_case",
    "claims": "claim",
}
ALLOWED_FIELDS = {
    "stakeholders": {"id", "name", "description", "provenance"},
    "elements": {"id", "name", "description", "provenance"},
    "views": {"id", "name", "question", "style"},
    "scenarios": {"id", "name", "description", "needed_product", "deadline_s", "deadline_origin", "dependency", "status", "provenance"},
    "terminal_classes": {"id", "name", "description", "code_key", "rate_bps", "derivation_time_s", "derivable_products", "can_derive_full_scene", "provenance"},
    "functions": {"id", "name", "description", "provenance"},
    "interfaces": {"id", "name", "from", "to", "carries", "boundary_crossing", "provenance"},
    "products": {"id", "name", "coverage", "resolution", "description", "provenance"},
    "alternatives": {"id", "name", "description", "generated_products", "encoding", "transmission_order", "policy", "terminal_derivation", "allocation_exceptions", "mode_overrides", "interfaces", "provenance"},
    "needs": {"id", "name", "description", "provenance"},
    "requirements": {"id", "name", "kind", "status", "statement", "rationale", "provenance"},
    "model_integrity_checks": {"id", "legacy_id", "statement", "provenance"},
    "measures": {"id", "name", "symbol", "unit", "description", "provenance"},
    "assumptions": {"id", "category", "value", "statement", "provenance"},
    "verification_cases": {"id", "name", "method", "status", "evidence", "reason", "description", "provenance"},
    "claims": {"id", "name", "statement", "status", "evidence", "reason", "provenance"},
}
RELATIONSHIPS = {
    "contextualized_by": ("need", "scenario"),
    "evaluated_by": ("need", "measure"),
    "derived_from": ("requirement", "need"),
    "constrains": ("requirement", ("function", "interface")),
    "verifies": ("verification_case", "requirement"),
    "contains": ("element", "element"),
    "allocated_to": ("function", "element"),
    "exchanges": (("element", "interface"), ("element", "interface")),
    "satisfies": ("alternative", "requirement"),
    "candidate_for": ("alternative", "requirement"),
    "uses_interface": ("alternative", "interface"),
    "supports_claim": ("verification_case", "claim"),
}
ARCH_IDS = {
    "A0_GROUND_ONLY", "A1_COMPRESSED_FULL", "A2_QUICKLOOK_FIRST",
    "A3_ROI_FIRST", "A4_PROGRESSIVE", "A5_CONTACT_AWARE",
    "A6_THREAD_AWARE_PRIORITY",
}
PRODUCT_IDS = {"P0_METADATA", "P1_THUMBNAIL", "P2_QUICKLOOK", "P3_ROI", "P4_FULL"}
SCENARIO_IDS = {"MT-1", "MT-2", "MT-3", "MT-4"}
SOURCE_CATEGORIES = {"MEASURED_BENCHMARK", "LITERATURE", "NASA_SMALLSAT_SOA", "PUBLIC_CONTEXT", "VENDOR", "ANALYTICAL_ASSUMPTION", "SENSITIVITY_ONLY"}
VERIFICATION_STATUSES = {"supported_by_test", "supported_by_simulation", "partial", "not_evaluated"}


def load_model(root: Path = ROOT) -> dict[str, Any]:
    """Load catalog files without mutating the repository."""
    model: dict[str, Any] = {}
    for filename in FILES:
        path = root / "model" / filename
        with path.open(encoding="utf-8") as handle:
            content = yaml.safe_load(handle)
        if not isinstance(content, dict):
            raise ValueError(f"{path}: expected YAML mapping")
        overlap = model.keys() & content.keys()
        if overlap:
            raise ValueError(f"{path}: duplicate top-level keys: {sorted(overlap)}")
        model.update(content)
    return model


def validate(model: dict[str, Any], root: Path = ROOT) -> list[str]:
    """Return actionable catalog errors; an empty list means structurally valid."""
    errors: list[str] = []
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection, kind in COLLECTIONS.items():
        records = model.get(collection)
        if not isinstance(records, list):
            errors.append(f"{collection}: expected a list")
            continue
        for record in records:
            if not isinstance(record, dict):
                errors.append(f"{collection}: expected mapping entry")
                continue
            unknown_fields = set(record) - ALLOWED_FIELDS[collection]
            if unknown_fields:
                errors.append(f"{collection} {record.get('id', '<no id>')}: unexpected fields {sorted(unknown_fields)}; quote commas in YAML flow values")
            identifier = record.get("id")
            if not isinstance(identifier, str) or not identifier:
                errors.append(f"{collection}: entry lacks string id")
                continue
            if identifier in index:
                errors.append(f"{identifier}: duplicate ID in {collection} and {index[identifier][0]}")
            index[identifier] = (kind, record)
            if not record.get("name") and kind not in {"requirement", "assumption", "model_integrity_check"}:
                errors.append(f"{identifier}: missing name")
            if not record.get("description") and not record.get("statement") and not (kind == "interface" and record.get("carries")) and kind != "view":
                errors.append(f"{identifier}: missing description or statement")
            if not record.get("provenance") and kind != "view":
                errors.append(f"{identifier}: missing provenance")
            elif kind != "view" and not (root / record["provenance"]).exists():
                errors.append(f"{identifier}: provenance path does not exist: {record['provenance']}")

    def require_set(collection: str, expected: set[str]) -> None:
        actual = {item.get("id") for item in model.get(collection, []) if isinstance(item, dict)}
        if actual != expected:
            errors.append(f"{collection}: expected {sorted(expected)}; got {sorted(str(x) for x in actual)}")

    require_set("alternatives", ARCH_IDS)
    require_set("products", PRODUCT_IDS)
    require_set("scenarios", SCENARIO_IDS)

    common = model.get("common_allocations", {})
    common_modes = model.get("common_function_modes", {})
    functions = {item.get("id") for item in model.get("functions", [])}
    elements = {item.get("id") for item in model.get("elements", [])}
    if set(common) != functions:
        errors.append("common_allocations: must cover every function exactly once")
    if set(common_modes) != functions or any(not isinstance(mode, str) or not mode for mode in common_modes.values()):
        errors.append("common_function_modes: must provide a nonempty mode for every function")
    for function, element in common.items():
        if element not in elements:
            errors.append(f"common_allocations {function}: unknown element {element}")

    for scenario in model.get("scenarios", []):
        if scenario.get("needed_product") not in PRODUCT_IDS:
            errors.append(f"{scenario.get('id')}: unknown needed product")
        if scenario.get("deadline_origin") not in {"request", "collection"}:
            errors.append(f"{scenario.get('id')}: invalid deadline origin")
        if not isinstance(scenario.get("deadline_s"), (int, float)) or scenario["deadline_s"] <= 0:
            errors.append(f"{scenario.get('id')}: deadline must be positive")
    for terminal in model.get("terminal_classes", []):
        terminal_id = terminal.get("id")
        if not terminal.get("code_key"):
            errors.append(f"{terminal_id}: missing simulation code key")
        if not isinstance(terminal.get("rate_bps"), (int, float)) or terminal["rate_bps"] <= 0:
            errors.append(f"{terminal_id}: rate must be positive")
        if not isinstance(terminal.get("derivation_time_s"), (int, float)) or terminal["derivation_time_s"] <= 0:
            errors.append(f"{terminal_id}: derivation time must be positive")
        derivable = terminal.get("derivable_products", [])
        if not isinstance(derivable, list) or not set(derivable) <= PRODUCT_IDS or terminal.get("can_derive_full_scene") != bool(derivable):
            errors.append(f"{terminal_id}: invalid full-scene derivation capability")

    for interface in model.get("interfaces", []):
        for end in ("from", "to"):
            if interface.get(end) not in elements:
                errors.append(f"{interface.get('id')}: unknown {end} element")
    for alternative in model.get("alternatives", []):
        identifier = alternative.get("id")
        generated = alternative.get("generated_products", [])
        order = alternative.get("transmission_order", [])
        if not generated or not set(generated) <= PRODUCT_IDS:
            errors.append(f"{identifier}: invalid generated products")
        actual_order = [tier for tier in order if tier in PRODUCT_IDS]
        if not actual_order or not set(actual_order) <= set(generated):
            errors.append(f"{identifier}: invalid transmission order")
        if identifier != "A6_THREAD_AWARE_PRIORITY" and set(actual_order) != set(generated):
            errors.append(f"{identifier}: transmission order must cover all generated products")
        if identifier == "A6_THREAD_AWARE_PRIORITY" and order != ["P0_METADATA", "THREAD_NEEDED", "REMAINING_PROGRESSIVE"]:
            errors.append(f"{identifier}: thread-aware ordering token sequence changed")
        overrides = alternative.get("allocation_exceptions")
        if not isinstance(overrides, dict) or not set(overrides) <= functions:
            errors.append(f"{identifier}: invalid allocation exceptions")
            overrides = {}
        if set(common | overrides) != functions or any(value not in elements for value in (common | overrides).values()):
            errors.append(f"{identifier}: incomplete or invalid function allocation")
        modes = alternative.get("mode_overrides")
        if not isinstance(modes, dict) or not {"F-04", "F-05", "F-08"} <= set(modes) or not set(modes) <= functions:
            errors.append(f"{identifier}: must specify valid F-04/F-05/F-08 execution modes")
            modes = {}
        if set(common_modes | modes) != functions or any(not isinstance(mode, str) or not mode for mode in (common_modes | modes).values()):
            errors.append(f"{identifier}: incomplete function execution modes")
        if not {"I-DOWNLINK", "I-STATUS"} <= set(alternative.get("interfaces", [])):
            errors.append(f"{identifier}: boundary interfaces missing")
        for interface_id in alternative.get("interfaces", []):
            if interface_id not in index or index[interface_id][0] != "interface":
                errors.append(f"{identifier}: unknown interface {interface_id}")

    rel_ids: set[str] = set()
    relationships = model.get("relationships", [])
    if not isinstance(relationships, list):
        errors.append("relationships: expected a list")
        relationships = []
    for rel in relationships:
        rel_id = rel.get("id")
        if rel_id in rel_ids:
            errors.append(f"{rel_id}: duplicate relationship ID")
        rel_ids.add(rel_id)
        rel_type = rel.get("type")
        if rel_type not in RELATIONSHIPS:
            errors.append(f"{rel_id}: unknown relationship type {rel_type}")
            continue
        allowed_source, allowed_target = RELATIONSHIPS[rel_type]
        for end, allowed in (("source", allowed_source), ("target", allowed_target)):
            ref = rel.get(end)
            if ref not in index:
                errors.append(f"{rel_id}: unknown {end} {ref}")
            elif index[ref][0] not in (allowed if isinstance(allowed, tuple) else (allowed,)):
                errors.append(f"{rel_id}: wrong {end} kind for {rel_type}")
        if rel.get("status") not in {"proposed", "modeled", "conditional", "open", "not_evaluated"}:
            errors.append(f"{rel_id}: missing or invalid status")
        source_record = index.get(rel.get("source"), (None, {}))[1]
        target_record = index.get(rel.get("target"), (None, {}))[1]
        if rel_type == "satisfies" and target_record.get("kind") == "study":
            errors.append(f"{rel_id}: a candidate cannot satisfy a study evaluation obligation; use candidate_for")
        if rel_type == "allocated_to" and common.get(rel.get("source")) != rel.get("target"):
            errors.append(f"{rel_id}: allocation trace disagrees with common_allocations")
        if rel_type == "exchanges":
            if index.get(rel.get("target"), (None,))[0] == "interface":
                agrees = target_record.get("from") == rel.get("source")
            elif index.get(rel.get("source"), (None,))[0] == "interface":
                agrees = source_record.get("to") == rel.get("target")
            else:
                agrees = False
            if not agrees:
                errors.append(f"{rel_id}: exchange trace disagrees with interface endpoints")

    for rel_id in model.get("representative_trace", []):
        if rel_id not in rel_ids:
            errors.append(f"representative_trace: unknown relationship {rel_id}")
    controls = model.get("logical_control_nodes", [])
    control_ids = {item.get("id") for item in controls}
    if len(control_ids) != len(controls) or control_ids & functions or any(item.get("kind") not in {"decision", "merge"} or not item.get("label") for item in controls):
        errors.append("logical_control_nodes: unique decision/merge nodes and labels required")
    flow = model.get("logical_flow", [])
    for edge in flow:
        if edge.get("from") not in functions | control_ids or edge.get("to") not in functions | control_ids or not edge.get("guard"):
            errors.append(f"logical_flow: invalid function edge {edge}")
    for identifier in functions:
        if sum(edge.get("from") == identifier for edge in flow) > 1 or sum(edge.get("to") == identifier for edge in flow) > 1:
            errors.append(f"logical_flow: {identifier} needs an explicit decision or merge for alternative paths")

    sequence = model.get("sequence_view", {})
    participants = sequence.get("participants", [])
    aliases = {item.get("alias") for item in participants}
    if len(aliases) != len(participants) or any(item.get("element") not in elements for item in participants):
        errors.append("sequence_view: aliases must be unique and reference elements")
    branches: list[str] = []
    participant_elements = {item.get("alias"): item.get("element") for item in participants}
    for step in sequence.get("steps", []):
        kind = step.get("kind")
        if kind == "message":
            if step.get("from") not in aliases or step.get("to") not in aliases or not step.get("label"):
                errors.append(f"sequence_view: invalid message {step}")
            if step.get("reference") and step["reference"] not in index:
                errors.append(f"sequence_view: unknown reference {step['reference']}")
            if "dashed" in step or step.get("message_sort", "signal") not in {"call", "signal", "reply"}:
                errors.append("sequence_view: use an explicit call/signal/reply sort, not a dashed flag")
            reference = index.get(step.get("reference"), (None, {}))
            if reference[0] == "interface" and (participant_elements.get(step.get("from")), participant_elements.get(step.get("to"))) != (reference[1].get("from"), reference[1].get("to")):
                errors.append(f"sequence_view: message endpoints disagree with {step['reference']}")
        elif kind == "note":
            if set(step.get("over", [])) - aliases or not step.get("label"):
                errors.append(f"sequence_view: invalid note {step}")
        elif kind in {"alt", "loop", "opt"}:
            branches.append(kind)
            if not step.get("label"):
                errors.append(f"sequence_view: unlabeled {kind}")
        elif kind == "else":
            if not branches or branches[-1] != "alt" or not step.get("label"):
                errors.append("sequence_view: else requires an open alt branch")
        elif kind == "end":
            if not branches:
                errors.append("sequence_view: unmatched end")
            else:
                branches.pop()
        else:
            errors.append(f"sequence_view: unknown step kind {kind}")
    if branches:
        errors.append("sequence_view: unclosed branch")

    use_case = model.get("use_case_view", {})
    element_ids = {item.get("id") for item in model.get("elements", [])}
    if use_case.get("subject") not in element_ids or use_case.get("actor") not in element_ids:
        errors.append("use_case_view: subject and actor must reference system elements")
    if not use_case.get("subject_label") or not use_case.get("actor_label") or use_case.get("actor_role") != "external actor":
        errors.append("use_case_view: named subject and external actor labels are required")
    # The actor must remain outside the subject's containment tree.
    contained_by: dict[str, set[str]] = {}
    for rel in relationships:
        if rel.get("type") == "contains":
            contained_by.setdefault(rel.get("source"), set()).add(rel.get("target"))
    parents: dict[str, set[str]] = {}
    for parent, children in contained_by.items():
        for child in children:
            parents.setdefault(child, set()).add(parent)
    if any(len(owners) > 1 for owners in parents.values()):
        errors.append("contains: a composite part cannot have multiple owners")
    for origin in contained_by:
        pending_parts = list(contained_by[origin])
        visited: set[str] = set()
        while pending_parts:
            part = pending_parts.pop()
            if part == origin:
                errors.append(f"contains: composition cycle involving {origin}")
                break
            if part not in visited:
                visited.add(part)
                pending_parts.extend(contained_by.get(part, set()))
    pending = [use_case.get("subject")]
    contained: set[str] = set()
    while pending:
        parent = pending.pop()
        for child in contained_by.get(parent, set()):
            if child not in contained:
                contained.add(child)
                pending.append(child)
    if use_case.get("actor") in contained:
        errors.append("use_case_view: external actor is inside the subject boundary")
    uc_items = use_case.get("use_cases", [])
    uc_ids = {item.get("id") for item in uc_items if isinstance(item, dict)}
    if not uc_items or len(uc_ids) != len(uc_items) or any(not isinstance(item.get("id"), str) or not item["id"].startswith("UC-") or not item.get("label") for item in uc_items if isinstance(item, dict)):
        errors.append("use_case_view: use cases need unique UC- IDs and labels")
    associations = use_case.get("associations", [])
    association_pairs = {(item.get("actor"), item.get("use_case")) for item in associations if isinstance(item, dict)}
    expected_pairs = {(use_case.get("actor"), identifier) for identifier in uc_ids}
    if association_pairs != expected_pairs:
        errors.append("use_case_view: every service must have one actor association")

    state_view = model.get("product_state_view", {})
    states = set(state_view.get("states", []))
    choices = set(state_view.get("choices", []))
    if not states or "START" in states or "END" in states:
        errors.append("product_state_view: invalid state inventory")
    if choices & states or len(choices) != len(state_view.get("choices", [])):
        errors.append("product_state_view: choices must be unique and separate from states")
    for transition in state_view.get("transitions", []):
        if transition.get("from") not in states | choices | {"START"} or transition.get("to") not in states | choices | {"END"}:
            errors.append(f"product_state_view: unknown transition endpoint {transition}")
        if transition.get("from") in choices and not transition.get("guard"):
            errors.append("product_state_view: choice branches require guards")

    parametric = model.get("parametric_view", {})
    parametric_nodes = parametric.get("nodes", [])
    parametric_ids = {item.get("id") for item in parametric_nodes}
    if not parametric_ids or len(parametric_ids) != len(parametric_nodes) or any(not item.get("label") or item.get("role") not in {"value_property", "constraint_property"} for item in parametric_nodes):
        errors.append("parametric_view: invalid nodes")
    roles = {item.get("id"): item.get("role") for item in parametric_nodes}
    for dependency in parametric.get("dependencies", []):
        if dependency.get("from") not in parametric_ids or dependency.get("to") not in parametric_ids or not dependency.get("type"):
            errors.append(f"parametric_view: invalid dependency {dependency}")
        if {roles.get(dependency.get("from")), roles.get(dependency.get("to"))} != {"value_property", "constraint_property"} or not str(dependency.get("type", "")).startswith("bind "):
            errors.append("parametric_view: binding must connect a value to a named constraint parameter")

    def linked(rel_type: str, source: str | None = None, target: str | None = None) -> bool:
        return any(r.get("type") == rel_type and (source is None or r.get("source") == source)
                   and (target is None or r.get("target") == target) for r in relationships)

    for need in model.get("needs", []):
        need_id = need.get("id")
        if not linked("contextualized_by", source=need_id):
            errors.append(f"{need_id}: no scenario trace")
        if not linked("evaluated_by", source=need_id):
            errors.append(f"{need_id}: no measure trace")
    for req in model.get("requirements", []):
        req_id = req.get("id")
        if not linked("derived_from", source=req_id):
            errors.append(f"{req_id}: no need trace")
        if not linked("constrains", source=req_id):
            errors.append(f"{req_id}: no function/interface trace")
        if not linked("verifies", target=req_id):
            errors.append(f"{req_id}: no verification case")
    for case in model.get("verification_cases", []):
        case_id = case.get("id")
        status = case.get("status")
        if status not in VERIFICATION_STATUSES:
            errors.append(f"{case_id}: invalid verification status")
        if status in {"not_evaluated", "partial"} and not case.get("reason"):
            errors.append(f"{case_id}: incomplete verification needs a reason")
        if status != "not_evaluated" and not case.get("evidence"):
            errors.append(f"{case_id}: verification support needs evidence")
        for path in case.get("evidence", []):
            if not (root / path).exists():
                errors.append(f"{case_id}: missing evidence artifact {path}")
        if status == "not_evaluated" and not linked("verifies", source=case_id):
            errors.append(f"{case_id}: not-evaluated case lacks explicit requirement trace")
    for assumption in model.get("assumptions", []):
        if assumption.get("category") not in SOURCE_CATEGORIES:
            errors.append(f"{assumption.get('id')}: invalid source category")
    for claim in model.get("claims", []):
        claim_id = claim.get("id")
        status = claim.get("status")
        evidence = claim.get("evidence", [])
        if status not in {"supported_by_model", "supported_by_test", "supported_by_simulation", "analytical", "not_evaluated"}:
            errors.append(f"{claim_id}: invalid claim status")
        if status == "not_evaluated":
            if not claim.get("reason"):
                errors.append(f"{claim_id}: not-evaluated claim needs a reason")
        elif not evidence:
            errors.append(f"{claim_id}: claim needs evidence or explicit not-evaluated status")
        for ref in evidence:
            if ref.startswith("V-") and (ref not in index or index[ref][0] != "verification_case"):
                errors.append(f"{claim_id}: unknown verification reference {ref}")
            elif not ref.startswith("V-") and not (root / ref).exists():
                errors.append(f"{claim_id}: missing evidence artifact {ref}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    args = parser.parse_args()
    try:
        model = load_model(args.root)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(f"Model load failed: {exc}")
        return 1
    errors = validate(model, args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Model catalog valid: IDs, references, allocations, and primary traces resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
