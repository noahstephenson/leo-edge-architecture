# Analysis model reference

The analysis checks whether a product can be prepared, transmitted, and made usable under the study's assumptions. The [assumptions page](ASSUMPTIONS.md) identifies input sources, and the [current configuration](../results/current/config.json) gives exact values.

## Timing and contact

A contact lasting `duration` seconds at `rate` bits per second can carry at most `duration × rate / 8` bytes in this model. A denied contact carries none. Remaining bytes carry to a later contact with the same collecting satellite. A tier receives a completion time only after all its bytes arrive.

The [hand calculation](HAND_CALC_BREAK_EVEN.md) compares processing time exposed to the user with transfer time saved. The contact model also accounts for separate collection and terminal access, same pass delivery, multiple contacts, tasking delay, and terminal derivation.

## Usable product

For each request, the model finds the earliest complete product with sufficient coverage and fidelity. A whole scene quicklook covers the requested scene at reduced resolution. A native resolution crop covers only its declared region. A complete full scene may let the terminal derive either view, subject to terminal capability, native spatial resolution, processing time, and deadline. The model does not test radiometric quality or user interpretation.

A late product remains a deadline miss. A partially received product is never usable. The repeated update scenario measures each collection separately. The [scenarios](MISSION_THREADS.md) define clocks and needs; [verification](V_AND_V.md) lists the logic and reproducibility checks.

The broader library computes processing and transmission energy, peak storage, and utilization. The selected comparative evidence does not report those measures, so this study draws no resource claim from its result files.
