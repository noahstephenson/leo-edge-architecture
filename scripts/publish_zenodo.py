"""Package frozen results, figures, and paper for Zenodo release.

Creates a zip archive and a metadata JSON with title, authors, description.
Prints release notes with DOI placeholder.
"""

from pathlib import Path
import json
import zipfile
import datetime

REPO_ROOT = Path(__file__).resolve().parents[1]

RESULTS_SRC = REPO_ROOT / "results" / "frozen" / "v1"
FIGURES_SRC = REPO_ROOT / "figures"
PAPER_SRC = REPO_ROOT / "paper"

OUTPUT_DIR = REPO_ROOT / "releases"
OUTPUT_DIR.mkdir(exist_ok=True)

ZIP_PATH = OUTPUT_DIR / "leo_edge_v1_release.zip"
METADATA_PATH = OUTPUT_DIR / "zenodo_metadata.json"

def load_citation():
    cff_path = REPO_ROOT / "CITATION.cff"
    title = "LEO Edge Architecture"
    authors = []
    if cff_path.exists():
        try:
            # Very simple parse, no yaml dependency
            lines = cff_path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("title:"):
                    title = line.split(":",1)[1].strip().strip('"')
                if line.strip().startswith("authors:"):
                    # collect next lines with names
                    for j in range(i+1, len(lines)):
                        l = lines[j]
                        if "family-names:" in l:
                            family = l.split(":",1)[1].strip().strip('"')
                            given = ""
                            # next line may have given-names
                            if j+1 < len(lines) and "given-names:" in lines[j+1]:
                                given = lines[j+1].split(":",1)[1].strip().strip('"')
                            name = f"{given} {family}".strip()
                            if name:
                                authors.append(name)
                        if l.strip() and not l.startswith(" "):
                            break
        except Exception:
            pass
    if not authors:
        authors = ["Noah H"]
    return title, authors

def load_description():
    manuscript = PAPER_SRC / "manuscript.md"
    description = "LEO edge architecture research for direct-to-edge imagery delivery."
    if manuscript.exists():
        try:
            text = manuscript.read_text(encoding="utf-8")
            # Extract Abstract line
            for line in text.splitlines():
                if line.strip().lower().startswith("## abstract"):
                    # next non-empty line
                    idx = text.splitlines().index(line)
                    for nxt in text.splitlines()[idx+1:]:
                        if nxt.strip():
                            description = nxt.strip()
                            break
                    break
        except Exception:
            pass
    return description

def create_zip():
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # Add results/frozen/v1
        if RESULTS_SRC.exists():
            for p in RESULTS_SRC.rglob("*"):
                if p.is_file():
                    arcname = Path("results_frozen_v1") / p.relative_to(RESULTS_SRC)
                    z.write(p, arcname)
        # Add figures
        if FIGURES_SRC.exists():
            for p in FIGURES_SRC.rglob("*"):
                if p.is_file():
                    arcname = Path("figures") / p.relative_to(FIGURES_SRC)
                    z.write(p, arcname)
        # Add paper
        if PAPER_SRC.exists():
            for p in PAPER_SRC.rglob("*"):
                if p.is_file():
                    arcname = Path("paper") / p.relative_to(PAPER_SRC)
                    z.write(p, arcname)
    return ZIP_PATH

def write_metadata(title, authors, description):
    metadata = {
        "title": title,
        "creators": [{"name": a} for a in authors],
        "description": description,
        "version": "v1",
        "keywords": ["LEO", "edge computing", "satellite", "imagery", "systems architecture"],
        "license": "MIT",
        "upload_type": "dataset",
        "date": datetime.date.today().isoformat(),
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return METADATA_PATH

def print_release_notes(title, doi_placeholder="10.5281/zenodo.xxxxxxx"):
    notes = f"""
Release notes for {title} v1
--------------------------------
Archive: {ZIP_PATH.name}
Metadata: {METADATA_PATH.name}

Contents packaged:
- results_frozen_v1/ (results/frozen/v1)
- figures/ (figures/*.png, scripts, html)
- paper/ (manuscript.md, hand_calc_break_even.md)

DOI placeholder: {doi_placeholder}
Cite as: {title} v1. {doi_placeholder}

Next steps:
1. Upload {ZIP_PATH.name} to Zenodo
2. Fill in metadata from {METADATA_PATH.name}
3. Replace DOI placeholder after publication
"""
    print(notes.strip())

def main():
    title, authors = load_citation()
    description = load_description()
    zip_path = create_zip()
    meta_path = write_metadata(title, authors, description)
    print(f"Created archive: {zip_path}")
    print(f"Created metadata: {meta_path}")
    print_release_notes(title)

if __name__ == "__main__":
    main()
