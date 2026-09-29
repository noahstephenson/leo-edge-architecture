# Model views

> Generated from the `model/` catalogs. Diagram purposes and relationship conventions follow Lenny Delligatti's *SysML Distilled*, Chapters 3–12. Diagrams show readable names; stable IDs remain in node keys and reference tables. These Mermaid views are analogues, not formal SysML diagrams.

## Need-to-evidence trace

**Question:** How does one notional need reach candidate, interface, and bounded evidence?

The corridor-detail need connects to a proposed requirement, responsible behavior, an alternative, and a bounded simulation claim. The selected comparison cites its trial and summary files in [Model catalog](MODEL_CATALOG.md). Full relationship inventory: [Traceability](TRACEABILITY.md).

```mermaid
flowchart LR
    n_REQ_THREAD_002["Corridor view within 900 seconds"]
    n_N_02["Native-resolution corridor view"]
    n_F_09["Make usable"]
    n_M_DEADLINE["Deadline met"]
    n_V_TIMING["Request-to-product timing"]
    n_E_TERMINAL["Army-owned tactical terminal"]
    n_A3_ROI_FIRST["Corridor crop first"]
    n_I_DOWNLINK["Product downlink"]
    n_CL_005["Selected comparative outcome"]
    n_REQ_THREAD_002 -.->|derived from| n_N_02
    n_REQ_THREAD_002 -.->|constrains| n_F_09
    n_N_02 -.->|evaluated by| n_M_DEADLINE
    n_V_TIMING -.->|verify| n_REQ_THREAD_002
    n_F_09 -.->|allocate| n_E_TERMINAL
    n_A3_ROI_FIRST -.->|candidate for| n_REQ_THREAD_002
    n_A3_ROI_FIRST -.->|uses interface| n_I_DOWNLINK
    n_V_TIMING -.->|supports claim| n_CL_005
```

## Logical delivery activity

**Question:** What happens from request to usable imagery?

Arrows show control sequencing and guarded alternatives, not data-object flow. This logical view does not assign behaviors to parts; the separate allocation view shows that relationship. Incomplete or late delivery is represented in the product-state view.

```mermaid
flowchart LR
    n_F_01["Task"]
    n_F_02["Collect"]
    n_F_03["Store"]
    n_F_04["Generate product"]
    n_F_05["Prioritize"]
    n_F_06["Transmit"]
    n_F_07["Receive"]
    n_F_08["Derive at terminal"]
    n_F_09["Make usable"]
    n_F_10["Disseminate"]
    n_F_01 -->|precedes| n_F_02
    n_F_02 -->|precedes| n_F_03
    n_F_03 -->|precedes| n_F_04
    n_F_04 -->|precedes| n_F_05
    n_F_05 -->|precedes| n_F_06
    n_F_06 -->|precedes| n_F_07
    n_F_07 -->|if full scene and capable| n_F_08
    n_F_07 -->|if sufficient as received| n_F_09
    n_F_08 -->|if sufficient and timely| n_F_09
    n_F_09 -->|precedes| n_F_10
```

## Function allocation

**Question:** Which system element performs each function?

Dashed allocation dependencies point from behavior to the receiving system element, following SysML allocation direction. All candidates currently inherit the same element allocations; their execution modes differ in the catalog.

```mermaid
flowchart LR
    subgraph behavior ["Functions"]
        n_F_01["Task"]
        n_F_02["Collect"]
        n_F_03["Store"]
        n_F_04["Generate product"]
        n_F_05["Prioritize"]
        n_F_06["Transmit"]
        n_F_07["Receive"]
        n_F_08["Derive at terminal"]
        n_F_09["Make usable"]
        n_F_10["Disseminate"]
    end
    subgraph structure_parts ["System elements"]
        n_E_SYSTEM["Imagery delivery system of interest"]
        n_E_PROVIDER["Commercial imagery service"]
        n_E_TASKING["Tasking path"]
        n_E_SATELLITE["Commercial LEO satellite"]
        n_E_TERMINAL["Army-owned tactical terminal"]
    end
    n_F_01 -.->|allocate| n_E_TASKING
    n_F_02 -.->|allocate| n_E_SATELLITE
    n_F_03 -.->|allocate| n_E_SATELLITE
    n_F_04 -.->|allocate| n_E_SATELLITE
    n_F_05 -.->|allocate| n_E_SATELLITE
    n_F_06 -.->|allocate| n_E_SATELLITE
    n_F_07 -.->|allocate| n_E_TERMINAL
    n_F_08 -.->|allocate| n_E_TERMINAL
    n_F_09 -.->|allocate| n_E_TERMINAL
    n_F_10 -.->|allocate| n_E_TERMINAL
```

