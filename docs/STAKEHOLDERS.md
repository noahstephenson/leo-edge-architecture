# Stakeholders

All notional. This describes the roles the allocation decision has to
satisfy simultaneously, and where their interests conflict, not real named
organizations or individuals.

## Tactical user

The soldier or unit consuming the imagery product at the edge terminal.

**Values**: speed to an actionable product, matched to the mission thread
at hand (`docs/MISSION_THREADS.md`); a product they can trust (known
fidelity, not silently degraded); the system working when the link is
degraded, not just under nominal conditions.

**Doesn't value**: product standardization for its own sake, or
architectural elegance; if a mission-tailored, non-standard product gets
them what they need faster, that's what they want.

## Terminal operators

The soldiers or small team responsible for setting up, operating, and
maintaining the edge terminal in the field.

**Values**: low SWaP burden (a terminal that's actually portable and power-
sufficient for its class, `docs/MISSION_THREADS.md`'s terminal classes);
simple operation under stress; graceful behavior when contact is lost or
degraded, not a system that just stops working.

**Conflicts with tactical user**: the user wants the richest product
possible; the operator has to live within whatever compute and power the
terminal class actually has. A dismounted terminal operator can't deliver
what a vehicle-mounted terminal can, no matter what the user wants.

## Rear-echelon intelligence and tasking cell

The element that plans collections, deconflicts requests across multiple
users, and (under the reachback tasking path) submits collection requests
to the commercial provider on the edge user's behalf.

**Values**: visibility into and control over what's being tasked, so
requests can be deconflicted and prioritized across the force, not just
satisfied one at a time; a tasking interface that works the same way
regardless of which commercial provider is being used.

**Conflicts with tactical user**: reachback tasking adds latency
(`docs/MISSION_THREADS.md`'s tasking-path parameters) that the tactical
user, especially on a time-sensitive thread, doesn't want to pay. Direct
edge tasking bypasses the rear-echelon cell's deconfliction role entirely.

## Commercial provider

The company operating the LEO imaging satellites and selling collection
and delivery as a service.

**Values**: a standardized product and tasking interface that works the
same way across all its customers, not a bespoke integration per customer;
predictable, well-specified requirements it can build a service catalog
around; not being locked into exposing proprietary onboard processing
details.

**Conflicts with tactical user and terminal operators**: the edge wants
mission-tailored products (a specific tier, a specific ROI, a specific
priority order) and terminal-specific delivery behavior; a provider
optimized for a broad customer base has limited incentive to build
military-specific tiering or terminal-specific delivery logic unless it's
required and paid for as a standard service feature, not a one-off.

## Army acquisition / program office

The organization responsible for contracting the commercial service and
fielding the edge terminal.

**Values**: low vendor lock-in (the terminal and tasking interface should
work with more than one commercial provider); requirements that are
specific enough to be enforceable in a contract but not so specific they
lock in one vendor's implementation; evidence that a requirement is
actually load-bearing (tied to a mission-thread outcome) before it goes
into a contract, not a wish list.

**Conflicts with commercial provider**: standardization and multi-vendor
interoperability, which acquisition wants to avoid lock-in, cost the
provider differentiation and may cost more to build than a proprietary
interface.

**Conflicts with tactical user**: the most mission-tailored possible
architecture is often the most vendor-specific and hardest to
re-compete, which is exactly what acquisition is trying to avoid.

## Where this goes next

`docs/TRADE_STUDY.md` turns "what each stakeholder values" into weighted
criteria (mission-thread success, latency, fidelity, terminal SWaP burden,
resilience, acquisition lock-in risk) and shows where the ranking of
candidate allocations changes depending on whose values are weighted
heaviest.
