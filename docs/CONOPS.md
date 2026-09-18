# Concept of Operations

The full concept of operations, with actors, product tiers, and the OV-1 through OV-5a operational viewpoints, lives in `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md`. This page is the short version.

## The idea in one paragraph

A user requests imagery of an area. Mission operations schedules the collection. A small COTS-heavy satellite in low Earth orbit captures the scene, optionally processes it onboard, and downlinks directly to a mobile ground terminal in the field during the next contact window, without needing to route through a centralized ground station first. The ground terminal finishes any remaining processing and hands the product to the user.

## Why direct-to-edge

A centralized processing chain (satellite to a fixed ground station to a data center to the field) adds hops and latency that a mobile user in the field cannot always wait for. Direct-to-edge delivery shortens that path. The tradeoff this project studies is what to do on the satellite before that direct downlink: send the image raw and let the ground terminal do all the work, or spend onboard compute and time to shrink the product first.

## Product tiers

The satellite can generate five tiers of product, from smallest and fastest to largest and slowest:

| Tier | What it is | Purpose |
|---|---|---|
| P0 Metadata | Timestamp, footprint, quality flags | Immediate awareness that a collection happened |
| P1 Thumbnail | Very small, low-resolution image | Fast confirmation the collection worked |
| P2 Quicklook | Reduced-resolution but interpretable image | Early situational understanding |
| P3 ROI | Full-resolution crop over a predeclared area of interest | Priority delivery of the part that matters most |
| P4 Full | Complete high-resolution image | Full analysis and archival |

## Scope

This is a research and simulation project, not an operational system. It uses public/synthetic imagery and generic ground-terminal locations, and it does not model target recognition, tracking, weapon cueing, or classified workflows. See `LEO_EDGE_OPERATIONAL_VIEWPOINTS.md` section 2 for the full in-scope/out-of-scope list.
