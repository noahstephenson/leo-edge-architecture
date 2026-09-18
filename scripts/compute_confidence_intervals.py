"""Compute mean and 95% confidence intervals for tfup_s and tcp_s per architecture.

Reads all CSVs in results/frozen/v1/, aggregates rows with tfup_s and tcp_s,
and writes results/frozen/v1/confidence_intervals.csv.

Deterministic sampling uses a fixed random seed for bootstrap.
"""

from pathlib import Path
import csv
import random
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "frozen" / "v1"
OUTPUT_PATH = RESULTS_DIR / "confidence_intervals.csv"

ARCH_COLUMNS = ["architecture_name", "architecture", "arch_name"]
METRICS = ["tfup_s", "tcp_s"]

ARCH_NAME_MAP = {
    "GroundOnly": "A0_GROUND_ONLY",
    "CompressedFull": "A1_COMPRESSED_FULL",
    "QuicklookFirst": "A2_QUICKLOOK_FIRST",
    "RoiFirst": "A3_ROI_FIRST",
    "Progressive": "A4_PROGRESSIVE",
}

N_BOOTSTRAP = 10000
SEED = 0
CI_LOW = 2.5
CI_HIGH = 97.5


def detect_arch_column(fieldnames):
    for col in ARCH_COLUMNS:
        if col in fieldnames:
            return col
    return None


def collect_data():
    data = defaultdict(lambda: {m: [] for m in METRICS})
    files = sorted(RESULTS_DIR.glob("*.csv"))
    for f in files:
        try:
            with f.open(newline="") as fh:
                reader = csv.DictReader(fh)
                fieldnames = reader.fieldnames or []
                arch_col = detect_arch_column(fieldnames)
                has_tfup = "tfup_s" in fieldnames
                has_tcp = "tcp_s" in fieldnames
                if not arch_col or not (has_tfup and has_tcp):
                    continue
                for row in reader:
                    arch = row.get(arch_col)
                    if not arch:
                        continue
                    arch = ARCH_NAME_MAP.get(arch, arch)
                    try:
                        tfup_val = float(row["tfup_s"])
                        tcp_val = float(row["tcp_s"])
                    except (ValueError, TypeError):
                        continue
                    data[arch]["tfup_s"].append(tfup_val)
                    data[arch]["tcp_s"].append(tcp_val)
        except Exception:
            # Skip unreadable files deterministically
            continue
    return data


def percentile(data, p):
    """Deterministic percentile using sorted list."""
    if not data:
        return float("nan")
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(data_sorted) - 1)
    if f == c:
        return data_sorted[int(k)]
    d0 = data_sorted[f] * (c - k)
    d1 = data_sorted[c] * (k - f)
    return d0 + d1


def bootstrap_ci(values, n_resamples=N_BOOTSTRAP, seed=SEED):
    n = len(values)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    means = []
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in range(n)]
        means.append(sum(sample) / n)
    mean = sum(values) / n
    lower = percentile(means, CI_LOW)
    upper = percentile(means, CI_HIGH)
    return mean, lower, upper


def main():
    data = collect_data()
    rows = []
    for arch in sorted(data.keys()):
        tfup_vals = data[arch]["tfup_s"]
        tcp_vals = data[arch]["tcp_s"]
        tfup_mean, tfup_low, tfup_high = bootstrap_ci(tfup_vals)
        tcp_mean, tcp_low, tcp_high = bootstrap_ci(tcp_vals)
        n_samples = len(tfup_vals)
        # If tcp samples differ, use min; they should be same per architecture
        rows.append({
            "architecture": arch,
            "tfup_mean": tfup_mean,
            "tfup_ci_lower": tfup_low,
            "tfup_ci_upper": tfup_high,
            "tcp_mean": tcp_mean,
            "tcp_ci_lower": tcp_low,
            "tcp_ci_upper": tcp_high,
            "n_samples": n_samples,
        })

    fieldnames = ["architecture", "tfup_mean", "tfup_ci_lower", "tfup_ci_upper",
                  "tcp_mean", "tcp_ci_lower", "tcp_ci_upper", "n_samples"]
    with OUTPUT_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} architectures to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
