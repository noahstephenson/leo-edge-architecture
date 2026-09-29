# Model catalog

> Generated from `model/*.yaml` by `scripts/generate_model_views.py`. Edit the YAML, then regenerate. This is a conceptual model, not a formal SysML artifact.

## System boundary

From a notional imagery request to a usable product at an Army-owned terminal.

## Stakeholders

| ID | Name | Definition | Provenance |
| --- | --- | --- | --- |
| ST-USER | Tactical imagery user | Requests and uses imagery products in the notional mission threads. | docs/OPERATIONAL_CONTEXT.md |
| ST-OPERATOR | Terminal operator | Operates the Army-owned receiving terminal under class-dependent constraints. | docs/MISSION_THREADS.md |
| ST-PROVIDER | Commercial imagery provider | Operates the collection spacecraft and delivers contracted products. | docs/CONOPS.md |
| ST-ACQUISITION | Acquisition analyst | Compares provider obligations and terminal capabilities using reproducible evidence. | docs/ACQUISITION_IMPLICATIONS.md |


## Elements

| ID | Name | Definition | Provenance |
| --- | --- | --- | --- |
| E-SYSTEM | Imagery delivery system of interest | End-to-end request, collection, product generation, transfer, and terminal use. | docs/CONOPS.md |
| E-PROVIDER | Commercial imagery service | Provider-owned tasking and spacecraft operations. | docs/ALLOCATION_SPACE.md |
| E-TASKING | Tasking path | Direct or reachback route from requester to provider; selected by scenario, not architecture ID. | docs/MISSION_THREADS.md |
| E-SATELLITE | Commercial LEO satellite | Collects imagery, stores and prepares products, and transmits during access windows. | docs/ALLOCATION_SPACE.md |
| E-TERMINAL | Army-owned tactical terminal | Receives products and, when capable, derives a needed product from a received full scene. | docs/MISSION_THREADS.md |
| E-USER | Imagery user | Submits a request and receives a usable product. | docs/CONOPS.md |


## Mission scenarios

| ID | Name | Needed product | Deadline | Clock | Status |
| --- | --- | --- | --- | --- | --- |
| MT-1 | Whole-area update | P2_QUICKLOOK | 120 s | request | notional |
| MT-2 | Corridor detail | P3_ROI | 900 s | request | notional |
| MT-3 | Compare with a prior image | P3_ROI | 600 s | request | proxy_only |
| MT-4 | Repeated whole-area updates | P1_THUMBNAIL | 300 s | collection | notional |


## Terminal classes

| ID | Code key | Rate (bit/s) | P4 derivation (s) | Derivable tiers | Definition |
| --- | --- | --- | --- | --- | --- |
| TC-VEHICLE | VEHICLE_MOUNTED | 50000000 | 5.0 | P0_METADATA, P1_THUMBNAIL, P2_QUICKLOOK, P3_ROI | Generic soldier-facing terminal that can derive a needed lower tier after full receipt in five assumed seconds. |
| TC-DISMOUNTED | DISMOUNTED_MANPACK | 5000000 | 30.0 | P0_METADATA, P1_THUMBNAIL, P2_QUICKLOOK, P3_ROI | Generic soldier-facing terminal that can derive a needed lower tier after full receipt in thirty assumed seconds. |


## Functions

| ID | Name | Definition | Common allocation |
| --- | --- | --- | --- |
| F-01 | Task | Submit and route a notional imagery request. | E-TASKING |
| F-02 | Collect | Capture a scene at the requested area. | E-SATELLITE |
| F-03 | Store | Retain raw scene and generated products before transmission. | E-SATELLITE |
| F-04 | Generate product | Retain raw or produce a compressed or tiered product. | E-SATELLITE |
| F-05 | Prioritize | Choose an eligible product transmission order. | E-SATELLITE |
| F-06 | Transmit | Send bytes within contact capacity. | E-SATELLITE |
| F-07 | Receive | Reconstruct delivered bytes at the terminal. | E-TERMINAL |
| F-08 | Derive at terminal | Derive a needed product from a received full scene when the terminal class permits. | E-TERMINAL |
| F-09 | Make usable | Present a complete and sufficient product to the user. | E-TERMINAL |
| F-10 | Disseminate | Make the usable product available within the edge segment. | E-TERMINAL |


## Interfaces

