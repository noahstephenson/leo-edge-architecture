# Audit Report
Scanned directory: results\frozen\v2
CSV files found: 14
Rows processed: 54012

## Metric Summary
Censored (NaN) counts rows where the product never completed within its contact window; Min/Max/Mean are computed only over completed deliveries.

| Metric | Count | Censored (NaN) | Min | Max | Mean |
| --- | --- | --- | --- | --- | --- |
| tfup_s | 39800 | 10248 | 3.6 | 277.449 | 106.267 |
| tcp_s | 9855 | 40373 | 44 | 500 | 268.946 |
| contact_utilization | 48 | 0 | 0.0676899 | 1 | 0.629342 |
| processing_energy_j | 54 | 0 | 0 | 600 | 217.222 |
| deadline_met | 0 | 0 | N/A | N/A | N/A |

## Invariant Checks
- Invariant OK: tfup_s >= 0
- Invariant OK: tcp_s >= 0
- Invariant OK: processing_energy_j >= 0
- Invariant OK: contact_utilization in [0,1]
- Invariant SKIP: deadline_met not found

## Files
- e01_access_windows.csv
- e02_compression.csv
- e02_quicklook.csv
- e02_roi.csv
- e03_results.csv
- e04_contact_sweep.csv
- e05_power_sweep.csv
- e06_queue_stress.csv
- e07_adaptive_policy.csv
- e08_uncertainty.csv
- e09_constellation.csv
- e10_storage_wear.csv
- fig04_data.csv
- monte_carlo.csv