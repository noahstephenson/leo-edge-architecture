# LEO imagery at the tactical edge

A soldier at a tactical terminal needs an image that covers the requested area and arrives in time to use it. This study asks which parts of that delivery a commercial low Earth orbit imagery service should perform and which parts belong at the Army-owned terminal. The scenarios, terminal locations, product utility, and deadlines are synthetic. The work is unofficial and states no Army requirement, service design, or operational capability.

## From request to usable image

A satellite must pass over the requested area to collect a scene and have contact with the receiving terminal to send it. Those opportunities may overlap. A short contact may carry only part of the image; the rest waits for another pass. The architecture choice is what the service prepares and sends first, and what the terminal does after receipt.

The satellite may send a full scene, a reduced whole-scene view, or a crop of a declared area. A crop cannot answer a whole-scene request solely because it has finer detail. A full scene may let the terminal derive a smaller view, but the transfer and processing must finish before the assumed deadline. The [concept of operations](docs/CONOPS.md) follows this sequence from the request to the soldier's terminal.

## Model and method

The project uses selected conceptual-design guidance from [NASA-HDBK-1009A](https://standards.nasa.gov/system/files/tmp/2025-03-12-NASA-HDBK-1009A.pdf). The [modeling plan](docs/MODELING_PLAN.md) records the scope and tailoring. Four structured [model catalogs](model/) define needs, requirements, functions, elements, interfaces, alternatives, measures, and their relationships. The [generated architecture views](docs/reference/VIEWS.md) and [traceability tables](docs/reference/TRACEABILITY.md) let a reader follow a need through a proposed requirement, behavior, allocation, interface, measure, and verification case. Mermaid presents SysML-aligned concepts; the files are not formal SysML or a NASA-reviewed product.

Start with the [stakeholders and assumed scenarios](docs/STAKEHOLDERS.md), then read the [requirements](docs/REQUIREMENTS.md) and [functional architecture](docs/FUNCTIONAL_ARCHITECTURE.md). The functions are defined before the [candidate allocations](docs/ALLOCATION_SPACE.md) assign them to the service and terminal. The [interfaces](docs/INTERFACES.md) describe what must be known about a request, received product, and delivery status. The full ID inventory is in the [model catalog](docs/reference/MODEL_CATALOG.md).

## Seven delivery choices

The candidates share the same request, collection, and contact opportunities within a comparison case. They differ in what the satellite prepares, its transmission order, and whether the terminal must wait for a complete scene before deriving the requested view.

| Candidate | Delivery approach |
|---|---|
| A0 | Raw full scene, followed by eligible terminal derivation |
| A1 | Compressed full scene |
| A2 | Whole-scene quicklook before the full scene |
| A3 | Declared-area crop before the full scene |
| A4 | Fixed progression from metadata through the full scene |
| A5 | Raw or compressed full scene chosen from an assumed contact-margin rule |
| A6 | Progressive products ordered around the scenario's needed tier |

The [allocation comparison](docs/ALLOCATION_SPACE.md) gives the complete product and function records. The [generated views](docs/reference/VIEWS.md) show selected behavior, product states, and boundary exchanges.

## What the analysis can show

A first calculation compares exposed processing time with the transfer time saved by sending fewer bytes. The selected [contact analysis](results/current/) then tests paired requests using individually propagated synthetic satellites, separate collection and terminal locations, interrupted contacts, and terminal processing. The [trade study](docs/TRADE_STUDY.md) reports where access prevents timely delivery and where a fitting early product changes a modeled outcome. It gives denominators and uncertainty intervals for sampled success rates. The [figure](figures/current/mt2_selected_deadline.png) shows one case.

The results concern delivery under stated assumptions. The study has not tested whether a soldier can use the image to make a decision, whether lossy compression preserves all needed content, or whether a real service can provide the modeled behavior. [Assumptions](docs/ASSUMPTIONS.md) identify measured, sourced, and sensitivity inputs; [verification and validation](docs/V_AND_V.md) separates tested model logic from open operational questions. [Engineering status](docs/ENGINEERING_STATUS.md) lists the remaining checks. The [manuscript draft](paper/manuscript_draft.md) presents the architecture and selected evidence; its [submitted abstract](paper/submitted_abstract.md) remains unchanged.

## Inspect and reproduce

Install [uv](https://docs.astral.sh/uv/). The project pins Python 3.11 in `.python-version`. From the repository root, run:

```bash
uv sync
uv run python scripts/validate_model.py
uv run python scripts/generate_model_views.py --check
uv run pytest
uv run python experiments/e13_mbse_evidence.py --check
```

After editing a catalog, regenerate the views with `uv run python scripts/generate_model_views.py`. To recompute the selected cases in an ignored scratch directory, run `uv run python experiments/e13_mbse_evidence.py --output results/reproduced/current`. The runner refuses to overwrite a nonempty directory. The [evidence manifest](results/current/manifest.json) records inputs, source hashes, and audit information.

The [project roadmap](docs/PROJECT_ROADMAP.md) tracks the method steps, and the [decision log](docs/DECISION_LOG.md) records changes to the model's meaning. The repository uses the [MIT license](LICENSE).
