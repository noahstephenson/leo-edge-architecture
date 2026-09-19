# Concept of Operations

The full operational picture, with actors, mission threads, and the OV-2/
OV-5b/OV-6c views, lives in `docs/OPERATIONAL_CONTEXT.md`,
`docs/MISSION_THREADS.md`, and `docs/ARCHITECTURE_VIEWS.md`. This page is
the short version. Everything here is notional and unofficial.

## The idea in one paragraph

A tactical user requests imagery of an area of interest, either through a
rear-echelon tasking cell or directly. A commercial LEO provider's
satellite captures the scene, generates one or more product tiers, and
downlinks to the Army-owned tactical edge terminal during a contact
window. The edge terminal receives and exploits whatever arrived. The
architectural question this project studies is which functions (tasking,
collection, processing, prioritization, delivery) should sit in the
commercial space segment versus the Army edge segment, and how the right
split changes with mission need, terminal class, and contested conditions.
`docs/ALLOCATION_SPACE.md` is the full answer to "what to do."

## Product tiers

A satellite can generate five tiers of product, from smallest and fastest
to largest and slowest:

| Tier | What it is | Purpose |
|---|---|---|
| P0 Metadata | Timestamp, footprint, quality flags | Immediate awareness that a collection happened |
| P1 Thumbnail | Very small, low-resolution image | Fast confirmation the collection worked |
| P2 Quicklook | Reduced-resolution but interpretable image | Early situational understanding |
| P3 ROI | Full-resolution crop over a predeclared area of interest | Priority delivery of the part that matters most |
| P4 Full | Complete high-resolution image | Full analysis and archival |

## Scope

This is a research and simulation project, not an operational system. It
uses public/synthetic imagery and generic ground-terminal locations, and
it does not model target recognition, tracking, weapon cueing, or
classified workflows. See `AGENTS.md`'s non-negotiable scope boundaries
for the full list.
