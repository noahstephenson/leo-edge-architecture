"""Mass memory storage model."""

from dataclasses import dataclass, field


@dataclass
class MassMemory:
    """Simple mass memory model.

    Attributes:
        capacity_bytes: Total storage capacity.
        used_bytes: Currently used bytes.
    """

    capacity_bytes: int
    used_bytes: int = field(default=0)
    write_amplification_factor: float = field(default=1.5)
    endurance_cycles_per_cell: int = field(default=3000)
    total_physical_writes_bytes: int = field(default=0)

    def __post_init__(self) -> None:
        self.used_bytes = max(0, min(self.used_bytes, self.capacity_bytes))

    def store(self, bytes_: int) -> None:
        """Allocate bytes in storage. Raises if over capacity."""
        if bytes_ < 0:
            raise ValueError("bytes must be non-negative")
        if self.used_bytes + bytes_ > self.capacity_bytes:
            raise ValueError("Insufficient storage capacity")
        # Wear model: physical writes = logical * amplification
        physical_bytes = int(bytes_ * self.write_amplification_factor)
        self.total_physical_writes_bytes += physical_bytes
        self.used_bytes += bytes_

    def free(self, bytes_: int) -> None:
        """Free bytes from storage."""
        if bytes_ < 0:
            raise ValueError("bytes must be non-negative")
        # Freeing also causes metadata writes; model with reduced amplification
        physical_bytes = int(bytes_ * self.write_amplification_factor * 0.3)
        self.total_physical_writes_bytes += physical_bytes
        self.used_bytes = max(0, self.used_bytes - bytes_)

    def occupancy(self) -> float:
        """Return storage occupancy as fraction 0-1."""
        if self.capacity_bytes == 0:
            return 0.0
        return self.used_bytes / self.capacity_bytes

    def max_writes_bytes(self) -> int:
        """Total physical write capacity before wear-out."""
        return self.capacity_bytes * self.endurance_cycles_per_cell

    def wear_fraction(self) -> float:
        """Fraction of endurance consumed [0-1]."""
        max_writes = self.max_writes_bytes()
        if max_writes == 0:
            return 0.0
        return min(1.0, self.total_physical_writes_bytes / max_writes)

    def health_fraction(self) -> float:
        """Remaining health fraction [0-1]."""
        return max(0.0, 1.0 - self.wear_fraction())
