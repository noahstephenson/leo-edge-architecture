# AGENTS.md

## Purpose

This file provides repository-level instructions for OpenCode, coding agents, review agents, and human contributors working on the LEO Edge Architecture research project.

Read this file before making changes.

## Mission

Build a reproducible systems-engineering research repository that evaluates how imagery functions should be allocated between a commercial LEO space segment and an Army-owned tactical edge segment. Everything operational is notional and unofficial; this repository does not represent an Army requirement, program, or acquisition decision. See `docs/OPERATIONAL_CONTEXT.md`.

The repository must connect:

**operational need → stakeholder value → requirement → function → allocation → experiment → trade study → acquisition implication**

Every major code feature should trace to that chain. See `docs/REQUIREMENTS.md` for the traceability matrix this chain is checked against.

## Highest-priority research question

> How should imagery functions (tasking, collection, processing, prioritization, delivery) be allocated between a commercial LEO space segment acquired as a service and an Army-owned tactical edge segment, and how does the preferred allocation shift across mission needs, terminal classes, and contested or DDIL conditions?

This question replaces the repository's original one (onboard vs. ground processing placement, preserved for history in `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md`); the pivot is recorded in `docs/DECISION_LOG.md` ADR-007, per this file's own governance rule below, which is why it was safe to change here.

Do not silently change this question again.

If results suggest a different question is stronger, document the proposed pivot in `docs/DECISION_LOG.md` before changing the design.

## Non-negotiable scope boundaries

Do not build:

- target recognition;
- target tracking;
- weapon cueing;
- strike support;
- classified workflows;
- real Army tactical collection plans;
- real operational terminal locations;
- offensive cyber capability;
- detailed orbital warfare scenarios.

Use public civilian imagery, synthetic mission requests, generic ground terminals, generic data-rate sweeps, and public technical literature.

## Repository quality rules

All code should be:

- deterministic when seeded;
- typed where practical;
- configuration-driven;
- modular;
- testable;
- documented;
- reproducible from a clean clone.

Avoid:

- notebook-only logic;
- hidden constants;
- magic numbers;
- giant scripts;
- state scattered across modules;
- unversioned result files;
- manual editing of generated data;
- figures created outside scripted pipelines.

## Preferred package layout

```text
src/leo_edge/
    architecture.py
    architectures.py
    mission.py
    products.py
    processing.py
    queues.py
    scheduler.py
    power.py
    storage.py
    link.py
    metrics.py
    metrics_arch.py
    analysis.py
    simulation.py
    orbit/
    imagery/
    policies/
```

Do not create a deep hierarchy until needed. Every module here should be imported by at least one experiment or test; delete anything that isn't.

## Build sequence

See `docs/PROJECT_ROADMAP.md` for what's actually built and how the pieces connect. The build order that got us here:

1. analytical timing model;
2. contact generator;
3. image benchmark;
4. static architectures;
5. first architecture crossover;
6. only then queues and adaptive logic.

Do not start with F Prime, cFS, Basilisk, a GUI, an SDR, or a constellation.

## Architecture alternatives

Use these IDs consistently:

- `A0_GROUND_ONLY`
- `A1_COMPRESSED_FULL`
- `A2_QUICKLOOK_FIRST`
- `A3_ROI_FIRST`
- `A4_PROGRESSIVE`
- `A5_CONTACT_AWARE`

Do not rename them casually because experiments, figures, and paper text will depend on them.

## Product tiers

Use these IDs:

- `P0_METADATA`
- `P1_THUMBNAIL`
- `P2_QUICKLOOK`
- `P3_ROI`
- `P4_FULL`

## Primary metrics

Implement these first:

- `tfup_s`
- `tcp_s`
- `contact_utilization`
- `processing_energy_j`
- `tx_energy_j`
- `storage_peak_bytes`
- `deadline_met`
- `product_completeness`

Every metric must have a unit test or invariant.

## Analytical baseline

The basic latency break-even relation is:

\[
T_{proc} + \frac{D_p}{R} < \frac{D_r}{R}
\]

or equivalently:

\[
T_{proc} < \frac{D_r-D_p}{R}
\]

where:

- \(T_{proc}\) is processing time;
- \(D_r\) is raw data size;
- \(D_p\) is processed data size;
- \(R\) is downlink rate.

If processing can occur before contact, use effective exposed processing time:

\[
T_{proc,exposed} = \max(0,T_{proc}-T_{lead})
\]

and compare that to the transmission time saved.

Simulation results should be checked against this first-order model.

## Validation mindset

Simulation precision is not physical validity.

A million runs do not rescue bad assumptions.

The repository must clearly distinguish:

- measured parameters;
- literature parameters;
- NASA SmallSat SoA parameters;
- public Army motivation;
- vendor parameters;
- analytical assumptions;
- sensitivity-only values.

Use the source labels defined in `docs/ASSUMPTIONS.md`.

## Testing requirements

Before freezing manuscript results:

- all unit tests pass;
- all scientific invariants pass;
- hand-check cases match;
- no transmitted bytes exceed contact capacity;
- no negative storage or battery states;
- TFUP and TCP semantics are verified;
- figures regenerate from frozen data.

## Result discipline

Never tune parameters just to make an architecture win.

Never hide cases where onboard processing performs worse.

The paper should identify **transition conditions**, not announce a universal winner.

## Agent workstreams

When parallel agents are available, divide work by responsibility.

### Agent A: Novelty and result claims
Own:
- `docs/NOVELTY.md`
- checking every claim in `docs/TRADE_STUDY.md` and `docs/ACQUISITION_IMPLICATIONS.md` against a real number in `results/frozen/v2/`

No claim should depend on a literature comparison unless a real literature review has actually been done and recorded with real citations, per `docs/NOVELTY.md`. `paper/manuscript.md` reflects the retired v1 research question (`docs/DECISION_LOG.md` ADR-005, ADR-007) and is not owned by this workstream going forward.

### Agent B: Architecture and requirements
Own:
- system architecture
- interfaces
- requirements
- traceability

### Agent C: Orbit and contact model
Own:
- Skyfield/SGP4 wrapper
- access windows
- contact validation

### Agent D: Image processing benchmark
Own:
- public imagery ingest
- compression/resize/tile benchmark
- benchmark result schema

### Agent E: Simulation
Own:
- products
- queues
- policies
- contact replay
- metrics

### Agent F: V&V
Own:
- unit tests
- invariants
- hand calculations
- result reproducibility

### Agent G: Paper and figures
Own:
- figure scripts
- paper outline
- number audit
- result freeze

Agents must not independently redefine shared IDs, schemas, or research questions.

## Code review questions

Before merging a meaningful change, ask:

1. Which research requirement does this support?
2. Which experiment needs it?
3. Is there a simpler implementation?
4. Is the parameter source clear?
5. Is the output deterministic?
6. Is there a test?
7. Could it alter a paper result?
8. Is the change documented?

## Commit style

Prefer focused commits:

```text
Add synthetic LEO contact-window generator
Benchmark quicklook processing on public imagery
Implement progressive product queue
Add contact-capacity invariants
Freeze AeroConf baseline experiment configuration
```

Avoid:
- `updates`
- `fix stuff`
- giant multi-feature commits.

## Stop rule

If a feature does not help answer the research question, validate the architecture, or produce a required paper artifact, defer it.
