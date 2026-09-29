# Repository guidance

Read this file before changing the LEO Edge Architecture research project.

## Mission and research question

Build a reproducible, notional systems engineering study of how imagery functions are divided between a commercial low Earth orbit imagery service and an Army owned tactical terminal. The repository must connect operational need, stakeholder value, requirement, function, allocation, interface, measure, verification, and a bounded trade implication. The [model catalogs](model/) hold those relationships.

> How should imagery functions (tasking, collection, processing, prioritization, delivery) be allocated between a commercial LEO space segment acquired as a service and an Army-owned tactical edge segment, and how does the preferred allocation shift across mission needs, terminal classes, and contested or DDIL conditions?

Do not silently change this question. Record a proposed pivot in [the decision log](docs/DECISION_LOG.md) before changing the design.

Everything operational is synthetic and unofficial. This repository does not represent an Army requirement, program, collection plan, or acquisition decision. See [operational context](docs/OPERATIONAL_CONTEXT.md).

## Scope boundaries

Do not build target recognition, target tracking, weapon cueing, strike support, classified workflows, real Army tactical collection plans, real operational terminal locations, offensive cyber capability, or detailed orbital warfare scenarios. Use public civilian imagery, synthetic requests, generic terminals, generic rate sweeps, and public technical literature.

## Model and code quality

The structured files in `model/` are the source of record for architecture and traceability. Generated Mermaid views and reference tables must be refreshed from them, not edited by hand. Code should be deterministic when seeded, typed where practical, configuration driven, modular, tested, and reproducible from a clean clone. Avoid notebook only logic, hidden constants, giant scripts, unversioned results, and manually edited generated data.

Use stable candidate IDs:

- `A0_GROUND_ONLY`
- `A1_COMPRESSED_FULL`
- `A2_QUICKLOOK_FIRST`
- `A3_ROI_FIRST`
- `A4_PROGRESSIVE`
- `A5_CONTACT_AWARE`
- `A6_THREAD_AWARE_PRIORITY`

Use stable product IDs `P0_METADATA`, `P1_THUMBNAIL`, `P2_QUICKLOOK`, `P3_ROI`, and `P4_FULL`. Do not redefine IDs independently in code, model, figures, or paper. The [modeling plan](docs/MODELING_PLAN.md) explains the catalog and view conventions.

## Analysis discipline

Check simplified timing calculations before interpreting contact simulations. With sizes in bytes and rate in bits per second, processing saves simple transfer time when:

`T_proc,exposed < 8(D_raw - D_product) / R`, where `T_proc,exposed = max(0, T_proc - T_lead)`.

Contact access, interrupted transfer, product sufficiency, and terminal derivation can change the deadline outcome. Simulation precision is not physical validity. Distinguish local measurements, cited literature, public context, vendor inputs, analytical assumptions, and sensitivity only values using [assumptions](docs/ASSUMPTIONS.md).

Never tune inputs merely to make a candidate win or hide cases where it performs worse. The paper should identify conditional differences and access limits, not a universal winner. Every numerical claim must link to [current evidence](results/current/) or be marked not evaluated.

## Verification and results

Before using a calculation in the manuscript, run tests and invariants, check hand calculations, verify that bytes do not exceed contact capacity, inspect nonnegative state and missing completion handling, and confirm that figures regenerate from recorded data. Check model identifiers, relationships, candidate allocations, and generated view freshness. The [verification page](docs/V_AND_V.md) separates internal checks from operational validation.

Primary measures include time to first usable product, time to complete product, contact utilization, processing and transmission energy, peak storage, deadline outcome, and completeness. Each computed measure needs a unit test or invariant. Report only measures actually present in an evidence set.

## Parallel work

When agents work in parallel, divide responsibility among architecture and requirements, contact model, imagery benchmark, simulation, verification, and paper. One agent owns shared IDs and schemas. All agents should use the same [model catalog](model/) and [current evidence](results/current/). Claims of novelty need a real literature review with citations. A result claim must be checked against its source data.

## Review questions

For a meaningful change, check which requirement and paper claim it supports, whether a simpler implementation exists, where parameters came from, whether outputs are deterministic, whether tests cover it, and whether it changes an evidence result. Prefer focused commits with descriptive messages.

If a feature does not help answer the research question, verify the architecture, or produce a needed paper artifact, defer it.
