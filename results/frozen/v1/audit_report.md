# Audit Report
Scanned directory: C:\Users\noahh\OneDrive - West Point\leo-edge-architecture\results\frozen\v1
CSV files found: 17
Rows processed: 54025

## Metric Summary
| Metric | Count | Min | Max | Mean |
| --- | --- | --- | --- | --- |
| tfup_s | 50048 | 3.6 | 820 | 145.813 |
| tcp_s | 50228 | 5.2 | 820 | 156.066 |
| contact_utilization | 48 | 0.0213333 | 2.66667 | 0.552009 |
| processing_energy_j | 54 | 0 | 600 | 217.222 |
| deadline_met | 0 | N/A | N/A | N/A |

## Invariant Checks
- Invariant OK: tfup_s >= 0
- Invariant OK: tcp_s >= 0
- Invariant OK: processing_energy_j >= 0
- Invariant OK: contact_utilization >= 0
- Warning: contact_utilization >1 in 1 rows (max 2.667)
- Invariant SKIP: deadline_met not found

## Files
- confidence_intervals.csv
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
- fig02_data.csv
- fig03_data.csv
- fig04_data.csv
- monte_carlo.csv