# Traceability

> Generated from `model/traceability.yaml`. Relationship direction is written explicitly; a modeled satisfaction link is not evidence of operational compliance.

## Need to scenario and measure

| Need | Scenario | Measure |
| --- | --- | --- |
| N-01 | MT-1 | M-TFUP |
| N-02 | MT-2 | M-DEADLINE |
| N-03 | MT-3 | M-DEADLINE |
| N-04 | MT-4 | M-DEADLINE |
| N-05 | MT-2 | M-COMPLETE |


## Requirement to function or interface and verification

| Requirement | Kind | Status | Need | Function/interface | Verification |
| --- | --- | --- | --- | --- | --- |
| REQ-ALLOC-001 | system | proposed | N-01 | F-04, F-05, F-06 | V-PRIORITY (supported_by_simulation) |
| REQ-ALLOC-002 | interface | proposed | N-05 | I-REQUEST, I-DIRECT, F-01 | V-TASK (not_evaluated) |
| REQ-ALLOC-003 | study | proposed | N-05 | F-05 | V-PRIORITY (supported_by_simulation) |
| REQ-ALLOC-004 | study | proposed | N-02 | F-05 | V-PRIORITY (supported_by_simulation) |
| REQ-THREAD-001 | system | proposed | N-01 | F-09, F-07, F-10 | V-TIMING (supported_by_simulation), V-PRODUCT (supported_by_test) |
| REQ-THREAD-002 | system | proposed | N-02 | F-09, F-07, F-10 | V-TIMING (supported_by_simulation), V-PRODUCT (supported_by_test) |
| REQ-THREAD-003 | system | open | N-03 | F-09 | V-REFERENCE (partial) |
| REQ-THREAD-004 | system | proposed | N-04 | F-09, F-07, F-10 | V-TIMING (supported_by_simulation) |
| REQ-TERM-001 | system | proposed | N-05, N-01, N-02 | F-08 | V-PRODUCT (supported_by_test) |
| REQ-DDIL-001 | study | proposed | N-05 | F-06 | V-CONTACT (supported_by_test) |
| REQ-DDIL-002 | study | proposed | N-05 | F-09 | V-MODEL (supported_by_test), V-TIMING (supported_by_simulation) |
| REQ-IF-001 | interface | proposed | N-05 | I-DOWNLINK | V-INTERFACE (not_evaluated) |
| REQ-IF-002 | interface | proposed | N-05 | I-DOWNLINK, F-06, F-07 | V-CONTACT (supported_by_test), V-INTERFACE (not_evaluated) |


## Verification evidence and gaps

