"""Experiment 10: Storage wear and power brownout over 30-day mission."""

from pathlib import Path
import csv

from leo_edge.storage import MassMemory
from leo_edge.power import PowerSystem


def main():
    # Mission parameters
    days = 30
    steps_per_day = 24  # hourly steps
    total_steps = days * steps_per_day

    # Storage config
    capacity_bytes = 256 * 1024**3  # 256 GB
    storage = MassMemory(capacity_bytes=capacity_bytes)

    # Power config
    capacity_wh = 100.0
    power = PowerSystem(capacity_wh=capacity_wh, soc=capacity_wh)

    # Workload parameters
    data_per_hour_bytes = 2 * 1024**3  # 2 GB per hour generated
    processing_power_w = 20.0
    solar_power_w = 40.0  # average charging power during daylight

    rows = []
    for step in range(total_steps):
        hour_of_day = step % 24
        # Simple day/night: 12h solar, 12h eclipse
        net_power_w = processing_power_w - (solar_power_w if 6 <= hour_of_day < 18 else 0.0)
        # Update power for 1 hour
        power.update(dt_s=3600.0, power_w=net_power_w)

        # Brownout-aware processing
        if power.can_process(energy_needed_wh=0.1):
            # Store generated data
            try:
                storage.store(data_per_hour_bytes)
                # Simulate immediate downlink of 50% to free space
                downlink_bytes = data_per_hour_bytes // 2
                storage.free(downlink_bytes)
            except ValueError:
                # Storage full, skip
                pass

        rows.append({
            "hour": step,
            "day": step // 24,
            "soc_wh": round(power.soc, 3),
            "processing_paused": power.processing_paused,
            "brownout_events": power.brownout_events,
            "storage_used_bytes": storage.used_bytes,
            "storage_occupancy": round(storage.occupancy(), 4),
            "total_physical_writes_bytes": storage.total_physical_writes_bytes,
            "wear_fraction": round(storage.wear_fraction(), 6),
            "health_fraction": round(storage.health_fraction(), 6),
        })

    # Save CSV
    out_dir = Path("results/frozen/v4")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "e10_storage_wear.csv"
    fieldnames = ["hour","day","soc_wh","processing_paused","brownout_events","storage_used_bytes","storage_occupancy","total_physical_writes_bytes","wear_fraction","health_fraction"]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved CSV to {csv_path}")

    # Plot storage health
    try:
        import matplotlib.pyplot as plt
        hours = [r["hour"] for r in rows]
        health = [r["health_fraction"] for r in rows]
        plt.figure(figsize=(8,5))
        plt.plot(hours, health)
        plt.xlabel("Hour")
        plt.ylabel("Storage Health Fraction")
        plt.title("30-Day Mission Storage Health with Wear")
        plt.grid(True)
        fig_path = Path("figures/fig16_storage_health.png")
        fig_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(fig_path, dpi=150)
        plt.close()
        print(f"Saved figure to {fig_path}")
    except Exception as e:
        print(f"Plotting skipped: {e}")


if __name__ == "__main__":
    main()
