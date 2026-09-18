# Direct-to-Edge Processing Placement for a COTS LEO Small Satellite

## Abstract

A small satellite in low Earth orbit only has a few minutes of contact with a ground terminal at a time, and the downlink rate during that contact can vary by two orders of magnitude depending on the mission's radio and terminal. This raises a basic systems-architecture question: should the satellite spend its own limited compute time and energy processing an image before sending it down, or should it send the raw scene and let the ground terminal do the work? We build a reproducible model of six imagery-delivery architectures, from raw downlink to a progressive metadata-thumbnail-quicklook-ROI-full pipeline, and evaluate them across a grid of downlink rates (1 to 100 Mbps) and contact durations (120 to 600 seconds), using processing and compression numbers measured from real image-processing benchmarks rather than assumed constants. The result is not a single best architecture. Quicklook-first delivery gives the lowest time-to-complete-product across most of the rate/duration grid we tested. Compressing the full image before transmission only wins once the downlink is fast enough that transmission is cheap and the fixed cost of onboard processing stops paying for itself, which in our model happens above about 25 Mbps. The fully staged progressive architecture wins only at the lowest rate and longest contact duration we tested, where even a small early product is worth more than the time spent producing anything larger. Onboard compression can also lose outright: at low rates the satellite is transmission-limited either way, so paying processing time for a smaller product buys nothing.

## Introduction

A satellite that can send a usable image to the ground faster, without sacrificing the full-resolution product later, is more useful to a time-sensitive user in the field. The question is where to do the processing. A ground terminal can be far more powerful than anything that fits on a small, power- and weight-constrained (SWaP-constrained) spacecraft, but it can only work with what the satellite actually downlinks, and downlink time is scarce: contact windows are short and intermittent, and available data rate depends on the specific link and terminal in use.

This project treats that as a systems-architecture problem, not a compression-algorithm problem. We define six architectures that each make a different decision about how much processing happens onboard before transmission, wrap them in a shared timing and energy model, and run that model against real measured processing costs and real orbital contact geometry.

## Background

**Contact geometry.** A satellite in low Earth orbit is visible to a given ground terminal for a few short windows a day, typically a few minutes each, whenever its ground track passes near the terminal above a minimum elevation angle. We generate these windows with a real SGP4 orbit propagation (the Skyfield library) rather than assuming an arrival distribution, and confirm they land in a realistic range: over a one-week horizon for a representative low-inclination-crossing orbit and mid-latitude terminal, we get windows from about 30 to 420 seconds (`figures/fig06.png`).

**Direct-to-edge delivery.** Instead of routing every product through a centralized ground station and processing center, this project assumes the satellite can downlink straight to a local or mobile ground terminal during any contact window. That removes network hops from the critical path but also means the satellite, not a data center, decides what to send first.

**Product tiers.** Rather than treating "the image" as one indivisible file, we model five product tiers a satellite can generate: metadata, thumbnail, quicklook, a region-of-interest (ROI) crop, and the full-resolution scene. An architecture's job is deciding which of these tiers to produce, in what order, and how much onboard processing time and energy that costs. See `docs/CONOPS.md` for the full tier definitions.

**Scope.** All orbit and contact geometry in this study is generated from a synthetic circular orbit propagated with a real SGP4 model, not from a flown mission's actual telemetry, and all imagery is public or synthetic. That's a deliberate design choice for a first-order architecture study: contact-window statistics from a synthetic orbit are realistic enough to compare architectures against each other, without needing operational mission data this project has no reason to depend on.

## Reference Architecture

The base system is a satellite bus carrying a payload (imager), an onboard processor, mass memory, and a downlink radio, communicating with a ground terminal that can do its own additional processing. `docs/ARCHITECTURE.md` and `docs/ARCHITECTURE_VIEWS.md` give the full block diagrams, sequence diagrams, and 4+1 view set; `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` gives the operational (DoDAF-style) view, including the OV-1 concept graphic.

We compare six architectures, implemented in `src/leo_edge/architectures.py`:

- **A0 Ground-only**: no onboard processing, transmit the raw scene.
- **A1 Compressed-full**: compress the scene onboard (to 30% of raw size in this model), then transmit.
- **A2 Quicklook-first**: transmit a small quicklook (2% of raw size) first, then the full scene if contact capacity allows.
- **A3 ROI-first**: transmit a region-of-interest crop (10% of raw size) first, then the full scene if capacity allows.
- **A4 Progressive**: transmit metadata, thumbnail, quicklook, ROI, and full scene in that order, filling as much of the contact window as capacity permits.
- **A5 Contact-aware**: a rule-based policy that only processes onboard if it can finish with a safety margin before contact ends, otherwise falls back to raw transmission.

## Model

The core timing relationship is the break-even condition between processing onboard and sending raw:

```
T_proc + D_p / R < D_r / R
```

which rearranges to a break-even downlink rate `R* = (D_r - D_p) / T_proc`, where `T_proc` is onboard processing time, `D_r` is raw scene size, `D_p` is the processed product size, and `R` is downlink rate. Each architecture's `run()` method computes closed-form time-to-first-useful-product (TFUP), time-to-complete-product (TCP), and energy from scene size, contact capacity, downlink rate, and processing time. Processing time and compression ratios for the quicklook and ROI benchmarks come from `src/leo_edge/imagery/benchmark.py`, which runs real Pillow JPEG compression, resize, and crop operations rather than assuming a compression ratio. `docs/ASSUMPTIONS.md` lists every numeric input to the model and whether it's measured, computed from a real geometric model, or a stated design assumption.

