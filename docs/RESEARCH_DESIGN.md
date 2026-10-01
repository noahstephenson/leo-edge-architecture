# Research design

The research question is: How should imagery functions (tasking, collection, processing, prioritization, delivery) be allocated between a commercial LEO space segment acquired as a service and an Army-owned tactical edge segment, and how does the preferred allocation shift across mission needs, terminal classes, and contested or DDIL conditions?

The [modeling plan](MODELING_PLAN.md) explains the conceptual design method. The [operational context](OPERATIONAL_CONTEXT.md) gives the motivation and scope for the notional scenarios. The quantitative study answers a bounded part of the question: what provider preparation and product order change when tasking, collection ownership, and contact opportunities are held fixed. It compares those choices with eligible terminal derivation after complete scene receipt. No optimization over every function owner is performed.

The architecture is the primary research product. A reader should be able to follow each claim from a stakeholder need through the requirement, function, candidate allocation, boundary exchange, measure, and verification case. The [structured model](../model/) records those links, and [generated traceability](reference/TRACEABILITY.md) displays them.

A simple timing relation checks when smaller product size can offset image processing time. Selected synthetic contact cases then examine collection access, terminal access, same pass delivery, interruptions, and byte carryover. Paired requests hold those opportunities constant within each comparison. The [trade study](TRADE_STUDY.md) interprets the selected outcomes without claiming a generally preferred candidate.

The study can test model consistency and compare delivery behavior under its inputs. It cannot establish the utility of imagery to an operator, the feasibility of a commercial implementation, or the performance of a real tactical terminal. [Assumptions](ASSUMPTIONS.md) and [verification](V_AND_V.md) make those limits explicit.

## The argument from request to interface consequence

A soldier requests a declared footprint and level of detail before a notional deadline. The provider must first obtain a collection opportunity. It then prepares or retains the selected products and transmits them within contacts with the receiving terminal. The terminal receives a fitting product directly or derives that view from an eligible complete scene. The deadline outcome is evaluated when sufficient information is available at the terminal. This sequence is the human story and the causal structure of the comparison.

| Link in the argument | What the study supplies | Limit on the inference |
|---|---|---|
| Need to requirement | A notional coverage, fidelity, and deadline rule linked in the catalogs. | No elicited or validated soldier requirement. |
| Requirement to product | An explicit sufficiency check for the requested tier or eligible terminal derivation. | Declared coverage and spatial resolution do not establish image quality or interpretation. |
| Product to responsibility | Common function owners plus candidate preparation and order in the allocation catalog. | Tasking and collection ownership are fixed. |
| Responsibility to arrival | One transfer engine with processing time, contact capacity, byte carryover, and product completion. | Idealized transfer without packet costs, retransmission, or decoding measurements. |
| Arrival to sufficient availability | Terminal derivation is added only after eligible full-scene receipt. | Assumed terminal capability and processing time. |
| Availability to outcome | Request-based deadlines and separate full-scene receipt criteria. | A modeled outcome, not demonstrated operational effectiveness. |
| Outcome to interface consequence | Identity, footprint, fidelity, and completeness must be interpretable at receipt. | A conceptual information obligation, not verified message exchange or interoperability. |

The successful request clock has three intervals: request to collection, collection to the relevant product's arrival, and any terminal derivation. The second interval already includes preparation, contact wait, transmission, and interruptions. Since processing can occur while waiting for contact, separate processing and wait durations must not be added again. A first completed metadata product, a sufficient image, a full scene, and the end of the whole candidate sequence can occur at different times. The comparison keeps these events distinct.

## What is controlled and what changes

Candidate comparisons pair the same request and contact-denial context within a fixed constellation, receiver, terminal, mission thread, and condition. Differences in those paired outcomes follow from candidate behavior under the common context and assumptions. Product sizes are common wherever the product is the same, so an ordering result is not explained by unequal crop or quicklook sizes. The trial audit checks this pairing. Comparisons across constellation and site-count cells use independent request draws and should not be read as paired effects.

Terminal class changes both rate and derivation time. Combined degradation changes tasking delay, rate, and denial together. Neither comparison by itself isolates a single causal parameter. Separate sensitivities vary those inputs, while finer sampling and nearby geometry cases show how dependent the classifications are on access assumptions. They use a separate paired request sample. The principal and all-miss examples also differ in receiver and terminal assumptions, so their contrast illustrates different conditions rather than measuring a constellation-size effect alone.

The one-site case concerns the requesting terminal. The four-site case concerns a logical connected receiver with instantaneous sharing. Repeated collection results start independent delivery opportunities, allowing the same contact capacity to be reused between evaluations. They therefore cannot establish a feasible repeated stream. These distinctions are part of the outcome definition, not optional qualifications added after interpreting the result.

## Evidence and contribution

The principal corridor comparison supports early delivery of the product that fits the assumed need. It does not show an additional deadline benefit from A6 over A3 in that case. Its timely crop outcomes also do not establish timely full-scene receipt. The all-miss example retains eventual sufficient products that arrived late, preventing an explanation based only on absent collection. The [trade study](TRADE_STUDY.md), [claim filters](../results/current/claims.json), and [paired differences](../results/current/principal_paired_differences.csv) preserve those distinctions.

Wilson intervals describe sampled candidate proportions. Paired bootstrap intervals describe differences under resampling of the observed request pairs. Conditional latency differences include only pairs where both candidates were timely. A degenerate bootstrap interval from identical observed differences does not establish equivalence, and these exploratory comparisons do not adjust for the many comparisons performed. No interval covers uncertainty in geometry, assumed fidelity, rates, or user requirements.

The [literature reference](reference/LITERATURE.md) establishes precedents for requirements-linked simulation, product-specific latency, onboard preparation, scheduling, and interrupted delivery. The contribution is the inspectable combination of those ideas in this notional service-boundary comparison. The literature review does not establish an unprecedented method or calibrate the numerical inputs. Lasting conclusions concern the conditions for provider preparation and terminal derivation, and the information the interface must expose to judge sufficient availability.
