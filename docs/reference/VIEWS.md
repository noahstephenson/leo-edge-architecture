# Model views

> Generated from the `model/` catalogs. View purposes are organized around Lenny Delligatti's *SysML Distilled*, Chapters 3–12; [modeling conventions](../MODELING_PLAN.md) record the semantic mapping and sources. Diagrams show readable names; stable IDs remain in node keys and reference tables. These Mermaid views are analogues, not formal SysML diagrams.

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
    n_REQ_THREAD_002 -.->|need trace| n_N_02
    n_REQ_THREAD_002 -.->|constrains| n_F_09
    n_N_02 -.->|evaluated by| n_M_DEADLINE
    n_V_TIMING -.->|verify| n_REQ_THREAD_002
    n_F_09 -.->|allocate| n_E_TERMINAL
    n_A3_ROI_FIRST -.->|candidate for| n_REQ_THREAD_002
    n_A3_ROI_FIRST -.->|uses interface| n_I_DOWNLINK
    n_V_TIMING -.->|supports claim| n_CL_005
```

## Soldier-facing use cases

**Question:** Which services does the imagery delivery system provide to the soldier?

This black-box view places the soldier outside the named system subject and shows the two services the soldier uses. It omits internal behavior and does not imply operational capability.

```mermaid
flowchart LR
    n_E_USER["Soldier (external actor)"]
    subgraph use_case_subject ["Imagery delivery system"]
        n_UC_REQUEST(["Request imagery"])
        n_UC_RECEIVE(["Receive product or delivery status"])
    end
    n_E_USER ---|association| n_UC_REQUEST
    n_E_USER ---|association| n_UC_RECEIVE
```

## Logical delivery activity

**Question:** What happens from request to usable imagery?

Arrows show a successful product path, not data-object flow or the engine's repeated transfer loop. The decision chooses direct sufficiency or required terminal derivation; the merge accepts either path without waiting for both. Failed paths appear in the lifecycle view. Candidate preparation and transmission can overlap across products; this coarse activity does not impose a batch barrier. Allocation is shown separately.

```mermaid
flowchart TB
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
    n_CTRL_DERIVE{"Requested view needs terminal derivation?"}
    n_CTRL_MERGE{" "}
    n_F_01 --> n_F_02
    n_F_02 --> n_F_03
    n_F_03 --> n_F_04
    n_F_04 --> n_F_05
    n_F_05 --> n_F_06
    n_F_06 --> n_F_07
    n_F_07 -->|"complete product"| n_CTRL_DERIVE
    n_CTRL_DERIVE -->|"[derivation needed and eligible full scene]"| n_F_08
    n_CTRL_DERIVE -->|"[sufficient as received]"| n_CTRL_MERGE
    n_F_08 -->|"sufficient derived view"| n_CTRL_MERGE
    n_CTRL_MERGE -->|"check deadline"| n_F_09
    n_F_09 --> n_F_10
```

## Function allocation

**Question:** Which system element performs each function?

Each grouped list names individual functions with the same owner. Its dashed allocation dependency applies to every listed function and points to the receiving element. All candidates inherit these owners; candidate execution modes and the individual allocation records remain in the catalog.

```mermaid
flowchart LR
    group_n_E_TASKING["F-01 Task"]
    n_E_TASKING["Tasking path"]
    group_n_E_TASKING -.->|allocate| n_E_TASKING
    group_n_E_SATELLITE["F-02 Collect<br/>F-03 Store<br/>F-04 Generate product<br/>F-05 Prioritize<br/>F-06 Transmit"]
    n_E_SATELLITE["Commercial LEO satellite"]
    group_n_E_SATELLITE -.->|allocate| n_E_SATELLITE
    group_n_E_TERMINAL["F-07 Receive<br/>F-08 Derive at terminal<br/>F-09 Make usable<br/>F-10 Disseminate"]
    n_E_TERMINAL["Army-owned tactical terminal"]
    group_n_E_TERMINAL -.->|allocate| n_E_TERMINAL
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
    n_E_SYSTEM *-- n_E_PROVIDER : part
    n_E_SYSTEM *-- n_E_TASKING : part
    n_E_SYSTEM *-- n_E_TERMINAL : part
    n_E_PROVIDER *-- n_E_SATELLITE : part
```

## Provider–terminal interfaces

**Question:** What information crosses each interface?

This internal-block analogue scopes the participating parts within the system of interest and leaves the user outside. Arrows describe item-flow direction, with interface IDs and exchange names. The full fields remain in the [interface inventory](MODEL_CATALOG.md#interfaces). Ports, typed part properties, multiplicities, and protocols are not specified.

```mermaid
flowchart TB
    subgraph delivery_system ["Imagery delivery system"]
        n_E_PROVIDER["Commercial imagery service"]
        n_E_SATELLITE["Commercial LEO satellite"]
        n_E_TERMINAL["Army-owned tactical terminal"]
        n_E_TASKING["Tasking path"]
    end
    n_E_USER["Imagery user"]
    n_E_TERMINAL -->|"I-REQUEST: Reachback imagery request"| n_E_TASKING
    n_E_TERMINAL -->|"I-DIRECT: Direct imagery request"| n_E_PROVIDER
    n_E_TASKING -->|"I-TASK: Collection task"| n_E_PROVIDER
    n_E_SATELLITE -->|"I-DOWNLINK: Product downlink"| n_E_TERMINAL
    n_E_PROVIDER -->|"I-STATUS: Delivery status"| n_E_TERMINAL
    n_E_TERMINAL -->|"I-USER: Imagery product or status"| n_E_USER
