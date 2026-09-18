# ARCHITECTURE

System architecture for LEO edge processing placement and progressive direct-to-edge imagery delivery.

## Overview

The architecture models a COTS-heavy small satellite with onboard processing, mass memory, and a radio downlink communicating with a generic ground terminal. Processing placement decisions are governed by contact windows and product tier prioritization.

## Block Definition Diagram

Logical blocks and key ports.

```mermaid
classDiagram
    class SatelliteBus {
        <<Block>>
        + powerPort : Power
        + dataPort : DataBus
        + commPort : RF
    }
    class Payload {
        <<Block>>
        + imagePort : Image
        + ctrlPort : Cmd
    }
    class OnboardProcessor {
        <<Block>>
        + procInPort : Image
        + procOutPort : Product
        + memPort : DataBus
    }
    class MassMemory {
        <<Block>>
        + storePort : DataBus
        + retrievePort : DataBus
    }
    class Downlink {
        <<Block>>
        + txPort : RF
        + dataInPort : DataBus
    }
    class GroundTerminal {
        <<Block>>
        + rxPort : RF
        + procPort : DataBus
    }

    SatelliteBus *-- Payload : contains
    SatelliteBus *-- OnboardProcessor : contains
    SatelliteBus *-- MassMemory : contains
    SatelliteBus *-- Downlink : contains
    Downlink --> GroundTerminal : communicates with
```

## Internal Block Diagram

Data flows for product tiers between onboard elements.

```mermaid
graph LR
    subgraph Satellite
        OP[Onboard Processor]
        MM[Mass Memory]
        Radio[Radio / Downlink]
    end
    Ground[Ground Terminal]

    OP -->|Metadata P0| MM
    OP -->|Thumbnail P1| MM
    OP -->|Quicklook P2| MM
    OP -->|ROI P3| MM
    OP -->|Full P4| MM

    MM -->|Metadata| Radio
    MM -->|Thumbnail| Radio
    MM -->|Quicklook| Radio
    MM -->|ROI| Radio
    MM -->|Full| Radio

    Radio --> Ground
```

## Activity Diagram

Progressive delivery pipeline with Contact-Aware policy decisions.

```mermaid
flowchart TD
    Start([Image Captured])
    Start --> Acquire
    Acquire --> GenerateProducts
    GenerateProducts --> CheckContact
    CheckContact -->|Contact imminent| Prioritize
    CheckContact -->|No contact| Store
    Prioritize --> SelectTier
    SelectTier -->|P0 Metadata| Transmit
    SelectTier -->|P1 Thumbnail| Transmit
    SelectTier -->|P2 Quicklook| Transmit
    SelectTier -->|P3 ROI| Transmit
    SelectTier -->|P4 Full| Queue
    Store --> WaitContact
    WaitContact --> ContactArrived
    ContactArrived --> Prioritize
    Queue --> WaitContact
    Transmit --> Ack
    Ack -->|Ack received| Done([Delivered])
    Ack -->|No ack| Store
    Done --> End([End])
```

## State Machine

ProductQueue lifecycle.

```mermaid
stateDiagram-v2
    [*] --> queued
    queued --> processing : start processing
    processing --> stored : processing complete
    stored --> transmitting : contact available and policy permits
    transmitting --> delivered : ack received
    transmitting --> stored : contact lost
    stored --> queued : reprioritize
    delivered --> [*]
```