| ID | Name | From | To | Carries |
| --- | --- | --- | --- | --- |
| I-REQUEST | Reachback imagery request | E-TERMINAL | E-TASKING | request identifier, area of interest, needed product, deadline |
| I-DIRECT | Direct imagery request | E-TERMINAL | E-PROVIDER | request identifier, area of interest, needed product, deadline |
| I-TASK | Collection task | E-TASKING | E-PROVIDER | provider task and status |
| I-DOWNLINK | Product downlink | E-SATELLITE | E-TERMINAL | collection and product identifiers, tier, coverage, fidelity, bytes, completeness or partial-transfer state, provenance |
| I-STATUS | Delivery status | E-PROVIDER | E-TERMINAL | availability, completeness, and failure status |
| I-USER | Usable imagery product | E-TERMINAL | E-USER | product and explicit utility caveat |


## Products

| ID | Name | Coverage | Resolution | Definition |
| --- | --- | --- | --- | --- |
| P0_METADATA | Metadata | scene | none | Collection and product metadata only. |
| P1_THUMBNAIL | Thumbnail | scene | coarse | Coarse whole-scene visual. |
| P2_QUICKLOOK | Quicklook | scene | reduced | Reduced-resolution whole-scene visual. |
| P3_ROI | Region of interest | crop | native | Native-resolution selected crop; does not imply whole-scene coverage. |
| P4_FULL | Full scene | scene | native | Full scene; raw or compressed encoding is an alternative property. |


## Alternatives

| ID | Name | Products | Order | F-04 generate/retain | F-05 prioritize | F-08 derive |
| --- | --- | --- | --- | --- | --- | --- |
| A0_GROUND_ONLY | Raw full scene with terminal derivation | P4_FULL | P4_FULL | retain raw scene only | one raw full product | required for reduced view if capable |
| A1_COMPRESSED_FULL | Compressed full scene | P4_FULL | P4_FULL | compress full scene | one compressed full product | required for reduced view if capable |
| A2_QUICKLOOK_FIRST | Quicklook first | P2_QUICKLOOK, P4_FULL | P2_QUICKLOOK → P4_FULL | make quicklook and full | quicklook before full | fallback if full received and capable |
| A3_ROI_FIRST | Corridor crop first | P3_ROI, P4_FULL | P3_ROI → P4_FULL | make roi and full | roi before full | fallback if full received and capable |
| A4_PROGRESSIVE | Progressive tiers | P0_METADATA, P1_THUMBNAIL, P2_QUICKLOOK, P3_ROI, P4_FULL | P0_METADATA → P1_THUMBNAIL → P2_QUICKLOOK → P3_ROI → P4_FULL | make five tiers | fixed progressive order | fallback if full received and capable |
| A5_CONTACT_AWARE | Contact-aware full delivery | P4_FULL | P4_FULL | conditional full compression | contact margin encoding choice | required for reduced view if capable |
| A6_THREAD_AWARE_PRIORITY | Thread-aware priority | P0_METADATA, P1_THUMBNAIL, P2_QUICKLOOK, P3_ROI, P4_FULL | P0_METADATA → THREAD_NEEDED → REMAINING_PROGRESSIVE | make five tiers | needed tier after metadata | fallback if full received and capable |


### Complete function allocations and execution modes

The common allocation is inherited by every alternative; execution modes expose the behavior that changes. F-08 remains on the terminal and is conditional on class and received data.