## System structure

**Question:** Which physical and organizational elements participate?

This block-definition view uses composition to show parts contained by the system and provider. The soldier-facing user is external to the system boundary.

```mermaid
classDiagram
    class n_E_SYSTEM["«block» Imagery delivery system of interest"]
    class n_E_PROVIDER["«block» Commercial imagery service"]
    class n_E_TASKING["«block» Tasking path"]
    class n_E_SATELLITE["«block» Commercial LEO satellite"]
    class n_E_TERMINAL["«block» Army-owned tactical terminal"]
    class n_E_USER["Imagery user (external user)"]
    n_E_SYSTEM *-- n_E_PROVIDER : part
    n_E_SYSTEM *-- n_E_TASKING : part
    n_E_SYSTEM *-- n_E_TERMINAL : part
    n_E_PROVIDER *-- n_E_SATELLITE : part
```

## Provider–terminal interfaces

**Question:** What information crosses each interface?

This internal-block view shows connected parts and labels each connector with the information exchanged. Interface records define the exchange contract; the interface itself is not shown as a transmitted item.

```mermaid
flowchart LR
    subgraph provider_boundary ["Commercial service"]
        n_E_PROVIDER["Commercial imagery service"]
        n_E_SATELLITE["Commercial LEO satellite"]
    end
    subgraph army_segment ["Army tactical edge segment"]
        n_E_TERMINAL["Army-owned tactical terminal"]
    end
    subgraph tasking_route ["Tasking route; ownership not modeled"]
        n_E_TASKING["Tasking path"]
    end
    n_E_USER["Imagery user"]
    n_E_TERMINAL -->|I-REQUEST item flow: request identifier, area of interest, needed product, deadline| n_E_TASKING
    n_E_TERMINAL -->|I-DIRECT item flow: request identifier, area of interest, needed product, deadline| n_E_PROVIDER
    n_E_TASKING -->|I-TASK item flow: provider task and status| n_E_PROVIDER
    n_E_SATELLITE -->|I-DOWNLINK item flow: collection and product identifiers, tier, coverage, fidelity, bytes, completeness or partial-transfer state, provenance| n_E_TERMINAL
    n_E_PROVIDER -->|I-STATUS item flow: availability, completeness, and failure status| n_E_TERMINAL
    n_E_TERMINAL -->|I-USER item flow: product and explicit utility caveat| n_E_USER
```

## Delivery sequence

**Question:** When do collection, contact, and terminal derivation occur?

The sequence allows same-pass delivery and byte carryover; it does not claim every request succeeds.

```mermaid
sequenceDiagram
    participant U as Soldier
    participant T as Army tactical terminal
    participant R as Reachback tasking path
    participant P as Commercial provider
    participant S as Collecting satellite
    U->>T: Submit request
    alt Reachback tasking
    T->>R: Route imagery request
    R->>P: Send collection task
    else Direct tasking
    T->>P: Request imagery directly
    end
    P->>S: Task collection and product preparation
    S->>S: Collect scene and prepare selected products
    Note over S,T: Collection and downlink may occur in one pass
    loop Available contacts until complete or censored
    S-->>T: Send product bytes and completeness
    end
    P-->>T: Report availability or delivery status
    opt Full scene received and terminal capable
    T->>T: Derive requested view
    end
    T-->>U: Present usable product or failure status
```

## Product state

**Question:** How can delivery progress or fail?

A product is usable only after complete delivery and any required terminal derivation.

```mermaid
stateDiagram-v2
    [*] --> Requested
    Requested --> Collected: access and collection
    Requested --> Unserved: no collection before horizon
    Collected --> Ready: product generated or raw retained
    Ready --> Partial: contact carries some bytes
    Partial --> Partial: next contact carries more bytes
    Ready --> Ready: contact interrupted or denied
    Partial --> Partial: contact interrupted; bytes retained
    Ready --> Received: whole product in one contact
    Partial --> Received: remaining bytes delivered
    Received --> Derived: full scene and capable terminal
    Received --> Usable: sufficient and within deadline
    Derived --> Usable: sufficient and within deadline
    Ready --> Censored: evaluation horizon ends
    Partial --> Censored: evaluation horizon ends
    Received --> Late: complete after deadline
    Received --> Insufficient: coverage or fidelity inadequate
    Received --> MissingPrior: change requested without prior reference
    Derived --> Insufficient: coverage or fidelity inadequate
    Derived --> Late: completed after deadline
    MissingPrior --> FallbackScene: new scene only; no change product
    Usable --> [*]
    Censored --> [*]
    Insufficient --> [*]
    Late --> [*]
    FallbackScene --> [*]
    Unserved --> [*]
```

