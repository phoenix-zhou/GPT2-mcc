"""Small, dependency-free local retrieval layer for versioned documents."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    content: str
    source_url: str
    keywords: tuple[str, ...]


class LocalKnowledgeBase:
    def __init__(self, path: str | Path | None = None) -> None:
        source_path = Path(path) if path else (
            Path(__file__).resolve().parent / "knowledge" / "medical_guidance.json"
        )
        with source_path.open(encoding="utf-8") as file:
            items = json.load(file)
        self.documents = tuple(
            KnowledgeDocument(
                title=item["title"],
                content=item["content"],
                source_url=item["source_url"],
                keywords=tuple(item["keywords"]),
            )
            for item in items
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
