"""Guard links from active documents to the current evidence."""

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


def test_referenced_current_evidence_exists():
    missing = [(d, r) for d, r in _refs(r"results/current/[A-Za-z0-9_]+\.(?:csv|json)") if not (ROOT / r).exists()]
    assert not missing, missing


def test_current_docs_do_not_point_at_old_frozen_results():
    stale = [(d, r) for d, r in _refs(r"results/frozen/v[0-9]+/")]
    assert not stale, stale
