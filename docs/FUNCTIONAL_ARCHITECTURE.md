# Functional architecture

The logical model follows a request until the image becomes usable. It defines the work before assigning it to the provider or terminal. Function identifiers below point to the [model catalog](reference/MODEL_CATALOG.md), and the [generated activity view](reference/VIEWS.md) shows their order.

| Work | Input and output | Key condition |
|---|---|---|
| Task and collect (F-01, F-02) | Information need becomes a request; an orbital opportunity produces a scene. | No opportunity means no image to deliver. |
| Store and prepare (F-03, F-04) | The scene is retained and any selected smaller products are generated. | A product may finish processing before contact or remain unavailable during it. |
| Prioritize and transmit (F-05, F-06) | Available products are ordered and bytes use contact capacity. | The unfinished remainder stays with the collecting satellite. |
| Receive (F-07) | Bytes become either an incomplete stream or a complete product. | Partial bytes are not credited as an image. |
| Derive and make usable (F-08, F-09) | A complete full scene may yield a smaller view; a product is checked against the requested coverage and fidelity. | Terminal capability, derivation time, and deadline may prevent use. |
| Deliver to the user (F-10) | The usable view and its timing are recorded. | A late product remains a deadline miss. |

The usual path is request, collection, preparation, transmission, receipt, sufficiency check, and delivery. Terminal derivation occurs only for a suitable full scene. A missing prior image blocks a change conclusion even if the new image arrives. The [concept of operations](CONOPS.md) walks through these paths.

A product moves through planned, generated, partially received, completely received, and usable states. Completeness and usefulness are separate: a complete crop may fail a whole area need; a complete full scene may still require terminal processing. The [product state view](reference/VIEWS.md) records these transitions. [Candidate allocations](ALLOCATION_SPACE.md) assign the functions without changing their meaning.
