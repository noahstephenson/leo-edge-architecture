# LEO Edge Architecture

**Everything in this repository is notional and unofficial. It does not
represent an Army requirement, program, doctrine position, or acquisition
decision.**

A reproducible systems-architecture study: the Army increasingly consumes
imagery from commercial LEO providers while owning its own tactical edge
ground terminals. How should imagery functions (tasking, collection,
processing, prioritization, delivery) be allocated between the commercial
space segment and the Army-owned edge segment, and how does the preferred
allocation shift with mission need, terminal class, and contested
conditions?

`docs/OPERATIONAL_CONTEXT.md` grounds that question in three real, publicly
documented Army programs (Remote Ground Terminal, TITAN, Next Generation
Tactical Terminal) without claiming to model any of them.

## The allocation decision space

`docs/ALLOCATION_SPACE.md` is the central document: it defines the
decisions (processing allocation, tasking path, product prioritization,
policy adaptivity), places the seven architectures this repository
evaluates (A0-A6) as points within that space, and states plainly which
regions (split processing, terminal-class-dependent allocation,
change-detection support) still aren't covered. Mission-thread-aware
prioritization (A6) used to be on that list; it's now covered, with a
result.

`docs/STAKEHOLDERS.md`, `docs/REQUIREMENTS.md` (with a full traceability
matrix), and `docs/FUNCTIONAL_ARCHITECTURE.md` round out the systems
architecture; `docs/ARCHITECTURE_VIEWS.md` has the diagrams.

## The headline result: buy access first

`experiments/e12_access_sweep.py` swept satellite count (1-32) and Army
ground-terminal count (1-4) -- 18 access levels -- and tested every pair
of the seven candidate architectures for a statistically significant
mission-thread-success difference at each one
(`src/leo_edge/stats.py::paired_bootstrap_diff_ci`, `figures/fig20.png`).

**17 of 18 access levels show no statistically significant difference
between any pair of architectures.** Pooled success rate rises about an
order of magnitude with more satellites (under 0.1% at 1-4 satellites to
about 1.0% at 16, single terminal) -- access density, not architecture
choice, drives that rise. Three of the seven architectures (raw downlink,
compressed-full, the contact-aware adaptive policy) score exactly 0% at
every access level tested, structurally: they never produce anything but
a single, full-scene-scale product, and three of the four mission threads
need an earlier tier. Tiering is necessary to ever succeed; beyond that,
which tiered architecture is used essentially never makes a statistically
detectable difference across the range tested.

`docs/ACQUISITION_IMPLICATIONS.md` draws out what that means: **the
acquisition lever that actually moves mission-thread success is
constellation and ground-site access, not which onboard processing
architecture is required.** An acquisition strategy that specifies
processing architecture in detail before securing enough access to make
mission-thread success non-trivial is optimizing a second-order variable.

`docs/V2_VS_V3.md` and `docs/V1_VS_V2.md` document what changed getting
here: v1 had a real correctness bug (uncapped byte counts scoring failed
deliveries as successes); v2 fixed that and found contact geometry
dominated at one access level; v3 fixed a methodology bug (an inverted
terminal-burden criterion), added real collection timing and statistical
testing, and confirmed the v2 finding at 18 access levels instead of one.

## System architecture

![System block diagram](figures/fig01.png)

A commercial LEO satellite images an area of interest, optionally tiers
the product onboard, and downlinks during a contact window to an Army-
owned tactical edge terminal, either directly or through a rear-echelon
tasking cell. `docs/ARCHITECTURE_VIEWS.md` has the full view set (OV-2
resource flows, OV-5b activities per mission thread, OV-6c event trace,
and the 4+1 software views); `docs/OV1_SPEC.md` describes what a concept
graphic for the recommended allocation should show (no image is generated
by this repository; the old OV-1 concept graphic predates this rework's
research question and is retired).

## The access/revisit sweep

![Mission-thread success vs. access level, by thread](figures/fig19.png)

![Best statistically-distinguishable architecture by access level](figures/fig20.png)

`docs/V2_VS_V3.md` has the full pooled-success-rate table and every
ASSUMED value behind these two figures, including a real, documented
limitation of the phase-offset satellite model used here (single orbital
plane, not multiple planes) that explains why success rate rises then
falls at the highest satellite counts even though total contact coverage
keeps rising.

## Single-contact-window regime map

Within one contact window, which architecture completes fastest still
depends heavily on rate and contact duration:

![Best architecture by rate and contact duration](figures/fig04.png)

Grid cells marked "no completion" are exactly that: no architecture
delivered a complete product within that single window, honestly reported
instead of a fabricated completion time (`docs/DECISION_LOG.md` ADR-008).
This is single-window evidence, distinct from the multi-contact mission-
thread-success result above; `docs/MODEL_REFERENCE.md` explains how the
two relate.

## Novelty

`docs/NOVELTY.md` includes a real, verified literature scan (ten sources,
each cited with a title and URL, found this session) and states honestly
where this repository's contribution does and doesn't distinguish itself
from that literature.

## Quick start

```bash
uv sync
uv run pytest
make experiments
make figures
make trade_study
```

`make experiments` runs `e00` through `e11`, including the mission-thread
Monte Carlo; run `experiments/e12_access_sweep.py` directly for the access
sweep (it isn't in the default `make experiments` loop yet, since it's
slower than a single experiment). `make trade_study` regenerates the
weighted scores in `docs/TRADE_STUDY.md` from that output. `make
reproduce` runs the first four. See `REPRODUCE_LOG.md` for a real run log.

## Repository map

| Path | What's there |
|---|---|
| `src/leo_edge/` | The architecture, orbit, imagery, metrics, mission-thread, and stats model |
| `experiments/` | `e00` through `e12`, each answering one question about the model |
| `results/frozen/v2/` | Frozen results from the v2 pass, kept as a historical record (`docs/V1_VS_V2.md`) |
| `results/frozen/v3/` | Current frozen results (`docs/V2_VS_V3.md` explains what changed) |
| `figures/` | Figures generated from `results/frozen/v3/`, see `figures/README.md` |
| `docs/` | Operational context, stakeholders, requirements, allocation space, trade study, acquisition implications, architecture views, novelty, assumptions, decisions, hand-calculation check |
| `app/dashboard.py` | A Streamlit dashboard for exploring the architectures interactively |

## License

Public source, unclassified, MIT licensed. See `LICENSE`.
