# Operational Context

Everything in this document is notional and unofficial. It does not
represent an Army requirement, program position, doctrine, or acquisition
decision. Where a claim is about a real, named Army program, it is cited to
a public source; where it is not verifiable from a public source, it is
marked UNVERIFIED and treated as a parameter in the model, not a fact.

## The problem, stated plainly

A tactical unit needs timely imagery of an area of interest. It does not
own the satellite that can collect that imagery. Commercial LEO imaging
providers can collect it and deliver it as a service. The Army owns the
ground side: a tactical edge terminal of some class, operated by soldiers
in the field, with whatever compute, power, and connectivity that terminal
actually has.

The architectural question this creates: which functions in the imagery
pipeline (tasking the collection, processing the raw sensor data,
prioritizing which product goes first, delivering it) should live in the
commercial provider's space segment, versus the Army-owned edge terminal,
versus be split between them? And does the right split change depending on
what the mission needs, what class of terminal is in the field, and how
contested or degraded the link is?

## What the unit experiences

The short version: the unit waits for a satellite to pass over the target,
then waits for that satellite to be in range of its terminal, and the time
limits are minutes. `docs/CONOPS.md` walks through both waits with real
numbers from the model and a worked example.

## Real public-source grounding

This is not a hypothetical direction for the Army. Three real, publicly
documented programs establish that the Army is actively building exactly
this kind of commercial-provider-to-tactical-edge pipeline:

- **Remote Ground Terminal (RGT)**: a Maxar-built, portable, direct-downlink
  tactical ground system, transportable by two people and set up in about
  an hour, that lets forces in remote locations downlink, analyze, and
  disseminate imagery from commercial Earth observation satellites
  (including Maxar's WorldView constellation) without routing through a
  centralized processing chain first. The Army awarded Maxar a sole-source
  IDIQ contract worth up to $49 million over eight years for RGT, with
  initial task orders totaling $8 million, announced September 2020. The
  Army's stated plan is to evolve RGT into a commercial-imagery receive
  node for TITAN (below).
  Source: [Portable satellite imagery ground systems to be delivered to U.S. Army, Military Embedded Systems, 2020-09-22](https://militaryembedded.com/comms/satellites/portable-satellite-imagery-ground-systems-to-be-delivered-to-us-army)
- **TITAN (Tactical Intelligence Targeting Access Node)**: the Army's
  next-generation intelligence ground station, designed to leverage both
  military and commercial space, high-altitude, aerial, and terrestrial
  sensors, process that data (with AI/ML assistance), and deliver targeting
  and situational-awareness products with a reduced sensor-to-shooter
  timeline. Northrop Grumman and Palantir have both been awarded Other
  Transaction Agreements for TITAN prototype development; the Palantir OTA
  is reported at $178.4 million for ten prototypes (five Advanced, five
  Basic variants).
  Source: [Army Tactical Intelligence Targeting Access Node (TITAN) Ground Station Prototype Award, army.mil](https://www.army.mil/article/274301/army_tactical_intelligence_targeting_access_node_titan_ground_station_prototype_award)
- **Next Generation Tactical Terminal (NGTT)**: an Army program to field a
  single terminal that can simultaneously use multiple LEO/MEO/GEO
  constellations and frequency bands, at-the-halt or on-the-move, alongside
  a parallel effort to establish a multi-vendor commercial-satellite-service
  contract vehicle (a Blanket Purchase Agreement spanning LEO/MEO/GEO
  providers), following a year-long commercial SATCOM pilot.
  Source: [Army to refine requirements for next-generation satellite terminals, SpaceNews](https://spacenews.com/army-to-refine-requirements-for-next-generation-satellite-terminals/)

These three programs are cited to establish that "commercial space segment
feeding an Army-owned tactical terminal" is a real direction the Army is
investing in, not an invented premise. **Nothing in this repository claims
to model RGT, TITAN, or NGTT specifically, or to represent their actual
architecture, performance, or requirements.** The simulation in this
repository uses its own notional terminal classes and parameters (see
`docs/MISSION_THREADS.md` and `docs/ASSUMPTIONS.md`), not any data from
these programs, none of which is public.

## What this repository actually studies

A notional scenario: a tactical unit requests imagery of an area of
interest, a commercial LEO provider collects and delivers it, and the
delivery path runs through some combination of onboard-satellite processing
and an Army-owned edge terminal's own processing, under a real orbital
contact-window schedule and a downlink rate that may be degraded by
contested conditions. The evaluation question is which allocation of
processing, prioritization, and tasking functions across that
provider/Army boundary gets the right product to the user fastest, under
which conditions, and what that implies for what the Army should require
from a commercial provider versus build into its own terminal.

## Scope boundaries

This repository does not model: real Army tasking authorities or approval
chains, classified requirements or data rates, actual RGT/TITAN/NGTT
architecture or performance, real operational terminal locations, or
target recognition, tracking, or weapon cueing. See `AGENTS.md` for the
full non-negotiable scope list, unchanged by this rework.
