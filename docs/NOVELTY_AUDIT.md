# Novelty Audit

This project does not claim to invent onboard image compression, Earth-observation edge computing, direct-to-Earth downlink, or region-of-interest transmission. Those are established ideas. What this project contributes is the combination and the result.

## What this project actually contributes

**A joint model, not a single technique.** Most treatments of "process onboard or downlink raw" look at one variable in isolation, usually compression ratio. This project models contact geometry, onboard compute time and energy, product size, storage, downlink capacity, and ground processing together, and asks where the crossover points are. That's what `figures/fig04.png` shows directly: a map of which architecture wins across a grid of downlink rate and contact duration, not a single number.

**A progressive, direct-to-edge product architecture.** Instead of one product decision per scene, `A4_PROGRESSIVE` sends metadata, thumbnail, quicklook, ROI, and full product in that order, adapting to whatever contact capacity is actually available, with no requirement to route through a centralized ground station first.

**A reproducible pipeline built on real measurements.** The image-processing timing and compression numbers in this repo come from actually running Pillow JPEG, resize, and crop operations, not from an assumed compression ratio pulled from a paper. The contact windows come from a real SGP4 orbit propagation (Skyfield), not a made-up arrival distribution. Every number in the results traces back to a script anyone can rerun.

## What the result actually says

The headline result is not "onboard processing wins" or "raw downlink wins." It's a set of transition boundaries: quicklook-first delivery wins across most of the low-to-mid downlink rate range, compressed full-frame delivery wins once the rate is high enough that transmission is cheap and processing delay just gets in the way, and the fully progressive architecture only wins at the lowest rate combined with the longest contact durations, where even a small first product matters most. See `paper/manuscript.md` for the full result with real numbers.

## Scope of this claim

This is a simulation and benchmarking study, not a flight-qualified system, and no formal literature review was carried out as part of this project. The contribution claim above rests on this project's own model and its own measured results, not on a comparison against prior published work.
