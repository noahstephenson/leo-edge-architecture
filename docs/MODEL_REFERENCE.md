# Analysis model reference

The analysis checks whether a product can be prepared, transmitted, and made usable under the study's assumptions. The [assumptions page](ASSUMPTIONS.md) identifies input sources, and the [current configuration](../results/current/config.json) gives exact values.

## Timing and contact

A contact lasting `duration` seconds at `rate` bits per second can carry at most `duration × rate / 8` bytes in this model. A denied contact carries none. Remaining bytes carry to a later contact with the same collecting satellite. A tier receives a completion time only after all its bytes arrive.

The [hand calculation](HAND_CALC_BREAK_EVEN.md) compares processing time exposed to the user with transfer time saved. The contact model also accounts for separate collection and terminal access, same pass delivery, multiple contacts, tasking delay, and terminal derivation.

## Usable product

For each request, the model finds the earliest complete product with sufficient coverage and fidelity. A whole scene quicklook covers the requested scene at reduced resolution. A native resolution crop covers only its declared region. A complete full scene may let the terminal derive either view, subject to terminal capability, native spatial resolution, processing time, and deadline. The model does not test radiometric quality or user interpretation.

A late product remains a deadline miss. A partially received product is never usable. The repeated update scenario measures each collection separately and does not reserve contact capacity across collections. Its cadence results describe independent delivery opportunities, not a shared stream of queued images. The [scenarios](MISSION_THREADS.md) define clocks and needs; [verification](V_AND_V.md) lists the logic and reproducibility checks.

For multiple terminal sites, the selected runner merges their contact windows into one logical receiver per satellite. It carries byte progress across that merged schedule. This assumes received bytes are available to a shared receiver without intersite delay or disruption. The model does not deliver bytes from a remote receiving site to the requesting terminal. Four-site results therefore require this additional assumption, especially when interpreting degraded conditions.

The single-contact interface adapts the same engine as multi-contact transfer. Invalid rates, scene sizes, processing times, or unordered/overlapping contacts are rejected. Empty contact lists mean no delivery. Individual product records retain target bytes, received bytes, completeness, and completion time. Full receipt of a compressed product has completeness one; incomplete bytes do not satisfy a need.

Selected evidence reports request-to-collection delay, product arrival, terminal derivation, sufficient availability, full-scene receipt, byte progress, transmitted bytes, and contact utilization. Full-scene receipt is the completion of P4, including the compressed encoding for A1, and is separate from completion of every offered tier. The 3,600-second criterion uses request-to-P4-receipt time. Energy uses constant assumed powers in the compatibility API but is outside selected evidence claims. Peak storage is not evaluated.
