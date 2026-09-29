# Interfaces

The service and terminal need to agree on what a request means and what has arrived. These conceptual information contracts define that exchange. They do not specify a radio protocol or an Army standard. The [model catalog](reference/MODEL_CATALOG.md) names the endpoints and identifiers; the [generated exchange view](reference/VIEWS.md) shows direction.

| Exchange | Information required for this study | Purpose |
|---|---|---|
| User request and tasking (I-REQUEST, I-TASK, I-DIRECT) | Request identity, synthetic area, coverage, needed product, assumed deadline, priority, and route. | Defines the need and starts the request clock. |
| Satellite downlink (I-DOWNLINK) | Collection and product identity, footprint, fidelity or encoding, byte count, and complete or partial state. | Lets the terminal decide what arrived and whether it might satisfy the request. |
| Provider status (I-STATUS) | Task acceptance, product readiness, and delivery progress or failure. | Keeps a missing or interrupted product visible. |
| User delivery (I-USER) | Complete usable view and arrival status. | Marks when the information need can be credited. |

The model has a direct tasking path and a path through an intermediate tasking node. The selected calculation includes an assumed delay for tasking. It does not exchange real messages along either path, so tasking interface verification remains open.

The downlink contract must distinguish a whole scene quicklook from a native resolution crop. It must also distinguish a complete image from a partial transfer. A full scene can support terminal derivation only when fidelity, terminal capability, processing time, and deadline allow it. The current fidelity check covers native spatial resolution; radiometric quality is outside the model.

Contact capacity equals duration times effective rate divided by eight, converting bits to bytes. Collection may occur during an open terminal contact; a later contact with the same satellite can carry the remaining bytes. [Requirements](REQUIREMENTS.md) states the interface obligations. [Verification](V_AND_V.md) separates capacity tests from inspection of the proposed fields.
