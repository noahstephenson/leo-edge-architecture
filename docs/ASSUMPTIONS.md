# Assumptions

These are the concrete assumptions built into the model, where they come from, and how confident we are in them. If a number here changes, the experiments and figures need to be regenerated.

| ID | Assumption | Source | Confidence |
|---|---|---|---|
| ASM-LINK-001 | Downlink rate is constant during a contact window | Design simplification | Low. Real rate varies with elevation; `link.py`'s `rate_bps()` models this separately but the static architecture comparisons use a fixed rate. |
| ASM-LINK-002 | Radio draws 25 W during transmission | Assumed, typical for a COTS smallsat transceiver | Medium |
| ASM-PROC-001 | Onboard processor draws 15 W while processing | Assumed, typical for a COTS smallsat compute module | Medium |
| ASM-PROC-002 | Compressed-full output is 30% of raw scene size | Assumed compression ratio in `architectures.py` | Medium. `imagery/benchmark.py` measures real JPEG compression ratios closer to 3-6%, but that's for aggressive quicklook-style compression; the compressed-full architecture is meant to represent lighter, higher-fidelity compression, so 30% is a deliberately conservative design value, not the JPEG benchmark result. |
| ASM-PROC-003 | Quicklook product is 2% of raw scene size | Assumed in `architectures.py` | Medium |
| ASM-PROC-004 | ROI product is 10% of raw scene size | Assumed in `architectures.py` | Medium |
| ASM-ORBIT-001 | Orbit is circular, propagated from a synthetic TLE at a fixed epoch (2020-01-01) | `orbit/access.py` | High for a first-order study. A circular orbit and Skyfield's SGP4 propagator are enough to generate realistic access-window statistics without needing a full mission-design tool. |
| ASM-ORBIT-002 | Minimum elevation for contact is 10 degrees | `experiments/e01_orbit_contacts.py`, `config/orbits.yaml` | Medium, a common working value for a low-gain ground terminal |
| ASM-STORAGE-001 | Flash write amplification factor is 1.5x | `storage.py`'s `MassMemory` | Low. Representative of typical flash overhead, not measured on real hardware. |
| ASM-BENCH-001 | Image-processing timing and compression numbers in `results/frozen/v1/e02_*.csv` are measured, not assumed | `imagery/benchmark.py`, real Pillow JPEG/resize/crop operations on real or synthetic tiles | High, this is a real benchmark, not a model |

## Why this matters

A million simulation runs do not fix a wrong assumption. The distinction that matters most here is between numbers that are **measured** (the image-processing benchmark), numbers that come from a **real geometric/physical model** (the orbit propagator), and numbers that are **design assumptions** picked to be reasonable for a COTS smallsat (compression ratios, power draws). The paper and figures are written to make clear which is which, and the regime map in `figures/fig04.png` should be read as showing where the assumed-parameter architectures cross over, not as a claim about a specific flown spacecraft.
