# Hand calculation break even rate

This document shows a worked example of the analytical break even condition

T_proc < (D_r - D_p) / R

where
T_proc is processing time on the satellite
D_r is raw image size
D_p is processed image size transmitted
R is downlink rate in bytes per second

Equivalently the break even rate is

R* = (D_r - D_p) / T_proc

## Example numbers

Use the nominal scene from e03:
D_r = 1,000,000,000 bytes = 1.0 GB
D_p for CompressedFull = 300,000,000 bytes = 0.3 GB
T_proc = 20 s

Rate in bytes per second:
R*_bytes = (1,000,000,000 - 300,000,000) / 20
R*_bytes = 700,000,000 / 20
R*_bytes = 35,000,000 bytes/s

Convert to bits per second:
R*_bps = 35,000,000 * 8 = 280,000,000 bps = 280 Mbps

Interpretation: with 20 s of onboard compression, transmitting 0.3 GB instead of 1.0 GB saves transmission time. The save is worth the 20 s processing cost when the downlink is slower than about 280 Mbps in this simple model.

If processing can start before contact, the exposed processing time is
T_proc_exposed = max(0, T_proc - T_lead)
and the effective break even rate increases.

## Mapping to simulation

Results file: results/frozen/v1/e03_results.csv

CompressedFull rows:
rate_bps 10,000,000 -> tfup_s 260.0, GroundOnly tfup_s 300.0
rate_bps 25,000,000 -> tfup_s 116.0, GroundOnly tfup_s 300.0

The simulation shows a benefit appearing between 10 Mbps and 25 Mbps, with a clear win at 25 Mbps:
architecture_name = CompressedFull, rate_bps = 25,000,000.0
scene_bytes = 1,000,000,000.0
processing_time_s = 20
tfup_s = 116.0
tcp_s = 116.0
bytes_transmitted = 300,000,000
contact_utilization = 0.32

GroundOnly at same rate:
tfup_s = 300.0, bytes_transmitted = 937,500,000

The analytical 280 Mbps estimate is higher than the simulated crossover. The difference is due to contact window limits, queueing, and the fact that TFUP and TCP in the simulation are contact constrained. The simulation captures intermittent LEO access, which reduces the effective transmission time saved and therefore lowers the observed break even rate.

This hand calc provides a first order sanity check. The simulation point at 25 Mbps is consistent with the direction of the effect, even if the absolute numbers differ because of contact and queue dynamics.
