# Trade Study

Multi-criteria evaluation of the six candidate architectures
(`docs/ALLOCATION_SPACE.md`) against the stakeholder values in
`docs/STAKEHOLDERS.md`. Computed by `scripts/trade_study.py`, which writes
`results/frozen/v2/trade_study_scores.csv` and
`results/frozen/v2/trade_study_sensitivity.csv`. Re-run it after any
change to `results/frozen/v2/e03_results.csv` or
`results/frozen/v2/e11_mission_thread_success.csv`.

## Criteria

| Criterion | Source | Direction |
|---|---|---|
| Mission-thread success | `e11_mission_thread_success.csv`, mean success rate across all threads/terminals/conditions | higher better |
| Latency | `e03_results.csv`, mean TFUP among completed single-window deliveries | lower better |
| Fidelity | Rubric (`scripts/trade_study.py::RUBRIC`): 1.0 if the complete product is lossless or full-resolution, 0.6 if it's lossy-compressed | higher better |
| Terminal SWaP burden | Rubric, proxied by how much onboard processing the architecture demands | higher (= lower burden) better |
| Resilience | `e11_mission_thread_success.csv`, mean success rate under degraded conditions only (excludes NOMINAL) | higher better |
| Acquisition lock-in risk | Rubric, proxied by how standardized/simple the architecture's behavior is to specify in a multi-vendor contract | higher (= lower risk) better |

The rubric-based criteria (fidelity, SWaP burden, lock-in risk) are stated
design judgments with a one-line rationale in the script, not measurements;
they are the same kind of ASSUMED value as the sizing ratios in
`docs/ASSUMPTIONS.md`, not evidence from a real acquisition or fielded
terminal.

## Result: mission-thread success is near zero for everyone, and that itself is the finding

Before the weighted scores: the raw mission-thread success rates in
`results/frozen/v2/e11_mission_thread_success.csv` are low across the
board, at best a few percent, for every architecture, under every
condition tested. This is not a bug in the trade study; it's a real
consequence of the underlying contact geometry. A single ground site
sees roughly 28 contact opportunities over a week
(`results/frozen/v2/e01_access_windows.csv`), averaging gaps of several
hours between passes. MT-1's 2-minute latency tolerance and even MT-2's
15-minute tolerance (`docs/MISSION_THREADS.md`) are almost never
achievable unless a request happens to land shortly before an already-
scheduled pass, because the wait for the next usable contact dominates
total latency far more than any difference in onboard processing speed
between architectures.

**Three architectures (GroundOnly, CompressedFull, ContactAware) scored
exactly 0% mission-thread success on every thread and every condition**,
for a structural reason distinct from contact geometry: none of them ever
produce anything but a single, full-scene-scale product (raw, compressed-
full, or a margin-gated compressed fallback). MT-1, MT-2, and MT-4 each
require an early tier (P2 quicklook, P3 ROI, P1 thumbnail respectively)
that these three architectures never generate at all. They aren't merely
slower; they are structurally incapable of serving a tiered mission thread,
independent of latency tolerance.

**QuicklookFirst, RoiFirst, and Progressive** are the only architectures
that ever succeed, and only when a request happens to land close to an
already-scheduled pass. Progressive's 5-tier plan gives it the widest
coverage (it's the only architecture with a P1 thumbnail, which MT-4
needs), which is why it leads every weight profile below.

## Scored results by stakeholder weight profile

From `results/frozen/v2/trade_study_scores.csv` (four profiles from
`docs/STAKEHOLDERS.md`'s value conflicts, plus a balanced/equal-weight
baseline):

| Profile | 1st | 2nd | 3rd | 4th | 5th | 6th |
|---|---|---|---|---|---|---|
| TACTICAL_USER_LEANING | Progressive | RoiFirst | QuicklookFirst | GroundOnly | CompressedFull | ContactAware |
| ACQUISITION_LEANING | Progressive | RoiFirst | GroundOnly | QuicklookFirst | CompressedFull | ContactAware |
| TERMINAL_OPERATOR_LEANING | Progressive | RoiFirst | GroundOnly | QuicklookFirst | CompressedFull | ContactAware |
| BALANCED | Progressive | RoiFirst | QuicklookFirst | GroundOnly | CompressedFull | ContactAware |

Progressive and RoiFirst are the top two under every profile tested; the
difference between profiles is mainly in what falls to third: the
tactical-user and balanced profiles put QuicklookFirst third (it's fast
when it succeeds), while the acquisition- and operator-leaning profiles
put the structurally-simpler GroundOnly third (nothing to specify or
build, so its zero mission-thread-success score matters less against
heavier lock-in-risk and SWaP weight).

## Weight-sensitivity: where rankings flip

`scripts/trade_study.py`'s sensitivity sweep (`trade_study_sensitivity.csv`)
varies each criterion's weight by up to +/-0.30 around each profile's
baseline. Real rank flips found:

- **Acquisition lock-in risk, swept under ACQUISITION_LEANING**: the top
  architecture moves between GroundOnly, Progressive, and RoiFirst as this
  weight increases. GroundOnly's simplicity (nothing onboard to specify in
  a multi-vendor contract) can outweigh its zero mission-thread-success
  score once lock-in-risk avoidance is weighted heavily enough.
- **Terminal SWaP burden, swept under ACQUISITION_LEANING,
  TERMINAL_OPERATOR_LEANING, and BALANCED**: the top architecture flips
  between GroundOnly and Progressive as this weight increases, for the
  same reason: GroundOnly does no onboard processing at all, so it wins
  outright once terminal burden dominates the score.
- **Mission-thread success and resilience, swept under
  ACQUISITION_LEANING**: the top architecture flips between Progressive
  and RoiFirst as these weights are turned down; RoiFirst's simpler,
  single-tier-then-full behavior scores closer to Progressive once the
  criteria that most reward Progressive's five-tier breadth are
  de-emphasized.

No sweep ever brought CompressedFull, ContactAware, or QuicklookFirst to
the top of any profile tested. QuicklookFirst's near-zero mission-thread
success (only MT-1 uses its one early tier) keeps it out of the top rank
even when its low-SWaP behavior is favored.

## Resilience: graceful vs. catastrophic degradation

None of the six architectures degrade gracefully in the sense of "still
delivers a first actionable product under contested conditions when it
couldn't under nominal ones" (`docs/ALLOCATION_SPACE.md` frames this as an
open question, not an assumption). The data shows the opposite pattern:
resilience scores (success rate under degraded conditions) never exceed
the corresponding nominal-condition success rate for any architecture in
this dataset; contested conditions only ever make things worse or leave
them unchanged (for the architectures already at 0%). The honest resilience
finding here is that **the dominant failure mode is contact scarcity, which
degradation only compounds**, not a case where one architecture visibly
survives contested conditions while others collapse.

## What this trade study does not show

It does not show that Progressive or RoiFirst are good enough in an
absolute sense, only that they're better than the alternatives tested. A
2-5% mission-thread success rate is not a system that works; it's evidence
that, given this notional single-ground-site contact schedule, no
processing-allocation choice can fix a latency problem whose dominant term
is the wait for the next satellite pass. See `docs/ACQUISITION_IMPLICATIONS.md`
for what that implies.
