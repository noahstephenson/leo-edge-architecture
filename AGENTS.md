# AGENTS.md

## Purpose

This file provides repository-level instructions for OpenCode, coding agents, review agents, and human contributors working on the LEO Edge Architecture research project.

Read this file before making changes.

## Mission

Build a reproducible systems-engineering research repository that can support an IEEE Aerospace Conference paper on processing placement and progressive direct-to-edge imagery delivery for a COTS-heavy LEO small-satellite system.

The repository must connect:

**operational need → architecture → requirements → model → experiment → figure → paper claim**

Every major code feature should trace to that chain.

## Highest-priority research question

> Under intermittent LEO contact and spacecraft SWaP constraints, when should geospatial imagery be processed onboard a COTS-heavy small satellite rather than transmitted for processing at a local ground terminal?

Do not silently change this question.

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
- `docs/NOVELTY_AUDIT.md`
- checking every claim in `paper/manuscript.md` against a real number in `results/frozen/v1/`

No claim in the paper should depend on a literature comparison unless a real literature review has actually been done and recorded. See `docs/DECISION_LOG.md` (ADR-005).

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