```

## Delivery sequence

**Question:** When do collection, contact, and terminal derivation occur?

Remote exchanges use solid open-arrow signal notation; self calls use filled arrows. Dashed replies are reserved for an explicitly modeled return. Product availability and conditional terminal derivation occur within the contact loop, before the candidate sequence necessarily ends. Message routes and status delivery are conceptual obligations, not simulated transport behavior.

```mermaid
sequenceDiagram
    participant U as Soldier
    participant T as Army tactical<br/>terminal
    participant R as Reachback tasking<br/>path
    participant P as Commercial<br/>provider
    participant S as Collecting<br/>satellite
    U-)T: Submit request
    alt Reachback tasking
    T-)R: Route imagery request
    R-)P: Send collection task
    else Direct tasking
    T-)P: Request imagery directly
    end
    P-)S: Task collection and<br/>product preparation
    S->>S: Collect scene
    S->>S: Prepare candidate products<br/>as needed
    Note over S,T: Collection and downlink may occur in one pass
    loop Available contacts until<br/>complete or censored
    S-)T: Send product bytes and<br/>completeness
    opt Product receipt complete
    opt Derivation needed and eligible
    T->>T: Derive requested view
    end
    T-)U: Present sufficient product<br/>or product status
    end
    end
    Note over S,T: Terminal derivation does not pause provider transfer#59;<br/>usable availability can precede sequence completion
    P-)T: Report final availability<br/>or delivery status
    T-)U: Present final delivery or<br/>failure status
```

## Product state

**Question:** How can delivery progress or fail?

This lifecycle combines product transfer states with request-level outcomes. Guard aliases: prior_ok means any required prior condition is met; direct_ok means sufficient as received; derive_ok means derivation is needed and eligible; timely and late refer to the request deadline. Full guard expressions remain in the system catalog. Choices separate direct sufficiency, derivation, and failure. Timing events and executable priorities are unspecified. MissingPrior and FallbackScene are conceptual obligations, not a change algorithm.

```mermaid
stateDiagram-v2
    state AssessReceipt <<choice>>
    state AssessDerived <<choice>>
    [*] --> Requested
    Requested --> Collected: [access and collection]
    Requested --> Unserved: [no collection before<br/>horizon]
    Collected --> Ready: [product generated or<br/>raw retained]
    Ready --> Partial: [contact carries some<br/>bytes]
    Partial --> Partial: [next contact carries<br/>more bytes]
    Ready --> Ready: [contact interrupted or<br/>denied]
    Partial --> Partial: [contact interrupted#59;<br/>bytes retained]
    Ready --> Received: [whole product in one<br/>contact]
    Partial --> Received: [remaining bytes<br/>delivered]
    Received --> AssessReceipt
    AssessReceipt --> Derived: [prior_ok and derive_ok]
    AssessReceipt --> Usable: [prior_ok and direct_ok<br/>and timely]
    Derived --> AssessDerived
    AssessDerived --> Usable: [sufficient and timely]
    Ready --> Censored: [evaluation horizon<br/>ends]
    Partial --> Censored: [evaluation horizon<br/>ends]
    AssessReceipt --> Late: [prior_ok and direct_ok<br/>and late]
    AssessReceipt --> Insufficient: [prior_ok and not<br/>direct_ok and not<br/>derive_ok]
    AssessReceipt --> MissingPrior: [change requested<br/>without prior<br/>reference]
    AssessDerived --> Insufficient: [coverage or fidelity<br/>inadequate]
    AssessDerived --> Late: [sufficient and late]
    MissingPrior --> FallbackScene: [new scene only#59; no<br/>change product]
    Usable --> [*]
    Censored --> [*]
    Insufficient --> [*]
    Late --> [*]
    FallbackScene --> [*]
    Unserved --> [*]
```

## Corridor product state

**Question:** How is the fresh corridor request assessed?

This manuscript view omits prior-reference branches, since the corridor request needs a new scene. It inherits the delivery and assessment transitions with compact guard labels; named outcomes end this assessment, with final-node connectors omitted. Direct means sufficient as received; derive_ok means needed and eligible terminal derivation; no sufficient path means neither direct sufficiency nor eligible derivation. Timely and late refer to the request deadline. The full guards remain in Product state and the system catalog.

```mermaid
stateDiagram-v2
    state AssessReceipt <<choice>>
    state AssessDerived <<choice>>
    [*] --> Requested
    Requested --> Collected: [collection]
    Requested --> Unserved: [no collection]
    Collected --> Ready: [product ready]
    Ready --> Partial: [partial bytes]
    Partial --> Partial: [more bytes]
    Ready --> Ready: [interrupted / denied]
    Partial --> Partial: [interrupted#59; retained]
    Ready --> Received: [complete]
    Partial --> Received: [complete]
    Received --> AssessReceipt
    AssessReceipt --> Derived: [derive_ok]
    AssessReceipt --> Usable: [direct, timely]
    Derived --> AssessDerived
    AssessDerived --> Usable: [sufficient, timely]
    Ready --> Censored: [horizon ends]
    Partial --> Censored: [horizon ends]
    AssessReceipt --> Late: [direct, late]
    AssessReceipt --> Insufficient: [no sufficient path]
    AssessDerived --> Insufficient: [insufficient]
    AssessDerived --> Late: [sufficient, late]
```

## Parametric timing constraint

**Question:** When can product reduction save exposed delivery time?

Rectangles stand for value properties and hexagons for constraint properties, which are usages of constraint definitions. Undirected bindings equate each value with the named constraint parameter; they do not show calculation order. Parameter ports and constraint types are omitted in this analogue. Sizes are bytes and rates are bits per second. The first-order crossover is separate from the contact simulation.

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
