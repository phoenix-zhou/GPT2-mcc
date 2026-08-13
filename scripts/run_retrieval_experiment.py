#!/usr/bin/env python3
"""Run reproducible Keyword-vs-BM25 retrieval comparison."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation import load_dataset, validate_dataset_manifest
from evaluation.retrieval_experiment import run_retrieval_experiment
from knowledge import LocalKnowledgeBase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare allow-listed retrieval strategies on frozen cases."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "evaluation" / "datasets" / "health_mvp_v1.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "evaluation" / "reports" / "rag-v2",
    )
    parser.add_argument(
        "--strategy",
        action="append",
        choices=("keyword", "bm25"),
        help="Strategy to compare; repeat to set order. Defaults to keyword and bm25.",
    )
    parser.add_argument("--retrieval-k", type=int, default=3)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.retrieval_k < 1:
        raise SystemExit("--retrieval-k must be at least 1")
    cases = load_dataset(args.dataset)
    validate_dataset_manifest(args.dataset, cases)
    knowledge_base = LocalKnowledgeBase()
    report = run_retrieval_experiment(
        cases,
        knowledge_base.documents,
        dataset_name=args.dataset.stem,
        strategies=tuple(args.strategy or ("keyword", "bm25")),
        retrieval_k=args.retrieval_k,
    )
    json_path, markdown_path = report.write(args.output_dir)
    print(f"Compared {len(report.strategies)} strategies on {report.candidate_count} cases.")
    for result in report.strategies:
        print(
            f"{result.strategy}: Recall@{report.retrieval_k}="
            f"{result.metrics['recall_at_k']:.4f}; "
            f"no-hit={result.metrics['no_hit_accuracy']:.4f}; "
            f"P95={result.metrics['latency_p95_ms']:.4f} ms"
        )
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
