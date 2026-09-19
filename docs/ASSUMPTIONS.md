# Assumptions

These are the concrete assumptions built into the model, where they come from, and how confident we are in them. If a number here changes, the experiments and figures need to be regenerated.

Every row is labeled MEASURED (a script actually ran on real hardware and produced this number) or ASSUMED (a design value chosen to be reasonable, not measured). A laptop timing a Pillow JPEG operation is a real measurement of that laptop, not of flight hardware or a tactical edge terminal; MEASURED here never means "representative of a fielded system," only "not made up."

| ID | Assumption | Label | Source | Confidence |
|---|---|---|---|---|
| ASM-LINK-001 | Downlink rate is constant during a contact window | ASSUMED | Design simplification | Low. Real rate varies with elevation; `link.py`'s `rate_bps()` models this separately but the static architecture comparisons use a fixed rate. |
| ASM-LINK-002 | Radio draws 25 W during transmission | ASSUMED | `config/product_sizing.yaml: power.radio_power_w`, typical for a COTS smallsat transceiver | Medium |
| ASM-PROC-001 | Onboard processor draws 15 W while processing | ASSUMED | `config/product_sizing.yaml: power.processing_power_w`, typical for a COTS smallsat compute module | Medium |
| ASM-PROC-002 | Compressed-full output is 30% of raw scene size | ASSUMED | `config/product_sizing.yaml: compressed_full.size_fraction` | Medium. `imagery/benchmark.py` measures real JPEG compression ratios closer to 3-6%, but that's for aggressive quicklook-style compression; the compressed-full architecture is meant to represent lighter, higher-fidelity compression, so 30% is a deliberately conservative design value, not the JPEG benchmark result. |
| ASM-PROC-003 | Quicklook product is 2% of raw scene size | ASSUMED | `config/product_sizing.yaml: quicklook.size_fraction` | Medium |
| ASM-PROC-004 | ROI product is 10% of raw scene size | ASSUMED | `config/product_sizing.yaml: roi.size_fraction` | Medium |
| ASM-PROC-005 | Progressive tier byte sizes (20 KB metadata, 512 KB thumbnail, 10 MB quicklook, 50 MB ROI) are fixed targets, not scene-relative fractions | ASSUMED | `config/product_sizing.yaml: progressive.*` | Low. These are independent of, and not reconciled with, the ratio-based sizes used by QuicklookFirst/RoiFirst (ASM-PROC-003/004); a scene where the two disagree is a known modeling seam, not a hidden consistency guarantee. |
| ASM-ORBIT-001 | Orbit is circular, propagated from a synthetic TLE at a fixed epoch (2020-01-01) | ASSUMED (real propagator) | `orbit/access.py` | High for a first-order study. A circular orbit is a design simplification, but Skyfield's SGP4 propagator is real, not a stand-in, so contact-window statistics come from real orbital mechanics given that simplified orbit. |
| ASM-ORBIT-002 | Minimum elevation for contact is 10 degrees | ASSUMED | `experiments/e01_orbit_contacts.py`, `config/orbits.yaml` | Medium, a common working value for a low-gain ground terminal |
| ASM-STORAGE-001 | Flash write amplification factor is 1.5x | ASSUMED | `storage.py`'s `MassMemory` | Low. Representative of typical flash overhead, not measured on real hardware. |
| ASM-BENCH-001 | Image-processing timing and compression numbers in `results/frozen/v3/e02_*.csv` and `results/frozen/image_benchmark*.csv` are measured, not assumed | MEASURED | `imagery/benchmark.py`, real Pillow JPEG/resize/crop operations on real or synthetic tiles, run on a laptop | High that the numbers are real; Low that they represent flight or tactical-terminal hardware. These are the only MEASURED rows in this table, and they are not currently wired into `architectures.py`'s sizing ratios (ASM-PROC-002/003/004) at all, so "measured" here describes the benchmark data only, not the simulation's product-size assumptions. |

## Why this matters

A million simulation runs do not fix a wrong assumption. The distinction that matters most here is between numbers that are **measured** (the image-processing benchmark, on a laptop, not flight or terminal hardware), numbers that come from a **real geometric/physical model** (the orbit propagator), and numbers that are **design assumptions** picked to be reasonable for a COTS smallsat (compression ratios, power draws, Progressive tier sizes). The docs and figures are written to make clear which is which, and the regime map in `figures/fig04.png` should be read as showing where the assumed-parameter architectures cross over, not as a claim about a specific flown spacecraft or a specific tactical terminal.
