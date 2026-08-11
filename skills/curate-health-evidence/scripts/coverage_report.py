#!/usr/bin/env python3
"""Print a deterministic Markdown inventory of the evidence corpus."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from _corpus import validate_project


def section(title: str, counts: Counter) -> None:
    print(f"\n## {title}\n")
    print("| Value | Documents |")
    print("|---|---:|")
    for value, count in sorted(counts.items()):
        print(f"| {value or '(missing)'} | {count} |")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()

    try:
        result = validate_project(args.project)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}")
        return 1

    print("# Health evidence corpus coverage")
    print(f"\n- Documents: {len(result.records)}")
    print(f"- Approved sources: {len(result.manifest.get('sources', []))}")
    print(f"- Stale review warnings: {len(result.warnings)}")
    section("Source", Counter(record.get("source_id") for record in result.records))
    section(
        "Jurisdiction",
        Counter(record.get("jurisdiction") for record in result.records),
    )
    section(
        "Source type", Counter(record.get("source_type") for record in result.records)
    )
    section(
        "Review status",
        Counter(record.get("review_status") for record in result.records),
    )
    section(
        "Evidence grade",
        Counter(record.get("evidence_grade") for record in result.records),
    )
    if result.warnings:
        print("\n## Warnings\n")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
