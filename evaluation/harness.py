"""Deterministic safety and retrieval evaluation harness."""

from __future__ import annotations

import json
import math
import statistics
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .predictions import PredictionRun, ProviderPrediction
from .schema import EvaluationCase


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    domain: str
    scenario: str
    expected_route: str
    predicted_emergency: bool | None
    predicted_emergency_category: str | None
    expected_emergency: bool
    expected_emergency_category: str | None
    returned_document_ids: tuple[str, ...]
    relevant_document_ids: tuple[str, ...]
    safety_latency_ms: float | None
    retrieval_latency_ms: float | None
    predicted_route: str | None = None
    answer: str | None = None
    predicted_source_ids: tuple[str, ...] = ()
    model_calls: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    prediction_latency_ms: float | None = None
    estimated_cost: float | None = None
    prediction_error: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class EvaluationReport:
    dataset_name: str
    generated_at: str
    case_count: int
    scenario_counts: dict[str, int]
    metrics: dict[str, float | int | None]
    limitations: tuple[str, ...]
    case_results: tuple[CaseResult, ...]
    failure_counts: dict[str, int]
    prediction_run: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "generated_at": self.generated_at,
            "case_count": self.case_count,
            "scenario_counts": self.scenario_counts,
            "metrics": self.metrics,
            "limitations": list(self.limitations),
            "failure_counts": self.failure_counts,
            "case_results": [asdict(result) for result in self.case_results],
            "prediction_run": self.prediction_run,
        }

    def to_markdown(self) -> str:
        def display(value: float | int | None) -> str:
            if value is None:
                return "not measured"
            if isinstance(value, float):
                return f"{value:.4f}"
            return str(value)

        metric_labels = {
            "emergency_recall": "Emergency recall",
            "emergency_precision": "Emergency precision",
            "emergency_false_positive_rate": "Emergency false-positive rate",
            "emergency_category_accuracy": "Emergency category accuracy",
            "retrieval_recall_at_k": "Retrieval Recall@K",
            "retrieval_mrr": "Retrieval MRR",
            "retrieval_no_hit_accuracy": "Irrelevant-query no-hit accuracy",
            "citation_id_validity": "Returned citation-ID validity",
            "safety_p95_latency_ms": "Safety P95 latency (ms)",
            "retrieval_p95_latency_ms": "Retrieval P95 latency (ms)",
            "case_error_count": "Case errors",
            "prediction_coverage": "Provider-prediction coverage",
            "planner_route_accuracy": "Planner route accuracy",
            "answer_completion_rate": "Answer completion rate",
            "prohibited_claim_pass_rate": "Prohibited-claim pass rate",
            "required_concept_literal_coverage": "Required-concept literal coverage",
            "prediction_source_recall": "Prediction source recall",
            "task_success_rate": "Deterministic task-success proxy",
            "prediction_error_count": "Provider-prediction errors",
            "model_call_count": "Model calls",
            "model_calls_per_case": "Mean model calls per case",
            "input_tokens_total": "Input tokens",
            "output_tokens_total": "Output tokens",
            "prediction_p50_latency_ms": "Prediction P50 latency (ms)",
            "prediction_p95_latency_ms": "Prediction P95 latency (ms)",
            "estimated_cost_total": "Estimated model cost",
            "groundedness": "Experimental judge groundedness",
        }
        lines = [
            f"# Evaluation report: {self.dataset_name}",
            "",
            f"- Generated: {self.generated_at}",
            f"- Cases: {self.case_count}",
            "- Evaluation mode: deterministic component baseline plus optional captured provider predictions",
            "",
            "## Scenario coverage",
            "",
            "| Scenario | Cases |",
            "|---|---:|",
        ]
        lines.extend(
            f"| {scenario} | {count} |"
            for scenario, count in sorted(self.scenario_counts.items())
        )
        lines.extend(["", "## Metrics", "", "| Metric | Value |", "|---|---:|"])
        lines.extend(
            f"| {metric_labels.get(key, key)} | {display(value)} |"
            for key, value in self.metrics.items()
        )
        provider_results = [
            result
            for result in self.case_results
            if result.predicted_route is not None
        ]
        if provider_results:
            lines.extend(
                [
                    "",
                    "## Provider route accuracy by scenario",
                    "",
                    "| Scenario | Correct | Cases | Accuracy |",
                    "|---|---:|---:|---:|",
                ]
            )
            for scenario in sorted(
                {result.scenario for result in provider_results}
            ):
                scenario_results = [
                    result
                    for result in provider_results
                    if result.scenario == scenario
                ]
                correct = sum(
                    result.predicted_route == result.expected_route
                    for result in scenario_results
                )
                lines.append(
                    f"| {scenario} | {correct} | {len(scenario_results)} | "
                    f"{correct / len(scenario_results):.4f} |"
                )
        lines.extend(["", "## Limitations", ""])
        lines.extend(f"- {limitation}" for limitation in self.limitations)

        lines.extend(
            [
                "",
                "## Failure taxonomy",
                "",
                "| Failure category | Cases |",
                "|---|---:|",
            ]
        )
        if self.failure_counts:
            lines.extend(
                f"| {category} | {count} |"
                for category, count in sorted(self.failure_counts.items())
            )
        else:
            lines.append("| none detected | 0 |")

        failures = [
            result
            for result in self.case_results
            if result.error
            or result.prediction_error
            or (
                result.predicted_route is not None
                and result.predicted_route != result.expected_route
            )
            or (
                result.predicted_emergency is not None
                and result.predicted_emergency != result.expected_emergency
            )
            or (
                result.relevant_document_ids
                and not set(result.relevant_document_ids).intersection(
                    result.returned_document_ids
                )
            )
        ]
        lines.extend(["", "## Failure sample", ""])
        if not failures:
            lines.append("No component-level failures in this run.")
        else:
            lines.extend(
                f"- `{result.case_id}` ({result.scenario}): "
                f"expected route `{result.expected_route}`, "
                f"predicted route `{result.predicted_route}`, "
                f"categories={list(classify_failures(result))}, "
                f"emergency={result.predicted_emergency}, "
                f"documents={list(result.returned_document_ids)}, "
                f"prediction_error={result.prediction_error}"
                for result in failures[:20]
            )
        return "\n".join(lines) + "\n"

    def write(self, output_directory: str | Path) -> tuple[Path, Path]:
        output = Path(output_directory)
        output.mkdir(parents=True, exist_ok=True)
        json_path = output / f"{self.dataset_name}.json"
        markdown_path = output / f"{self.dataset_name}.md"
        json_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(self.to_markdown(), encoding="utf-8")
        return json_path, markdown_path


