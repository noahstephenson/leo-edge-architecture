"""Guards against doc drift: every docs/*.md file and results/frozen/v4 file
that a current doc points at must exist. DECISION_LOG.md and REPRODUCE_LOG.md
are excluded because they legitimately describe deleted or older files."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [p for p in ROOT.glob("docs/*.md") if p.name not in {"DECISION_LOG.md", "NOVELTY.md"}]
DOCS.append(ROOT / "README.md")


def _refs(pattern):
    found = set()
    for doc in DOCS:
        for m in re.finditer(pattern, doc.read_text(encoding="utf-8")):
            found.add((doc.name, m.group(0)))
    return found


def test_referenced_docs_exist():
    missing = [(d, r) for d, r in _refs(r"docs/[A-Z0-9_]+\.md") if not (ROOT / r).exists()]
    assert not missing, missing


def test_referenced_frozen_v4_files_exist():
    missing = [(d, r) for d, r in _refs(r"results/frozen/v4/[A-Za-z0-9_]+\.(?:csv|yaml|md)") if not (ROOT / r).exists()]
    assert not missing, missing


def test_current_docs_do_not_point_at_old_frozen_results():
    stale = [(d, r) for d, r in _refs(r"results/frozen/v[123]/") ]
    assert not stale, stale
