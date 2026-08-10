"""Small, dependency-free local retrieval layer for versioned documents."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


class KnowledgeValidationError(ValueError):
    """Raised when a governed knowledge record fails integrity checks."""


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    content: str
    source_url: str
    keywords: tuple[str, ...]
    document_id: str = ""
    source_id: str = ""
    issuer: str = ""
    jurisdiction: str = ""
    language: str = "zh-CN"
    source_language: str = ""
    published_at: str | None = None
    last_reviewed_at: str = ""
    version: str = ""
    evidence_grade: str = "not_assessed"
    source_type: str = ""
    applicable_population: str = ""
    review_status: str = ""
    license: str = ""
    content_sha256: str = ""


REQUIRED_FIELDS = {
    "document_id", "source_id", "issuer", "jurisdiction", "language",
    "source_language", "last_reviewed_at", "version", "evidence_grade",
    "source_type", "applicable_population", "review_status", "license",
    "content_sha256", "title", "content", "source_url", "keywords",
}


def _validated_document(
    item: dict, known_sources: set[str] | None
) -> KnowledgeDocument:
    missing = REQUIRED_FIELDS - item.keys()
    if missing:
        raise KnowledgeValidationError(
            f"Knowledge record is missing fields: {', '.join(sorted(missing))}"
        )
    if known_sources is not None and item["source_id"] not in known_sources:
        raise KnowledgeValidationError(
            f"Unknown source_id {item['source_id']!r} in {item['document_id']!r}"
        )
    if urlparse(item["source_url"]).scheme != "https":
        raise KnowledgeValidationError("Knowledge source URLs must use HTTPS")
    try:
        date.fromisoformat(item["last_reviewed_at"])
        if item.get("published_at"):
            date.fromisoformat(item["published_at"])
    except (TypeError, ValueError) as exc:
        raise KnowledgeValidationError(
            "Knowledge dates must use ISO YYYY-MM-DD"
        ) from exc
    expected_hash = hashlib.sha256(item["content"].encode("utf-8")).hexdigest()
    if item["content_sha256"] != expected_hash:
        raise KnowledgeValidationError(
            f"Content hash mismatch for {item['document_id']!r}"
        )
    if not isinstance(item["keywords"], list) or not item["keywords"]:
        raise KnowledgeValidationError("Knowledge keywords must be a non-empty list")
    return KnowledgeDocument(**{**item, "keywords": tuple(item["keywords"])})


class LocalKnowledgeBase:
    def __init__(
        self,
        path: str | Path | None = None,
        manifest_path: str | Path | None = None,
    ) -> None:
        source_path = Path(path) if path else (
            Path(__file__).resolve().parent / "knowledge" / "medical_guidance.json"
        )
        manifest_source = Path(manifest_path) if manifest_path else (
            Path(__file__).resolve().parent / "knowledge" / "source_manifest.json"
        )
        with manifest_source.open(encoding="utf-8") as file:
            manifest = json.load(file)
        if manifest.get("schema_version") != 1:
            raise KnowledgeValidationError("Unsupported source manifest schema")
        known_sources = {
            source["source_id"] for source in manifest.get("sources", [])
        }
        with source_path.open(encoding="utf-8") as file:
            items = json.load(file)
        document_ids = [item.get("document_id") for item in items]
        if len(document_ids) != len(set(document_ids)):
            raise KnowledgeValidationError(
                "Knowledge document_id values must be unique"
            )
        self.source_manifest = manifest
        self.documents = tuple(
            _validated_document(item, known_sources) for item in items
        )

    def search(self, query: str, limit: int = 2) -> list[KnowledgeDocument]:
        normalized = query.lower()
        query_terms = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2,}", normalized))
        scored: list[tuple[int, KnowledgeDocument]] = []
        for document in self.documents:
            score = sum(3 for keyword in document.keywords if keyword.lower() in normalized)
            score += sum(
                1
                for term in query_terms
                if term in document.title.lower() or term in document.content.lower()
            )
            if score:
                scored.append((score, document))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored[:limit]]


def augment_with_context(
    user_input: str, documents: list[KnowledgeDocument]
) -> str:
    if not documents:
        return user_input
    context = "\n\n".join(
        f"资料：{document.title}\n{document.content}\n来源：{document.source_url}"
        for document in documents
    )
    return f"""请回答下面的用户问题。仅将参考资料用于一般健康信息；不要把资料当作对用户的诊断。引用使用到的资料标题；资料不足时明确说明。

用户问题：{user_input}

参考资料：
{context}"""
