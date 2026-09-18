# Novelty

Replaces `docs/NOVELTY_AUDIT.md` (retired, see `docs/DECISION_LOG.md`
ADR-007). Unlike the v1 version, this document includes a real literature
scan: every source below was found via a web search performed in this
session and is cited with a title and URL I can point to. Nothing here is
invented. Where a source's content beyond its title/topic could not be
verified (e.g., a page that couldn't be fetched), that's stated explicitly
rather than described as if it had been read in full.

## Literature scan

### Onboard/edge processing for EO smallsats and progressive/tiered delivery

- **"Revisiting-Aware In-Orbit Edge Computing for Earth Observation"** (the
  STRIDE framework), arXiv 2607.25813. Leverages orbital revisiting
  properties to reference historical imagery onboard and transmit only
  regions of interest against temporal redundancy in revisit imagery.
  Directly relevant to this repo's ROI-first (A3) and adaptive (A5)
  architectures, though STRIDE's mechanism (revisit-based redundancy
  exploitation) is different from anything modeled here.
  [arxiv.org/html/2607.25813](https://arxiv.org/html/2607.25813)
- **"Advancing Earth Observation: A Survey on AI-Powered Image Processing
  in Satellites"**, arXiv 2501.12030 / Tandfonline 2025. A survey covering
  onboard compute hardware trends and AI-based processing approaches for
  EO satellites.
  [arxiv.org/pdf/2501.12030](https://arxiv.org/pdf/2501.12030)
- **"Trends and Applications of On-Board Image Processing for Earth
  Observation Nanosatellites: A Systematic Review"**, International
  Journal of Aeronautical and Space Sciences (Springer Nature), 2025.
  [link.springer.com/article/10.1007/s42405-025-00885-y](https://link.springer.com/article/10.1007/s42405-025-00885-y)
- **"Opportunities and challenges of on-board AI-based image recognition
  for small satellite Earth observation missions"**, ScienceDirect
  (Acta Astronautica), 2024.
  [sciencedirect.com/science/article/pii/S0273117724002886](https://www.sciencedirect.com/science/article/pii/S0273117724002886)
- **"Demonstrating Onboard Inference for Earth Science Applications with
  Spectral Analysis Algorithms and Deep Learning"**, arXiv 2508.15053.
  [arxiv.org/pdf/2508.15053](https://arxiv.org/pdf/2508.15053)
- **"Assessing the Added Value of Onboard Earth Observation Processing
  with the IRIDE HEO Service Segment"**, arXiv 2604.07120.
  [arxiv.org/pdf/2604.07120](https://arxiv.org/pdf/2604.07120)

**Gap relative to this literature**: every source above is about onboard
processing *quality or capability* (what AI/compute can do on a satellite).
None of them frame the question as an allocation decision across a
commercial-provider/military-customer ownership boundary, or evaluate how
the preferred processing choice shifts with a receiving terminal's class
or a contested link, which is this repository's actual subject.

### Commercial space integration for military users, and tactical ground segment

- **RAND Corporation, "Integrating Commercial Space Services into
  Department of Defense Architecture"** (research brief). I confirmed this
  source's title and topic via its RAND URL; I could not fetch its full
  text in this session (the page returned an access error), so I am not
  citing specific findings from it, only that it exists and is on-topic.
  UNVERIFIED beyond title/URL.
  [rand.org/pubs/research_briefs/RBA2562-1.html](https://www.rand.org/pubs/research_briefs/RBA2562-1.html)
- **Defense Science Board, "Commercial Space" Final Report**, May 2024,
  cleared for open publication by the Department of Defense. A real,
  official, publicly released DoD report on commercial space integration.
  I have not read its full content in this session; citing it as a real,
  on-topic source, not summarizing its findings.
  [dsb.cto.mil, PDF](https://dsb.cto.mil/wp-content/uploads/2024/07/DSB_Commercial-Space-Final-Report_ForPublicRelease.pdf)
- **Army Remote Ground Terminal (RGT), TITAN, and Next Generation Tactical
  Terminal (NGTT)**: real Army programs establishing that a commercial-
  provider-to-tactical-edge pipeline is an active investment area, not a
  hypothetical. Full citations in `docs/OPERATIONAL_CONTEXT.md`; not
  repeated here to avoid duplicate sourcing.
- **SMDC/ARSTRAT Future Warfare Center, Tactical Ground Station (TGS) Fact
  Sheet**. A real Army fact sheet on tactical ground station downlink
  capability, including theater tasking and direct downlink of imagery
  products. I have not read its full content in this session.
  [smdc.army.mil, PDF](https://www.smdc.army.mil/Portals/38/Documents/Publications/Fact_Sheets/Archived_Fact_Sheets/TGS.pdf)

**Gap relative to this literature**: these sources establish that
commercial-military space integration is a real, actively studied policy
and acquisition area, and that real tactical ground/downlink programs
exist. None of them (as far as I can verify from what I read) evaluate the
question this repository asks quantitatively: given a specific mission
thread, terminal class, and contested condition, which allocation of
processing and tasking functions across the ownership boundary actually
gets a usable product to the user fastest, with simulated evidence rather
than a policy-level argument.

### What the scan did not find

I did not find a source that combines all three elements this repository's
claims rest on: (1) the commercial-provider/Army-edge ownership boundary as
the explicit unit of allocation analysis, (2) mission-thread-driven
evaluation with terminal-class and contested-condition sensitivity, and
(3) a reproducible, re-parameterizable simulation pipeline producing that
evidence. That doesn't mean no such source exists; it means this scan,
conducted in one session with a general web search, didn't turn one up.
Fewer real references beat many doubtful ones, per this project's own
ground rules, so the scan stops here rather than padding the list.

## Ranked candidate claims

Each tied to a repository artifact, with a falsification condition, and
evaluated against the scan above rather than assumed:

1. **Imagery-function allocation across a commercial-provider/Army-edge
   ownership boundary as the unit of analysis.** Artifact:
   `docs/ALLOCATION_SPACE.md`. Falsification: a source in the scan above
   that frames the same allocation question the same way. Not found.
   **Holds**, with the caveat that the scan is one session's search, not an
   exhaustive review.
2. **Mission-thread-driven evaluation showing preferred allocations shift
   with terminal class and contested conditions, including where they
   flip.** Artifact: `docs/TRADE_STUDY.md`'s weight-sensitivity sweep.
   Falsification: a source with the same evaluation structure. Not found.
   **Holds**, but weakened by this repository's own honest finding that
   terminal class did not produce a measurable difference in this
   dataset (`docs/ACQUISITION_IMPLICATIONS.md`), which is itself a result
   worth reporting, not evidence the claim is false; the claim is about
   the evaluation approach existing, not about every axis showing a large
   effect.
3. **Acquisition guidance (require vs. build vs. standardize) derived
   traceably from the trade study.** Artifact:
   `docs/ACQUISITION_IMPLICATIONS.md`, each item tied to a specific
   finding. Falsification: a source doing the same traceable derivation.
   Not found in the scan, though the RAND brief and DSB report (both
   UNVERIFIED beyond title in this scan) plausibly contain policy-level
   acquisition guidance on commercial space integration generally; I
   cannot confirm or rule out overlap without reading them.
4. **An open, reproducible, re-parameterizable architecture evaluation
   pipeline with end-to-end traceability.** Artifact: this repository,
   `docs/REQUIREMENTS.md`'s traceability matrix, `REPRODUCE_LOG.md`.
   Falsification: a source shipping an equivalent open pipeline. Not
   found, though open EO-processing benchmarking code likely exists
   elsewhere and simply wasn't surfaced by this scan.

## Recommended contribution statement

This repository's contribution is a reproducible simulation and trade-
study pipeline that evaluates how imagery-pipeline functions should be
allocated between a commercial LEO provider and an Army-owned tactical
edge terminal, across mission threads, terminal classes, and contested
conditions, and that derives specific acquisition-relevant implications
traceably from that evaluation. It does not claim to be the first work on
onboard EO processing, commercial-military space integration policy, or
tactical ground terminals individually; each of those is an established,
active area (see the scan above). What it contributes is putting the
allocation question, the mission-thread evaluation, and the acquisition
guidance in one open, rerunnable pipeline, and reporting honestly when the
evidence doesn't support a strong claim (`docs/TRADE_STUDY.md`'s near-zero
mission-thread success rates, `docs/ACQUISITION_IMPLICATIONS.md`'s
contact-frequency finding) rather than only reporting the results that
flatter the model.
