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

The [local image benchmark](../data/imagery/benchmark/image_benchmark_normalized.csv) is labeled measured in the catalog. Its ratios and timings are not used as flight processor or terminal capability estimates in the selected cases. More simulation runs cannot show whether a quicklook or crop helps a user. [Verification](V_AND_V.md) separates tested calculations from open questions about product quality and operational use.
