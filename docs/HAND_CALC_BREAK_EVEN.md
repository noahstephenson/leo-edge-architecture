# Hand Calculation: Break-Even Rate

Worked example of the analytical break-even condition used to sanity-check
the simulation (`docs/MODEL_REFERENCE.md`, `docs/ARCHITECTURE_VIEWS.md`'s
Physical View). This math is unaffected by the Part 1 correctness fixes
(`docs/DECISION_LOG.md` ADR-008); only the "mapping to simulation" section
below was refreshed to use `results/frozen/v2/e03_results.csv` instead of
the retired v1 numbers.

```
T_proc < (D_r - D_p) / R
```

where `T_proc` is onboard processing time, `D_r` is raw scene size, `D_p`
is the processed (transmitted) size, and `R` is downlink rate in bytes per
second. Equivalently, the break-even rate is:

```
R* = (D_r - D_p) / T_proc
```

## Example numbers

Using the nominal scene from `e03_static_architectures.py`:

```
D_r = 1,000,000,000 bytes  (1.0 GB raw)
D_p = 300,000,000 bytes    (0.3 GB, CompressedFull's output)
T_proc = 20 s

R*_bytes = (1,000,000,000 - 300,000,000) / 20 = 35,000,000 bytes/s
R*_bps = 35,000,000 * 8 = 280,000,000 bps = 280 Mbps
```

Interpretation: with 20 s of onboard compression, transmitting 0.3 GB
instead of 1.0 GB saves transmission time. That save is worth the 20 s
processing cost, in this simple closed-form model, once the downlink is
slower than about 280 Mbps.

If processing can start before contact, the exposed processing time is
`T_proc_exposed = max(0, T_proc - T_lead)`, and the effective break-even
rate increases.

## Mapping to simulation (results/frozen/v2/e03_results.csv)

```
CompressedFull, rate_bps=10,000,000:  tfup_s=260.0, tcp_s=260.0, completed=True
CompressedFull, rate_bps=25,000,000:  tfup_s=116.0, tcp_s=116.0, completed=True
GroundOnly,     rate_bps=10,000,000:  tfup_s=NaN,   tcp_s=NaN,   completed=False (bytes_transmitted capped at 375,000,000 of 1,000,000,000 needed)
GroundOnly,     rate_bps=25,000,000:  tfup_s=NaN,   tcp_s=NaN,   completed=False (bytes_transmitted capped at 937,500,000 of 1,000,000,000 needed)
```

The simulation shows CompressedFull winning even more decisively than the
280 Mbps analytical estimate suggests: at 10 and 25 Mbps, GroundOnly
doesn't just lose on speed, it doesn't complete a delivery in this single
300 s contact window at all (`docs/DECISION_LOG.md` ADR-008's censoring
fix). The analytical model assumes both options eventually finish and asks
which is faster; the simulation shows that below the break-even rate, raw
downlink of a 1 GB scene in a single 300 s window isn't just slower, it's
frequently impossible.

GroundOnly does complete at 50 and 100 Mbps (`tfup_s` 160.0 and 80.0
respectively), where capacity exceeds the full 1 GB scene. The analytical
280 Mbps break-even and the simulated crossover (somewhere between 25 and
50 Mbps, where GroundOnly starts completing) are in the same direction but
not numerically identical, which is expected: the analytical model has no
notion of a single fixed contact window's byte capacity, while the
simulation does.

This hand calc is a first-order sanity check on the model's direction, not
a claim that the analytical and simulated numbers should match exactly.