| Alternative | Function | Allocated element | Execution mode |
| --- | --- | --- | --- |
| A0_GROUND_ONLY | F-01 | E-TASKING | scenario selected tasking path |
| A0_GROUND_ONLY | F-02 | E-SATELLITE | scheduled scene collection |
| A0_GROUND_ONLY | F-03 | E-SATELLITE | retain scene and products |
| A0_GROUND_ONLY | F-04 | E-SATELLITE | retain raw scene only |
| A0_GROUND_ONLY | F-05 | E-SATELLITE | one raw full product |
| A0_GROUND_ONLY | F-06 | E-SATELLITE | contact limited transfer |
| A0_GROUND_ONLY | F-07 | E-TERMINAL | reconstruct complete product |
| A0_GROUND_ONLY | F-08 | E-TERMINAL | required for reduced view if capable |
| A0_GROUND_ONLY | F-09 | E-TERMINAL | check sufficiency and deadline |
| A0_GROUND_ONLY | F-10 | E-TERMINAL | edge dissemination |
| A1_COMPRESSED_FULL | F-01 | E-TASKING | scenario selected tasking path |
| A1_COMPRESSED_FULL | F-02 | E-SATELLITE | scheduled scene collection |
| A1_COMPRESSED_FULL | F-03 | E-SATELLITE | retain scene and products |
| A1_COMPRESSED_FULL | F-04 | E-SATELLITE | compress full scene |
| A1_COMPRESSED_FULL | F-05 | E-SATELLITE | one compressed full product |
| A1_COMPRESSED_FULL | F-06 | E-SATELLITE | contact limited transfer |
| A1_COMPRESSED_FULL | F-07 | E-TERMINAL | reconstruct complete product |
| A1_COMPRESSED_FULL | F-08 | E-TERMINAL | required for reduced view if capable |
| A1_COMPRESSED_FULL | F-09 | E-TERMINAL | check sufficiency and deadline |
| A1_COMPRESSED_FULL | F-10 | E-TERMINAL | edge dissemination |
| A2_QUICKLOOK_FIRST | F-01 | E-TASKING | scenario selected tasking path |
| A2_QUICKLOOK_FIRST | F-02 | E-SATELLITE | scheduled scene collection |
| A2_QUICKLOOK_FIRST | F-03 | E-SATELLITE | retain scene and products |
| A2_QUICKLOOK_FIRST | F-04 | E-SATELLITE | make quicklook and full |
| A2_QUICKLOOK_FIRST | F-05 | E-SATELLITE | quicklook before full |
| A2_QUICKLOOK_FIRST | F-06 | E-SATELLITE | contact limited transfer |
| A2_QUICKLOOK_FIRST | F-07 | E-TERMINAL | reconstruct complete product |
| A2_QUICKLOOK_FIRST | F-08 | E-TERMINAL | fallback if full received and capable |
| A2_QUICKLOOK_FIRST | F-09 | E-TERMINAL | check sufficiency and deadline |
| A2_QUICKLOOK_FIRST | F-10 | E-TERMINAL | edge dissemination |
| A3_ROI_FIRST | F-01 | E-TASKING | scenario selected tasking path |
| A3_ROI_FIRST | F-02 | E-SATELLITE | scheduled scene collection |
| A3_ROI_FIRST | F-03 | E-SATELLITE | retain scene and products |
| A3_ROI_FIRST | F-04 | E-SATELLITE | make roi and full |
| A3_ROI_FIRST | F-05 | E-SATELLITE | roi before full |
| A3_ROI_FIRST | F-06 | E-SATELLITE | contact limited transfer |
| A3_ROI_FIRST | F-07 | E-TERMINAL | reconstruct complete product |
| A3_ROI_FIRST | F-08 | E-TERMINAL | fallback if full received and capable |
| A3_ROI_FIRST | F-09 | E-TERMINAL | check sufficiency and deadline |
| A3_ROI_FIRST | F-10 | E-TERMINAL | edge dissemination |
| A4_PROGRESSIVE | F-01 | E-TASKING | scenario selected tasking path |
| A4_PROGRESSIVE | F-02 | E-SATELLITE | scheduled scene collection |
| A4_PROGRESSIVE | F-03 | E-SATELLITE | retain scene and products |
| A4_PROGRESSIVE | F-04 | E-SATELLITE | make five tiers |
| A4_PROGRESSIVE | F-05 | E-SATELLITE | fixed progressive order |
| A4_PROGRESSIVE | F-06 | E-SATELLITE | contact limited transfer |
| A4_PROGRESSIVE | F-07 | E-TERMINAL | reconstruct complete product |
| A4_PROGRESSIVE | F-08 | E-TERMINAL | fallback if full received and capable |
| A4_PROGRESSIVE | F-09 | E-TERMINAL | check sufficiency and deadline |
| A4_PROGRESSIVE | F-10 | E-TERMINAL | edge dissemination |
| A5_CONTACT_AWARE | F-01 | E-TASKING | scenario selected tasking path |
| A5_CONTACT_AWARE | F-02 | E-SATELLITE | scheduled scene collection |
| A5_CONTACT_AWARE | F-03 | E-SATELLITE | retain scene and products |
| A5_CONTACT_AWARE | F-04 | E-SATELLITE | conditional full compression |
| A5_CONTACT_AWARE | F-05 | E-SATELLITE | contact margin encoding choice |
| A5_CONTACT_AWARE | F-06 | E-SATELLITE | contact limited transfer |
| A5_CONTACT_AWARE | F-07 | E-TERMINAL | reconstruct complete product |
| A5_CONTACT_AWARE | F-08 | E-TERMINAL | required for reduced view if capable |
| A5_CONTACT_AWARE | F-09 | E-TERMINAL | check sufficiency and deadline |
| A5_CONTACT_AWARE | F-10 | E-TERMINAL | edge dissemination |
| A6_THREAD_AWARE_PRIORITY | F-01 | E-TASKING | scenario selected tasking path |
| A6_THREAD_AWARE_PRIORITY | F-02 | E-SATELLITE | scheduled scene collection |
| A6_THREAD_AWARE_PRIORITY | F-03 | E-SATELLITE | retain scene and products |
| A6_THREAD_AWARE_PRIORITY | F-04 | E-SATELLITE | make five tiers |
| A6_THREAD_AWARE_PRIORITY | F-05 | E-SATELLITE | needed tier after metadata |
| A6_THREAD_AWARE_PRIORITY | F-06 | E-SATELLITE | contact limited transfer |
| A6_THREAD_AWARE_PRIORITY | F-07 | E-TERMINAL | reconstruct complete product |
| A6_THREAD_AWARE_PRIORITY | F-08 | E-TERMINAL | fallback if full received and capable |
| A6_THREAD_AWARE_PRIORITY | F-09 | E-TERMINAL | check sufficiency and deadline |
| A6_THREAD_AWARE_PRIORITY | F-10 | E-TERMINAL | edge dissemination |


