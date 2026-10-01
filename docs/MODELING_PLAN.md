# Modeling plan

## Purpose and operational need

This study asks how imagery tasking, collection, preparation, prioritization, and delivery should be divided between a commercial satellite service and an Army-owned tactical terminal. The principal user is a notional soldier who needs a timely, usable image at the edge. The Army terminal operator, commercial service provider, and acquisition decision-maker are also represented because each shapes the service boundary and its interfaces.

The soldier-centered need is deliberately limited: receive imagery with declared coverage and fidelity before an assumed mission deadline, despite intermittent satellite access or a delayed contact. Scenarios, sites, deadlines, rates, and needs are synthetic. They do not describe Army doctrine, a real mission, a collection plan, an operational location, or a validated capability. No target recognition, tracking, weapon cueing, strike support, or classified workflow is modeled. The [concept of operations](CONOPS.md) describes the notional request and delivery. [Operational context](OPERATIONAL_CONTEXT.md) sets the public scope boundaries.

A systems engineering reviewer should be able to start with the soldier's information need and follow it through an expectation, requirement, function, candidate allocation, interface, measure, verification case, and bounded trade implication.

## Method and handbook tailoring

[NASA-HDBK-1009A](https://standards.nasa.gov/system/files/tmp/2025-03-12-NASA-HDBK-1009A.pdf) is the primary method reference. The handbook explains how models support selected NASA systems engineering work products. It covers stakeholder expectation definition, technical requirements definition, product verification, and product validation; it is not a complete end-to-end development standard (§§1.1, 4.1.1, pp. 6, 10). The project uses its planning, model setup, metamodel, example views, and work-product mapping (§§5–9, pp. 15–53) as a guide for this scoped conceptual model.

The handbook distinguishes modeling language, methodology, and framework (§4.3.1–4.3.3, pp. 11–14). Here, structured YAML catalogs define model elements and relationships; Mermaid diagrams and tables show selected views of those records. The mapping to the handbook metamodel is documented, but the catalogs are not a formal SysML model. Diagram edges name their relationship. The catalogs remain the source of record, and generated views are not edited by hand. NASA has not reviewed or endorsed this project.

NASA places model planning in technical planning and model setup at the beginning of system design (§§4.3.2, 5–6, pp. 12, 15–16). This repository is a conceptual study, not an approved project plan or systems engineering management plan. This page, the model catalogs, conventions, generated-view manifest, validation scripts, and decision log provide the corresponding planning record. They name expected outputs, model authority, users, boundaries, and checks and establish naming, relationship, and completeness conventions. That is the project's explicit tailoring of the handbook's planning and setup work products.

| Method step | Engineering question | Project work product and completion evidence | NASA-HDBK-1009A reference |
|---|---|---|---|
| Plan modeling | Who uses the model, which decisions should it support, and what products will it produce? | This plan; stated soldier-centered need; system boundary; model authority; view list; evidence rules; open-item record. | §5, p. 15 |
| Set up model | How are elements organized, named, related, and controlled? | Four structured catalogs in [model/](../model/), stable identifiers, relationship types, view manifest, validator, and generated reference views. | §6, p. 16; §7, pp. 17–21 |
| Define expectations and concept of operations | Who needs what information, under what conditions, and how is the service used? | [Stakeholders](STAKEHOLDERS.md), [scenarios](MISSION_THREADS.md), [concept of operations](CONOPS.md), context and interface descriptions. | §§8.1–8.8, 9.1–9.2, pp. 22–30, 46–48 |
| Define effectiveness measures | How will the notional soldier's expectation be judged? | Stakeholder-linked measures of timely delivery, product sufficiency, and incomplete delivery, with assumed criteria identified. | §§8.12, 9.3, pp. 31–33, 48–49 |
| Define technical requirements | What behavior is expected of the notional service and its interface? | [Requirements](REQUIREMENTS.md), traces to expectations and measures, candidate allocation, and planned checks. | §§8.10–8.13, 9.4–9.6, pp. 30–34, 49–52 |
| Describe logical and candidate architecture | Which behaviors and interfaces are needed, and which party performs them in each candidate? | [Functional architecture](FUNCTIONAL_ARCHITECTURE.md), [candidate allocations](ALLOCATION_SPACE.md), [interfaces](INTERFACES.md), and generated behavior and structure views. | §§8.3–8.9, pp. 24–30; the handbook's broader model examples in §8 |
| Verify model and analysis | Does the implementation satisfy the model's stated rules, and do calculations match hand checks? | [Verification and validation record](V_AND_V.md), verification cases, tests, evidence audit, and selected [trade study](TRADE_STUDY.md). | §§8.14–8.20, 9.7, pp. 35–43, 52–53 |
| Assess operational validity | Would the product and service satisfy the real user's need in context? | Explicitly open; no operational user evaluation, Army terminal, or field data is available. | §8.21–8.22, 9.7, pp. 43–45, 52–53 |

The sequence gives this study a reviewable order from need through evidence. NASA-HDBK-1009A permits diagrams and tables to be built in an order suited to the engineering activity (§8, p. 22); it does not mandate these exact project steps.

## Model content and conventions

The model contains stakeholders and needs, scenarios, measures, requirements, functions, system elements, interfaces, products, candidate allocations, verification and validation statements, analysis cases, and typed relationships. These concepts align with the elements and relationships shown in the handbook's system and verification metamodels (§7, pp. 17–21). The model's [catalog](reference/MODEL_CATALOG.md) defines them; [traceability tables](reference/TRACEABILITY.md) and [Mermaid views](reference/VIEWS.md) expose selected paths for readers.

Each catalog element has a stable identifier, definition, and provenance. Each relationship states its endpoints, type, and status. The validator checks identifiers, references, selected allocation completeness, and consistency between model data and generated views. The system boundary runs from a synthetic imagery request to a product received and judged usable at a generic Army terminal. Collection opportunity and terminal contact are separate. A scene stays with the satellite that collected it; the model includes no crosslink. Interface descriptions identify the request, product identity, declared coverage and fidelity, completeness, and delivery status.

The soldier receiving the image is the principal human perspective. The study models delivery time and stated product properties. Human performance remains untested: a simulated transfer does not establish that the image is interpretable, relevant, or useful. The synthetic deadline is a scenario criterion rather than a threshold validated with soldiers. A successful modeled transfer supports only a bounded architecture comparison.

## SysML interpretation and view consistency

The view set is organized around Lenny Delligatti's *SysML Distilled*, Chapters 3 through 12. The [publisher's contents](https://www.informit.com/store/sysml-distilled-a-brief-guide-to-the-systems-modeling-9780133430363) identifies the relevant diagram purposes and treats allocation as a relationship across views. This review uses that organization, rather than claiming a complete textbook audit. Relationship meanings are checked against [OMG SysML 1.6](https://www.omg.org/spec/SysML/1.6/), especially Chapters 8, 9, 10, 15, and 16. The repository retains the established SysML v1 concepts; it does not claim formal language conformance or introduce a SysML v2 migration.

| Concept | Repository convention |
|---|---|
| Structure and boundary | E-SYSTEM contains the provider, tasking path, and terminal. The provider contains the satellite. The user is external. Composition describes the conceptual system, not common asset ownership; tasking-route ownership remains unspecified. |
| Internal structure | Interface views use the same participating elements and system boundary. Arrows show item direction on conceptual connections. Typed ports, part multiplicities, connector ends, and operational schemas remain unspecified. |
| Allocation | `allocated_to` points from function to responsible element. Common ownership is separate from candidate execution modes. The activity stays unallocated; the allocation view supplies that mapping. |
| Requirements | `satisfies` points from candidate design to requirement and records design intent, not a passing verdict. `candidate_for` identifies a design evaluated against a criterion. Study-evaluation obligations belong to the research process and are not satisfied by selecting a candidate. |
| Trace and verification | `derived_from` is a project-specific need trace, not SysML `deriveReqt`, which relates requirements. `constrains` is also project-specific. `verifies` points from case to requirement; its existence does not establish success. Case status and cited evidence state the actual support. |
| Activity | Explicit decision and merge nodes distinguish alternative paths from parallel execution or a join. The drawing shows one successful product path. It does not impose a batch preparation barrier, represent the repeated transfer loop, or replace the failure view. |
| Interaction | Remote information exchanges use solid open-arrow signals; self processing uses calls. Dashed replies require a modeled return. The contact loop contains product receipt and eligible derivation, since usable availability can precede completion of all products. |
| Lifecycle | Product transfer states and request-level outcomes share a conceptual lifecycle view. Choices distinguish receipt assessment and derived-view assessment. Prior-reference branches describe the unimplemented change-product obligation. Guards do not make this an executable state machine. |
| Parametrics | Constraint properties are usages of constraint definitions. Undirected bindings equate values with named parameters; they do not order calculations. The displayed crossover remains separate from the contact simulation. |

The exact normative anchors include SysML §§8.3.2.3, 16.3.2.7, and 16.3.2.9 for bindings, satisfaction, and verification. Interaction and activity meanings also follow [OMG UML 2.5.1](https://www.omg.org/spec/UML/2.5.1/), Chapters 15 and 17, including §17.4.4.1 for message notation. The validator checks composition ownership and cycles, relationship endpoints, allocation consistency, explicit activity alternatives, sequence branch nesting, interface-message endpoints, guarded lifecycle choices, and value-to-constraint bindings. Those checks preserve the repository's conventions. They do not validate an executable SysML model, a communications protocol, or the operational system.

## Measures and evidence

The effectiveness question is whether the notional soldier receives a product with sufficient declared coverage and fidelity in time for the synthetic scenario. Quantitative performance measures include elapsed delivery time, deadline outcome, and incomplete delivery where the evidence set actually reports them. Energy, storage, contact utilization, or any other metric is included in a conclusion only when recorded and checked. The model distinguishes stakeholder effectiveness from measurable implementation performance, following the handbook's separate treatment of measures of effectiveness and measures of performance (§§9.3, 9.5–9.6, pp. 48–52).

Code and configuration define each calculation. The [current evidence](../results/current/) records selected inputs and outputs. Every paper claim must link to an expectation or requirement, measure, verification case, and evidence, or state that it was not evaluated. Product sufficiency depends on coverage, fidelity, terminal capability, processing time, and deadline. [Assumptions](ASSUMPTIONS.md) labels input sources and confidence. Passing a timing check does not validate image utility or operational suitability.

## References

NASA. *NASA Systems Modeling Handbook for Systems Engineering*, NASA-HDBK-1009A, March 12, 2025. Relevant guidance is cited above by section and printed handbook page. [Official handbook PDF](https://standards.nasa.gov/system/files/tmp/2025-03-12-NASA-HDBK-1009A.pdf).
