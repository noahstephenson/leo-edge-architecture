# Assumptions and sources

The [assurance catalog](../model/assurance.yaml) gives each assumption an identifier and provenance. The [current configuration](../results/current/config.json) records the values used in the selected contact cases. Those values describe study cases; they are not measurements of a spacecraft or terminal.

| Source label | Meaning |
|---|---|
| Measured benchmark | Local test with stated hardware and method; it does not measure a flight processor. |
| Literature, public context, or vendor | A value or motivation tied to an exact cited source. Public context does not create a requirement. |
| Analytical assumption | A simplification chosen to make the model calculable. |
| Sensitivity only | A notional value used to explore how results change. |

## Inputs most important to interpretation

| Assumption | Selected input | Consequence |
|---|---|---|
| Scene and product size | A full raw scene is one billion bytes. The compressed full scene is assumed to be 30% of raw size. A crop is 5% of raw size in the crop-first candidate. | Transmission order matters only if a product fits into available contact capacity. |
| Image quality | A crop is assumed to cover its declared corridor. All full scene encodings retain native spatial resolution for the terminal derivation check. | The model does not test crop geometry, radiometric quality, or operator interpretation. |
| Terminal | The vehicle case receives at 50 megabits per second and derives a smaller view in 5 seconds. The dismounted case uses 5 megabits per second and 30 seconds. | These are generic sensitivity cases, not actual terminal specifications. |
| Contact | Synthetic satellites are individually propagated. Effective rate is constant within a contact; rate degradation and denied contacts are scenario inputs. | The resulting access schedule is internally consistent, not a service forecast. |
| Scenario | Product needs, deadlines, tasking delays, and prior-image availability are assumed. | Deadline success means success under these stated case rules only. |

The [configuration](../results/current/config.json) gives the other product sizes, orbit geometry, terminal coordinates, processing delay, and degradation settings. The [model reference](MODEL_REFERENCE.md) explains how they enter the calculations.

The optional [synthetic image benchmark](../experiments/image_benchmark.py) records local timings and machine information. It is outside the selected evidence and does not calibrate flight processing, terminal performance, or image utility. The previous inputs lacked a source/license record and have been removed. [Verification](V_AND_V.md) separates tested calculations from open questions about product quality and operational use.

Quicklook and crop sizes are 2% and 5% of scene bytes across A2/A3/A4/A6; only metadata and thumbnail bytes are fixed. These values and processing fractions come from the [packaged configuration](../src/leo_edge/product_sizing.yaml). Collection occurs at peak elevation in a sampled visibility window. This is a proxy without optical field of regard, illumination, clouds, or collection duration. Baseline scans use 30 seconds; a 5-second scan and nearby synthetic time/location cases test sensitivity.

One-site results mean receipt at the requesting terminal. Four-site results assume a pooled connected receiver and zero forwarding delay. Repeated collections each reuse an independent transfer budget; their results are opportunity tests, not a sustained stream. Combined degradation changes several inputs together. Its 180-second tasking delay alone exceeds MT-1's 120-second deadline, so no transfer policy can make those requests timely.
