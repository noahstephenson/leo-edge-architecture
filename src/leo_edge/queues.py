"""Product queue with priority handling."""

from dataclasses import dataclass, field
from typing import Any, List, Tuple


@dataclass
class ProductQueue:
    """Priority queue for products.

    Higher priority values are served first.
    """

    _items: List[Tuple[int, Any]] = field(default_factory=list)

    def add(self, product: Any, priority: int) -> None:
        """Add product with given priority."""
        self._items.append((priority, product))

    def pop_next(self) -> Any:
        """Pop and return highest priority product. Returns None if empty."""
        if not self._items:
            return None
        # Find max priority
        idx = max(range(len(self._items)), key=lambda i: self._items[i][0])
        priority, product = self._items.pop(idx)
        return product

    def __len__(self) -> int:
        return len(self._items)
