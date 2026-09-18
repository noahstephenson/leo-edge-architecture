"""fig01_system_architecture.py - Block diagram of the LEO edge architecture."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

OUT_PATH = Path(__file__).resolve().parents[1] / "fig01.png"


def main():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Satellite (left column, top to bottom) and ground segment (right column)
    blocks = [
        ("Imager\nSensor", 1, 6.3, 2, 1.0),
        ("Satellite\nOnboard\nProcessor", 1, 4.3, 2, 1.5),
        ("Downlink\nRadio", 1, 2.3, 2, 1.0),
        ("Ground\nTerminal", 7, 5.3, 2, 1.5),
        ("Edge\nServer", 7, 3.3, 2, 1.0),
        ("Cloud\nArchive", 7, 1.3, 2, 1.0),
    ]

    for label, x, y, w, h in blocks:
        rect = Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor='#e8f0fe', zorder=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha='center', va='center', fontsize=9)

    def draw_arrow(x1, y1, x2, y2):
        arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->', mutation_scale=15, linewidth=1.2)
        ax.add_patch(arrow)

    draw_arrow(2, 6.3, 2, 5.8)    # sensor down to onboard processor
    draw_arrow(2, 4.3, 2, 3.3)    # onboard processor down to downlink radio
    draw_arrow(3, 3.05, 7, 5.6)   # downlink radio to ground terminal
    draw_arrow(8, 5.3, 8, 4.3)    # ground terminal to edge server
    draw_arrow(8, 3.3, 8, 2.3)    # edge server to cloud archive

    ax.set_title("LEO Edge Architecture - System Block Diagram", fontsize=14, pad=20)
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
