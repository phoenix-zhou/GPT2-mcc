import hashlib
import json

import pytest

from knowledge import (
    KnowledgeValidationError,
    LocalKnowledgeBase,
    augment_with_context,
)


def governed_record(**overrides):
    content = overrides.pop("content", "胸痛资料内容")
    record = {
        "document_id": "test-guidance-v1",
        "source_id": "cdc",
        "issuer": "Test issuer",
        "jurisdiction": "US",
        "language": "zh-CN",
        "source_language": "en",
        "published_at": None,
        "last_reviewed_at": "2026-08-09",
        "version": "v1",
        "evidence_grade": "not_assessed",
        "source_type": "official_public_health_guidance",
        "applicable_population": "general_public",
        "review_status": "project_summary_unverified_by_clinician",
        "license": "source-terms-apply",
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "title": "测试资料",
        "content": content,
        "source_url": "https://example.test/source",
        "keywords": ["胸痛"],
    }
    record.update(overrides)
    return record


def test_search_returns_relevant_versioned_document(tmp_path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [governed_record()],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    knowledge_base = LocalKnowledgeBase(path)

    documents = knowledge_base.search("胸痛怎么办")

    assert [document.title for document in documents] == ["测试资料"]
    assert "测试资料" in augment_with_context("胸痛怎么办", documents)


def test_search_does_not_return_irrelevant_documents(tmp_path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps([governed_record(content="内容", title="资料")], ensure_ascii=False),
        encoding="utf-8",
    )

    assert LocalKnowledgeBase(path).search("皮肤护理") == []


def test_knowledge_loader_rejects_changed_content_without_hash_update(tmp_path):
    path = tmp_path / "knowledge.json"
    record = governed_record()
    record["content"] = "内容被修改"
    path.write_text(json.dumps([record], ensure_ascii=False), encoding="utf-8")

    with pytest.raises(KnowledgeValidationError, match="hash mismatch"):
        LocalKnowledgeBase(path)


def test_production_knowledge_has_governance_metadata():
    knowledge_base = LocalKnowledgeBase()

    assert len(knowledge_base.documents) == 3
    assert all(document.document_id for document in knowledge_base.documents)
    assert all(document.last_reviewed_at for document in knowledge_base.documents)
    assert all(document.review_status for document in knowledge_base.documents)
