# Soldier information needs

Each scenario describes a generic soldier’s request at a tactical terminal. The areas and events are synthetic, and the time limits are study assumptions. Scenario identifiers connect the model, tests, and evidence. They are not Army mission names or requirements.

| Scenario | Soldier needs | Assumed time limit | When the study counts the product as sufficient |
|---|---|---|---|
| Whole-area update (MT-1) | A quick view covering the entire requested area. | 120 seconds from request. | A whole-scene quicklook or an eligible view derived from the full scene. A corridor crop does not cover the whole area. |
| Corridor detail (MT-2) | Native-resolution detail for a declared corridor. | 900 seconds from request; full-scene receipt is assessed separately at 3,600 seconds. | A crop covering the corridor or an eligible view derived from the full scene. |
| Compare with a prior image (MT-3) | A new image and, when available, a suitable earlier image. | 600 seconds from request when a prior exists; 900 seconds for review of the new image otherwise. | The calculation uses crop size as a proxy. It does not compare images or support a claim that a change was detected. |
| Repeated whole-area updates (MT-4) | A coarse view after each successive collection. | 300 seconds from each collection. | Independent opportunities for complete thumbnail delivery. Consecutive misses are recorded without a shared transfer budget. |

The products are metadata, a coarse whole-scene thumbnail, a reduced-resolution whole-scene quicklook, a native-resolution crop, and a full scene. They differ in coverage and detail. A corridor crop cannot satisfy a request for the whole area. A terminal can derive a smaller view from a full scene only after complete receipt, and only when its capability, the image detail, and remaining time allow it. The model assumes the declared crop covers the corridor; it does not check image geometry or interpret imagery. “Readable” means the terminal can present the complete product at its modeled tier. The study does not test whether a soldier can interpret it.

The comparison uses two generic terminals. The vehicle-mounted case assumes a receive rate of 50 megabits per second and 5 seconds to derive a smaller view. The dismounted case assumes 5 megabits per second and 30 seconds. These values support sensitivity analysis; they are not terminal specifications.

Nominal conditions use 60 seconds of tasking delay, with no rate reduction or denied contacts. The combined degraded case uses 180 seconds of delay, half the nominal rate, and a seeded 30 percent contact denial setting. These are study settings, not a fallback communications plan. When a link is unavailable, partial data wait for a later eligible contact. The request remains incomplete until a sufficient product arrives. The model generates collection opportunities and terminal contacts separately for each satellite. [Concept of operations](CONOPS.md) describes the sequence; [assumptions](ASSUMPTIONS.md) lists the sources for inputs.