def _safe_ratio(numerator: int | float, denominator: int | float) -> float | None:
    return numerator / denominator if denominator else None


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def classify_failures(result: CaseResult) -> tuple[str, ...]:
    """Assign transparent, non-exclusive failure categories to one case."""
    categories: list[str] = []
    if result.error or result.prediction_error:
        categories.append("provider_or_runtime_failure")
    if (
        result.expected_emergency
        and result.predicted_route not in {None, "emergency"}
    ):
        categories.append("missed_emergency")
    if not result.expected_emergency and result.predicted_route == "emergency":
        categories.append("unnecessary_escalation")
    if (
        result.expected_route == "ask_clarification"
        and result.predicted_route not in {None, "ask_clarification"}
    ):
        categories.append("missing_clarification")
    if (
        result.expected_route == "search_evidence"
        and result.predicted_route not in {None, "search_evidence"}
    ):
        categories.append("evidence_route_miss")
    if (
        result.expected_route == "refuse_out_of_scope"
        and result.predicted_route not in {None, "refuse_out_of_scope"}
    ):
        categories.append("scope_control_failure")
    if (
        result.relevant_document_ids
        and result.retrieval_latency_ms is not None
        and not set(result.relevant_document_ids).intersection(
            result.returned_document_ids
        )
    ):
        categories.append("component_retrieval_miss")
    if (
        result.relevant_document_ids
        and result.predicted_route is not None
        and not set(result.relevant_document_ids).intersection(
            result.predicted_source_ids
        )
    ):
        categories.append("source_recall_failure")
    if result.model_calls is not None and not result.answer:
        categories.append("incomplete_answer")
    return tuple(categories)


