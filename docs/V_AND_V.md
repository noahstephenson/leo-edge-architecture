# Verification and validation

## Purpose and limits

NASA-HDBK-1009A separates product verification from product validation and shows different work products for each (§§4.1.1, 8.14–8.22, 9.7, pp. 10, 35–45, 52–53). This study uses that distinction to describe its own evidence. It has not tested an Army system, commercial imagery service, or operational concept.

Model verification checks the structured records and generated views against their rules. Analysis verification checks the code against selected assumptions, hand calculations, and invariants. Operational validation would test whether a real soldier can use the delivered imagery for a defined need. That work remains open: the project has not tested user utility, human performance, operational procedures, or real interfaces.

The [assurance catalog](../model/assurance.yaml) defines cases and status. The generated [traceability view](reference/TRACEABILITY.md) connects cases to requirements, measures, and evidence. A passing internal check is evidence about this research model only.

## Verification and validation products

| Product or check | Purpose | Current project evidence | Status and limit |
|---|---|---|---|
| Verification requirements and trace | State what internal rules or requirements a case checks. | Requirement and case records in the assurance catalog; generated traceability. | Internal study scope. Not a system acceptance basis. |
| Verification planning | Identify case, configuration, inputs, procedure, and expected result before interpreting an output. | Verification cases, experiment configuration, and reproduction commands. | Available for selected model and analysis checks; does not cover every operational interface. |
| Verification results | Record whether the model or calculation meets its stated check. | Tests, hand calculations, current evidence audit, and reproducible output files. | Supports internal correctness claims only. |
| Validation requirements or statements | State what user need should be assessed in context. | Soldier-centered need, scenarios, product sufficiency conditions, and explicit validation limits. | Notional statements; no real-user validation criteria have been agreed. |
| Validation planning and configuration | Identify real users, representative conditions, product configuration, and assessment procedure. | None for operational validation. | Open. No soldier participants, representative operational data, or field configuration. |
| Validation results | Report whether a real system satisfies the user need in its intended context. | None. | Not evaluated. Simulation success is not operational validation. |

The handbook lists requirements verification matrices, cases and events, configuration descriptions, validation requirements and events, and traceability as possible products (§§8.14–8.22, 9.7). This repository includes machine-readable requirement and case records, generated traces, automated internal tests, a result audit, and reproducible configurations. A formal compliance spreadsheet or a real system verification or operational validation event plan lies outside this conceptual study. The omitted products are part of its documented tailoring.

## Current internal checks

| Check | What it establishes | What remains outside its evidence |
|---|---|---|
| Model structure and generated views | Identifiers are unique, typed relationships resolve, selected candidate allocations are complete, and committed views reflect the catalog. | Physical feasibility, contract compliance, and operational effectiveness. |
| Product logic | A crop does not substitute for a whole-scene view; terminal derivation requires a complete scene and the modeled capability, fidelity, processing time, and deadline. | Image interpretation, mission relevance, radiometric quality, and user acceptance. |
| Contact logic | Transfer respects modeled contact capacity, carries partial bytes across contacts, preserves collecting-satellite identity, and handles interruption. | Real orbit prediction performance, field link behavior, actual site access, or communications interoperability. |
| Timing and priority | Selected seeded runs and deadline outcomes are reproducible and consistent with the recorded configuration. | Reliability estimates for an actual constellation or operational service. |
| Tasking and interface | Proposed request, product, and status fields can be inspected within the conceptual model. | Operational message routes, common data standards, cyber accreditation, and interoperability tests. |
| Prior image and change product | The model can flag that a suitable prior is absent. | Actual change detection, which is not implemented or validated. |

Automated tests and invariants check that transmitted bytes do not exceed modeled contact capacity, incomplete products have no invented completion time, selected state remains nonnegative, and seeded replay is deterministic. The [current evidence audit](../results/current/audit.json) checks selected result counts and pairing. [Engineering status](ENGINEERING_STATUS.md) records open checks. Only measures present in the evidence set may appear as numerical findings.

The optional manuscript job uses the real Mermaid parser on all generated reference views and renders the manuscript's diagrams, table, and figures. It checks diagram text size at page width and retains the PDF, HTML, figure images, and render manifest. This supplements the restricted grammar and freshness checks. Visual page review checks labels, arrows, captions, and pagination; rendering alone does not establish SysML conformance or scientific validity.

The [catalog regressions](../tests/test_model_catalog.py) also reject composition cycles and multiple owners, conflicting allocation and exchange traces, candidate satisfaction of study-evaluation obligations, implicit activity branches, invalid sequence fragments, mismatched interface messages, unguarded choices, and invalid binding roles. They check the [documented SysML interpretation](MODELING_PLAN.md#sysml-interpretation-and-view-consistency), not formal SysML conformance. A verification dependency names a check; its evidence and status determine what has been demonstrated.

Product size, link rate, processing time, deadlines, terminal capability, and utility are mostly analytical or sensitivity inputs. Their origins are labeled in [assumptions](ASSUMPTIONS.md). More simulation draws can narrow uncertainty around modeled success rates. Whether a soldier finds a product useful still needs assessment with representative users and conditions.

## Evidence sequence for a claim

The [transfer contract tests](../tests/test_transfer_contract.py) check exposed and hidden processing, exact contact completion, interrupted byte conservation, encoded-product completeness, invalid contact inputs, injected configuration, and identical single/multi-contact behavior. Current rows distinguish missing collection, incomplete transfer, insufficient fidelity, and late availability. Per-product progress and full-scene receipt are separate from mission-sufficient availability.

The [claim filters](../results/current/claims.json) are recomputed by the evidence check. The [paired comparison](../results/current/principal_paired_differences.csv) uses matching request contexts; latency differences are conditional on both candidates being timely. Sensitivity outputs retain changes caused by finer sampling, next-day propagation, and the shifted synthetic AOI. These changes limit the stability of the conclusion rather than verify optical collection accuracy.

CI runs frozen installation and internal checks. A separate [regeneration command](../scripts/verify_reproduction.py) propagates again and compares all evidence and generated figures, including manifests. Figure regeneration uses the pinned environment on Windows; a separate Linux job checks logic and committed hashes. The [workflow](https://github.com/astral-sh/setup-uv) documents the pinned setup action used for installation.

A claim is ready for the paper only when a reader can follow this path:

1. A stakeholder expectation identifies the information need and its notional context.
2. A requirement or measure states what behavior or outcome is examined.
3. A function, allocation, and interface show how the candidate is intended to produce it.
4. A named verification case identifies the configuration, inputs, procedure, and expected result.
5. The current evidence file records the output and audit status.
6. The wording states the sampling limits, assumptions, and any unvalidated interpretation.

If a link is missing, mark the claim open or not evaluated. The handbook's product-validation examples ask whether a product meets stakeholder expectations in context. This project can report a synthetic outcome under stated assumptions; a real user assessment is still needed for validation.

## Handbook reference

NASA. *NASA Systems Modeling Handbook for Systems Engineering*, NASA-HDBK-1009A, March 12, 2025. See §§4.1.1, 8.14–8.22, and 9.7, printed pp. 10, 35–45, and 52–53. [Official handbook PDF](https://standards.nasa.gov/system/files/tmp/2025-03-12-NASA-HDBK-1009A.pdf).
