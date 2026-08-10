"""Validate governed source metadata and document integrity."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from knowledge import LocalKnowledgeBase  # noqa: E402


def main() -> None:
    knowledge_base = LocalKnowledgeBase()
    source_count = len(knowledge_base.source_manifest["sources"])
    print(
        f"Validated {len(knowledge_base.documents)} governed documents "
        f"from {source_count} approved sources."
    )


if __name__ == "__main__":
    main()
