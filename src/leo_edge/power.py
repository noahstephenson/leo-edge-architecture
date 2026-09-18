"""Power system energy ledger."""

from dataclasses import dataclass, field


@dataclass
class PowerSystem:
    """Simple energy ledger for satellite power.

    Attributes:
        capacity_wh: Total battery capacity in Watt-hours.
        soc: Current state of charge in Watt-hours.
        power_draw_w: Last reported power draw in Watts.
    """

    capacity_wh: float
    soc: float = field(default=0.0)
    power_draw_w: float = field(default=0.0)
    brownout_threshold_wh: float = field(default=0.0)
    hysteresis_wh: float = field(default=5.0)
    processing_paused: bool = field(default=False)
    brownout_events: int = field(default=0)

    def __post_init__(self) -> None:
        if self.soc == 0.0:
            self.soc = self.capacity_wh
        self.soc = max(0.0, min(self.soc, self.capacity_wh))
        if self.brownout_threshold_wh <= 0.0:
            # Default 10% of capacity
            self.brownout_threshold_wh = 0.1 * self.capacity_wh

    def update(self, dt_s: float, power_w: float) -> None:
        """Update state of charge over dt_s seconds at power_w Watts.

        Energy consumed = power_w * dt_s / 3600 Wh.
        SOC is clamped to [0, capacity_wh].
        Brownout policy pauses processing when SOC falls below threshold.
        """
        self.power_draw_w = power_w
        energy_wh = power_w * dt_s / 3600.0
        self.soc = self.soc - energy_wh
        self.soc = max(0.0, min(self.soc, self.capacity_wh))
        self._apply_brownout_policy()

    def _apply_brownout_policy(self) -> None:
        """Pause processing on brownout, resume safely with hysteresis."""
        if not self.processing_paused and self.soc <= self.brownout_threshold_wh:
            self.processing_paused = True
            self.brownout_events += 1
        elif self.processing_paused and self.soc >= self.brownout_threshold_wh + self.hysteresis_wh:
            # Resume safely: ensure SOC is sufficiently recovered
            self.processing_paused = False

    def is_brownout(self) -> bool:
        """Return True if processing is currently paused due to brownout."""
        return self.processing_paused

    def can_process(self, energy_needed_wh: float) -> bool:
        """Check if processing can proceed given brownout and energy."""
        if self.processing_paused:
            return False
        return self.soc >= energy_needed_wh

    def get_available_energy(self) -> float:
        """Return available energy in Watt-hours."""
        return max(0.0, self.soc)
