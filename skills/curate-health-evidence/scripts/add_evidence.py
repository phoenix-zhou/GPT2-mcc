#!/usr/bin/env python3
"""Normalize and optionally append one governed evidence record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _corpus import content_hash, load_corpus, validate_payload, write_records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        if not isinstance(candidate, dict):
            raise ValueError("candidate must contain one JSON object")
        content = candidate.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("candidate content must be non-empty text")
        calculated_hash = content_hash(content)
        supplied_hash = candidate.get("content_sha256")
        if supplied_hash and supplied_hash != calculated_hash:
            raise ValueError("candidate content_sha256 does not match content")
        candidate["content_sha256"] = calculated_hash

        records, manifest = load_corpus(args.project)
        document_id = candidate.get("document_id")
        if any(record.get("document_id") == document_id for record in records):
            raise ValueError(f"document_id already exists: {document_id!r}")
        proposed = [*records, candidate]
        result = validate_payload(proposed, manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}")
        return 1

    print(json.dumps(candidate, ensure_ascii=False, indent=2))
    if args.apply:
        write_records(args.project, proposed)
        print(f"Applied document {candidate['document_id']!r}.")
    else:
        print("Check passed; no files changed. Re-run with --apply to append.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