## Needs

| ID | Name | Definition |
| --- | --- | --- |
| N-01 | Early useful imagery | A notional user needs a usable screening view within a short request timeline. |
| N-02 | Native-resolution corridor view | A notional planner needs corridor detail and later whole-scene context. |
| N-03 | Honest change status | A user needs to know whether a prior reference supports change assessment. |
| N-04 | Repeated situational view | A user needs coarse imagery per collection opportunity. |
| N-05 | Boundary clarity | Provider and Army stakeholders need explicit product and tasking responsibilities. |


## Requirements

| ID | Kind | Status | Statement | Rationale |
| --- | --- | --- | --- | --- |
| REQ-ALLOC-001 | system | proposed | A candidate delivery service shall be able to deliver a reduced image product before its full-scene product when that candidate offers tiered delivery. | Allows an early useful tier to be assessed independently of full delivery. |
| REQ-ALLOC-002 | interface | proposed | The tasking interface shall identify whether a request uses direct or reachback routing and shall retain the resulting delay in end-to-end timing. | The request clock begins before collection and tasking delay can dominate delivery. |
| REQ-ALLOC-003 | study | proposed | The study shall evaluate a contact-aware candidate under the same contacts as fixed candidates. | Prevents an adaptive policy from being claimed without a paired comparison. |
| REQ-ALLOC-004 | study | proposed | The study shall evaluate thread-aware product ordering against fixed progressive ordering. | Isolates the effect of product priority from orbital access. |
| REQ-THREAD-001 | system | proposed | For MT-1, a complete P2-class whole-scene quicklook shall be usable within 120 seconds of a request in an evaluated case. | Notional time-sensitive screening criterion; failure is reported rather than hidden. |
| REQ-THREAD-002 | system | proposed | For MT-2, a complete native-resolution corridor ROI shall be usable within 900 seconds of a request in an evaluated case. | A reduced whole-scene quicklook lacks the assumed detail for the corridor. |
| REQ-THREAD-003 | system | open | For MT-3, the system shall identify absent prior reference data and shall not report a change product as delivered when no reference exists. | Current P3-sized proxy is not a validated change product. |
| REQ-THREAD-004 | system | proposed | For MT-4, a complete thumbnail-class view shall be usable within 300 seconds of each collection pass in an evaluated case. | Per-pass cadence differs from request-to-product latency. |
| REQ-TERM-001 | system | proposed | The terminal shall identify whether its class supports local derivation before a full-scene delivery is credited as a smaller needed product. | A raw scene alone does not establish that a constrained terminal can exploit it. |
| REQ-DDIL-001 | study | proposed | The study shall evaluate candidates with identical contact-denial and rate-derate inputs. | Keeps degraded-condition comparisons paired. |
| REQ-DDIL-002 | study | proposed | The study shall report sampled mission-thread successes with a numerator, denominator, and uncertainty interval. | Distinguishes a sample estimate from operational probability. |
| REQ-IF-001 | interface | proposed | Each downlinked product shall carry identity, tier, coverage, fidelity, and completeness information. | A terminal cannot judge usefulness from bytes alone. |
| REQ-IF-002 | interface | proposed | The provider-terminal interface shall preserve partial-delivery status across contacts until the product is complete or the case is censored. | Short contacts can require multi-contact byte carryover. |


