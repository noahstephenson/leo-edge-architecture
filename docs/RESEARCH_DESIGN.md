# Research design

The study asks how a commercial imagery service and an Army owned tactical terminal should divide tasking, collection, preparation, prioritization, and delivery as information needs and contact conditions change. The [modeling plan](MODELING_PLAN.md) explains the conceptual design method. The [operational context](OPERATIONAL_CONTEXT.md) gives the motivation and scope for the notional scenarios.

The architecture is the primary research product. A reader should be able to follow each claim from a stakeholder need through the requirement, function, candidate allocation, boundary exchange, measure, and verification case. The [structured model](../model/) records those links, and [generated traceability](reference/TRACEABILITY.md) displays them.

A simple timing relation checks when smaller product size can offset image processing time. Selected synthetic contact cases then examine collection access, terminal access, same pass delivery, interruptions, and byte carryover. Paired requests hold those opportunities constant within each comparison. The [trade study](TRADE_STUDY.md) interprets the selected outcomes without claiming a generally preferred candidate.

The study can test model consistency and compare delivery behavior under its inputs. It cannot establish the utility of imagery to an operator, the feasibility of a commercial implementation, or the performance of a real tactical terminal. [Assumptions](ASSUMPTIONS.md) and [verification](V_AND_V.md) make those limits explicit.
