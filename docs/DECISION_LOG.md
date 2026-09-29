# Decision log

This file records decisions that changed the study. The [model catalogs](../model/) hold current definitions; this log gives the reasons for them. Git history retains earlier calculations and prose.

## ADR-007: Study the service boundary

The research question covers tasking, collection, preparation, prioritization, and delivery between a commercial imagery service and an Army owned terminal. Earlier work focused on processor placement. The exact question and scope boundaries are in [AGENTS.md](../AGENTS.md).

## ADR-019 and ADR-024: Propagate each satellite and check source data

Each synthetic constellation member has its own orbit and access windows. A previous phase-shift approximation and a source-data column error produced misleading access claims. Those claims were withdrawn. The current contact model propagates satellites individually and keeps collection and terminal locations separate.

## ADR-020: Permit delivery during the collection pass

If terminal contact remains open after collection, the collecting satellite can use the time left in that pass. Unsent bytes carry to later eligible contacts with the same satellite. This allows the model to test same pass delivery.

## ADR-026: Use a structured conceptual model

The project applies selected conceptual-design guidance from [NASA-HDBK-1009A](https://standards.nasa.gov/system/files/tmp/2025-03-12-NASA-HDBK-1009A.pdf) at the scope documented in the modeling plan. Four small catalogs define elements and typed relationships. Generated Mermaid diagrams and tables provide readable views; they are not formal SysML files or NASA-approved products.

## ADR-027: Define sufficiency by the information need

Product number alone does not establish usefulness. A native resolution crop leaves part of the scene unseen, so it does not meet a whole scene preview need. A delivered full scene supports a derived view only after complete receipt and eligible terminal processing, with adequate spatial fidelity and time. Radiometric quality and user interpretation remain open.

## ADR-029: Keep supporting calculations auditable

The selected analysis uses paired synthetic requests and records its configuration, source hashes, output files, and audit in [current evidence](../results/current/). A number in the paper must connect to a specific case and its assumptions. Internal model verification must not be described as operational validation.

## ADR-030: Keep one active reading path

The [README](../README.md) leads from the service boundary through needs, requirements, functions, allocations, interfaces, and verification. The manuscript follows the same structure. The author requested one active evidence set and a shorter reading path. Git history can retain the provenance of removed drafts and results.
