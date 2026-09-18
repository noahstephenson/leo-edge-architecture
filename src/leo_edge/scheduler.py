"""Simple product scheduler for contact capacity."""

from dataclasses import dataclass
from typing import Any, List, Dict

from .queues import ProductQueue
from .power import PowerSystem
from .storage import MassMemory


@dataclass
class ProductScheduler:
    """Schedule products to fit within contact downlink capacity."""

    def schedule(self, products: List[Any], contact_capacity_bytes: int) -> List[Any]:
        """Return subset of products fitting in capacity.

        Products are expected to have attribute `size_bytes` or dict key `size_bytes`.
        Greedy first-fit in given order.
        """
        scheduled: List[Any] = []
        used = 0
        for p in products:
            size = getattr(p, "size_bytes", None)
            if size is None and isinstance(p, dict):
                size = p.get("size_bytes", 0)
            else:
                size = size or 0
            if used + size <= contact_capacity_bytes:
                scheduled.append(p)
                used += size
        return scheduled

    def simulate_step(
        self,
        queue: ProductQueue,
        power: PowerSystem,
        storage: MassMemory,
        contact_capacity_bytes: int,
        dt_s: float = 1.0,
    ) -> Dict[str, Any]:
        """Process one product from queue with power and storage checks.

        Returns updated state dict with invariants enforced:
        - SOC never < 0
        - storage used never negative
        - tx bytes <= contact capacity
        """
        product = queue.pop_next()
        state = {
            "product": None,
            "processed": False,
            "tx_bytes": 0,
            "soc_wh": power.soc,
            "storage_used_bytes": storage.used_bytes,
            "queue_len": len(queue),
        }

        if product is None:
            return state

        # Size and energy from product
        size_bytes = int(getattr(product, "bytes", getattr(product, "size_bytes", 0)))
        energy_j = float(getattr(product, "energy_cost", 0.0))
        energy_needed_wh = energy_j / 3600.0

        # Check power and storage before processing
        if power.soc < energy_needed_wh:
            # insufficient power, requeue product
            priority = int(getattr(product, "priority", 0))
            queue.add(product, priority)
            state["product"] = product
            return state

        free_bytes = storage.capacity_bytes - storage.used_bytes
        if free_bytes < size_bytes:
            # insufficient storage, requeue product
            priority = int(getattr(product, "priority", 0))
            queue.add(product, priority)
            state["product"] = product
            return state

        # Process: consume energy, store product
        power.soc = max(0.0, power.soc - energy_needed_wh)
        storage.store(size_bytes)

        state["product"] = product
        state["processed"] = True
        state["soc_wh"] = power.soc
        state["storage_used_bytes"] = storage.used_bytes

        # Transmit if fits in contact capacity
        if size_bytes <= contact_capacity_bytes and contact_capacity_bytes > 0:
            storage.free(size_bytes)
            state["tx_bytes"] = size_bytes
        else:
            # keep product in storage, no tx
            state["tx_bytes"] = 0

        state["queue_len"] = len(queue)
        state["storage_used_bytes"] = storage.used_bytes
        state["soc_wh"] = power.soc
        return state