## Parametric timing constraint

**Question:** When can product reduction save exposed delivery time?

In this Mermaid analogue, rectangular nodes stand for value properties, hexagons stand for constraint blocks, and undirected labeled lines stand for binding connectors. The view does not encode SysML parameter directions or a formal constraint model. Sizes are bytes, rates are bits per second, and the factor of 8 converts bytes to bits. This is a first-order crossover model, not the full contact simulation.

```mermaid
flowchart LR
    lead["T_lead [s]: processing completed before contact"]
    proc["T_proc [s]: total processing time"]
    raw["D_raw [byte]: full-scene data size"]
    product["D_product [byte]: reduced-product data size"]
    rate["R [bit/s]: downlink rate"]
    exposed["T_exposed [s]: processing that delays transmission"]
    saved["T_saved [s]: transmission time saved"]
    earlier["Earlier product? [Boolean]"]
    c_exposed{{"C1: T_exposed = max(0, T_proc - T_lead)"}}
    c_saved{{"C2: T_saved = 8*(D_raw - D_product) / R"}}
    c_compare{{"C3: Earlier if T_exposed < T_saved"}}
    proc ---|bind T_proc| c_exposed
    lead ---|bind T_lead| c_exposed
    c_exposed ---|bind T_exposed| exposed
    raw ---|bind D_raw| c_saved
    product ---|bind D_product| c_saved
    rate ---|bind R| c_saved
    c_saved ---|bind T_saved| saved
    exposed ---|bind T_exposed| c_compare
    saved ---|bind T_saved| c_compare
    c_compare ---|bind Earlier| earlier
```

## Candidate product order: Raw full scene with terminal derivation

**Question:** Which products does Raw full scene with terminal derivation prioritize?

This flow view communicates product order, not activity control flow or functional allocation. Labeled arrows mean transmission priority. The model catalog defines each candidate's complete allocations and execution modes.

```mermaid
flowchart LR
    start["Raw full scene with terminal derivation"]
    terminal["Terminal receives each completed tier"]
    step0["Full scene"]
    start -->|candidate transmits| step0
    step0 -->|complete downlink| terminal
```

## Candidate product order: Progressive tiers

**Question:** Which products does Progressive tiers prioritize?

This flow view communicates product order, not activity control flow or functional allocation. Labeled arrows mean transmission priority. The model catalog defines each candidate's complete allocations and execution modes.

```mermaid
flowchart LR
    start["Progressive tiers"]
    terminal["Terminal receives each completed tier"]
    step0["Metadata"]
    start -->|candidate rule| step0
    step0 -->|complete downlink| terminal
    step1["Thumbnail"]
    step0 -->|transmits before| step1
    step1 -->|complete downlink| terminal
    step2["Quicklook"]
    step1 -->|transmits before| step2
    step2 -->|complete downlink| terminal
    step3["Region of interest"]
    step2 -->|transmits before| step3
    step3 -->|complete downlink| terminal
    step4["Full scene"]
    step3 -->|transmits before| step4
    step4 -->|complete downlink| terminal
```

## Candidate encoding choice: Contact-aware full delivery

**Question:** How does contact margin choose full-scene encoding?

This flow view shows the conditional encoding choice and following transfer. It is not an activity control-flow or functional-allocation diagram. The model catalog defines the full candidate behavior.

```mermaid
flowchart LR
    start["Contact-aware full delivery"]
    choice["Contact margin selects compressed or raw full"]
    full["Full scene"]
    terminal["Terminal receives complete full scene"]
    start -->|selects encoding| choice
    choice -->|prepares| full
    full -->|complete downlink| terminal
```

## Candidate product order: Thread-aware priority

**Question:** Which products does Thread-aware priority prioritize?

This flow view communicates product order, not activity control flow or functional allocation. Labeled arrows mean transmission priority. The model catalog defines each candidate's complete allocations and execution modes.

```mermaid
flowchart LR
    start["Thread-aware priority"]
    terminal["Terminal receives each completed tier"]
    step0["Metadata"]
    start -->|candidate rule| step0
    step0 -->|complete downlink| terminal
    step1["Scenario requested tier"]
    step0 -->|transmits before| step1
    step1 -->|complete downlink| terminal
    step2["Remaining progressive tiers"]
    step1 -->|transmits before| step2
    step2 -->|complete downlink| terminal
```
