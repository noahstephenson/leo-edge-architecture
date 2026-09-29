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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify figure and source hashes")
    args = parser.parse_args()
    sources = {
        "summary.csv": _hash(SOURCE, text=True),
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
        and row["terminal_class"] == "VEHICLE_MOUNTED"
        and row["condition"] == "NOMINAL"
        and row["terminal_sites"] == "4"
    }
    expected = {(walker, arch) for walker in WALKERS for arch in ARCHITECTURES}
    if set(selected) != expected:
        raise ValueError("The selected MT-2 slice is incomplete or duplicated")

    plt.rcParams["svg.hashsalt"] = "leo-edge-current"
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
    fig.suptitle("MT-2 corridor view · vehicle terminal · four sites · nominal",
                 fontsize=12, fontweight="bold", y=0.97)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.84, bottom=0.25, wspace=0.08)
    fig.text(0.5, 0.06,
             "24 paired synthetic requests per candidate and Walker; points are fractions, bars are 95% Wilson intervals.\n"
             "Source: results/current/summary.csv (seed 7, 48 h). Product utility and deadlines are assumed.",
             ha="center", va="bottom", fontsize=8)
    DEST.mkdir(parents=True, exist_ok=True)
    fig.savefig(DEST / "mt2_selected_deadline.png", dpi=180, bbox_inches="tight")
    fig.savefig(DEST / "mt2_selected_deadline.svg", bbox_inches="tight",
                metadata={"Date": None})
    svg_path = DEST / "mt2_selected_deadline.svg"
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n",
                        encoding="utf-8")
    plt.close(fig)
    outputs = ("mt2_selected_deadline.png", "mt2_selected_deadline.svg")
    manifest = {
        "source_sha256": sources,
        "output_sha256": {name: _hash(DEST / name) for name in outputs},
        "matplotlib_version": matplotlib.__version__,
        "selection": "MT-2; vehicle; nominal; four sites; all seven candidates; three Walker configurations",
        "hash_method": "SHA-256 with source text line endings normalized to LF",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")


if __name__ == "__main__":
    main()
