# Interface implications

The conceptual architecture raises questions for a future service agreement or interface specification. This study makes no Army acquisition recommendation.

A request needs to state the coverage and timing required. A delivered product needs to identify its collection, footprint, fidelity, completeness, and whether more data remain queued. The terminal uses those fields to tell when the user has a complete image that meets the request. A crop label alone cannot establish whole scene coverage. A full scene may need further processing at the terminal before a smaller view is ready.

When contact ends mid-transfer, the product identity and byte progress must carry into a later pass. The conceptual [interfaces](INTERFACES.md) describe that exchange, and the [contact tests](V_AND_V.md) check the arithmetic. Interoperability with a real service has not been tested.

Provider preparation can reduce transmitted bytes and place a useful view earlier in a contact. Terminal derivation offers another path if a complete scene arrives in time. Collection and terminal access may prevent both paths from meeting a deadline. The [trade study](TRADE_STUDY.md) shows selected synthetic examples. A real decision would require image quality, terminal, service, cost, and user evidence beyond this project.
