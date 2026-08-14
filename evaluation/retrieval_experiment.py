"""Compare retrieval candidates on one frozen dataset without model calls."""

from __future__ import annotations

import json
import math
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from knowledge import KnowledgeDocument
from retrieval import DEFAULT_BM25_MINIMUM_SCORE, Retriever, create_retriever

from .schema import EvaluationCase


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


@dataclass(frozen=True)
class RetrievalCaseResult:
    case_id: str
    scenario: str
    tags: tuple[str, ...]
    relevant_document_ids: tuple[str, ...]
    returned_document_ids: tuple[str, ...]
    latency_ms: float


@dataclass(frozen=True)
class RetrievalStrategyResult:
    strategy: str
    build_latency_ms: float
    index_size_bytes: int
    metrics: dict[str, float | int | None]
    case_results: tuple[RetrievalCaseResult, ...]


@dataclass(frozen=True)
class RetrievalExperimentReport:
    dataset_name: str
    generated_at: str
    retrieval_k: int
    candidate_count: int
    relevant_case_count: int
    no_hit_case_count: int
    strategies: tuple[RetrievalStrategyResult, ...]
    bm25_threshold_sweep: tuple[dict[str, float], ...]
    recommendation: str
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "generated_at": self.generated_at,
            "retrieval_k": self.retrieval_k,
            "candidate_count": self.candidate_count,
            "relevant_case_count": self.relevant_case_count,
            "no_hit_case_count": self.no_hit_case_count,
            "strategies": [asdict(result) for result in self.strategies],
            "bm25_threshold_sweep": list(self.bm25_threshold_sweep),
            "recommendation": self.recommendation,
            "limitations": list(self.limitations),
        }

    def to_markdown(self) -> str:
        def display(value: float | int | None) -> str:
            if value is None:
                return "not measured"
            if isinstance(value, float):
                return f"{value:.4f}"
            return str(value)

        lines = [
            f"# Retrieval experiment: {self.dataset_name}",
            "",
            f"- Generated: {self.generated_at}",
            f"- Eligible non-emergency retrieval cases: {self.candidate_count}",
            f"- Cases with a relevant governed document: {self.relevant_case_count}",
            f"- Expected no-hit cases: {self.no_hit_case_count}",
            f"- Retrieval K: {self.retrieval_k}",
            "- Model/API calls: none",
            "",
            "## Strategy comparison",
            "",
            "| Strategy | Recall@K | MRR | No-hit accuracy | P50 ms | P95 ms | Build ms | Index bytes |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for result in self.strategies:
            metrics = result.metrics
            lines.append(
                f"| {result.strategy} | {display(metrics['recall_at_k'])} | "
                f"{display(metrics['mrr'])} | {display(metrics['no_hit_accuracy'])} | "
                f"{display(metrics['latency_p50_ms'])} | "
                f"{display(metrics['latency_p95_ms'])} | "
                f"{display(result.build_latency_ms)} | {result.index_size_bytes} |"
            )
        if self.bm25_threshold_sweep:
            lines.extend(
                [
                    "",
                    "## BM25 development-set threshold sweep",
                    "",
                    "| Minimum score | Recall@K | No-hit accuracy |",
                    "|---:|---:|---:|",
                ]
            )
            lines.extend(
                f"| {point['minimum_score']:.1f} | {point['recall_at_k']:.4f} | "
                f"{point['no_hit_accuracy']:.4f} |"
                for point in self.bm25_threshold_sweep
            )
            lines.extend(
                [
                    "",
                    "The committed BM25 candidate uses "
                    f"`minimum_score={DEFAULT_BM25_MINIMUM_SCORE:.1f}`, the "
                    "highest-recall tested point that does not reduce no-hit "
                    "accuracy relative to the keyword baseline. Because the same "
                    "MVP set selected this value, the result is a development "
                    "candidate—not an unbiased test estimate.",
                ]
            )
        lines.extend(["", "## Recommendation", "", self.recommendation])

        lines.extend(["", "## Misses by strategy", ""])
        for result in self.strategies:
            misses = [
                case
                for case in result.case_results
                if case.relevant_document_ids
                and not set(case.relevant_document_ids).intersection(
                    case.returned_document_ids
                )
            ]
            lines.append(f"### {result.strategy}")
            lines.append("")
            if not misses:
                lines.append("No relevant-document misses.")
            else:
                lines.extend(
                    f"- `{case.case_id}` tags={list(case.tags)} returned={list(case.returned_document_ids)}"
                    for case in misses
                )
            lines.append("")

        lines.extend(["## False hits by strategy", ""])
        for result in self.strategies:
            false_hits = [
                case
                for case in result.case_results
                if not case.relevant_document_ids and case.returned_document_ids
            ]
            lines.append(f"### {result.strategy}")
            lines.append("")
            if not false_hits:
                lines.append("No false hits on expected no-hit cases.")
            else:
                lines.extend(
                    f"- `{case.case_id}` tags={list(case.tags)} returned={list(case.returned_document_ids)}"
                    for case in false_hits
                )
            lines.append("")

        lines.extend(["## Limitations", ""])
        lines.extend(f"- {limitation}" for limitation in self.limitations)
        return "\n".join(lines) + "\n"

    def write(self, output_directory: str | Path) -> tuple[Path, Path]:
        output = Path(output_directory)
        output.mkdir(parents=True, exist_ok=True)
        json_path = output / "retrieval_experiment.json"
        markdown_path = output / "retrieval_experiment.md"
        json_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(self.to_markdown(), encoding="utf-8")
        return json_path, markdown_path


def _evaluate_retriever(
    retriever: Retriever,
    cases: Sequence[EvaluationCase],
    retrieval_k: int,
    build_latency_ms: float,
) -> RetrievalStrategyResult:
    results: list[RetrievalCaseResult] = []
    for case in cases:
        started = time.perf_counter()
        documents = retriever.search(case.user_input, limit=retrieval_k)
        latency_ms = (time.perf_counter() - started) * 1000
        results.append(
            RetrievalCaseResult(
                case_id=case.case_id,
                scenario=case.scenario,
                tags=case.tags,
                relevant_document_ids=case.relevant_document_ids,
                returned_document_ids=tuple(
                    document.document_id for document in documents
                ),
                latency_ms=latency_ms,
            )
        )

    relevant = [result for result in results if result.relevant_document_ids]
    no_hit = [result for result in results if not result.relevant_document_ids]
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    for result in relevant:
        relevant_ids = set(result.relevant_document_ids)
        returned = list(result.returned_document_ids)
        recalls.append(len(relevant_ids.intersection(returned)) / len(relevant_ids))
        ranks = [
            index + 1 for index, document_id in enumerate(returned)
            if document_id in relevant_ids
        ]
        reciprocal_ranks.append(1 / min(ranks) if ranks else 0.0)
    latencies = [result.latency_ms for result in results]
    metrics: dict[str, float | int | None] = {
        "recall_at_k": statistics.fmean(recalls) if recalls else None,
        "mrr": statistics.fmean(reciprocal_ranks) if reciprocal_ranks else None,
        "no_hit_accuracy": (
            sum(not result.returned_document_ids for result in no_hit) / len(no_hit)
            if no_hit else None
        ),
        "latency_p50_ms": _percentile(latencies, 0.50),
        "latency_p95_ms": _percentile(latencies, 0.95),
        "relevant_miss_count": sum(recall == 0 for recall in recalls),
        "false_hit_count": sum(bool(result.returned_document_ids) for result in no_hit),
    }
    return RetrievalStrategyResult(
        strategy=retriever.name,
        build_latency_ms=build_latency_ms,
        index_size_bytes=retriever.index_size_bytes,
        metrics=metrics,
        case_results=tuple(results),
    )


def run_retrieval_experiment(
    cases: Sequence[EvaluationCase],
    documents: Sequence[KnowledgeDocument],
    *,
    dataset_name: str,
    strategies: Sequence[str] = ("keyword", "bm25"),
    retrieval_k: int = 3,
) -> RetrievalExperimentReport:
    """Run isolated retrieval comparison on non-emergency retrieval cases."""
    eligible = tuple(
        case
        for case in cases
        if "retrieval" in case.checks and not case.expected_emergency
    )
    results: list[RetrievalStrategyResult] = []
    for strategy in strategies:
        started = time.perf_counter()
        retriever = create_retriever(strategy, documents)
        build_latency_ms = (time.perf_counter() - started) * 1000
        results.append(
            _evaluate_retriever(retriever, eligible, retrieval_k, build_latency_ms)
        )

    threshold_sweep: list[dict[str, float]] = []
    if "bm25" in strategies:
        from retrieval import BM25Retriever

        for minimum_score in (0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
            candidate = _evaluate_retriever(
                BM25Retriever(documents, minimum_score=minimum_score),
                eligible,
                retrieval_k,
                0.0,
            )
            threshold_sweep.append(
                {
                    "minimum_score": minimum_score,
                    "recall_at_k": float(candidate.metrics["recall_at_k"] or 0.0),
                    "no_hit_accuracy": float(
                        candidate.metrics["no_hit_accuracy"] or 0.0
                    ),
                }
            )

    baseline = results[0]
    best = max(
        results,
        key=lambda result: (
            result.metrics["recall_at_k"] or 0.0,
            result.metrics["no_hit_accuracy"] or 0.0,
            -(result.metrics["latency_p95_ms"] or 0.0),
        ),
    )
    recall_gain = (best.metrics["recall_at_k"] or 0.0) - (
        baseline.metrics["recall_at_k"] or 0.0
    )
    no_hit_delta = (best.metrics["no_hit_accuracy"] or 0.0) - (
        baseline.metrics["no_hit_accuracy"] or 0.0
    )
    if best.strategy != baseline.strategy and recall_gain > 0 and no_hit_delta >= 0:
        recommendation = (
            f"Promote `{best.strategy}` to the next candidate gate: it improves "
            f"Recall@{retrieval_k} by {recall_gain:.4f} without reducing no-hit "
            "accuracy. Keep `keyword` as the production default until an "
            "independent holdout confirms the development-set result; the "
            "separate end-to-end comparison is recorded alongside this report."
        )
    else:
        recommendation = (
            "Keep `keyword` as the production default. The candidates do not "
            "improve relevant-document recall without a no-hit trade-off."
        )
    relevant_count = sum(bool(case.relevant_document_ids) for case in eligible)
    return RetrievalExperimentReport(
        dataset_name=dataset_name,
        generated_at=datetime.now(UTC).isoformat(),
        retrieval_k=retrieval_k,
        candidate_count=len(eligible),
        relevant_case_count=relevant_count,
        no_hit_case_count=len(eligible) - relevant_count,
        strategies=tuple(results),
        bm25_threshold_sweep=tuple(threshold_sweep),
        recommendation=recommendation,
        limitations=(
            "The corpus has nine short project-authored summaries across five topic clusters.",
            "Cases and labels are synthetic and pending qualified review.",
            "BM25 uses deterministic Chinese character n-grams, not a linguistic segmenter.",
            "Latency and index-size values describe this local run and tiny corpus.",
            "This component experiment does not rerun Qwen or measure answer groundedness.",
        ),
    )
