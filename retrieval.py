"""Inspectable lexical retrieval candidates for measured RAG experiments."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from typing import Protocol, Sequence

from knowledge import KnowledgeDocument


DEFAULT_BM25_MINIMUM_SCORE = 4.5


class Retriever(Protocol):
    """Minimal interface shared by production and experiment retrievers."""

    name: str
    index_size_bytes: int

    def search(self, query: str, limit: int = 2) -> list[KnowledgeDocument]: ...


def _keyword_terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2,}", text.lower()))


class KeywordRetriever:
    """The original exact keyword/token scoring baseline."""

    name = "keyword"

    def __init__(self, documents: Sequence[KnowledgeDocument]) -> None:
        self.documents = tuple(documents)
        self.index_size_bytes = 0

    def search(self, query: str, limit: int = 2) -> list[KnowledgeDocument]:
        normalized = query.lower()
        query_terms = _keyword_terms(normalized)
        scored: list[tuple[int, str, KnowledgeDocument]] = []
        for document in self.documents:
            score = sum(
                3 for keyword in document.keywords
                if keyword.lower() in normalized
            )
            score += sum(
                1
                for term in query_terms
                if term in document.title.lower()
                or term in document.content.lower()
            )
            if score:
                scored.append((score, document.document_id, document))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [document for _, _, document in scored[:limit]]


_LEXICAL_STOP_TOKENS = {
    "一个", "一些", "什么", "哪些", "关于", "可能", "如何", "怎么",
    "资料", "信息", "来源", "可靠", "权威", "科普", "日常", "管理",
    "相关", "常见", "通常", "查询", "查找", "寻找", "需要", "可以",
}


def lexical_tokens(text: str) -> tuple[str, ...]:
    """Tokenize Latin words and Chinese character bi/trigrams deterministically."""
    normalized = text.lower()
    tokens = re.findall(r"[a-z0-9]+", normalized)
    for sequence in re.findall(r"[\u4e00-\u9fff]+", normalized):
        for size in (2, 3):
            tokens.extend(
                sequence[index:index + size]
                for index in range(len(sequence) - size + 1)
            )
    return tuple(token for token in tokens if token not in _LEXICAL_STOP_TOKENS)


class BM25Retriever:
    """Small-corpus BM25 candidate using dependency-free Chinese n-grams."""

    name = "bm25"

    def __init__(
        self,
        documents: Sequence[KnowledgeDocument],
        *,
        k1: float = 1.5,
        b: float = 0.75,
        minimum_score: float = DEFAULT_BM25_MINIMUM_SCORE,
    ) -> None:
        self.documents = tuple(documents)
        self.k1 = k1
        self.b = b
        self.minimum_score = minimum_score
        self._term_frequencies: list[Counter[str]] = []
        document_frequencies: Counter[str] = Counter()
        for document in self.documents:
            weighted_text = " ".join(
                (document.title, document.content, *document.keywords, *document.keywords)
            )
            frequencies = Counter(lexical_tokens(weighted_text))
            self._term_frequencies.append(frequencies)
            document_frequencies.update(frequencies.keys())
        self._document_lengths = tuple(
            sum(frequencies.values()) for frequencies in self._term_frequencies
        )
        self._average_length = (
            sum(self._document_lengths) / len(self._document_lengths)
            if self._document_lengths else 0.0
        )
        document_count = len(self.documents)
        self._inverse_document_frequency = {
            term: math.log(1 + (document_count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequencies.items()
        }
        index_payload = {
            "tf": [dict(sorted(frequencies.items())) for frequencies in self._term_frequencies],
            "idf": dict(sorted(self._inverse_document_frequency.items())),
        }
        self.index_size_bytes = len(
            json.dumps(index_payload, ensure_ascii=False, separators=(",", ":")).encode()
        )

    def search(self, query: str, limit: int = 2) -> list[KnowledgeDocument]:
        query_terms = Counter(lexical_tokens(query))
        scored: list[tuple[float, str, KnowledgeDocument]] = []
        for index, document in enumerate(self.documents):
            frequencies = self._term_frequencies[index]
            length = self._document_lengths[index]
            score = 0.0
            for term, query_frequency in query_terms.items():
                term_frequency = frequencies.get(term, 0)
                if not term_frequency:
                    continue
                normalization = term_frequency + self.k1 * (
                    1 - self.b
                    + self.b * length / (self._average_length or 1.0)
                )
                score += (
                    self._inverse_document_frequency.get(term, 0.0)
                    * term_frequency
                    * (self.k1 + 1)
                    / normalization
                    * query_frequency
                )
            if score >= self.minimum_score:
                scored.append((score, document.document_id, document))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [document for _, _, document in scored[:limit]]


def create_retriever(
    strategy: str,
    documents: Sequence[KnowledgeDocument],
) -> Retriever:
    """Create an allow-listed retrieval strategy."""
    normalized = strategy.strip().lower()
    if normalized == "keyword":
        return KeywordRetriever(documents)
    if normalized == "bm25":
        return BM25Retriever(documents)
    raise ValueError(f"Unsupported retrieval strategy: {strategy}")
