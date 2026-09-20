# Architecture Views

The system from several angles: who talks to whom, what happens in what
order, which function lives in which segment, how the code is organized, and
what physically connects. All views answer one question: how should imagery
functions be split between a commercial LEO provider and an Army-owned edge
terminal (`docs/DECISION_LOG.md` ADR-007). Everything here is notional.

Where to go next: `docs/FUNCTIONAL_ARCHITECTURE.md` (what each function
does), `docs/ALLOCATION_SPACE.md` (who owns each function, and the seven
candidate architectures), `docs/ARCHITECTURE.md` (inside the satellite),
`docs/INTERFACES.md` (what crosses the ownership boundary).

## System context

```mermaid
flowchart LR
    subgraph REQ["Army: requesting side"]
        User(["Tactical user"])
        Rear["Rear-echelon<br/>tasking cell"]
    end
    subgraph COM["Commercial provider: bought as a service"]
        Sat["LEO satellites<br/>collect, tier, prioritize, transmit"]
    end
    subgraph EDGE["Army: edge"]
        Term["Edge terminal<br/>vehicle or dismounted"]
    end
    User -->|"1 reachback request"| Rear
    Rear -->|"2 collection request"| Sat
    User -.->|"1b direct edge tasking"| Sat
    Sat ==>|"3 tiered product P0 to P4<br/>only in contact windows"| Term
    Term -->|"4 actionable product"| User
    classDef army fill:#dfeadf,stroke:#3b6b3b,color:#111
    classDef com fill:#dde7f5,stroke:#2f5a94,color:#111
    class User,Term,Rear army
    class Sat com
```

How to read it: green is Army-owned, blue is commercial. The thick arrow is
the ownership boundary and the only place the Army depends on a provider's
implementation. Everything the study varies (which tiers exist, in what
order they are sent, how a satellite decides) happens to the left of that
arrow; everything the terminal can do with what arrives happens to the right.

## Operational view

Actors: tactical user, rear-echelon tasking cell, commercial provider, Army
edge terminal (`docs/STAKEHOLDERS.md` says what each values).

### What each mission thread needs

Every thread walks the same function chain (`docs/FUNCTIONAL_ARCHITECTURE.md`)
and stops at a different point for "first actionable":

| Thread | First-needed product is ready when | Complete product |
|---|---|---|
| MT-1 cueing | P2 quicklook is processed, transmitted, received, exploited | Not required |
| MT-2 route recon | P3 ROI arrives and is exploited | P4 full scene arrives |
| MT-3 damage assessment | Change product from stored prior plus new collection | P4 full scene arrives |
| MT-4 persistent monitoring | P1 thumbnail arrives, repeated per pass | P4 when capacity allows |

### Event trace: MT-2 route reconnaissance, nominal case

```mermaid
sequenceDiagram
    participant User as Tactical user
    participant Rear as Tasking cell
    participant Sat as Satellite X
    participant Term as Edge terminal

    User->>Rear: request imagery of the area (reachback)
    Rear->>Sat: collection request
    Note over Rear,Sat: tasking delay, 60 s nominal
    Note over Sat: waits for its next pass over the area
    Sat->>Sat: collect at closest approach, process P3 ROI
    Note over Sat,Term: any of X's downlink windows still open can be used,<br/>including the rest of this pass
    Sat->>Term: transmit P3 ROI
    Term->>User: first-needed product delivered
    Note over User,Term: MT-2 success check: within 900 s of the request
    Sat->>Term: transmit P4 full, if capacity allows
    Term->>User: complete product delivered
```

**TFUP** (time to first useful product) is the time from the user's request
to the thread's first-needed tier arriving, including the tasking delay, the
wait for a collection pass, and the wait for a downlink window. **TCP** (time
to complete product) is the same for the complete product, and is `NaN` when
that product never arrives in the windows evaluated (`docs/DECISION_LOG.md`
ADR-008). `docs/MODEL_REFERENCE.md` has the exact accounting.

## Logical view: who owns which function

The function-to-segment allocation is drawn in `docs/ALLOCATION_SPACE.md`
(the ownership-boundary diagram) and tabulated in `docs/INTERFACES.md`. In
short, Task is shared with a rear-echelon cell, Collect through Transmit are
commercial, and Receive, Exploit, and Disseminate are Army.

The seven candidate architectures differ only in how the commercial side
processes and orders products. No architecture here moves any processing to
the Army edge; `docs/ALLOCATION_SPACE.md` lists that as a gap, not a finding.

