#!/usr/bin/env python3
"""Validate governed health-evidence metadata, hashes, and freshness."""

from __future__ import annotations

import argparse
from pathlib import Path

from _corpus import validate_project


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--fail-on-stale", action="store_true")
    args = parser.parse_args()

    try:
        result = validate_project(args.project)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    source_count = len(result.manifest.get("sources", []))
    print(
        f"Checked {len(result.records)} documents from "
        f"{source_count} approved sources."
    )
    if result.errors or (args.fail_on_stale and result.warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
