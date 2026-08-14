"""Shared corpus validation helpers for the curate-health-evidence skill."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

RECORD_FIELDS = {
    "document_id",
    "source_id",
    "issuer",
    "jurisdiction",
    "language",
    "source_language",
    "published_at",
    "last_reviewed_at",
    "version",
    "evidence_grade",
    "source_type",
    "topic_cluster",
    "applicable_population",
    "review_status",
    "license",
    "content_sha256",
    "title",
    "content",
    "source_url",
    "keywords",
}

SOURCE_FIELDS = {
    "source_id",
    "organization",
    "homepage",
    "jurisdiction",
    "source_type",
    "update_method",
    "reuse_status",
}

COVERAGE_CLUSTER_FIELDS = {
    "cluster_id",
    "display_name_en",
    "display_name_zh",
    "target_documents",
    "inclusion_scope",
    "exclusion_scope",
    "preferred_jurisdictions",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    records: tuple[dict, ...]
    manifest: dict
    coverage_plan: dict | None = None


def knowledge_paths(project: Path) -> tuple[Path, Path]:
    knowledge_dir = project.resolve() / "knowledge"
    return (
        knowledge_dir / "medical_guidance.json",
        knowledge_dir / "source_manifest.json",
    )


def coverage_plan_path(project: Path) -> Path:
    return project.resolve() / "knowledge" / "coverage_plan.json"


def load_corpus(project: Path) -> tuple[list[dict], dict]:
    records_path, manifest_path = knowledge_paths(project)
    with records_path.open(encoding="utf-8") as file:
        records = json.load(file)
    with manifest_path.open(encoding="utf-8") as file:
        manifest = json.load(file)
    if not isinstance(records, list):
        raise ValueError("medical_guidance.json must contain a JSON list")
    if not isinstance(manifest, dict):
        raise ValueError("source_manifest.json must contain a JSON object")
    return records, manifest


def load_coverage_plan(project: Path) -> dict:
    with coverage_plan_path(project).open(encoding="utf-8") as file:
        plan = json.load(file)
    if not isinstance(plan, dict):
        raise ValueError("coverage_plan.json must contain a JSON object")
    return plan


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _https_host(value: str) -> str | None:
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        return None
    return parsed.hostname.lower().rstrip(".")


def _host_is_allowed(candidate: str, approved: str) -> bool:
    return candidate == approved or candidate.endswith(f".{approved}")


def _iso_date(value, label: str, errors: list[str]) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{label}: expected ISO YYYY-MM-DD, got {value!r}")
        return None


def validate_payload(
    records: list[dict],
    manifest: dict,
    *,
    coverage_plan: dict | None = None,
    today: date | None = None,
) -> ValidationResult:
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []

    known_clusters: set[str] | None = None
    if coverage_plan is not None:
        if coverage_plan.get("schema_version") != 1:
            errors.append("coverage_plan: unsupported or missing schema_version")
        if coverage_plan.get("status") not in {"planning", "frozen"}:
            errors.append("coverage_plan: status must be 'planning' or 'frozen'")
        for field in ("corpus_id", "required_review_status"):
            if not isinstance(coverage_plan.get(field), str) or not coverage_plan[
                field
            ].strip():
                errors.append(f"coverage_plan: {field} must be non-empty text")
        for field in (
            "target_document_count",
            "target_topic_cluster_count",
            "minimum_sources_per_cluster",
        ):
            if not isinstance(coverage_plan.get(field), int) or coverage_plan[field] <= 0:
                errors.append(f"coverage_plan: {field} must be a positive integer")
        clusters = coverage_plan.get("clusters", [])
        if not isinstance(clusters, list):
            errors.append("coverage_plan: clusters must be a list")
            clusters = []
        cluster_ids: list[str] = []
        target_sum = 0
        for index, cluster in enumerate(clusters):
            label = f"coverage_plan.clusters[{index}]"
            if not isinstance(cluster, dict):
                errors.append(f"{label}: expected an object")
                continue
            missing = COVERAGE_CLUSTER_FIELDS - cluster.keys()
            if missing:
                errors.append(f"{label}: missing {', '.join(sorted(missing))}")
            for field in (
                "display_name_en",
                "display_name_zh",
                "inclusion_scope",
                "exclusion_scope",
            ):
                if not isinstance(cluster.get(field), str) or not cluster.get(
                    field, ""
                ).strip():
                    errors.append(f"{label}: {field} must be non-empty text")
            cluster_id = cluster.get("cluster_id")
            if not isinstance(cluster_id, str) or not cluster_id.strip():
                errors.append(f"{label}: cluster_id must be non-empty text")
            else:
                cluster_ids.append(cluster_id)
            target = cluster.get("target_documents")
            if not isinstance(target, int) or target <= 0:
                errors.append(f"{label}: target_documents must be a positive integer")
            else:
                target_sum += target
            jurisdictions = cluster.get("preferred_jurisdictions")
            if not isinstance(jurisdictions, list) or not jurisdictions or not all(
                isinstance(value, str) and value.strip() for value in jurisdictions
            ):
                errors.append(
                    f"{label}: preferred_jurisdictions must be a non-empty string list"
                )
        duplicates = sorted(
            key for key, count in Counter(cluster_ids).items() if count > 1
        )
        if duplicates:
            errors.append(f"coverage_plan: duplicate cluster_id values {duplicates}")
        if coverage_plan.get("target_topic_cluster_count") != len(cluster_ids):
            errors.append(
                "coverage_plan: target_topic_cluster_count does not match clusters"
            )
        if coverage_plan.get("target_document_count") != target_sum:
            errors.append(
                "coverage_plan: target_document_count does not match cluster targets"
            )
        phenomena = coverage_plan.get("required_query_phenomena")
        if not isinstance(phenomena, list) or not phenomena or not all(
            isinstance(value, str) and value.strip() for value in phenomena
        ):
            errors.append(
                "coverage_plan: required_query_phenomena must be a non-empty string list"
            )
        known_clusters = set(cluster_ids)

    if manifest.get("schema_version") != 1:
        errors.append("manifest: unsupported or missing schema_version")
    sources = manifest.get("sources", [])
    if not isinstance(sources, list):
        errors.append("manifest: sources must be a list")
        sources = []

    source_ids: list[str] = []
    source_registry: dict[str, dict] = {}
    for index, source in enumerate(sources):
        label = f"manifest.sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label}: expected an object")
            continue
        missing = SOURCE_FIELDS - source.keys()
        if missing:
            errors.append(f"{label}: missing {', '.join(sorted(missing))}")
        source_id = source.get("source_id")
        if source_id:
            source_ids.append(source_id)
        if not _https_host(str(source.get("homepage", ""))):
            errors.append(f"{label}: homepage must use absolute HTTPS without credentials")
        if isinstance(source_id, str) and source_id:
            source_registry[source_id] = source

    duplicate_sources = sorted(
        key for key, count in Counter(source_ids).items() if count > 1
    )
    if duplicate_sources:
        errors.append(f"manifest: duplicate source_id values {duplicate_sources}")

    review_interval = manifest.get("review_policy", {}).get(
        "review_interval_days", 180
    )
    if not isinstance(review_interval, int) or review_interval <= 0:
        errors.append("manifest: review_interval_days must be a positive integer")
        review_interval = 180

    document_ids: list[str] = []
    known_sources = set(source_ids)
    for index, record in enumerate(records):
        label = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: expected an object")
            continue
        missing = RECORD_FIELDS - record.keys()
        if missing:
            errors.append(f"{label}: missing {', '.join(sorted(missing))}")
        document_id = record.get("document_id")
        label = str(document_id or label)
        if document_id:
            document_ids.append(document_id)
        source = source_registry.get(record.get("source_id"))
        if record.get("source_id") not in known_sources or source is None:
            errors.append(f"{label}: unknown source_id {record.get('source_id')!r}")
        source_host = _https_host(str(record.get("source_url", "")))
        if not source_host:
            errors.append(
                f"{label}: source_url must use absolute HTTPS without credentials"
            )
        if source and source_host:
            approved_host = _https_host(str(source.get("homepage", "")))
            if approved_host and not _host_is_allowed(source_host, approved_host):
                errors.append(
                    f"{label}: source_url host is not approved for source_id"
                )
            metadata_pairs = {
                "issuer": "organization",
                "jurisdiction": "jurisdiction",
                "source_type": "source_type",
            }
            for record_field, source_field in metadata_pairs.items():
                if record.get(record_field) != source.get(source_field):
                    errors.append(
                        f"{label}: {record_field} does not match source registry"
                    )
        content = record.get("content")
        if not isinstance(content, str) or not content.strip():
            errors.append(f"{label}: content must be non-empty text")
        elif record.get("content_sha256") != content_hash(content):
            errors.append(f"{label}: content_sha256 mismatch")
        keywords = record.get("keywords")
        if not isinstance(keywords, list) or not keywords or not all(
            isinstance(keyword, str) and keyword.strip() for keyword in keywords
        ):
            errors.append(f"{label}: keywords must be a non-empty string list")
        topic_cluster = record.get("topic_cluster")
        if not isinstance(topic_cluster, str) or not topic_cluster.strip():
            errors.append(f"{label}: topic_cluster must be non-empty text")
        elif known_clusters is not None and topic_cluster not in known_clusters:
            errors.append(f"{label}: unknown topic_cluster {topic_cluster!r}")
        reviewed = _iso_date(
            record.get("last_reviewed_at"),
            f"{label}.last_reviewed_at",
            errors,
        )
        published = _iso_date(
            record.get("published_at"), f"{label}.published_at", errors
        )
        if published and published > today:
            errors.append(f"{label}: published_at is in the future")
        if reviewed:
            age = (today - reviewed).days
            if age < 0:
                errors.append(f"{label}: last_reviewed_at is in the future")
            elif age > review_interval:
                warnings.append(
                    f"{label}: review is stale ({age} days; limit {review_interval})"
                )
        required_status = manifest.get("review_policy", {}).get(
            "required_review_status"
        )
        if required_status and record.get("review_status") != required_status:
            errors.append(f"{label}: review_status violates review policy")
        if (
            coverage_plan is not None
            and record.get("review_status")
            != coverage_plan.get("required_review_status")
        ):
            errors.append(
                f"{label}: review_status violates coverage-plan policy"
            )

    duplicate_documents = sorted(
        key for key, count in Counter(document_ids).items() if count > 1
    )
    if duplicate_documents:
        errors.append(f"records: duplicate document_id values {duplicate_documents}")

    if coverage_plan is not None and coverage_plan.get("status") == "frozen":
        target_documents = coverage_plan.get("target_document_count")
        if isinstance(target_documents, int) and len(records) != target_documents:
            errors.append(
                "coverage_plan: frozen corpus document count does not match target"
            )
        cluster_counts = Counter(record.get("topic_cluster") for record in records)
        cluster_sources: dict[str, set[str]] = {}
        for record in records:
            cluster_sources.setdefault(record.get("topic_cluster"), set()).add(
                record.get("source_id")
            )
        minimum_sources = coverage_plan.get("minimum_sources_per_cluster")
        for cluster in coverage_plan.get("clusters", []):
            if not isinstance(cluster, dict):
                continue
            cluster_id = cluster.get("cluster_id")
            target = cluster.get("target_documents")
            if isinstance(target, int) and cluster_counts[cluster_id] < target:
                errors.append(
                    f"coverage_plan: frozen cluster {cluster_id!r} is below target"
                )
            if (
                isinstance(minimum_sources, int)
                and len(cluster_sources.get(cluster_id, set())) < minimum_sources
            ):
                errors.append(
                    f"coverage_plan: frozen cluster {cluster_id!r} is below "
                    "the source minimum"
                )

    return ValidationResult(
        tuple(errors), tuple(warnings), tuple(records), manifest, coverage_plan
    )


def validate_project(project: Path) -> ValidationResult:
    records, manifest = load_corpus(project)
    coverage_plan = load_coverage_plan(project)
    return validate_payload(records, manifest, coverage_plan=coverage_plan)


def write_records(project: Path, records: list[dict]) -> None:
    records_path, _ = knowledge_paths(project)
    records_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
