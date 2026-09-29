# Architecture trade

The study compares how much image preparation the commercial service does before sending data to a generic tactical terminal. The [allocation catalog](ALLOCATION_SPACE.md) defines seven candidates. Within a comparison case, they face the same collection and contact opportunities. They prepare different products, send them in different orders, and place different amounts of derivation work at the terminal.

## What makes an allocation useful

The satellite needs a collection opportunity, terminal contact, and enough time to send the required bytes. The image must also cover the requested area at the declared fidelity. A corridor crop can satisfy a corridor-detail request. Its finer pixels do not make it a whole-scene quicklook. A full scene supports a terminal-created view only after complete receipt and enough processing time.

The first-order timing check compares exposed processing time with the transmission time saved by reducing the scene. When processing finishes before contact, little or none of its time is exposed to the user. The [hand calculation](HAND_CALC_BREAK_EVEN.md) gives the relation and units. Actual contact windows can split a transfer across passes, so the orbit/contact model is needed to test delivery by a deadline.

Early reduced products require the provider to generate and order more than one product. The terminal needs product identity, footprint, fidelity, and completeness to judge what arrived. A service sending only full scenes leaves more derivation work at the terminal and may consume more downlink capacity before a lower product is usable. The [interface model](INTERFACES.md) specifies these exchanges. This study has no cost data with which to price them.

## What the selected cases show

The [current evidence](../results/current/) compares the seven candidates on paired synthetic requests. It uses three individually propagated Walker constellations, one or four generic terminal sites, two terminal classes, and nominal or combined-degraded conditions. Each fixed comparison cell has 24 single requests per candidate. The [configuration](../results/current/config.json), [summary](../results/current/summary.csv), and [audit](../results/current/audit.json) record the inputs, outcomes, and pairing checks. Requests are paired across candidates within a cell. Different constellation and site-count cells use independently drawn requests.

Two corridor-detail cases illustrate different limits. With one satellite and one orbital plane, a vehicle terminal, four sites, and nominal conditions, the raw full-scene, corridor-first, and need-aware candidates each had zero deadline successes in 24 requests. In this sample, access dominated product ordering. With the larger 24-satellite configuration, one site, a dismounted terminal, and nominal conditions, the raw full-scene candidate had zero successes while corridor-first and need-aware delivery each had 12 in 24. The corresponding 95% Wilson intervals are 0 to 13.8% and 31.4 to 68.6%. This second case shows that a fitting early product can change modeled delivery when access is available but the link and deadline constrain a full scene. The intervals and small sample do not establish a universal preferred candidate.

The [summary](../results/current/summary.csv) contains every scenario and candidate outcome with its denominator and uncertainty interval. The [trial rows](../results/current/single_request_trials.csv) show individual paired requests. The [selected figure](../figures/current/mt2_selected_deadline.png) plots one case; the architecture definition remains in the model catalog.

## How to interpret the evidence

The simulation tests delivery under assumed product usefulness. It does not assess image interpretation, radiometric quality after compression, real terminal performance, or service availability. The prior-reference scenario checks whether a prerequisite exists; it does not implement change detection. The current summary reports deadline outcomes and whether any sufficient product arrived by the horizon. It does not report partial-byte fraction, complete-product time, contact utilization, energy, or peak storage for these cases.

Generating and sending a smaller product early can matter when that product fits the need and a contact can deliver it before the deadline. Changing the order cannot recover a missed collection or terminal opportunity. The [requirements trace](REQUIREMENTS.md), [verification plan](V_AND_V.md), and [assumptions](ASSUMPTIONS.md) show which parts have been checked and which remain open.
