"""Plot one preselected mission-thread slice with its sample uncertainty.

Run from the repository root: uv run python figures/scripts/fig_mt2_deadline.py
This reads the current evidence summary and writes only to figures/current/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/current/summary.csv"
DEST = ROOT / "figures/current"
MANIFEST = DEST / "manifest.json"
WALKERS = ("1/1/0", "8/4/1", "24/8/1")
ARCHITECTURES = (
    "A0_GROUND_ONLY", "A1_COMPRESSED_FULL", "A2_QUICKLOOK_FIRST",
    "A3_ROI_FIRST", "A4_PROGRESSIVE", "A5_CONTACT_AWARE",
    "A6_THREAD_AWARE_PRIORITY",
)


def _hash(path: Path, *, text: bool = False) -> str:
    content = path.read_bytes()
    if text:
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    global SOURCE, DEST, MANIFEST
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify figure and source hashes")
    parser.add_argument("--evidence", type=Path, default=ROOT / "results/current")
    parser.add_argument("--output", type=Path, default=DEST)
    args = parser.parse_args()
    SOURCE = args.evidence / "summary.csv"
    DEST = args.output
    MANIFEST = DEST / "manifest.json"
    sources = {
        "summary.csv": _hash(SOURCE, text=True),
        "sensitivity_summary.csv": _hash(args.evidence / "sensitivity_summary.csv", text=True),
        "fig_mt2_deadline.py": _hash(Path(__file__), text=True),
        "uv.lock": _hash(ROOT / "uv.lock", text=True),
    }
    if args.check:
        if not MANIFEST.is_file():
            raise FileNotFoundError(MANIFEST)
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if (manifest["source_sha256"] != sources or
                manifest["output_sha256"] != {
                    name: _hash(DEST / name) for name in manifest["output_sha256"]
                }):
            raise RuntimeError("Figure or source hash mismatch")
        print("Figure and source hashes verified")
        return

    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    selected = {
        (row["walker"], row["architecture_id"]): row
        for row in rows
        if row["mode"] == "single_request"
        and row["thread"] == "MT2_ROUTE_RECON_FIRST"
        and row["terminal_class"] == "DISMOUNTED_MANPACK"
        and row["condition"] == "NOMINAL"
        and row["terminal_sites"] == "1"
    }
    expected = {(walker, arch) for walker in WALKERS for arch in ARCHITECTURES}
    if set(selected) != expected:
        raise ValueError("The selected MT-2 slice is incomplete or duplicated")

    plt.rcParams["svg.hashsalt"] = "leo-edge-current"
    # The three-panel figure is printed at manuscript page width.
    plt.rcParams["font.size"] = 14
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 5.0), sharey=True)
    for ax, walker in zip(axes, WALKERS):
        case_rows = [selected[(walker, arch)] for arch in ARCHITECTURES]
        values = [float(row["success_rate"]) for row in case_rows]
        lower = [float(row["ci95_lower"]) for row in case_rows]
        upper = [float(row["ci95_upper"]) for row in case_rows]
        if any(int(row["n_trials"]) != 24 for row in case_rows):
            raise ValueError("Expected 24 paired requests per architecture")
        xs = list(range(len(ARCHITECTURES)))
        ax.errorbar(xs, values,
                    yerr=[[v - lo for v, lo in zip(values, lower)],
                          [hi - v for v, hi in zip(values, upper)]],
                    fmt="o", color="#24536d", ecolor="#7595a4",
                    capsize=3, markersize=5, linewidth=1.3)
        ax.set_xticks(xs, [f"A{i}" for i in range(7)])
        ax.set_title(f"Walker {walker}")
        ax.set_ylim(-0.06, 1.04)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.grid(axis="y", alpha=0.25)
        ax.set_xlabel("Candidate architecture")
    axes[0].set_ylabel("Sampled deadline fraction")
    fig.suptitle("MT-2 corridor view · requesting dismounted terminal · nominal",
                 fontsize=16, fontweight="bold", y=0.97)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.84, bottom=0.25, wspace=0.08)
    fig.text(0.5, 0.06,
             "24 paired synthetic requests per candidate and Walker; 95% Wilson intervals.\n"
             "Source: results/current/summary.csv (seed 7, 48 h).\n"
             "Product utility and deadlines are assumed.",
             ha="center", va="bottom", fontsize=14)
    DEST.mkdir(parents=True, exist_ok=True)
    fig.savefig(DEST / "mt2_selected_deadline.png", dpi=180, bbox_inches="tight")
    fig.savefig(DEST / "mt2_selected_deadline.svg", bbox_inches="tight",
                metadata={"Date": None})
    svg_path = DEST / "mt2_selected_deadline.svg"
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n",
                        encoding="utf-8", newline="\n")
    plt.close(fig)
    plt.rcParams["font.size"] = 12
    counter = [r for r in rows if r["walker"] == "1/1/0" and r["mode"] == "single_request"
               and r["thread"] == "MT2_ROUTE_RECON_FIRST" and r["terminal_sites"] == "4"
               and r["terminal_class"] == "VEHICLE_MOUNTED" and r["condition"] == "NOMINAL"]
    counter = sorted(counter, key=lambda r: r['architecture_id'])
    if len(counter) != 7:
        raise ValueError("Missing counterexample rows")
    fig, ax = plt.subplots(figsize=(7, 4))
    values = [float(r['success_rate']) for r in counter]
    ax.errorbar(range(7), values, yerr=[[v-float(r['ci95_lower']) for v,r in zip(values,counter)],
                [float(r['ci95_upper'])-v for v,r in zip(values,counter)]], fmt='o', capsize=4)
    ax.set_xticks(range(7), [f'A{i}' for i in range(7)])
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel('Sampled deadline fraction')
    ax.set_title('All-miss counterexample: Walker 1/1/0, nominal vehicle link')
    fig.text(0.5, 0.01, 'Four pooled sites with zero forwarding delay; 24 requests; 95% Wilson intervals.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(DEST / 'mt2_counterexample.png', dpi=180)
    plt.close(fig)
    with (args.evidence / 'sensitivity_summary.csv').open(newline='') as stream:
        sensitivity = list(csv.DictReader(stream))
    cases = list(dict.fromkeys(r['case'] for r in sensitivity))
    lookup = {(r['case'], r['architecture_id']): float(r['success_rate']) for r in sensitivity}
    matrix = [[lookup[(case, arch)] for arch in ARCHITECTURES] for case in cases]
    fig, ax = plt.subplots(figsize=(9, 6))
    heat = ax.imshow(matrix, vmin=0, vmax=1, cmap='Blues', aspect='auto')
    ax.set_xticks(range(7), [f'A{i}' for i in range(7)])
    labels = {'baseline': 'Baseline', 'tasking_delay_s': 'Tasking delay: 180 s',
              'interference_derate': 'Degraded effective rate', 'contact_denial_frac': 'Contact denial: 30%',
              'rate_0.5x': 'Receive rate: half', 'processing_0.5x': 'Preparation time: half',
              'rate_2x': 'Receive rate: double', 'processing_2x': 'Preparation time: double',
              'sampling_5s': 'Access sampling: 5 s', 'next_day': 'Next day',
              'aoi_shift_1deg': 'Collection area shifted 1 degree'}
    ax.set_yticks(range(len(cases)), [labels.get(case, case) for case in cases])
    ax.set_title('Corridor sensitivities at the requesting terminal: 24 paired requests')
    fig.colorbar(heat, ax=ax, label='Sampled deadline fraction')
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, f'{value:.2f}', ha='center', va='center', color='white' if value > .5 else 'black', fontsize=12)
    fig.tight_layout()
    fig.savefig(DEST / 'mt2_sensitivity.png', dpi=180)
    plt.close(fig)
    outputs = ("mt2_selected_deadline.png", "mt2_selected_deadline.svg", "mt2_counterexample.png", "mt2_sensitivity.png")
    manifest = {
        "source_sha256": sources,
        "output_sha256": {name: _hash(DEST / name) for name in outputs},
        "matplotlib_version": matplotlib.__version__,
        "selection": "Principal: MT-2 dismounted requesting terminal, nominal, one site; counterexample: vehicle, four pooled sites, Walker 1/1/0; bounded corridor sensitivities",
        "hash_method": "SHA-256 with source text line endings normalized to LF",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")


if __name__ == "__main__":
    main()