## Model integrity checks

| ID | Legacy ID | Statement |
| --- | --- | --- |
| MIC-001 | REQ-CORRECT-001 | Transmitted bytes never exceed available contact capacity. |
| MIC-002 | REQ-CORRECT-002 | Contact utilization remains between zero and one. |
| MIC-003 | REQ-CORRECT-003 | Undelivered products are censored rather than assigned a completion time. |
| MIC-004 | REQ-CORRECT-004 | Product fidelity and coverage are reported explicitly. |
| MIC-005 | none | Storage and battery state never become negative. |
| MIC-006 | none | Identical seeds and configuration reproduce selected results. |


## Measures

| ID | Symbol | Unit | Definition |
| --- | --- | --- | --- |
| M-TFUP | tfup_s | s | Elapsed time from thread-specific clock origin to first sufficient completed product. |
| M-TCP | tcp_s | s | Elapsed time to required complete product when applicable. |
| M-DEADLINE | deadline_met | boolean | True only for a complete sufficient product by the notional deadline. |
| M-COMPLETE | product_completeness | fraction | Delivered fraction of product bytes. |
| M-UTIL | contact_utilization | fraction | Transmitted bytes divided by available contact capacity. |
| M-PROC-E | processing_energy_j | J | Energy expended generating onboard products. |
| M-TX-E | tx_energy_j | J | Energy expended transmitting product bytes. |
| M-STORE | storage_peak_bytes | byte | Largest modeled stored byte count. |


## Assumptions

| ID | Source category | Value | Statement | Provenance |
| --- | --- | --- | --- | --- |
| ASM-LINK-001 | ANALYTICAL_ASSUMPTION |  | Link rate is constant within each contact window. | docs/ASSUMPTIONS.md |
| ASM-PROC-002 | ANALYTICAL_ASSUMPTION | compressed_full_fraction=0.3 | Compressed-full product is 30% of raw scene bytes; laptop benchmark data do not validate this flight value. | config/product_sizing.yaml |
| ASM-PROC-003 | ANALYTICAL_ASSUMPTION | quicklook_fraction=0.02 | A2 quicklook is 2% of raw scene bytes. | config/product_sizing.yaml |
| ASM-PROC-004 | ANALYTICAL_ASSUMPTION | roi_fraction=0.05 | A3 ROI is 5% of raw scene bytes; this is a sensitivity choice, not a measured crop ratio. | config/product_sizing.yaml |
| ASM-PROC-005 | ANALYTICAL_ASSUMPTION | metadata_bytes=20480, thumbnail_bytes=524288, quicklook_bytes=20971520, roi_bytes=52428800 | A4 and A6 progressive products use fixed byte targets independent of scene size. | config/product_sizing.yaml |
| ASM-TERM-001 | SENSITIVITY_ONLY | rate_bps=50000000, derivation_time_s=5.0 | The vehicle terminal has a notional 50 Mbps link and takes five seconds to derive a lower tier from received P4. | experiments/e11_mission_thread_success.py |
| ASM-TERM-002 | SENSITIVITY_ONLY | rate_bps=5000000, derivation_time_s=30.0 | The dismounted terminal has a notional 5 Mbps link and takes thirty seconds to derive a lower tier from received P4. | experiments/e11_mission_thread_success.py |
| ASM-ORBIT-001 | ANALYTICAL_ASSUMPTION |  | Synthetic circular orbits are propagated at a fixed epoch. | docs/ASSUMPTIONS.md |
| ASM-BENCH-001 | MEASURED_BENCHMARK |  | Laptop image-processing measurements are measurements of that hardware only. | docs/ASSUMPTIONS.md |
| ASM-CONTEXT-001 | PUBLIC_CONTEXT |  | Public Army motivation informs the study without defining an Army requirement. | docs/OPERATIONAL_CONTEXT.md |
| ASM-THREAD-001 | SENSITIVITY_ONLY |  | Thread product needs and deadlines are notional study parameters. | docs/MISSION_THREADS.md |