## Verification

`uv run pytest` runs the full test suite (36 tests covering metrics, link/contact-capacity math, storage and power invariants, the scheduler, the queue, and every static architecture). `docs/V_AND_V.md` lists the invariants the model enforces (storage and battery state never go negative, transmitted bytes never exceed contact capacity, TFUP and TCP are never negative, and so on) and how each is enforced in code.

We also checked the simulation's timing model by hand. `paper/hand_calc_break_even.md` works the break-even formula for the nominal e03 scene (1.0 GB raw, 0.3 GB compressed, 20 s processing) and gets `R* = 280` Mbps: above that rate, in the pure closed-form model, compressing before sending stops being worth it. The actual simulated crossover, from `e03_results.csv`, is lower, between 10 and 25 Mbps: at 10 Mbps CompressedFull's TFUP is 260 s against GroundOnly's 300 s, and at 25 Mbps it's 116 s against 300 s. The two agree in direction (compression helps as rate rises) but not in magnitude, because the closed-form formula doesn't account for the contact window's fixed capacity limit or partial-scene transmission, both of which the simulation does model.

## Results

**The core result is a regime map, not a single winner.** `figures/fig04.png` shows which architecture gives the lowest time-to-complete-product across a grid of downlink rate (1 to 100 Mbps) and contact duration (120 to 600 s), computed directly from the same simulation code as every other result in this project. Three regions appear:

- **Quicklook-first (A2)** wins across almost the entire middle of the grid, from 5 Mbps up through 25 to 50 Mbps depending on contact duration.
- **Compressed-full (A1)** wins at the highest rates, generally 50 to 100 Mbps, extending down to 25 Mbps for the two longest contact durations we tested (420 and 600 s), where transmission is cheap enough that onboard processing delay stops paying for itself.
- **Progressive (A4)** only wins at the single lowest rate (1 Mbps) combined with the two longest contact durations (420 and 600 s) we tested, where its near-instant metadata/thumbnail product is worth more than the time any larger product would take to arrive.

**Time-to-first-useful-product tells a different story than time-to-complete-product.** Looking at `e03_results.csv` directly: for TFUP rather than TCP, Progressive wins at the two lowest rates (1 and 5 Mbps, TFUP of about 20.2 s and 20.0 s) because its first product is tiny and transmits almost instantly regardless of rate, while Quicklook-first wins from 10 Mbps up (TFUP falling from 18.0 s at 10 Mbps to 3.6 s at 100 Mbps). Which architecture is "best" genuinely depends on whether the mission cares about getting something useful fast or getting the complete product fast.

**Onboard processing can lose outright at low rates.** At 1 Mbps, CompressedFull's TFUP is 320.0 s, worse than GroundOnly's 300.0 s. At that rate the contact window is the binding constraint for both architectures (only 37.5 MB fits in a 300 s contact either way), so paying 20 s of processing time to shrink the product buys nothing: the transmission is capacity-limited regardless of product size.

**Energy and latency don't always trade off against each other.** `figures/fig05.png` plots processing energy against TFUP for every architecture and rate in the sweep. GroundOnly and QuicklookFirst cluster in the low-energy region (0 and about 30 J respectively) but span a wide range of TFUP depending on rate, while CompressedFull and RoiFirst sit at a fixed 300 J regardless of rate, since processing time (and therefore processing energy) doesn't depend on downlink rate in this model.

## Discussion

The transition conditions matter more than any single number. In this model, quicklook-first delivery is the safe default across most realistic downlink rates: it produces a usable product almost immediately and rarely loses on time-to-complete-product either, since the model tries to fit the full scene in afterward whenever capacity allows. Full-scene compression only becomes worthwhile once the link is fast enough that raw transmission time stops dominating, which for the assumed 30% compression ratio and 20 s processing time happens somewhere between 10 and 25 Mbps. The fully staged progressive architecture is the most consistent performer on time-to-first-product across every rate we tested, because its first product's size barely depends on the link, but that consistency costs it the time-to-complete-product race everywhere except the lowest-rate, longest-contact corner of the grid.

The scope of what this shows should stay narrow: it's a first-order model built on real image-processing benchmarks and a real SGP4 contact-window generator, but the specific power draws (15 W processing, 25 W radio) and compression ratios (30% for compressed-full, 2% for quicklook, 10% for ROI) in `docs/ASSUMPTIONS.md` are design assumptions for a representative COTS smallsat, not measurements from a flown mission. The transition boundaries would shift with different hardware, but the underlying pattern, that the best architecture depends on downlink rate and which latency metric matters, should hold generally.

## Conclusion

Processing-placement decisions for a LEO small satellite are not a single yes-or-no question. This project's architecture-level evaluation shows where each of six delivery strategies wins and loses across downlink rate and contact duration, using a model grounded in real image-processing measurements and real orbital contact geometry. The practical takeaway for a systems engineer choosing a delivery architecture is: default to quicklook-first unless the link is consistently fast (above roughly 25 Mbps in this model), in which case full-scene compression is simpler and just as fast, and only reach for a fully staged progressive pipeline when contacts are both slow and long enough that an early, tiny product is worth more than a faster complete one.
