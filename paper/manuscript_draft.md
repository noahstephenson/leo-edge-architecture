# Function allocation and interface design for commercial satellite imagery delivery

Noah Stephenson

## Abstract

Commercial low Earth orbit imagery services connect satellites operated by commercial providers with tactical terminals owned by the Army. Designing this interface requires decisions about which imagery products the provider generates, their transmission order, and the access opportunities needed to deliver useful information within mission timelines. These decisions become more consequential when bandwidth is limited or scheduled contacts are unavailable. This paper presents a systems architecture trade study of imagery delivery from commercial satellites to Army tactical terminals. The study connects notional mission needs to functional responsibilities, interface requirements, and alternative delivery strategies. Alternatives include full scene delivery, early delivery of quicklook images or regions of interest, progressive delivery, and prioritization based on contact availability or mission needs. A reproducible simulation evaluates these alternatives using individually propagated satellites in synthetic Walker constellations, separate collection and terminal locations, collection and downlink during the same pass, and transmission across multiple contacts. Scenarios vary constellation configuration, terminal availability, link rate, tasking delay, and contact denial. Evaluation measures include elapsed time from request to product delivery, delivery within assumed mission timelines, and incomplete delivery. The analysis distinguishes limitations imposed by orbital access from differences attributable to product generation and transmission order. Its purpose is to identify the conditions under which particular delivery strategies are useful and the assumptions that shape those judgments. The contribution is a traceable approach to evaluating imagery delivery architectures at the tactical edge, with explicit distinctions between simulated performance, assumed product utility, and operational capability. All mission scenarios and performance requirements are notional.

## 1. Introduction

For a soldier waiting at a tactical terminal, an image matters only when it arrives with the requested area and enough detail to use. The satellite may collect the scene well before it can contact the terminal. A short contact may carry only part of the scene, forcing the transfer into another pass. Sending a smaller image first may help, depending on its coverage and detail. Those conditions make product preparation on the satellite and processing at the terminal part of the same architecture decision.

This paper studies that division of work for a commercial low Earth orbit imagery service and a generic Army-owned tactical terminal. The question is how tasking, collection, product preparation, priority, and delivery should be allocated across their boundary as mission needs and contact conditions change. All scenarios, locations, deadlines, and performance requirements are notional. The project does not represent an Army program or a tested field capability.

The paper traces a user's need through a proposed requirement, the functions needed to meet it, the elements assigned those functions, the information exchanged, and the evidence used to check the design. Selected contact simulations test the timing implications. The model and its [generated views](../docs/reference/VIEWS.md) provide the architecture record behind those claims.

## 2. Modeling approach