## Verification cases

| ID | Method | Status | Definition | Evidence or gap |
| --- | --- | --- | --- | --- |
| V-TIMING | simulation | supported_by_simulation | Compare complete sufficient delivery time with scenario deadline in the selected synthetic cases. | [results/current/single_request_trials.csv](../../results/current/single_request_trials.csv), [results/current/cadence_trials.csv](../../results/current/cadence_trials.csv), [results/current/summary.csv](../../results/current/summary.csv), [results/current/config.json](../../results/current/config.json), [results/current/audit.json](../../results/current/audit.json) |
| V-PRODUCT | test | supported_by_test | Check coverage and resolution; full-scene derivation requires terminal capability and time. | [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |
| V-INTERFACE | inspection | not_evaluated | Inspect tier, coverage, fidelity, completeness, and identifiers at delivery. | The conceptual fields are modeled but no operational message schema or complete exchange inspection exists. |
| V-CONTACT | test | supported_by_test | Check capacity and multi-contact completion under paired contacts. | [tests/test_simulation.py](../../tests/test_simulation.py), [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |
| V-TASK | analysis | not_evaluated | Check path availability and delay are reflected in request timing. | The current sweep varies tasking delay but does not verify distinct direct and reachback message routes. |
| V-PRIORITY | simulation | supported_by_simulation | Compare fixed, thread-aware, and contact-aware policies on paired requests in selected synthetic cases. | [results/current/single_request_trials.csv](../../results/current/single_request_trials.csv), [results/current/cadence_trials.csv](../../results/current/cadence_trials.csv), [results/current/summary.csv](../../results/current/summary.csv), [results/current/config.json](../../results/current/config.json), [results/current/audit.json](../../results/current/audit.json) |
| V-REFERENCE | test | partial | Verify no change product is credited without a prior reference. | [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |
| V-MODEL | test | supported_by_test | Validate capacity, censoring, bounds, and determinism invariants covered by the cited tests. | [tests/test_architectures.py](../../tests/test_architectures.py), [tests/test_simulation.py](../../tests/test_simulation.py), [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |


## Paper claim register

| ID | Status | Claim | Evidence or reason |
| --- | --- | --- | --- |
| CL-001 | supported_by_model | The catalog connects each recorded need to a scenario and measure and each requirement to a need, function or interface, and verification case. | [model/traceability.yaml](../../model/traceability.yaml), [scripts/validate_model.py](../../scripts/validate_model.py) |
| CL-002 | analytical | Exposed processing time must be less than transmission time saved for a reduced product to arrive earlier in the first-order model. | [AGENTS.md](../../AGENTS.md), [docs/MODEL_REFERENCE.md](../../docs/MODEL_REFERENCE.md) |
| CL-003 | supported_by_test | Under the assumed P4 native-spatial-resolution rule, full-scene reception can support a derived view only when terminal capability, processing time, and deadline permit it; radiometric utility is not evaluated. | [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |
| CL-004 | not_evaluated | MT-3 change-product performance has not been established by the P3-sized proxy. | The proxy represents size and processing cost only; no change algorithm or valid prior-reference chain is verified. |
| CL-005 | supported_by_simulation | The selected 48-hour synthetic cases include both an access-limited MT-2 vehicle/four-site 1/1/0 cell with 0/24 for all candidates and a strategy-sensitive MT-2 dismounted/one-site 24/8/1 cell with 0/24 for A0 and 12/24 for A3 and A6; these samples do not establish general operating regimes. | [results/current/single_request_trials.csv](../../results/current/single_request_trials.csv), [results/current/cadence_trials.csv](../../results/current/cadence_trials.csv), [results/current/summary.csv](../../results/current/summary.csv), [results/current/config.json](../../results/current/config.json), [results/current/manifest.json](../../results/current/manifest.json), [results/current/audit.json](../../results/current/audit.json) |
