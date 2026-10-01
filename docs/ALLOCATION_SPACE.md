# Candidate allocations

All seven candidates share the same service boundary. The commercial service tasks and collects a scene. The collecting satellite stores and sends it, and the Army owned terminal receives the data. The terminal may then derive or present a usable view. The candidates differ in which products the satellite prepares, what it sends first, and how long the terminal waits for a complete scene.

| Candidate | What the satellite prepares and sends | What the terminal may do |
|---|---|---|
| Raw scene first (A0) | Sends the full raw scene. | Derives a requested smaller view after complete receipt, if capable and in time. |
| Compressed scene (A1) | Sends one compressed full scene. | May derive a smaller view if the required fidelity is retained. |
| Quicklook first (A2) | Sends a small whole scene preview, then the full scene. | Uses the preview for a whole area need or waits for the scene. |
| Crop first (A3) | Sends a native resolution crop of the declared area, then the full scene. | Uses the crop only if it covers the requested area. |
| Progressive delivery (A4) | Sends metadata, thumbnail, quicklook, crop, and full scene in fixed order. | Uses the first complete product that satisfies the need. |
| Contact aware full scene (A5) | Chooses raw or compressed full scene using an assumed contact margin rule. | May derive a smaller view after complete receipt. |
| Need aware priority (A6) | Prepares the progressive product set but moves the needed tier earlier. | Uses the first complete, sufficient product. |

The names in parentheses are stable catalog and code identifiers. The [generated catalog](reference/MODEL_CATALOG.md) records each function allocation, product, and ordering rule. [Interfaces](INTERFACES.md) identifies what crosses the provider and terminal boundary.

A corridor crop shows detail in part of the scene; a quicklook shows the whole scene at reduced resolution. The crop cannot stand in for a whole scene preview, even if its product number is higher. After receiving a full scene, the terminal may still need time to derive the requested smaller view. The [product verification](V_AND_V.md) tests these rules, which also shape the [trade study](TRADE_STUDY.md).

The comparison leaves provider hardware, terminal power and mass, real image quality, crosslinks, and actual tasking authority open. It is an allocation study, not a detailed implementation design.

Tasking and collection ownership are held fixed in the evaluated alternatives. The tested allocation choice concerns where a needed view is prepared: by the provider before transmission, or by an eligible terminal after complete full-scene receipt. Candidate execution modes describe this choice even where common function owners remain unchanged. The broader research question also covers responsibilities that this bounded experiment does not vary.

The [packaged sizing configuration](../src/leo_edge/product_sizing.yaml) gives A2/A3/A4/A6 common scene-relative quicklook and crop sizes. A6 sends metadata, then the requested product, then remaining products in catalog order. It retains an unfinished product instead of skipping to a smaller one. Priority between competing requests is not evaluated.