The project follows a documented conceptual-design adaptation of the [NASA Systems Modeling Handbook for Systems Engineering](https://standards.nasa.gov/system/files/tmp/2025-03-12-NASA-HDBK-1009A.pdf). The sequence begins with the modeling plan and system boundary, then develops stakeholder expectations, technical requirements, a logical architecture, candidate allocations, and verification evidence. The [modeling plan](../docs/MODELING_PLAN.md) states which handbook activities the project uses and how its scope shapes the model.

Four small catalogs hold the scope, architecture, assurance records, and relationships. Each element has an identifier and definition. Typed links connect needs, functions, requirements, interfaces, measures, and checks. A validator catches missing references and incomplete allocations. The tables and Mermaid diagrams are generated from those catalogs, so a changed allocation or requirement appears in the views. The diagrams use concepts aligned with the Systems Modeling Language. They do not claim formal conformance or NASA review.

The model stops at one useful level of decomposition. It describes the service, satellite, tasking path, and terminal well enough to compare delivery responsibilities. It does not attempt to specify spacecraft hardware, provider algorithms, or an operational message standard.

## 3. Need, boundary, and requirements

The soldier at the terminal needs information by an assumed decision time. The provider needs to know which product to send and what counts as delivery. The terminal operator must be able to tell whether an arriving image is complete and covers the requested area. The [operational concept](../docs/CONOPS.md) uses four example threads: a quick whole-scene view, detailed imagery of a declared corridor, a comparison needing a prior reference, and repeated small-image delivery. Their deadlines are study assumptions.

The terminal needs a product identifier, footprint, fidelity description, and completeness status along with the image bytes. A partial transfer must retain its identity when the contact ends and resumes. Without these facts, the terminal cannot reliably decide whether the delivered image meets a need. The [interface definitions](../docs/INTERFACES.md) describe these exchanges without prescribing a vendor implementation.

Requirements are written as proposed, testable statements for this notional system. One asks for a complete corridor view at native spatial resolution within an assumed 900 seconds of request. Another asks the downlink exchange to identify the product's footprint and completeness. Each requirement links to a stakeholder need, responsible function or interface, and planned verification case in the [requirements model](../docs/REQUIREMENTS.md). The project also keeps software correctness checks separate. A rule that transmitted bytes cannot exceed contact capacity tests the simulation; it is not a requirement imposed on a real provider.

## 4. From functions to candidate architectures

The logical architecture begins when the request enters the service. A satellite collects and stores the scene when access permits. The service may retain the full scene or create smaller products, then chooses their transmission order. At the terminal, received bytes become a complete product only after the transfer finishes. The terminal may then derive the requested view from a full scene and check whether it meets the need before the deadline. The flow also records interrupted contacts, a missing product or prior reference, and deadline misses. The [functional model](../docs/FUNCTIONAL_ARCHITECTURE.md) defines these steps before assigning ownership.

Seven candidates allocate product preparation and ordering differently. Full-scene delivery has three forms: raw transfer followed by possible terminal derivation, compressed full-scene transfer, and a contact-aware choice between those two. Two candidates send an early whole-scene quicklook or a cropped region before the full scene. A progressive candidate sends increasingly detailed products in a fixed order. The final candidate advances the product needed by the scenario. The [allocation catalog](../docs/ALLOCATION_SPACE.md) records all seven by stable identifier, including their products, ordering rules, terminal behavior, and boundary exchanges.

A cropped corridor can show native detail yet leave the rest of the scene unseen. It cannot answer a whole-scene request. A complete full scene may let the terminal create a quicklook or crop, provided the modeled processing finishes before the deadline. The sufficiency check therefore considers coverage, native spatial resolution, completeness, terminal capability, and time together. Image interpretation and radiometric quality after lossy compression remain outside the current verification.

## 5. A trace through the model

Consider a soldier requesting detail in a declared corridor. The need becomes a proposed requirement for a complete, native-resolution corridor view within 900 seconds. After collection, product generation may create a crop, and the ordering function may place it before the full scene. Transmission and reception carry that product across the provider-terminal interface. At the terminal, the final check asks whether the received footprint covers the corridor, whether all bytes arrived, and whether the view was ready in time.

With corridor-first delivery, a fitting crop may arrive before the full scene. With raw full-scene delivery, the terminal must receive the scene and then derive the corridor view. The interface requirement exposes footprint and completeness, allowing the deadline measure and product-sufficiency check to evaluate both paths. The [generated trace](../docs/reference/TRACEABILITY.md) records the need, requirement, functions, allocations, interface, measure, and verification links. Neither path is counted as successful merely because it appears in the architecture.

## 6. Supporting analysis

A first-order relation checks whether the time exposed by onboard processing is less than the transmission time saved by reducing the image. Processing that finishes before a contact can make an early product attractive. The [hand calculation](../docs/HAND_CALC_BREAK_EVEN.md) records the equation and byte-to-bit conversion. It cannot account for a missed collection opportunity or a transfer spread across several contacts.

The simulation propagates individual satellites in three synthetic Walker constellations. Collection occurs over a different location from the generic terminal sites. The same satellite can collect and downlink during one pass, and unfinished bytes carry into later contacts. Cases vary terminal-site count, terminal class, and nominal or degraded conditions. Every candidate in a case receives the same seeded requests and contact-denial inputs. The [current evidence](../results/current/) contains configuration, individual trials, summary measures, and an audit of those pairings.

Two corridor cases show different limits. In a sparse-access case, raw full-scene, corridor-first, and need-aware delivery all missed the assumed deadline on 24 sampled requests. Changing product order could not create a timely contact in those requests. In a case with more collection opportunities but one dismounted terminal site, raw full-scene delivery met the deadline on none of 24 requests; corridor-first and need-aware delivery each met it on 12. The 95% Wilson intervals are 0 to 13.8% and 31.4 to 68.6%, respectively. These are modeled outcomes for paired requests within that second case. The intervals are broad, and the project does not claim an operational success rate or a universal winner. The [trade explanation](../docs/TRADE_STUDY.md) and [complete summary](../results/current/summary.csv) give the exact filters and remaining candidate results.

## 7. Discussion and conclusion

### Benefits

A reader can start with a soldier's information need, find the proposed requirement, see where each function occurs, and identify the information the terminal needs to judge an arriving product. The trace also identifies the check or experiment supporting a claim and shows which requirement remains open. In the selected simulations, orbital access sometimes limits every illustrated strategy. Where contact is available, the timing of a fitting product can change the outcome.

### Shortcomings

The geometry, terminal rates, tasking delays, product sizes, and deadlines are synthetic or sensitivity inputs documented in the [assumption register](../docs/ASSUMPTIONS.md). The model assumes that a product meeting declared footprint and spatial-resolution conditions is useful; no user study or image-quality experiment verifies that assumption. The prior-reference thread checks a prerequisite but does not produce a real change image. Tasking and interface messages are conceptual. The current evidence does not evaluate energy, storage, partial-byte fractions, or complete-product time for these selected cases. More representative data and direct interface and product-quality tests are needed before applying the architecture to an operational service.

For the cases studied, a fitting crop helps when a contact can carry it before the deadline. Terminal derivation can help when the complete scene arrives with time left to process it. The assumed usefulness of either view remains untested. A follow-on test with public imagery should check whether an early crop contains enough detail for the declared task.

## References and evidence

1. NASA, [*NASA Systems Modeling Handbook for Systems Engineering*, NASA-HDBK-1009A](https://standards.nasa.gov/system/files/tmp/2025-03-12-NASA-HDBK-1009A.pdf).
2. [Structured architecture and assurance catalogs](../model/), with [generated model views](../docs/reference/VIEWS.md) and [traceability](../docs/reference/TRACEABILITY.md).
3. [Current experiment configuration](../results/current/config.json), [trial data](../results/current/single_request_trials.csv), [summary](../results/current/summary.csv), and [audit](../results/current/audit.json).