Product tiers (`src/leo_edge/products.py`): P0 metadata, P1 thumbnail, P2
quicklook, P3 ROI, P4 full.

## Process view

### Progressive delivery (A4)

```mermaid
flowchart TD
    A["Capture scene"] --> B["Create P0 metadata"]
    B --> C["Process P1 thumbnail, then P2 quicklook"]
    C --> D["Queue P0 to P2 for the next contact"]
    D --> F["Contact window opens"]
    F --> G["Transmit tiers in priority order"]
    G --> H{"Tier finished<br/>in this window?"}
    H -->|"yes, more tiers and capacity left"| G
    H -->|"no, window ran out mid-tier"| I["Carry the remainder to the next window"]
    I --> F
    H -->|"P4 full finished"| J["Complete product delivered (TCP)"]
    G --> K{"First tier finished?"}
    K -->|"yes"| L["First useful product delivered (TFUP)"]
```

This mirrors `leo_edge.simulation.simulate_multi_contact`'s carry-forward
logic, not an idealized version of it.

### Adaptive policy (A5)

```mermaid
sequenceDiagram
    participant Policy as AdaptivePolicy
    participant Contact as Contact predictor
    participant Arch as Chosen architecture

    Policy->>Contact: predicted capacity in bytes
    Policy->>Policy: choose() using the margin rule
    Note over Policy: config/product_sizing.yaml, contact_aware.margin_alpha
    Policy->>Arch: instantiate and run()
    Arch-->>Policy: tfup_s, tcp_s, completed, fidelity
```

`AdaptivePolicy.choose()` returns a real architecture class, not a label
(`docs/DECISION_LOG.md` ADR-008).

## Development view

```mermaid
flowchart TD
    subgraph Model["src/leo_edge: the model"]
        arch["architecture.py, architectures.py, products.py"]
        sim["simulation.py: single-window and multi-contact delivery"]
        phys["link.py, power.py, storage.py, processing.py"]
        orbit["orbit/: access windows, Walker-delta constellations"]
        mt["mission_threads.py: thread tiers and tolerances"]
        stats["stats.py: paired bootstrap, Wilson, Kaplan-Meier"]
        pol["policies/adaptive.py"]
    end
    subgraph Exp["experiments/ and scripts/"]
        e07["e07: adaptive policy"]
        e11["e11: baseline mission-thread trials"]
        e12["e12: access sweep"]
        ts["trade_study.py"]
    end
    orbit --> e11
    phys --> sim
    pol --> e07
    arch --> sim
    sim --> e11
    mt --> e11
    stats --> e11
    e11 --> e12
    e11 --> ts
    e12 --> ts
```

`docs/EXPERIMENT_PLAN.md` lists every experiment and what it answers.

## Physical view

```mermaid
flowchart LR
    Rear["Rear-echelon<br/>tasking cell"]
    Term["Army edge terminal<br/>vehicle or dismounted"]
    subgraph SAT["Commercial satellite"]
        direction LR
        CAM["Imager"] --> CPU["Onboard CPU"] --> MEM["Flash storage"] --> TX["Transceiver"]
    end
    Rear -.->|"tasking (reachback)"| CPU
    Term -.->|"tasking (direct)"| CPU
    TX ==>|"RF, contact windows only"| Term
```

The dotted lines are tasking commands going up to the satellite; the thick
line is imagery coming down to the terminal.

Constraints that shape every result:

- Contact is intermittent and windowed. This dominates the mission-thread
  results (`docs/TRADE_STUDY.md`).
- Terminal class bounds downlink rate and edge compute, independently of
  which architecture the satellite runs (`docs/MISSION_THREADS.md`).
- Onboard energy is limited: `processing_energy_j` against `tx_energy_j`
  (`config/product_sizing.yaml`).
- `storage_peak_bytes` is limited and `contact_utilization` stays in [0, 1]
  (`docs/DECISION_LOG.md` ADR-008).

The single-window analytical check (`docs/HAND_CALC_BREAK_EVEN.md`) is
`T_proc + D_p/R < D_r/R`, equivalently `T_proc < (D_r - D_p)/R`.

## Keeping these views current

The requirement-to-test matrix lives in `docs/REQUIREMENTS.md`. These views
are maintained by hand; a change to architecture IDs, product tiers, or
metrics means updating this file, `docs/DATA_DICTIONARY.md`, and
`docs/ASSUMPTIONS.md` together.