| Case | Status | Evidence or gap |
| --- | --- | --- |
| V-TIMING | supported_by_simulation | [results/current/single_request_trials.csv](../../results/current/single_request_trials.csv), [results/current/cadence_trials.csv](../../results/current/cadence_trials.csv), [results/current/summary.csv](../../results/current/summary.csv), [results/current/config.json](../../results/current/config.json), [results/current/audit.json](../../results/current/audit.json) |
| V-PRODUCT | supported_by_test | [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |
| V-INTERFACE | not_evaluated | The conceptual fields are modeled but no operational message schema or complete exchange inspection exists. |
| V-CONTACT | supported_by_test | [tests/test_simulation.py](../../tests/test_simulation.py), [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py), [tests/test_transfer_contract.py](../../tests/test_transfer_contract.py) |
| V-TASK | not_evaluated | The current sweep varies tasking delay but does not verify distinct direct and reachback message routes. |
| V-PRIORITY | supported_by_simulation | [results/current/single_request_trials.csv](../../results/current/single_request_trials.csv), [results/current/cadence_trials.csv](../../results/current/cadence_trials.csv), [results/current/summary.csv](../../results/current/summary.csv), [results/current/config.json](../../results/current/config.json), [results/current/audit.json](../../results/current/audit.json) |
| V-REFERENCE | partial | [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |
| V-MODEL | supported_by_test | [tests/test_architectures.py](../../tests/test_architectures.py), [tests/test_simulation.py](../../tests/test_simulation.py), [tests/test_product_sufficiency.py](../../tests/test_product_sufficiency.py) |


## All typed relationships

| ID | Type | Source | Target | Status |
| --- | --- | --- | --- | --- |
| T-001 | contextualized_by | N-01 | MT-1 | proposed |
| T-002 | evaluated_by | N-01 | M-TFUP | proposed |
| T-003 | contextualized_by | N-02 | MT-2 | proposed |
| T-004 | evaluated_by | N-02 | M-DEADLINE | proposed |
| T-005 | contextualized_by | N-03 | MT-3 | open |
| T-006 | evaluated_by | N-03 | M-DEADLINE | open |
| T-007 | contextualized_by | N-04 | MT-4 | proposed |
| T-008 | evaluated_by | N-04 | M-DEADLINE | proposed |
| T-009 | contextualized_by | N-05 | MT-2 | proposed |
| T-010 | evaluated_by | N-05 | M-COMPLETE | proposed |
| T-011 | derived_from | REQ-ALLOC-001 | N-01 | proposed |
| T-012 | constrains | REQ-ALLOC-001 | F-04 | proposed |
| T-013 | verifies | V-PRIORITY | REQ-ALLOC-001 | proposed |
| T-014 | derived_from | REQ-ALLOC-002 | N-05 | proposed |
| T-015 | constrains | REQ-ALLOC-002 | I-REQUEST | proposed |
| T-016 | verifies | V-TASK | REQ-ALLOC-002 | proposed |
| T-017 | derived_from | REQ-ALLOC-003 | N-05 | proposed |
| T-018 | constrains | REQ-ALLOC-003 | F-05 | proposed |
| T-019 | verifies | V-PRIORITY | REQ-ALLOC-003 | proposed |
| T-020 | derived_from | REQ-ALLOC-004 | N-02 | proposed |
| T-021 | constrains | REQ-ALLOC-004 | F-05 | proposed |
| T-022 | verifies | V-PRIORITY | REQ-ALLOC-004 | proposed |
| T-023 | derived_from | REQ-THREAD-001 | N-01 | proposed |
| T-024 | constrains | REQ-THREAD-001 | F-09 | proposed |
| T-025 | verifies | V-TIMING | REQ-THREAD-001 | proposed |
| T-026 | derived_from | REQ-THREAD-002 | N-02 | proposed |
| T-027 | constrains | REQ-THREAD-002 | F-09 | proposed |
| T-028 | verifies | V-TIMING | REQ-THREAD-002 | proposed |
| T-029 | derived_from | REQ-THREAD-003 | N-03 | open |
| T-030 | constrains | REQ-THREAD-003 | F-09 | open |
| T-031 | verifies | V-REFERENCE | REQ-THREAD-003 | not_evaluated |
| T-032 | derived_from | REQ-THREAD-004 | N-04 | proposed |
| T-033 | constrains | REQ-THREAD-004 | F-09 | proposed |
| T-034 | verifies | V-TIMING | REQ-THREAD-004 | proposed |
| T-035 | derived_from | REQ-TERM-001 | N-05 | proposed |
| T-036 | constrains | REQ-TERM-001 | F-08 | proposed |
| T-037 | verifies | V-PRODUCT | REQ-TERM-001 | proposed |
| T-038 | derived_from | REQ-DDIL-001 | N-05 | proposed |
| T-039 | constrains | REQ-DDIL-001 | F-06 | proposed |
| T-040 | verifies | V-CONTACT | REQ-DDIL-001 | proposed |
| T-041 | derived_from | REQ-DDIL-002 | N-05 | proposed |
| T-042 | constrains | REQ-DDIL-002 | F-09 | proposed |
| T-043 | verifies | V-MODEL | REQ-DDIL-002 | proposed |
| T-044 | derived_from | REQ-IF-001 | N-05 | proposed |
| T-045 | constrains | REQ-IF-001 | I-DOWNLINK | proposed |
| T-046 | verifies | V-INTERFACE | REQ-IF-001 | proposed |
| T-047 | derived_from | REQ-IF-002 | N-05 | proposed |
| T-048 | constrains | REQ-IF-002 | I-DOWNLINK | proposed |
| T-049 | verifies | V-CONTACT | REQ-IF-002 | proposed |
| T-050 | contains | E-SYSTEM | E-PROVIDER | modeled |
| T-051 | contains | E-SYSTEM | E-TASKING | modeled |
| T-052 | contains | E-SYSTEM | E-TERMINAL | modeled |
| T-053 | contains | E-PROVIDER | E-SATELLITE | modeled |
| T-054 | allocated_to | F-02 | E-SATELLITE | modeled |
| T-055 | allocated_to | F-06 | E-SATELLITE | modeled |
| T-056 | allocated_to | F-07 | E-TERMINAL | modeled |
| T-057 | allocated_to | F-08 | E-TERMINAL | conditional |
| T-058 | exchanges | E-SATELLITE | I-DOWNLINK | modeled |
| T-059 | exchanges | I-DOWNLINK | E-TERMINAL | modeled |
| T-060 | satisfies | A4_PROGRESSIVE | REQ-ALLOC-001 | modeled |
| T-061 | candidate_for | A5_CONTACT_AWARE | REQ-ALLOC-003 | modeled |
| T-062 | candidate_for | A6_THREAD_AWARE_PRIORITY | REQ-ALLOC-004 | modeled |
| T-063 | constrains | REQ-ALLOC-002 | I-DIRECT | proposed |
| T-064 | verifies | V-PRODUCT | REQ-THREAD-001 | proposed |
| T-065 | verifies | V-PRODUCT | REQ-THREAD-002 | proposed |
| T-066 | derived_from | REQ-TERM-001 | N-01 | proposed |
| T-067 | derived_from | REQ-TERM-001 | N-02 | proposed |
| T-068 | verifies | V-TIMING | REQ-DDIL-002 | proposed |
| T-069 | verifies | V-INTERFACE | REQ-IF-002 | proposed |
| T-070 | constrains | REQ-ALLOC-001 | F-05 | proposed |
| T-071 | constrains | REQ-ALLOC-001 | F-06 | proposed |
| T-072 | constrains | REQ-ALLOC-002 | F-01 | proposed |
| T-073 | constrains | REQ-THREAD-001 | F-07 | proposed |
| T-074 | constrains | REQ-THREAD-001 | F-10 | proposed |
| T-075 | constrains | REQ-THREAD-002 | F-07 | proposed |
| T-076 | constrains | REQ-THREAD-002 | F-10 | proposed |
| T-077 | constrains | REQ-THREAD-004 | F-07 | proposed |
| T-078 | constrains | REQ-THREAD-004 | F-10 | proposed |
| T-079 | constrains | REQ-IF-002 | F-06 | proposed |
| T-080 | constrains | REQ-IF-002 | F-07 | proposed |
| T-081 | allocated_to | F-09 | E-TERMINAL | modeled |
| T-082 | candidate_for | A3_ROI_FIRST | REQ-THREAD-002 | conditional |
| T-083 | uses_interface | A3_ROI_FIRST | I-DOWNLINK | modeled |
| T-084 | supports_claim | V-TIMING | CL-005 | modeled |


## ID migrations

| Previous label | Current label | Reason |
| --- | --- | --- |
| REQ-CORRECT-001 | MIC-001 | Simulation correctness is a model integrity check |
| REQ-CORRECT-002 | MIC-002 | Simulation correctness is a model integrity check |
| REQ-CORRECT-003 | MIC-003 | Simulation correctness is a model integrity check |
| REQ-CORRECT-004 | MIC-004 | Simulation correctness is a model integrity check |
| MT-3 battle damage assessment | MT-3 notional change assessment | Scope wording excludes strike support; P3 remains only a size proxy for an unimplemented change product. |
