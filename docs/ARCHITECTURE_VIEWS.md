# Reading the generated architecture views

The diagrams and tables in [generated views](reference/VIEWS.md) come from the four [model catalogs](../model/). Each view answers a different question about the conceptual system:

| View | Question |
|---|---|
| System structure | Which elements are within the commercial service and Army owned terminal boundary? |
| Functional activity | What work must happen from request to usable image before it is allocated? |
| Interfaces and delivery sequence | What information crosses the boundary, and when can processing, contact, and terminal derivation occur? |
| Product state | When is an image planned, partially received, complete, usable, or too late? |
| Requirements and traceability | Which need, requirement, function, interface, measure, and verification case support a claim? |
| Parametric dependencies | Which assumptions affect preparation, transfer, access, and deadline outcome? |

Each edge names its relationship: containment, function allocation, information exchange, requirement satisfaction, or verification. The [candidate allocations](ALLOCATION_SPACE.md) define all seven designs. Selected behavior drawings show the strategies with the clearest differences.

Mermaid communicates elements and relationships aligned with SysML concepts. It is not a formal SysML file. The [modeling plan](MODELING_PLAN.md) records that choice. Validate the catalog and regenerate views after a model edit; do not change the generated diagrams by hand.
