# Stakeholders and measures

The study follows a soldier using a generic Army-owned terminal. The soldier requests imagery of a synthetic area and needs to know whether a complete product is available before the stated time limit. Here, “readable” means the terminal can present the modeled product. The study does not test whether a soldier can interpret it or use it to make a real decision.

| Stakeholder | Need in the study | Outside the model |
|---|---|---|
| Soldier at the terminal | Request imagery, check its delivery state, and view a complete product with the requested coverage and detail. | Soldier trials, display testing, image interpretation, and operational usefulness. |
| Terminal operator | Check whether a product is complete and whether the terminal can derive a smaller view from a full scene. | Actual hardware, workload, training, and procedures. |
| Commercial imagery provider | Receive a clear request and identify each product, its order, and its delivery state. | Provider implementation, service guarantees, and contracts. |
| Acquisition decision maker | See which functions and exchanges belong to the service and which belong at the terminal. | Costs, procurement choices, and acquisition recommendations. |

An interrupted contact can leave only part of a product at the terminal. The study records that transfer as incomplete. If no sufficient product arrives before the limit, the soldier has no new usable product in time. The model does not substitute an old image or infer what the soldier should do.

The main measure is the time until the first complete product meets the requested coverage and assumed detail. Repeated area updates start the clock at each collection; the other scenarios start it when the request is made. The study also records whether the time limit was met and whether a usable product arrived. Other measures are reported only when the selected evidence includes them. The [scenarios](MISSION_THREADS.md) define the requests, and [requirements](REQUIREMENTS.md) connect them to system behavior. A simulated success depends on assumed product usefulness and says nothing about soldier effectiveness.
