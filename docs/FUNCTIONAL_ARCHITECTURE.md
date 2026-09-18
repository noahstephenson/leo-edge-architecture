# Functional Architecture

The end-to-end imagery service decomposed into functions, independent of
which segment (commercial space, Army edge, or a rear-echelon node)
performs each one. `docs/ALLOCATION_SPACE.md` is where these functions get
assigned to segments; this document only says what each function does and
what it needs from its neighbors.

## Functions

1. **Task**: turn a user need into a collection request against a specific
   area of interest, with a priority and a mission-thread context
   attached. Produces: a tasking request. Consumes: user need, tasking-path
   choice (reachback or direct edge, `docs/MISSION_THREADS.md`).
2. **Collect**: acquire raw sensor data over the tasked area. Produces: raw
   scene bytes. Consumes: a tasking request, an orbital collection
   opportunity.
3. **Store**: retain raw and processed products until they can be
   transmitted, and retain prior-reference imagery for change-detection
   threads (MT-3). Produces: retrievable products. Consumes: raw scene
   bytes, processed products, storage capacity.
4. **Process (tiered)**: derive a reduced-fidelity or full-fidelity product
   from the raw scene. Five tiers, from `src/leo_edge/products.py`:
   - P0 metadata: lossless, no image content, generation time and
     location only.
   - P1 thumbnail: lossy, coarse.
   - P2 quicklook: lossy, reduced resolution.
   - P3 ROI: lossy, full resolution but cropped to a region of interest.
   - P4 full: the complete scene, lossy (compressed) or lossless (raw),
     depending on architecture.
   Produces: a product at some tier. Consumes: raw scene bytes, processing
   time, processing energy.
5. **Prioritize**: decide which product, among what's queued, goes out
   next given remaining contact capacity. Produces: an ordered delivery
   queue. Consumes: queued products, contact-capacity estimate, mission-
   thread priority.
6. **Transmit**: send bytes over the downlink during a contact window.
   Produces: bytes delivered. Consumes: prioritized queue, contact window
   (start, duration, rate), possibly degraded by contested conditions.
7. **Receive**: the edge terminal's radio receiving the downlink.
   Produces: received bytes. Consumes: transmitted bytes, terminal class
   (affects nothing about receipt itself, but affects what happens next).
8. **Exploit**: turn received bytes into something the user can act on
   (render an image, run change detection against a stored prior,
   assemble a route-corridor mosaic). Produces: an actionable product.
   Consumes: received bytes, terminal edge-compute capability (a
   dismounted terminal may not be able to exploit a partial or tiered
   product the way a vehicle-mounted one can), stored prior reference (for
   MT-3).
9. **Disseminate**: deliver the actionable product to the user at the
   edge terminal. Produces: mission-thread success/failure determination.
   Consumes: an actionable product, the thread's latency tolerance and
   fidelity floor.

## Function dependency order

Task -> Collect -> {Process, Store} -> Prioritize -> Transmit -> Receive ->
Exploit -> Disseminate, with Store also feeding Exploit directly for
change-detection threads (a stored prior reference, not something that
comes down the downlink again).

## Why this decomposition, not a bigger one

This list stops at the granularity the simulation actually models. Finer
decomposition (e.g., splitting Transmit into modulation, coding, and RF
stages) would add detail with no corresponding parameter or metric in
`src/leo_edge/`, which is exactly the kind of complexity
`docs/RESEARCH_DESIGN.md`'s undergrad-scope principle rules out.
