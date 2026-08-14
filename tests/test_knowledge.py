import hashlib
import json
from datetime import date

import pytest

from knowledge import (
    KnowledgeValidationError,
    LocalKnowledgeBase,
    augment_with_context,
)
from retrieval import BM25Retriever, KeywordRetriever, lexical_tokens


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
        "last_reviewed_at": date.today().isoformat(),
        "version": "v1",
        "evidence_grade": "not_assessed",
        "source_type": "official_public_health_guidance",
        "topic_cluster": "cardiovascular_warning_signs",
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


def governed_manifest():
    return {
        "schema_version": 1,
        "review_policy": {
            "review_interval_days": 180,
            "required_review_status": "project_summary_unverified_by_clinician",
        },
        "sources": [
            {
                "source_id": "cdc",
                "organization": "Test issuer",
                "homepage": "https://example.test/",
                "jurisdiction": "US",
                "source_type": "official_public_health_guidance",
                "update_method": "manual_review",
                "reuse_status": "source terms apply",
            }
        ],
    }


def write_test_corpus(tmp_path, records):
    path = tmp_path / "knowledge.json"
    manifest_path = tmp_path / "manifest.json"
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(governed_manifest(), ensure_ascii=False), encoding="utf-8"
    )
    return path, manifest_path


def test_search_returns_relevant_versioned_document(tmp_path):
    path, manifest_path = write_test_corpus(tmp_path, [governed_record()])
    knowledge_base = LocalKnowledgeBase(path, manifest_path)

    documents = knowledge_base.search("胸痛怎么办")

    assert [document.title for document in documents] == ["测试资料"]
    assert "测试资料" in augment_with_context("胸痛怎么办", documents)


def test_search_does_not_return_irrelevant_documents(tmp_path):
    path, manifest_path = write_test_corpus(
        tmp_path, [governed_record(content="内容", title="资料")]
    )

    assert LocalKnowledgeBase(path, manifest_path).search("皮肤护理") == []


def test_knowledge_loader_rejects_changed_content_without_hash_update(tmp_path):
    record = governed_record()
    record["content"] = "内容被修改"
    path, manifest_path = write_test_corpus(tmp_path, [record])

    with pytest.raises(KnowledgeValidationError, match="hash mismatch"):
        LocalKnowledgeBase(path, manifest_path)


def test_knowledge_loader_requires_topic_cluster(tmp_path):
    record = governed_record()
    del record["topic_cluster"]
    path, manifest_path = write_test_corpus(tmp_path, [record])

    with pytest.raises(KnowledgeValidationError, match="topic_cluster"):
        LocalKnowledgeBase(path, manifest_path)


def test_knowledge_loader_rejects_source_id_impersonation(tmp_path):
    record = governed_record(source_url="https://cdc.gov.attacker.example/topic")
    path, manifest_path = write_test_corpus(tmp_path, [record])

    with pytest.raises(KnowledgeValidationError, match="not approved"):
        LocalKnowledgeBase(path, manifest_path)


def test_knowledge_loader_rejects_registry_metadata_mismatch(tmp_path):
    record = governed_record(issuer="Impersonated issuer")
    path, manifest_path = write_test_corpus(tmp_path, [record])

    with pytest.raises(KnowledgeValidationError, match="issuer"):
        LocalKnowledgeBase(path, manifest_path)


def test_knowledge_loader_rejects_stale_review(tmp_path):
    record = governed_record(last_reviewed_at="2020-01-01")
    path, manifest_path = write_test_corpus(tmp_path, [record])

    with pytest.raises(KnowledgeValidationError, match="stale"):
        LocalKnowledgeBase(path, manifest_path)


def test_production_knowledge_has_governance_metadata():
    knowledge_base = LocalKnowledgeBase()

    assert len(knowledge_base.documents) == 6
    assert all(document.document_id for document in knowledge_base.documents)
    assert all(document.last_reviewed_at for document in knowledge_base.documents)
    assert all(document.review_status for document in knowledge_base.documents)
    assert all(document.topic_cluster for document in knowledge_base.documents)


def test_production_default_preserves_keyword_baseline():
    knowledge_base = LocalKnowledgeBase()

    assert knowledge_base.retrieval_strategy == "keyword"
    assert isinstance(knowledge_base.retriever, KeywordRetriever)


def test_bm25_candidate_handles_lexical_paraphrase_without_false_allergy_hit():
    knowledge_base = LocalKnowledgeBase(strategy="bm25")

    heart_results = knowledge_base.search("持续的胸部压迫感伴随冷汗可能参考什么资料")
    allergy_results = knowledge_base.search("想查权威的过敏性鼻炎日常管理资料")

    assert heart_results[0].document_id == "nhs-heart-attack-signs-2026-08-review"
    assert allergy_results == []


@pytest.mark.parametrize("strategy", ["keyword", "bm25"])
def test_gastrointestinal_batch_retrieves_without_unrelated_hits(strategy):
    knowledge_base = LocalKnowledgeBase(strategy=strategy)

    relevant = knowledge_base.search(
        "最近一直拉肚子和呕吐，尿量也变少了", limit=3
    )
    unrelated = knowledge_base.search("如何修复 Python 单元测试", limit=3)

    assert len(relevant) >= 2
    assert all(
        document.topic_cluster == "gastrointestinal_symptoms"
        for document in relevant
    )
    assert unrelated == []


def test_chinese_lexical_tokens_are_deterministic_and_remove_generic_terms():
    tokens = lexical_tokens("权威的心理危机支持资料 FAST")

    assert "心理" in tokens
    assert "危机" in tokens
    assert "fast" in tokens
    assert "资料" not in tokens
