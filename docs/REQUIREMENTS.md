# Requirements

These are the requirements the system architecture and simulation are built against. Each one maps to code in `src/leo_edge/` and is checked either by a unit test in `tests/` or by an experiment in `experiments/`.

## Mission

- **MR-001**: The system delivers a geospatial data product from a LEO spacecraft to a local ground user.
- **MR-002**: The system supports direct spacecraft-to-ground-terminal downlink, with no requirement to route through a centralized ground station first.
- **MR-003**: The system supports at least one reduced-size product tier in addition to the complete, full-resolution product.

## Spacecraft

- **SR-001**: The spacecraft model includes imaging, processing, storage, power, and communications functions (`processing.py`, `storage.py`, `power.py`, `link.py`).
- **SR-002**: Processing can be configured between bypass (raw downlink) and onboard-processing modes. Each architecture in `architectures.py` implements this choice differently.
- **SR-003**: The spacecraft maintains a prioritized queue of generated data products (`queues.py`).
- **SR-004**: Spacecraft storage is finite and enforced (`storage.py`'s `MassMemory` raises on overflow).
- **SR-005**: Processing is constrained by available energy (`power.py`'s `PowerSystem`, including a brownout policy that pauses processing when charge is low).

## Ground

- **GR-001**: The ground terminal receives direct downlink during line-of-sight contact windows.
- **GR-002**: The ground terminal can perform additional processing after receiving a product.
- **GR-003**: Ground-side processing throughput is finite, not instantaneous.

## Simulation

- **SIM-001**: Contact windows are generated from an explicit orbit and ground-station geometry model (`orbit/access.py`, using Skyfield).
- **SIM-002**: Image-product sizes and processing times come from real or reproducible benchmarks (`imagery/benchmark.py`), not invented numbers.
- **SIM-003**: All results in `results/frozen/v1/` are reproducible from version-controlled code and configuration by running the scripts in `experiments/`.

## Key interfaces

| Interface | Data or resource passed |
|---|---|
| payload to processor | raw imagery |
| processor to storage | product files |
| storage to scheduler | product metadata |
| scheduler to radio | prioritized product stream |
| radio to ground | RF downlink |
| receiver to ground processor | received product |
| ground processor to user | final or quicklook product |
| contact predictor to scheduler | predicted contact capacity |
| power manager to processor | processing permission |

See `docs/INTERFACES.md` for data formats, units, and timing/energy budgets.
