# Research Design

## Central research question

Under intermittent LEO contact and spacecraft power/size/weight constraints, when should geospatial imagery be processed onboard a COTS-heavy small satellite rather than transmitted for processing at a local ground terminal?

## The design principle behind every experiment

The study does not ask "which architecture is best?" It asks "under what conditions does each architecture become advantageous?" The output is a set of transition boundaries, not a single winner. That's why `figures/fig04.png`, the regime map, is the central figure: it shows which architecture wins across a grid of downlink rate and contact duration, not a single best answer.

## Supporting questions

- **Processing placement**: how do onboard compute time, compute power, storage, downlink rate, and contact duration change the relative performance of raw downlink, compressed downlink, quicklook-first delivery, ROI-first delivery, and adaptive delivery?
- **Progressive delivery**: can a progressive-product architecture reduce time to first useful product without materially increasing time to complete product or spacecraft energy use?
- **Direct-to-edge**: how does a direct local ground terminal change the preferred processing placement compared with routing through a centralized processing chain first?
- **Adaptive policy**: can a simple rule-based, contact-aware policy stay close to the best static architecture as conditions change?
- **Transition boundaries**: where exactly does onboard processing start helping, stop helping, or get bottlenecked by compute energy or storage instead of downlink capacity?

## Working hypotheses

These are testable, not conclusions, and the experiments are allowed to reject any of them.

1. When contact capacity is much larger than image volume, extra onboard processing gives little latency benefit and may cost more energy than it saves.
2. When contact capacity is comparable to or smaller than image volume, onboard compression or progressive products reduce time to first useful product.
3. Quicklook-first delivery often reduces user-visible latency more effectively than trying to fully process the final product onboard.
4. Under short or uncertain contacts, a contact-aware hybrid scheduler outperforms any single fixed delivery policy across more of the design space.
5. At high downlink rates, ground-processing speed matters more than onboard compute capability.
6. At low downlink rates, the value of onboard data reduction keeps rising until processing energy or processing delay offsets the transmission savings.

## What the results actually showed

See `paper/manuscript.md` for the full write-up. In short: quicklook-first delivery dominates most of the low-to-mid rate range, compressed full-frame delivery wins at high rates where transmission is cheap enough that onboard processing delay just gets in the way, and the fully progressive architecture only pulls ahead at the lowest rate combined with the longest contact durations.
