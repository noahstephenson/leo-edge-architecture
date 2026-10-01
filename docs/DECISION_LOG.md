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

## ADR-031: Bound the architecture evidence without changing the question

On September 30, 2026, the author selected a technically modest system architecture study. Tasking and collection owners remain fixed; the evaluated choice is provider preparation and product order versus eligible terminal derivation. This tests part of the existing research question without asserting an optimized allocation of every function.

Principal delivery claims use one requesting terminal. Four-site cases assume one connected logical receiver with instantaneous sharing; they do not establish delivery to an isolated terminal. Repeated collections remain independent opportunity tests with no shared capacity reservation. A forwarding simulator and competing-request scheduler are outside this study.

## ADR-032: Share product assumptions and transfer accounting

The packaged [product configuration](../src/leo_edge/product_sizing.yaml) is authoritative for candidate sizing, processing fractions, power bookkeeping, and contact margin. Quicklooks and crops use 2% and 5% of scene bytes across A2/A3/A4/A6. Metadata and thumbnails retain fixed sizes. This corrects a previous decimal MB versus binary MiB difference; it is not input tuning to favor an alternative.

Single-contact calls now adapt the multi-contact engine. Each product retains its byte progress and ordering across contacts. Completeness is received bytes divided by that encoded product's target bytes. Full-scene receipt differs from completion of the candidate sequence. Constant-power energy bookkeeping is available to callers; resource feasibility and peak storage remain unevaluated.

## ADR-033: Preserve the baseline and close the research workflow

The [historical baseline](../results/history/pre-completion-2026-09-30/) preserves the pre-correction evidence. Current evidence records exact claim filters, paired differences, a baseline comparison, full-scene receipt, product progress, and bounded sensitivities. Elevation remains a collection proxy. Sampling and geometry sensitivities qualify the result rather than establish orbital accuracy.

Unsupported imagery inputs and unused resource/scheduling helpers were removed. The optional image benchmark generates a synthetic gradient and records the execution machine and processing boundary. It does not calibrate the study. Catalog-backed manuscript diagrams, frozen dependency checks, and independent regeneration replace manual copies and hash-only assurance. Final literature synthesis, venue formatting, and author submission review remain manuscript work.

## ADR-034: Position the contribution against established work

On September 30, 2026, the author requested an in-depth review of the manuscript argument and literature. The [source synthesis](reference/LITERATURE.md) establishes precedents for requirements-linked simulation, product-specific latency, onboard products, download scheduling, and interrupted delivery. The contribution is a traceable application and conditional comparison. No first-of-its-kind method, scheduling algorithm, or transport protocol is claimed.

The manuscript now states the original research question verbatim and distinguishes it from the evaluated preparation and delivery subset. It separates request latency, complete receipt, sufficient availability, and full-scene receipt. Progressive candidates send separate products; byte carryover is an idealized transfer abstraction. Paired intervals and conditional latency are interpreted within sampled requests, and contrasting examples do not isolate constellation size. These are clarifications of the existing model and evidence, without changed candidate behavior or numerical results. Venue preparation and author submission review remain open.

## ADR-035: Keep SysML view semantics consistent

On September 30, 2026, the author requested a focused Delligatti and SysML pass to reduce later model rework. The [modeling conventions](MODELING_PLAN.md#sysml-interpretation-and-view-consistency) now distinguish project-specific traces from SysML relationships and design intent from verification evidence. Candidates participate in study evaluations; they do not themselves satisfy the obligation to conduct those evaluations. The catalog now repeats the original research question verbatim.

The activity uses explicit decision and merge nodes. The sequence places sufficient-product receipt and conditional derivation within the transfer loop and distinguishes information signals from replies. Lifecycle choices separate direct sufficiency, derivation, and failure; the missing-prior branch remains conceptual. The interface contract includes delivery failure status. Generated manuscript diagrams and captions follow those meanings. Automated checks protect ownership, relationship endpoints, branch structure, and binding roles. The changes clarify the existing candidate implementation, without adding transport behavior or a formal SysML tool dependency. Evidence is regenerated because catalog hashes changed.

## ADR-036: Review the manuscript at reading size

On September 30, 2026, the author requested a rendered manuscript review and a committed repository milestone. The optional [renderer](../paper/render/README.md) uses pinned Node dependencies to produce a Letter-size reading copy. Real Mermaid rendering found unquoted activity guards and semicolons that the earlier restricted grammar check had accepted. The generator now quotes guards and encodes statement separators. CI parses all generated reference diagrams and renders the manuscript, retaining its reading copy as an artifact.

Compact interface labels refer to the full field inventory. Grouped allocation lists retain each function ID and its common owner. The manuscript lifecycle follows the fresh corridor request, with compact guards and named outcomes; it is generated from the same catalog transitions. The full lifecycle retains final-node connections and conceptual prior-reference branches. These presentation choices reduce crowded diagrams without changing allocation or transfer behavior.

The manuscript now embeds the principal figure, all-miss counterexample, and sensitivity figure with source filters in their captions. Larger plot fonts remain readable at page width. The draft abstract reports the corrected conditional findings and sensitivity limitation, while the submitted abstract is unchanged. Prose revisions preserve the request-to-receipt argument and distinguish the delivery finding from interface responsibility. Numerical evidence is unchanged; figures are regenerated from the independently reproduced data. Venue formatting and author submission approval remain open.
