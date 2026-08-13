#!/usr/bin/env python3
"""Validate label consistency and write a human-review gate report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation import load_dataset, review_labels, validate_dataset_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review deterministic consistency of evaluation labels."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "evaluation" / "datasets" / "health_mvp_v1.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "evaluation"
        / "reports"
        / "health_mvp_v1-label-review.md",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cases = load_dataset(args.dataset)
    validate_dataset_manifest(args.dataset, cases)
    report = review_labels(cases)
    report.write(args.output, args.dataset.stem)
    print(f"Reviewed {report.case_count} labels.")
    print(f"Consistency issues: {report.issue_count}")
    print(f"Human review pending: {report.human_review_pending_count}")
    print(f"Report: {args.output}")
    return 1 if report.issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
