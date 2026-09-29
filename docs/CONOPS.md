# Concept of operations

## Soldier’s view

A soldier at a generic Army-owned terminal requests imagery of a synthetic area. The request states the area, the kind of view needed, and the time limit. It can go through a generic tasking coordinator or directly to the commercial service, depending on the scenario.

A satellite collects the scene, stores it, and prepares the products required by its assigned architecture. It sends data when it can contact the terminal. Collection and transmission may occur during the same pass. A short contact can stop before a product is complete. The satellite keeps the remaining bytes for a later contact.

The terminal counts a product as complete after all its bytes arrive. It then checks whether the product covers the requested area and meets the assumed detail level. A terminal may derive a smaller view from a full scene when its modeled capability and the remaining time allow it.

The soldier needs to distinguish a request that is still pending from a partial transfer, a complete product, a late arrival, and a request with no product available by the limit. The model represents these delivery states; it does not test a soldier interface. Partial data remain incomplete. If contact is lost, the study carries the remaining bytes to the next eligible contact. Previously received imagery may be identified, but the study does not treat it as a replacement for the requested image. Without a complete, sufficient product, the request remains unmet.

The [delivery sequence](reference/VIEWS.md) shows the request, collection, transmission, receipt, and presentation. [Functional architecture](FUNCTIONAL_ARCHITECTURE.md) defines the work before assigning it to an owner. [Candidate allocations](ALLOCATION_SPACE.md) describe how the assignments and product order vary.

## Paths the model must handle

| Path | What the study records |
|---|---|
| Timely delivery | A complete product meets the assumed coverage and detail before the time limit. |
| Interrupted contact | Remaining bytes carry to another eligible contact; the product stays incomplete until all bytes arrive. |
| No contact or missed limit | No sufficient product is available in time. Previously received imagery does not count as a replacement. |
| Missing prior image | A new image may arrive, but the study cannot credit a change conclusion without a suitable prior. |

The [four scenarios](MISSION_THREADS.md) represent different soldier requests and time limits. Their product value is an assumption; no soldier or operator study establishes it. The model does not interpret imagery or describe a real Army procedure.
