"""Audit result numbers from frozen results CSVs.

Scans results/frozen/v4/*.csv, extracts key metrics, computes min/max/mean,
and checks basic invariants. Deterministic and pathlib-based.
"""
from pathlib import Path
import csv
import statistics
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "frozen" / "v4"
OUTPUT_PATH = RESULTS_DIR / "audit_report.md"

METRICS = ["tfup_s", "tcp_s", "contact_utilization", "processing_energy_j", "deadline_met"]


def scan_csv_files():
    files = sorted(RESULTS_DIR.glob("*.csv"))
    return files


def read_metrics(files):
    data = {m: [] for m in METRICS}
    censored = {m: 0 for m in METRICS}
    rows_processed = 0
    for f in files:
        with f.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows_processed += 1
                for m in METRICS:
                    if m not in reader.fieldnames:
                        continue
                    raw = row.get(m)
                    if raw is None or raw == "":
                        # pandas writes NaN as an empty cell: a censored,
                        # uncompleted delivery, not a missing column.
                        censored[m] += 1
                        continue
                    try:
                        val = float(raw)
                    except ValueError:
                        continue
                    if val != val:  # NaN written out literally
                        censored[m] += 1
                    else:
                        data[m].append(val)
    return data, censored, rows_processed, files


def check_invariants(data):
    notes = []
    # Non-negative for energy and times
    for m in ["tfup_s", "tcp_s", "processing_energy_j"]:
        vals = data.get(m, [])
        if vals:
            if any(v < 0 for v in vals):
                notes.append(f"Invariant FAILED: {m} contains negative values")
            else:
                notes.append(f"Invariant OK: {m} >= 0")
        else:
            notes.append(f"Invariant SKIP: {m} not found in data")
    # contact_utilization is a fraction of contact capacity used and must be
    # in [0,1]; values above 1 indicate more bytes were reported transmitted
    # than the window could hold, which is a modeling bug, not noise.
    vals = data.get("contact_utilization", [])
    if vals:
        if any(v < 0 for v in vals):
            notes.append("Invariant FAILED: contact_utilization < 0")
        elif any(v > 1.0 for v in vals):
            over = [v for v in vals if v > 1.0]
            notes.append(f"Invariant FAILED: contact_utilization >1 in {len(over)} rows (max {max(over):.3f})")
        else:
            notes.append("Invariant OK: contact_utilization in [0,1]")
    else:
        notes.append("Invariant SKIP: contact_utilization not found")
    # deadline_met in [0,1]
    vals = data.get("deadline_met", [])
    if vals:
        if all(0 <= v <= 1 for v in vals):
            notes.append("Invariant OK: deadline_met in [0,1]")
        else:
            notes.append("Invariant FAILED: deadline_met out of [0,1]")
    else:
        notes.append("Invariant SKIP: deadline_met not found")
    return notes


def summarize(data, censored):
    lines = []
    header = ["Metric", "Count", "Censored (NaN)", "Min", "Max", "Mean"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for m in METRICS:
        vals = data.get(m, [])
        cen = censored.get(m, 0)
        if not vals:
            lines.append(f"| {m} | 0 | {cen} | N/A | N/A | N/A |")
        else:
            cnt = len(vals)
            mn = min(vals)
            mx = max(vals)
            mean = statistics.mean(vals)
            lines.append(f"| {m} | {cnt} | {cen} | {mn:.6g} | {mx:.6g} | {mean:.6g} |")
    return "\n".join(lines)


def main():
    files = scan_csv_files()
    data, censored, rows, files = read_metrics(files)
    invariants = check_invariants(data)
    summary = summarize(data, censored)

    scanned_dir = RESULTS_DIR.relative_to(REPO_ROOT)

    report = []
    report.append("# Audit Report")
    report.append(f"Scanned directory: {scanned_dir}")
    report.append(f"CSV files found: {len(files)}")
    report.append(f"Rows processed: {rows}")
    report.append("")
    report.append("## Metric Summary")
    report.append(
        "Censored (NaN) counts rows where the product never completed within its contact "
        "window; Min/Max/Mean are computed only over completed deliveries."
    )
    report.append("")
    report.append(summary)
    report.append("")
    report.append("## Invariant Checks")
    for note in invariants:
        report.append(f"- {note}")
    report.append("")
    report.append("## Files")
    for f in files:
        report.append(f"- {f.name}")

    OUTPUT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Audit report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