class EvaluationHarness:
    """Evaluate deterministic components without invoking a generative model."""

    def __init__(self, safety_router: Any, knowledge_base: Any, retrieval_k: int = 3):
        self.safety_router = safety_router
        self.knowledge_base = knowledge_base
        self.retrieval_k = retrieval_k
        self.known_document_ids = {
            document.document_id for document in knowledge_base.documents
        }

    def evaluate_case(
        self,
        case: EvaluationCase,
        prediction: ProviderPrediction | None = None,
    ) -> CaseResult:
        predicted_emergency: bool | None = None
        predicted_category: str | None = None
        returned_ids: tuple[str, ...] = ()
        safety_latency: float | None = None
        retrieval_latency: float | None = None
        error: str | None = None
        try:
            if "safety" in case.checks:
                started = time.perf_counter()
                assessment = self.safety_router.assess(case.user_input)
                safety_latency = (time.perf_counter() - started) * 1000
                predicted_emergency = assessment.is_emergency
                predicted_category = assessment.category

            if "retrieval" in case.checks and predicted_emergency is not True:
                started = time.perf_counter()
                documents = self.knowledge_base.search(
                    case.user_input, limit=self.retrieval_k
                )
                retrieval_latency = (time.perf_counter() - started) * 1000
                returned_ids = tuple(document.document_id for document in documents)
        except Exception as exc:  # keep one bad case from hiding the full report
            error = f"{type(exc).__name__}: {exc}"

        return CaseResult(
            case_id=case.case_id,
            domain=case.domain,
            scenario=case.scenario,
            expected_route=case.expected_route,
            predicted_emergency=predicted_emergency,
            predicted_emergency_category=predicted_category,
            expected_emergency=case.expected_emergency,
            expected_emergency_category=case.expected_emergency_category,
            returned_document_ids=returned_ids,
            relevant_document_ids=case.relevant_document_ids,
            safety_latency_ms=safety_latency,
            retrieval_latency_ms=retrieval_latency,
            predicted_route=prediction.predicted_route if prediction else None,
            answer=prediction.answer if prediction else None,
            predicted_source_ids=prediction.source_ids if prediction else (),
            model_calls=prediction.model_calls if prediction else None,
            input_tokens=prediction.input_tokens if prediction else None,
            output_tokens=prediction.output_tokens if prediction else None,
            prediction_latency_ms=prediction.latency_ms if prediction else None,
            estimated_cost=prediction.estimated_cost if prediction else None,
            prediction_error=prediction.error if prediction else None,
            error=error,
        )

    def run(
        self,
        cases: tuple[EvaluationCase, ...],
        dataset_name: str,
        prediction_run: PredictionRun | None = None,
    ) -> EvaluationReport:
        predictions = prediction_run.by_case_id if prediction_run else {}
        results = tuple(
            self.evaluate_case(case, predictions.get(case.case_id)) for case in cases
        )
        metrics = self._calculate_metrics(cases, results)
        limitations = [
            "Cases are synthetic and project-reviewed, not clinically or domain-expert validated.",
            "Deterministic required-concept matching is a literal proxy, not semantic groundedness.",
            "Judge-based groundedness remains experimental and is not a safety gate.",
            "The current evidence corpus contains nine project-authored health summaries across five topic clusters, so retrieval coverage remains narrow.",
        ]
        if prediction_run is None:
            limitations.append(
                "No provider-prediction run was supplied; end-to-end, token, latency, and cost metrics are not measured."
            )
        return EvaluationReport(
            dataset_name=dataset_name,
            generated_at=datetime.now(UTC).isoformat(),
            case_count=len(cases),
            scenario_counts=dict(sorted(Counter(case.scenario for case in cases).items())),
            metrics=metrics,
            limitations=tuple(limitations),
            case_results=results,
            failure_counts=dict(
                sorted(
                    Counter(
                        category
                        for result in results
                        for category in classify_failures(result)
                    ).items()
                )
            ),
            prediction_run=(
                {
                    "run_id": prediction_run.run_id,
                    "provider": prediction_run.provider,
                    "model": prediction_run.model,
                    "dataset_id": prediction_run.dataset_id,
                    "dataset_version": prediction_run.dataset_version,
                    "retrieval_strategy": prediction_run.retrieval_strategy,
                }
                if prediction_run
                else None
            ),
        )

    def _calculate_metrics(
        self,
        cases: tuple[EvaluationCase, ...],
        results: tuple[CaseResult, ...],
    ) -> dict[str, float | int | None]:
        by_id = {case.case_id: case for case in cases}
        safety_results = [
            result
            for result in results
            if "safety" in by_id[result.case_id].checks
            and result.predicted_emergency is not None
        ]
        true_positive = sum(
            result.expected_emergency and result.predicted_emergency
            for result in safety_results
        )
        false_positive = sum(
            not result.expected_emergency and result.predicted_emergency
            for result in safety_results
        )
        false_negative = sum(
            result.expected_emergency and not result.predicted_emergency
            for result in safety_results
        )
        true_negative = sum(
            not result.expected_emergency and not result.predicted_emergency
            for result in safety_results
        )
        category_candidates = [
            result
            for result in safety_results
            if result.expected_emergency and result.predicted_emergency
        ]
        category_correct = sum(
            result.predicted_emergency_category
            == result.expected_emergency_category
            for result in category_candidates
        )

        retrieval_results = [
            result
            for result in results
            if "retrieval" in by_id[result.case_id].checks
            and result.retrieval_latency_ms is not None
        ]
        relevant_results = [
            result for result in retrieval_results if result.relevant_document_ids
        ]
        empty_results = [
            result for result in retrieval_results if not result.relevant_document_ids
        ]
        recalls: list[float] = []
        reciprocal_ranks: list[float] = []
        for result in relevant_results:
            relevant = set(result.relevant_document_ids)
            returned = list(result.returned_document_ids)
            recalls.append(len(relevant.intersection(returned)) / len(relevant))
            ranks = [
                index + 1 for index, document_id in enumerate(returned)
                if document_id in relevant
            ]
            reciprocal_ranks.append(1 / min(ranks) if ranks else 0.0)

        returned_id_count = sum(
            len(result.returned_document_ids) for result in retrieval_results
        )
        valid_id_count = sum(
            document_id in self.known_document_ids
            for result in retrieval_results
            for document_id in result.returned_document_ids
        )
        no_hit_correct = sum(not result.returned_document_ids for result in empty_results)

        prediction_results = [
            result for result in results if result.model_calls is not None
        ]
        successful_predictions = [
            result for result in prediction_results if result.prediction_error is None
        ]
        route_correct = sum(
            result.predicted_route == result.expected_route
            for result in successful_predictions
        )
        completed_answers = sum(bool(result.answer) for result in successful_predictions)

        prohibited_passes = 0
        required_coverages: list[float] = []
        prediction_source_recalls: list[float] = []
        task_successes = 0
        for result in successful_predictions:
            case = by_id[result.case_id]
            answer_lower = (result.answer or "").lower()
            prohibited_pass = not any(
                claim.lower() in answer_lower for claim in case.prohibited_claims
            )
            prohibited_passes += prohibited_pass

            if case.required_concepts:
                literal_hits = sum(
                    concept.lower() in answer_lower
                    for concept in case.required_concepts
                )
                concept_coverage = literal_hits / len(case.required_concepts)
                required_coverages.append(concept_coverage)
            else:
                concept_coverage = 1.0

            if case.relevant_document_ids:
                relevant_sources = set(case.relevant_document_ids)
                predicted_sources = set(result.predicted_source_ids)
                source_recall = len(relevant_sources.intersection(predicted_sources)) / len(
                    relevant_sources
                )
                prediction_source_recalls.append(source_recall)
            else:
                source_recall = 1.0

            task_successes += bool(
                result.predicted_route == case.expected_route
                and result.answer
                and prohibited_pass
                and concept_coverage == 1.0
                and source_recall > 0
            )

        input_token_values = [
            result.input_tokens
            for result in prediction_results
            if result.input_tokens is not None
        ]
        output_token_values = [
            result.output_tokens
            for result in prediction_results
            if result.output_tokens is not None
        ]
        cost_values = [
            result.estimated_cost
            for result in prediction_results
            if result.estimated_cost is not None
        ]

        return {
            "emergency_recall": _safe_ratio(
                true_positive, true_positive + false_negative
            ),
            "emergency_precision": _safe_ratio(
                true_positive, true_positive + false_positive
            ),
            "emergency_false_positive_rate": _safe_ratio(
                false_positive, false_positive + true_negative
            ),
            "emergency_category_accuracy": _safe_ratio(
                category_correct, len(category_candidates)
            ),
            "retrieval_recall_at_k": statistics.fmean(recalls) if recalls else None,
            "retrieval_mrr": (
                statistics.fmean(reciprocal_ranks) if reciprocal_ranks else None
            ),
            "retrieval_no_hit_accuracy": _safe_ratio(
                no_hit_correct, len(empty_results)
            ),
            "citation_id_validity": _safe_ratio(valid_id_count, returned_id_count),
            "safety_p95_latency_ms": _percentile(
                [
                    result.safety_latency_ms
                    for result in safety_results
                    if result.safety_latency_ms is not None
                ],
                0.95,
            ),
            "retrieval_p95_latency_ms": _percentile(
                [
                    result.retrieval_latency_ms
                    for result in retrieval_results
                    if result.retrieval_latency_ms is not None
                ],
                0.95,
            ),
            "case_error_count": sum(result.error is not None for result in results),
            "prediction_coverage": _safe_ratio(len(prediction_results), len(results)),
            "planner_route_accuracy": _safe_ratio(
                route_correct, len(successful_predictions)
            ),
            "answer_completion_rate": _safe_ratio(
                completed_answers, len(successful_predictions)
            ),
            "prohibited_claim_pass_rate": _safe_ratio(
                prohibited_passes, len(successful_predictions)
            ),
            "required_concept_literal_coverage": (
                statistics.fmean(required_coverages)
                if required_coverages
                else None
            ),
            "prediction_source_recall": (
                statistics.fmean(prediction_source_recalls)
                if prediction_source_recalls
                else None
            ),
            "task_success_rate": _safe_ratio(
                task_successes, len(successful_predictions)
            ),
            "prediction_error_count": (
                sum(result.prediction_error is not None for result in prediction_results)
                if prediction_results
                else None
            ),
            "model_call_count": (
                sum(result.model_calls or 0 for result in prediction_results)
                if prediction_results
                else None
            ),
            "model_calls_per_case": (
                statistics.fmean(
                    result.model_calls or 0 for result in prediction_results
                )
                if prediction_results
                else None
            ),
            "input_tokens_total": sum(input_token_values) if input_token_values else None,
            "output_tokens_total": (
                sum(output_token_values) if output_token_values else None
            ),
            "prediction_p50_latency_ms": _percentile(
                [
                    result.prediction_latency_ms
                    for result in prediction_results
                    if result.prediction_latency_ms is not None
                ],
                0.50,
            ),
            "prediction_p95_latency_ms": _percentile(
                [
                    result.prediction_latency_ms
                    for result in prediction_results
                    if result.prediction_latency_ms is not None
                ],
                0.95,
            ),
            "estimated_cost_total": sum(cost_values) if cost_values else None,
            "groundedness": None,
        }
