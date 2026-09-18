"""fig_infographic_pdf.py - One page PDF summary with system diagram, regime map, and key metrics."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from PIL import Image

DATA_PATH = Path(__file__).resolve().parents[2] / "results" / "frozen" / "v1" / "e03_results.csv"
FIG_DIR = Path(__file__).resolve().parents[1]
OUT_PATH = FIG_DIR / "infographic_summary.pdf"

SYS_IMG = FIG_DIR / "fig01.png"
REGIME_IMG = FIG_DIR / "fig04.png"

def load_metrics():
    df = pd.read_csv(DATA_PATH)
    # Median metrics per architecture
    med = df.groupby('architecture_name')[['tfup_s','tcp_s','processing_energy_j','tx_energy_j']].median()
    med['total_energy_j'] = med['processing_energy_j'] + med['tx_energy_j']
    # Mapping to standard IDs
    arch_map = {
        "GroundOnly": "A0_GROUND_ONLY",
        "CompressedFull": "A1_COMPRESSED_FULL",
        "QuicklookFirst": "A2_QUICKLOOK_FIRST",
        "RoiFirst": "A3_ROI_FIRST",
        "Progressive": "A4_PROGRESSIVE",
    }
    med = med.copy()
    med.index = med.index.map(arch_map)
    return med

def main():
    metrics = load_metrics()
    
    fig = plt.figure(figsize=(11, 8.5))
    gs = GridSpec(2, 2, height_ratios=[1.2, 0.8], hspace=0.3, wspace=0.25)
    
    # System diagram
    ax_sys = fig.add_subplot(gs[0, 0])
    if SYS_IMG.exists():
        img = Image.open(SYS_IMG)
        ax_sys.imshow(img)
    ax_sys.axis('off')
    ax_sys.set_title("System Block Diagram", fontsize=12, pad=10)
    
    # Regime map
    ax_reg = fig.add_subplot(gs[0, 1])
    if REGIME_IMG.exists():
        img2 = Image.open(REGIME_IMG)
        ax_reg.imshow(img2)
    ax_reg.axis('off')
    ax_reg.set_title("Regime map: best architecture by rate/contact", fontsize=12, pad=10)
    
    # Key numbers
    ax_text = fig.add_subplot(gs[1, :])
    ax_text.axis('off')
    ax_text.set_title("Key Metrics (median across sweep)", fontsize=14, pad=15)
    
    # Build table text
    lines = []
    lines.append("Architecture      TFUP (s)   TCP (s)   Process Energy (J)   Tx Energy (J)   Total Energy (J)")
    lines.append("-"*95)
    for arch in sorted(metrics.index):
        row = metrics.loc[arch]
        lines.append(f"{arch:18s} {row['tfup_s']:8.1f} {row['tcp_s']:8.1f} {row['processing_energy_j']:19.0f} {row['tx_energy_j']:14.0f} {row['total_energy_j']:16.0f}")
    
    table_text = "\n".join(lines)
    ax_text.text(0.01, 0.9, table_text, fontsize=9, family='monospace', va='top')
    
    # Footer notes
    note = ("Notes: TFUP = time to first useful product; TCP = time to complete product.\n"
            "Metrics are medians over the rate/contact sweep from frozen v1 results. "
            "System diagram and regime map are from fig01 and fig04.")
    ax_text.text(0.01, 0.1, note, fontsize=8, va='bottom', wrap=True)
    
    plt.suptitle("LEO Edge Architecture - One Page Summary", fontsize=16, y=0.98)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {OUT_PATH}")

if __name__ == "__main__":
    main()
