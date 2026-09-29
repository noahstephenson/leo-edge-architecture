# Operational Context and Scope

This study examines how commercial low Earth orbit imagery might reach a soldier at a generic Army-owned terminal. The system, requests, and terminal capabilities are notional and unofficial. They do not represent an Army requirement, program, or acquisition decision.

A soldier requests an image of a synthetic area and needs to know its delivery state while waiting. A commercial provider collects the scene, may prepare smaller products, and sends data when a satellite can contact the terminal. The terminal’s modeled states are pending, partial, complete, and unavailable by the assumed time limit. It presents a product as usable only when it is complete and meets the study’s assumed coverage and detail. The study asks which imagery functions belong to the commercial service and which belong at the soldier’s terminal as requests, terminal classes, and contact conditions change.

The Army has publicly described efforts to integrate information from space and other sensors through tactical ground systems. Its [TITAN prototype announcement](https://www.army.mil/article/274301/army_tactical_intelligence_targeting_access_node_titan_ground_station_prototype_award) provides context for this study. The project does not model TITAN or assign it any performance, interface, or requirement. Study scenarios, locations, time limits, product utility, and terminal parameters are synthetic or identified in [assumptions](ASSUMPTIONS.md).

## Boundary

The commercial service and satellite collect and store imagery, prepare products when required, choose transmission order, and send data. The Army side receives the data and presents a complete product to the soldier. A generic tasking coordinator may carry the request. [Interfaces](INTERFACES.md) describes the product and status exchanges. Partial data wait between contacts and do not count as a usable product. The same satellite collects and sends the image; the model includes no crosslink. Collection access and terminal contact are separate events.

## Exclusions

The study excludes target recognition, target tracking, weapon cueing, strike support, classified workflows, real collection plans or terminal locations, offensive cyber capabilities, and detailed orbital warfare. It does not interpret imagery or test whether soldiers can use the product. [Concept of operations](CONOPS.md) describes the synthetic soldier interaction. [Mission threads](MISSION_THREADS.md) list the assumed requests, and [modeling plan](MODELING_PLAN.md) explains the method and evidence limits.
