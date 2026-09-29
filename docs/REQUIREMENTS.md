# Requirements

These requirements describe what the notional service and interface would need to provide for a soldier using a generic Army-owned terminal. They are study criteria, with no Army doctrinal or contract status. The [assurance catalog](../model/assurance.yaml) holds each exact statement, rationale, status, and provenance; [generated traceability](reference/TRACEABILITY.md) lists its connections. “Proposed” means the behavior still needs to be checked for a candidate.

## System and interface obligations

| Soldier's information need | Requirement | How it is checked |
|---|---|---|
| See an early reduced image before the full scene when the candidate offers product tiers. | REQ-ALLOC-001 | Compare product generation and transmission order. |
| Know whether the request went directly to the provider or through a coordinator, and include the delay. | REQ-ALLOC-002 | Inspect request and route behavior; operational message path remains open. |
| Receive a whole-scene screening image within an assumed 120 seconds of request. | REQ-THREAD-001 | Check product coverage, receipt, and elapsed time in the rapid area update scenario. |
| Receive a native-resolution view of a declared corridor within an assumed 900 seconds. | REQ-THREAD-002 | Check crop sufficiency, receipt, and elapsed time in the corridor review scenario. |
| Know when no prior image is available to support a change product. | REQ-THREAD-003 | The real change product remains open; the current scenario uses a proxy. |
| Receive a thumbnail within an assumed 300 seconds of each collection. | REQ-THREAD-004 | Check collection-based timing and repeated misses. |
| Only receive credit for a derived view when terminal capability, fidelity, processing time, and deadline allow it. | REQ-TERM-001 | Test complete full scene receipt followed by derivation. |
| See each product's type, coverage, fidelity, and completion status. | REQ-IF-001 | Inspect the conceptual downlink fields; no operational format is implemented. |
| Retain partial-transfer status when a contact ends before delivery is complete. | REQ-IF-002 | Test byte carryover and inspect product identity and status. |

The timing thresholds are assumed case criteria. A synthetic request meeting one threshold says nothing about a real service's reliability. The catalog also records study obligations for paired comparisons, contact degradation, sample counts, and uncertainty intervals. Model integrity checks cover capacity, nonnegative state, censoring, product semantics, and deterministic replay. Those checks apply to the research model.

## One trace through the architecture

A soldier needs detail along a declared corridor. The corridor requirement sets a coverage and timing test. After collection, the service may crop the scene and send that product first. The terminal checks whether the crop covers the corridor. Raw scene delivery follows another path: the terminal receives the entire scene and then derives the crop. Both paths need the downlink interface to convey footprint and completeness. The verification case checks sufficiency and timing, while [current evidence](../results/current/) gives selected synthetic contact outcomes. Whether the soldier finds the crop useful remains untested.

The complete relation from this need to its scenario, functions, candidates, interface, measures, verification cases, and evidence is in the [traceability view](reference/TRACEABILITY.md). Open links remain marked there and in [engineering status](ENGINEERING_STATUS.md).
