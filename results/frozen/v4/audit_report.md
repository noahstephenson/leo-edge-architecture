# Audit Report
Scanned directory: results\frozen\v4
CSV files found: 30
Rows processed: 120450

## Metric Summary
Censored (NaN) counts rows where the product never completed within its contact window; Min/Max/Mean are computed only over completed deliveries.

| Metric | Count | Censored (NaN) | Min | Max | Mean |
| --- | --- | --- | --- | --- | --- |
| tfup_s | 39810 | 10250 | 3.6 | 277.449 | 106.255 |
| tcp_s | 9861 | 40379 | 44 | 500 | 268.862 |
| contact_utilization | 60 | 0 | 0.0676899 | 1 | 0.588145 |
| processing_energy_j | 66 | 0 | 0 | 600 | 223.182 |
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
- e11_cadence_success.csv
- e11_cadence_trials.csv
- e11_mission_thread_success.csv
- e11_mission_thread_trials.csv
- e11_significance_tests.csv
- e12_access_sweep.csv
- e12_cell_status.csv
- e12_cost_tradeoff.csv
- e12_feasibility_floors.csv
- e12_km_summary.csv
- e12_significance_by_cell.csv
- e12_tolerance_sensitivity.csv
- fig02_data.csv
- fig03_data.csv
- fig04_data.csv
- monte_carlo.csv
- trade_study_scores.csv
- trade_study_sensitivity.csv