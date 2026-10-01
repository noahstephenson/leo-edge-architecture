"""Check local links in the active GitHub reading path."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "README.md",
    "AGENTS.md",
    "data/README.md",
    "data/imagery/README.md",
    "docs/MODELING_PLAN.md",
    "docs/CONOPS.md",
    "docs/STAKEHOLDERS.md",
    "docs/MISSION_THREADS.md",
    "docs/OPERATIONAL_CONTEXT.md",
    "docs/REQUIREMENTS.md",
    "docs/FUNCTIONAL_ARCHITECTURE.md",
    "docs/ALLOCATION_SPACE.md",
    "docs/INTERFACES.md",
    "docs/ARCHITECTURE_VIEWS.md",
    "docs/ASSUMPTIONS.md",
    "docs/MODEL_REFERENCE.md",
    "docs/HAND_CALC_BREAK_EVEN.md",
    "docs/TRADE_STUDY.md",
    "docs/ACQUISITION_IMPLICATIONS.md",
    "docs/ENGINEERING_STATUS.md",
    "docs/PROJECT_ROADMAP.md",
    "docs/RESEARCH_DESIGN.md",
    "docs/PUBLIC_RELEASE.md",
    "docs/DECISION_LOG.md",
    "docs/reference/MODEL_CATALOG.md",
    "docs/reference/TRACEABILITY.md",
    "docs/reference/VIEWS.md",
    "docs/reference/LITERATURE.md",
    "figures/README.md",
    "paper/manuscript_draft.md",
    "paper/submitted_abstract.md",
)
LINK = re.compile(r"(?<!!)\[[^\]]+\]\((<?[^)]+>?)\)")


def main() -> int:
    errors: list[str] = []
    for relative in PAGES:
        page = ROOT / relative
        if not page.is_file():
            errors.append(f"Missing reading-path page: {relative}")
            continue
        for destination in LINK.findall(page.read_text(encoding="utf-8")):
            destination = destination.strip("<>").split("#", 1)[0]
            if not destination or "://" in destination or destination.startswith("mailto:"):
                continue
            resolved = (page.parent / unquote(destination)).resolve()
            if not resolved.exists():
                errors.append(f"{relative}: missing link target {destination}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Reading path: {len(PAGES)} pages and local links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
