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


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    records: tuple[dict, ...]
    manifest: dict


def knowledge_paths(project: Path) -> tuple[Path, Path]:
    knowledge_dir = project.resolve() / "knowledge"
    return (
        knowledge_dir / "medical_guidance.json",
        knowledge_dir / "source_manifest.json",
    )


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


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _iso_date(value, label: str, errors: list[str]) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{label}: expected ISO YYYY-MM-DD, got {value!r}")
        return None


def validate_payload(
    records: list[dict], manifest: dict, *, today: date | None = None
) -> ValidationResult:
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []

    if manifest.get("schema_version") != 1:
        errors.append("manifest: unsupported or missing schema_version")
    sources = manifest.get("sources", [])
    if not isinstance(sources, list):
        errors.append("manifest: sources must be a list")
        sources = []

    source_ids: list[str] = []
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
        if urlparse(str(source.get("homepage", ""))).scheme != "https":
            errors.append(f"{label}: homepage must use HTTPS")

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
        if record.get("source_id") not in known_sources:
            errors.append(f"{label}: unknown source_id {record.get('source_id')!r}")
        if urlparse(str(record.get("source_url", ""))).scheme != "https":
            errors.append(f"{label}: source_url must use HTTPS")
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
        reviewed = _iso_date(
            record.get("last_reviewed_at"),
            f"{label}.last_reviewed_at",
            errors,
        )
        _iso_date(record.get("published_at"), f"{label}.published_at", errors)
        if reviewed:
            age = (today - reviewed).days
            if age < 0:
                errors.append(f"{label}: last_reviewed_at is in the future")
            elif age > review_interval:
                warnings.append(
                    f"{label}: review is stale ({age} days; limit {review_interval})"
                )

    duplicate_documents = sorted(
        key for key, count in Counter(document_ids).items() if count > 1
    )
    if duplicate_documents:
        errors.append(f"records: duplicate document_id values {duplicate_documents}")

    return ValidationResult(
        tuple(errors), tuple(warnings), tuple(records), manifest
    )


def validate_project(project: Path) -> ValidationResult:
    records, manifest = load_corpus(project)
    return validate_payload(records, manifest)


def write_records(project: Path, records: list[dict]) -> None:
    records_path, _ = knowledge_paths(project)
    records_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
