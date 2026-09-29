"""Generate GitHub-readable catalog, trace tables, and Mermaid views.

Run `python scripts/generate_model_views.py` after catalog edits. Run with
`--check` in CI or before committing to detect stale generated documents.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from .validate_model import ROOT, load_model, validate
except ImportError:  # direct `python scripts/generate_model_views.py`
    from validate_model import ROOT, load_model, validate


DESTINATION = Path("docs/reference")
GENERATED = ("MODEL_CATALOG.md", "TRACEABILITY.md", "VIEWS.md")


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines += ["| " + " | ".join(cell(value) for value in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def evidence_text(record: dict) -> str:
    paths = record.get("evidence", [])
    if paths:
        return ", ".join(f"[{path}](../../{path})" if not path.startswith("V-") else path for path in paths)
    return record.get("reason", "")


def name(index: dict[str, dict], identifier: str) -> str:
    return index[identifier].get("name", index[identifier].get("statement", identifier))


def catalog(model: dict) -> str:
    out = [
        "# Model catalog", "",
        "> Generated from `model/*.yaml` by `scripts/generate_model_views.py`. Edit the YAML, then regenerate. This is a conceptual model, not a formal SysML artifact.", "",
        "## System boundary", "", model["model"]["boundary"], "",
    ]
    sections = [
        ("Stakeholders", "stakeholders", ["ID", "Name", "Definition", "Provenance"], lambda x: [x["id"], x["name"], x["description"], x["provenance"]]),
        ("Elements", "elements", ["ID", "Name", "Definition", "Provenance"], lambda x: [x["id"], x["name"], x["description"], x["provenance"]]),
        ("Mission scenarios", "scenarios", ["ID", "Name", "Needed product", "Deadline", "Clock", "Status"], lambda x: [x["id"], x["name"], x["needed_product"], f'{x["deadline_s"]} s', x["deadline_origin"], x.get("status", "notional")]),
        ("Terminal classes", "terminal_classes", ["ID", "Code key", "Rate (bit/s)", "P4 derivation (s)", "Derivable tiers", "Definition"], lambda x: [x["id"], x["code_key"], x["rate_bps"], x["derivation_time_s"], ", ".join(x["derivable_products"]), x["description"]]),
        ("Functions", "functions", ["ID", "Name", "Definition", "Common allocation"], lambda x: [x["id"], x["name"], x["description"], model["common_allocations"][x["id"]]]),
        ("Interfaces", "interfaces", ["ID", "Name", "From", "To", "Carries"], lambda x: [x["id"], x["name"], x["from"], x["to"], x["carries"]]),
        ("Products", "products", ["ID", "Name", "Coverage", "Resolution", "Definition"], lambda x: [x["id"], x["name"], x["coverage"], x["resolution"], x["description"]]),
        ("Alternatives", "alternatives", ["ID", "Name", "Products", "Order", "F-04 generate/retain", "F-05 prioritize", "F-08 derive"], lambda x: [x["id"], x["name"], ", ".join(x["generated_products"]), " → ".join(x["transmission_order"]), x["mode_overrides"]["F-04"].replace("_", " "), x["mode_overrides"]["F-05"].replace("_", " "), x["mode_overrides"]["F-08"].replace("_", " ")]),
        ("Needs", "needs", ["ID", "Name", "Definition"], lambda x: [x["id"], x["name"], x["description"]]),
        ("Requirements", "requirements", ["ID", "Kind", "Status", "Statement", "Rationale"], lambda x: [x["id"], x["kind"], x["status"], x["statement"], x["rationale"]]),
        ("Model integrity checks", "model_integrity_checks", ["ID", "Legacy ID", "Statement"], lambda x: [x["id"], x["legacy_id"], x["statement"]]),
        ("Measures", "measures", ["ID", "Symbol", "Unit", "Definition"], lambda x: [x["id"], x["symbol"], x["unit"], x["description"]]),
        ("Assumptions", "assumptions", ["ID", "Source category", "Value", "Statement", "Provenance"], lambda x: [x["id"], x["category"], ", ".join(f"{k}={v}" for k, v in x.get("value", {}).items()), x["statement"], x["provenance"]]),
        ("Verification cases", "verification_cases", ["ID", "Method", "Status", "Definition", "Evidence or gap"], lambda x: [x["id"], x["method"], x["status"], x["description"], evidence_text(x)]),
        ("Paper claim register", "claims", ["ID", "Status", "Claim", "Evidence or reason"], lambda x: [x["id"], x["status"], x["statement"], evidence_text(x)]),
    ]
    for heading, key, headers, project in sections:
        out += [f"## {heading}", "", table(headers, [project(item) for item in model[key]]), ""]
        if key == "alternatives":
            out += ["### Complete function allocations and execution modes", "",
                    "The common allocation is inherited by every alternative; execution modes expose the behavior that changes. F-08 remains on the terminal and is conditional on class and received data.", ""]
            rows = [[alt["id"], function["id"], (model["common_allocations"] | alt["allocation_exceptions"])[function["id"]],
                     (model["common_function_modes"] | alt["mode_overrides"])[function["id"]].replace("_", " ")]
                    for alt in model["alternatives"] for function in model["functions"]]
            out += [table(["Alternative", "Function", "Allocated element", "Execution mode"], rows), ""]
    return "\n".join(out).rstrip() + "\n"


def traceability(model: dict) -> str:
    index = {record["id"]: record for key in ("stakeholders", "elements", "views", "scenarios", "terminal_classes", "functions", "interfaces", "products", "alternatives", "needs", "requirements", "model_integrity_checks", "measures", "assumptions", "verification_cases") for record in model[key]}
    rels = model["relationships"]
    out = ["# Traceability", "", "> Generated from `model/traceability.yaml`. Relationship direction is written explicitly; a modeled satisfaction link is not evidence of operational compliance.", "", "## Need to scenario and measure", ""]
    rows = []
    for need in model["needs"]:
        scenario = [r["target"] for r in rels if r["source"] == need["id"] and r["type"] == "contextualized_by"]
        measures = [r["target"] for r in rels if r["source"] == need["id"] and r["type"] == "evaluated_by"]
        rows.append([need["id"], ", ".join(scenario), ", ".join(measures)])
    out += [table(["Need", "Scenario", "Measure"], rows), "", "## Requirement to function or interface and verification", ""]
    rows = []
    for req in model["requirements"]:
        req_id = req["id"]
        needs = [r["target"] for r in rels if r["source"] == req_id and r["type"] == "derived_from"]
        constrained = [r["target"] for r in rels if r["source"] == req_id and r["type"] == "constrains"]
        cases = [r["source"] for r in rels if r["target"] == req_id and r["type"] == "verifies"]
        rows.append([req_id, req["kind"], req["status"], ", ".join(needs), ", ".join(constrained), ", ".join(f'{case} ({index[case]["status"]})' for case in cases)])
    out += [table(["Requirement", "Kind", "Status", "Need", "Function/interface", "Verification"], rows), "", "## Verification evidence and gaps", ""]
    out += [table(["Case", "Status", "Evidence or gap"], [[case["id"], case["status"], evidence_text(case)] for case in model["verification_cases"]]), "", "## All typed relationships", ""]
    out += [table(["ID", "Type", "Source", "Target", "Status"], [[r["id"], r["type"], r["source"], r["target"], r["status"]] for r in rels]), "", "## ID migrations", ""]
    out += [table(["Previous label", "Current label", "Reason"], [[r["old"], r["new"], r["reason"]] for r in model["id_migrations"]])]
    return "\n".join(out).rstrip() + "\n"


def mermaid_node(identifier: str, label: str) -> str:
    node_id = "n_" + re.sub(r"[^A-Za-z0-9_]", "_", identifier)
    clean = str(label).replace('"', "'").replace("\n", " ")
    return f'{node_id}["{clean}"]'


def views(model: dict) -> str:
    index = {item["id"]: item for key in ("elements", "functions", "interfaces", "products", "alternatives", "needs", "requirements", "measures", "verification_cases", "claims") for item in model[key]}
    node = lambda identifier: mermaid_node(identifier, name(index, identifier))
    nid = lambda identifier: "n_" + re.sub(r"[^A-Za-z0-9_]", "_", identifier)
    out = [
        "# Model views", "",
        "> Generated from the `model/` catalogs. Diagram purposes and relationship conventions follow Lenny Delligatti's *SysML Distilled*, Chapters 3–12. Diagrams show readable names; stable IDs remain in node keys and reference tables. These Mermaid views are analogues, not formal SysML diagrams.", "",
    ]

    def section(title: str, question: str, explanation: str, lines: list[str]) -> None:
        out.extend([f"## {title}", "", f"**Question:** {question}", "", explanation, "", "```mermaid", *lines, "```", ""])

    trace_by_id = {rel["id"]: rel for rel in model["relationships"]}
    trace = [trace_by_id[rel_id] for rel_id in model["representative_trace"]]
    trace_nodes = dict.fromkeys(end for rel in trace for end in (rel["source"], rel["target"]))
    trace_lines = ["flowchart LR", *[f"    {node(identifier)}" for identifier in trace_nodes]]
    trace_labels = {"allocated_to": "allocate", "satisfies": "satisfy", "verifies": "verify"}
    trace_lines += [f'    {nid(rel["source"])} -.->|{trace_labels.get(rel["type"], rel["type"].replace("_", " "))}| {nid(rel["target"])}' for rel in trace]
    section("Need-to-evidence trace", "How does one notional need reach candidate, interface, and bounded evidence?",
            "The corridor-detail need connects to a proposed requirement, responsible behavior, an alternative, and a bounded simulation claim. The selected comparison cites its trial and summary files in [Model catalog](MODEL_CATALOG.md). Full relationship inventory: [Traceability](TRACEABILITY.md).",
            trace_lines)

    functions = model["functions"]
    act = ["flowchart LR"] + [f"    {node(f['id'])}" for f in functions]
    act += [f'    {nid(edge["from"])} -->|{edge["guard"]}| {nid(edge["to"])}'
            for edge in model["logical_flow"]]
    section("Logical delivery activity", "What happens from request to usable imagery?",
            "Arrows show control sequencing and guarded alternatives, not data-object flow. This logical view does not assign behaviors to parts; the separate allocation view shows that relationship. Incomplete or late delivery is represented in the product-state view.", act)

    allocation = ["flowchart LR", '    subgraph behavior ["Functions"]']
    allocation += [f"        {node(function['id'])}" for function in model["functions"]]
    allocation += ['    end', '    subgraph structure_parts ["System elements"]']
    allocation += [f"        {node(element['id'])}" for element in model["elements"] if element["id"] != "E-USER"]
    allocation += ['    end']
    allocation += [f'    {nid(function["id"])} -.->|allocate| {nid(element_id)}'
                   for function in model["functions"]
                   for element_id in [model["common_allocations"][function["id"]]]]
    section("Function allocation", "Which system element performs each function?",
            "Dashed allocation dependencies point from behavior to the receiving system element, following SysML allocation direction. All candidates currently inherit the same element allocations; their execution modes differ in the catalog.", allocation)

    structure = ["classDiagram"]
    for element in model["elements"]:
        label = name(index, element["id"]).replace('"', "'")
        if element["id"] == "E-USER":
            label += " (external user)"
        else:
            label = f"«block» {label}"
        structure.append(f'    class {nid(element["id"])}["{label}"]')
    structure += [f'    {nid(r["source"])} *-- {nid(r["target"])} : part' for r in model["relationships"] if r["type"] == "contains"]
    section("System structure", "Which physical and organizational elements participate?",
            "This block-definition view uses composition to show parts contained by the system and provider. The soldier-facing user is external to the system boundary.", structure)

    interface = ["flowchart LR", '    subgraph provider_boundary ["Commercial service"]',
                 f"        {node('E-PROVIDER')}", f"        {node('E-SATELLITE')}", "    end",
                 '    subgraph army_segment ["Army tactical edge segment"]',
                 f"        {node('E-TERMINAL')}", "    end",
                 '    subgraph tasking_route ["Tasking route; ownership not modeled"]',
                 f"        {node('E-TASKING')}", "    end",
                 f"    {node('E-USER')}"]
    for item in model["interfaces"]:
        carries = item["carries"].replace("|", "/").replace("\n", " ")
        interface.append(f'    {nid(item["from"])} -->|{item["id"]} item flow: {carries}| {nid(item["to"])}')
    section("Provider–terminal interfaces", "What information crosses each interface?",
            "This internal-block view shows connected parts and labels each connector with the information exchanged. Interface records define the exchange contract; the interface itself is not shown as a transmitted item.", interface)

    seq_model = model["sequence_view"]
    sequence = ["sequenceDiagram"]
    sequence += [f'    participant {participant["alias"]} as {participant["label"]}'
                 for participant in seq_model["participants"]]
    for step in seq_model["steps"]:
        kind = step["kind"]
        if kind == "message":
            arrow = "-->>" if step.get("dashed") else "->>"
            sequence.append(f'    {step["from"]}{arrow}{step["to"]}: {step["label"]}')
        elif kind == "note":
            sequence.append(f'    Note over {",".join(step["over"])}: {step["label"]}')
        elif kind == "end":
            sequence.append("    end")
        else:
            sequence.append(f'    {kind} {step["label"]}')
    section("Delivery sequence", "When do collection, contact, and terminal derivation occur?",
            "The sequence allows same-pass delivery and byte carryover; it does not claim every request succeeds.", sequence)

    state = ["stateDiagram-v2"]
    for transition in model["product_state_view"]["transitions"]:
        source = "[*]" if transition["from"] == "START" else transition["from"]
        target = "[*]" if transition["to"] == "END" else transition["to"]
        guard = f': {transition["guard"]}' if transition.get("guard") else ""
        state.append(f"    {source} --> {target}{guard}")
    section("Product state", "How can delivery progress or fail?",
            "A product is usable only after complete delivery and any required terminal derivation.", state)

    par_model = model["parametric_view"]
    parametric = ["flowchart LR"]
    for item in par_model["nodes"]:
        if item.get("role") == "constraint_property":
            parametric.append(f'    {item["id"]}{{{{"{item["label"]}"}}}}')
        else:
            parametric.append(f'    {item["id"]}["{item["label"]}"]')
    parametric += [f'    {item["from"]} ---|{item["type"]}| {item["to"]}'
                   for item in par_model["dependencies"]]
    section("Parametric timing constraint", "When can product reduction save exposed delivery time?",
            "In this Mermaid analogue, rectangular nodes stand for value properties, hexagons stand for constraint blocks, and undirected labeled lines stand for binding connectors. The view does not encode SysML parameter directions or a formal constraint model. Sizes are bytes, rates are bits per second, and the factor of 8 converts bytes to bits. This is a first-order crossover model, not the full contact simulation.", parametric)

    for alt_id in ("A0_GROUND_ONLY", "A4_PROGRESSIVE", "A5_CONTACT_AWARE", "A6_THREAD_AWARE_PRIORITY"):
        alt = index[alt_id]
        order = alt["transmission_order"]
        steps = ["flowchart LR", f'    start["{alt["name"]}"]',
                 '    terminal["Terminal receives each completed tier"]']
        prior = "start"
        for sequence_number, tier in enumerate(order):
            labels = {"THREAD_NEEDED": "Scenario requested tier", "REMAINING_PROGRESSIVE": "Remaining progressive tiers"}
            label = name(index, tier) if tier in index else labels.get(tier, tier.replace("_", " ").lower())
            current = f"step{sequence_number}"
            steps.append(f'    {current}["{label}"]')
            steps.append(f"    {prior} -->|orders| {current}")
            steps.append(f"    {current} -->|complete downlink| terminal")
            prior = current
        if alt_id == "A0_GROUND_ONLY":
            steps += ['    derive["Derive if terminal capable and time remains"]', '    terminal -->|conditional| derive']
        if alt_id == "A5_CONTACT_AWARE":
            steps = ["flowchart LR", f'    start["{alt["name"]}"]',
                     '    choice["Contact margin selects compressed or raw full"]',
                     '    full["Full scene"]',
                     '    terminal["Terminal receives complete full scene"]',
                     '    start -->|selects encoding| choice', '    choice -->|prepares| full',
                     '    full -->|complete downlink| terminal']
        if len(order) > 1:
            steps = [line.replace("|orders|", "|transmits before|") for line in steps]
            steps = [line.replace("|transmits before|", "|candidate rule|") if "start -->" in line else line for line in steps]
        else:
            steps = [line.replace("|orders|", "|candidate transmits|") for line in steps]
        if alt_id == "A0_GROUND_ONLY":
            steps = [line for line in steps if not line.startswith("    derive[") and not line.startswith("    terminal -->|conditional|")]
        if alt_id == "A5_CONTACT_AWARE":
            title = f"Candidate encoding choice: {alt['name']}"
            question = "How does contact margin choose full-scene encoding?"
            explanation = "This flow view shows the conditional encoding choice and following transfer. It is not an activity control-flow or functional-allocation diagram. The model catalog defines the full candidate behavior."
        else:
            title = f"Candidate product order: {alt['name']}"
            question = f"Which products does {alt['name']} prioritize?"
            explanation = "This flow view communicates product order, not activity control flow or functional allocation. Labeled arrows mean transmission priority. The model catalog defines each candidate's complete allocations and execution modes."
        section(title, question, explanation, steps)
    return "\n".join(out).rstrip() + "\n"


def render(model: dict) -> dict[str, str]:
    return {"MODEL_CATALOG.md": catalog(model), "TRACEABILITY.md": traceability(model), "VIEWS.md": views(model)}


def validate_mermaid(markdown: str) -> list[str]:
    """Check the deliberately small Mermaid grammar emitted by this generator.

    The project uses only flowchart nodes/labeled edges, state transitions,
    and sequence participants/messages/blocks. This rejects syntax drift
    without requiring a network-dependent Mermaid CLI installation.
    """
    blocks = re.findall(r"```mermaid\n(.*?)\n```", markdown, re.DOTALL)
    errors: list[str] = []
    if not blocks:
        return ["No Mermaid blocks found"]
    for number, block in enumerate(blocks, 1):
        lines = block.splitlines()
        diagram = lines[0]
        if diagram not in {"flowchart LR", "flowchart TB", "classDiagram", "stateDiagram-v2", "sequenceDiagram"}:
            errors.append(f"diagram {number}: unsupported diagram declaration {diagram!r}")
            continue
        depth = 0
        for line_number, line in enumerate(lines[1:], 2):
            item = line.strip()
            if not item:
                errors.append(f"diagram {number}, line {line_number}: empty line in Mermaid block")
                continue
            valid = False
            if diagram.startswith("flowchart"):
                valid = bool(re.fullmatch(r'subgraph [A-Za-z_]\w* \["[^"\n]*"\]', item) or
                             re.fullmatch(r'end', item) or
                             re.fullmatch(r'[A-Za-z_]\w*\["[^"\n]*"\]', item) or
                             re.fullmatch(r'[A-Za-z_]\w*\{\{"[^"\n]*"\}\}', item) or
                             re.fullmatch(r'[A-Za-z_]\w* (?:-->|-\.->|---)\|[^|\n]+\| [A-Za-z_]\w*', item))
            elif diagram == "classDiagram":
                valid = bool(re.fullmatch(r'class [A-Za-z_]\w*\["[^"\n]+"\]', item) or
                             re.fullmatch(r'[A-Za-z_]\w* \*-- [A-Za-z_]\w* : [^\n]+', item))
            elif diagram == "stateDiagram-v2":
                valid = bool(re.fullmatch(r'(?:\[\*\]|[A-Za-z_]\w*) --> (?:\[\*\]|[A-Za-z_]\w*)(?:: [^\n]+)?', item))
            else:
                if item.startswith(("loop ", "opt ", "alt ")):
                    depth += 1
                    valid = True
                elif item.startswith("else "):
                    valid = depth > 0
                elif item == "end":
                    depth -= 1
                    valid = depth >= 0
                else:
                    valid = bool(re.fullmatch(r'participant [A-Za-z_]\w* as [^\n]+', item) or
                                 re.fullmatch(r'Note over [A-Za-z_]\w*,[A-Za-z_]\w*: [^\n]+', item) or
                                 re.fullmatch(r'[A-Za-z_]\w*(?:->>|-->>)[A-Za-z_]\w*: [^\n]+', item))
            if not valid:
                errors.append(f"diagram {number}, line {line_number}: unsupported Mermaid syntax {item!r}")
        if depth:
            errors.append(f"diagram {number}: unclosed sequence block")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed views differ from catalog")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    args = parser.parse_args()
    model = load_model(args.root)
    errors = validate(model, args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    rendered = render(model)
    syntax_errors = validate_mermaid(rendered["VIEWS.md"])
    if syntax_errors:
        for error in syntax_errors:
            print(f"ERROR: {error}")
        return 1
    target_dir = args.root / DESTINATION
    if args.check:
        stale = [filename for filename, content in rendered.items() if not (target_dir / filename).exists() or (target_dir / filename).read_text(encoding="utf-8") != content]
        if stale:
            print("Stale generated model views: " + ", ".join(stale))
            return 1
        print("Generated model views are current.")
        return 0
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in rendered.items():
        (target_dir / filename).write_text(content, encoding="utf-8", newline="\n")
        print(f"Wrote {target_dir / filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
