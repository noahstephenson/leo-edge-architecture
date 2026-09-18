"""Experiment 06: Queue stress with multiple scenes per day."""

import csv
from pathlib import Path


def main():
    scenes_per_day = 20
    scene_bytes = 500e6  # 500 MB
    arrival_interval_s = 86400 / scenes_per_day

    # Contact assumptions: 4 contacts per day, each 300 s at 10 Mbps
    contacts_per_day = 4
    contact_duration_s = 300
    rate_bps = 10e6
    bytes_per_contact = (rate_bps / 8) * contact_duration_s

    # Simple discrete event simulation
    backlog = 0.0
    time = 0.0
    next_arrival = 0.0
    next_contact_idx = 0
    contact_times = [i * 86400 / contacts_per_day for i in range(contacts_per_day)]

    rows = []
    max_backlog = 0.0

    # simulate day
    t = 0.0
    # merge events
    events = []
    for i in range(scenes_per_day):
        events.append(("arrival", i * arrival_interval_s, scene_bytes))
    for ct in contact_times:
        events.append(("contact", ct, bytes_per_contact))
    # sort by time
    events.sort(key=lambda x: x[1])

    backlog = 0.0
    for ev_type, ev_time, amount in events:
        # advance time
        if ev_type == "arrival":
            backlog += amount
        else:  # contact
            transmitted = min(backlog, amount)
            backlog -= transmitted
        if backlog > max_backlog:
            max_backlog = backlog
        rows.append({
            "time_s": ev_time,
            "event": ev_type,
            "backlog_bytes": backlog,
            "amount": amount,
        })

    print(f"Scenes per day: {scenes_per_day}")
    print(f"Bytes per contact: {bytes_per_contact:.0f}")
    print(f"Max backlog: {max_backlog/1e6:.1f} MB")
    print(f"Final backlog: {backlog/1e6:.1f} MB")

    out_path = Path("results/raw/e06_queue_stress.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["time_s", "event", "backlog_bytes", "amount"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
