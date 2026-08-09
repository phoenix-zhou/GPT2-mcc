import json

from knowledge import LocalKnowledgeBase, augment_with_context


def test_search_returns_relevant_versioned_document(tmp_path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [{
                "title": "测试资料",
                "content": "胸痛资料内容",
                "source_url": "https://example.test/source",
                "keywords": ["胸痛"],
            }],
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
        '[{"title":"资料","content":"内容","source_url":"https://example.test","keywords":["胸痛"]}]',
        encoding="utf-8",
    )

    assert LocalKnowledgeBase(path).search("皮肤护理") == []
