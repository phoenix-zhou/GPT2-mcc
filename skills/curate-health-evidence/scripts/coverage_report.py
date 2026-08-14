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

    plan = result.coverage_plan or {}
    target_documents = plan.get("target_document_count", 0)
    clusters = plan.get("clusters", [])
    cluster_counts = Counter(
        record.get("topic_cluster") for record in result.records
    )
    cluster_sources: dict[str, set[str]] = {
        cluster.get("cluster_id"): set() for cluster in clusters
    }
    for record in result.records:
        cluster_sources.setdefault(record.get("topic_cluster"), set()).add(
            record.get("source_id")
        )

    print("# Health evidence corpus coverage")
    print(f"\n- Corpus ID: {plan.get('corpus_id', '(missing)')}")
    print(f"- Status: {plan.get('status', '(missing)')}")
    print(f"- Documents: {len(result.records)} / {target_documents}")
    print(f"- Approved sources: {len(result.manifest.get('sources', []))}")
    print(f"- Stale review warnings: {len(result.warnings)}")
    print("\n## Topic-cluster gaps\n")
    print("| Cluster | Current | Target | Gap | Sources |")
    print("|---|---:|---:|---:|---:|")
    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        current = cluster_counts[cluster_id]
        target = cluster.get("target_documents", 0)
        gap = max(target - current, 0)
        sources = len(cluster_sources.get(cluster_id, set()))
        print(f"| {cluster_id} | {current} | {target} | {gap} | {sources} |")
    print(
        f"\n- Remaining document gap: {max(target_documents - len(result.records), 0)}"
    )
    clusters_at_target = sum(
        cluster_counts[cluster.get("cluster_id")]
        >= cluster.get("target_documents", 0)
        for cluster in clusters
    )
    minimum_sources = plan.get("minimum_sources_per_cluster", 0)
    clusters_at_source_minimum = sum(
        len(cluster_sources.get(cluster.get("cluster_id"), set()))
        >= minimum_sources
        for cluster in clusters
    )
    print(f"- Clusters at document target: {clusters_at_target} / {len(clusters)}")
    print(
        "- Clusters at source minimum: "
        f"{clusters_at_source_minimum} / {len(clusters)}"
    )
    print(
        "- Required query phenomena: "
        + ", ".join(plan.get("required_query_phenomena", []))
    )
    section("Source", Counter(record.get("source_id") for record in result.records))
    section("Topic cluster", cluster_counts)
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
