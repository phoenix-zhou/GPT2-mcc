"""Capture provider outputs through the same bounded path used by the demo."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent_runtime import GovernedEvidenceAgent
from chat_models import MEDICAL_SYSTEM_PROMPT
from safety import EMERGENCY_MESSAGE

from .predictions import ProviderPrediction, parse_prediction
from .schema import EvaluationCase


class InstrumentedModel:
    """Count calls and tokens without changing the provider interface."""

    def __init__(self, model: Any) -> None:
        self.model = model
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def reset(self) -> None:
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def _count_input(self, user_input: str) -> int | None:
        tokenizer = getattr(self.model, "tokenizer", None)
        if tokenizer is None:
            return None
        messages = [
            {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        return len(tokenizer.encode(prompt))

    def _count_output(self, answer: str) -> int | None:
        tokenizer = getattr(self.model, "tokenizer", None)
        return len(tokenizer.encode(answer)) if tokenizer is not None else None

    def generate(self, user_input: str) -> str:
        self.calls += 1
        input_count = self._count_input(user_input)
        if input_count is not None:
            self.input_tokens += input_count
        answer = self.model.generate(user_input)
        output_count = self._count_output(answer)
        if output_count is not None:
            self.output_tokens += output_count
        return answer


def capture_case(
    case: EvaluationCase,
    *,
    model: InstrumentedModel,
    safety_router: Any,
    knowledge_base: Any,
    estimated_cost: float | None = None,
) -> ProviderPrediction:
    """Capture one independent case, including deterministic emergency bypass."""
    model.reset()
    started = time.perf_counter()
    predicted_route: str | None = None
    answer = ""
    source_ids: tuple[str, ...] = ()
    error: str | None = None
    try:
        assessment = safety_router.assess(case.user_input)
        if assessment.is_emergency:
            predicted_route = "emergency"
            answer = EMERGENCY_MESSAGE
        else:
            result = GovernedEvidenceAgent(
                model_call=model.generate,
                knowledge_search=knowledge_base.search,
            ).run(case.user_input, case.user_input)
            predicted_route = result.trace[0].detail.split(" · ", maxsplit=1)[0]
            answer = result.answer
            source_ids = tuple(
                document.document_id for document in result.sources
            )
    except Exception as exc:  # preserve provider/runtime failures as data
        error = f"{type(exc).__name__}: {exc}"

    return ProviderPrediction(
        case_id=case.case_id,
        predicted_route=predicted_route,
        answer=answer,
        source_ids=source_ids,
        model_calls=model.calls,
        input_tokens=model.input_tokens if model.calls else 0,
        output_tokens=model.output_tokens if model.calls else 0,
        latency_ms=(time.perf_counter() - started) * 1000,
        estimated_cost=estimated_cost,
        error=error,
    )


def prediction_to_dict(prediction: ProviderPrediction) -> dict[str, Any]:
    payload = asdict(prediction)
    payload["source_ids"] = list(prediction.source_ids)
    return payload


def load_partial_predictions(path: Path) -> tuple[ProviderPrediction, ...]:
    """Load an interrupted JSONL file without requiring a synchronized manifest."""
    if not path.exists():
        return ()
    predictions: list[ProviderPrediction] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("record must be an object")
            predictions.append(parse_prediction(payload))
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
    case_ids = [prediction.case_id for prediction in predictions]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("partial prediction file contains duplicate case IDs")
    return tuple(predictions)


def write_prediction_manifest(
    prediction_path: Path,
    *,
    run_id: str,
    provider: str,
    model_name: str,
    dataset_manifest: dict[str, Any],
    prediction_count: int,
    retrieval_strategy: str = "keyword",
    cost_basis: str = "not reported by capture adapter",
) -> Path:
    """Atomically synchronize run metadata after each appended record."""
    manifest_path = prediction_path.with_suffix(".meta.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "provider": provider,
        "model": model_name,
        "dataset_id": dataset_manifest["dataset_id"],
        "dataset_version": dataset_manifest["dataset_version"],
        "prediction_count": prediction_count,
        "retrieval_strategy": retrieval_strategy,
        "contains_personal_data": False,
        "captured_at": datetime.now(UTC).isoformat(),
        "token_counting": "provider_tokenizer_chat_template",
        "cost_basis": cost_basis,
    }
    temporary = manifest_path.with_name(f"{manifest_path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, manifest_path)
    return manifest_path


def append_prediction(path: Path, prediction: ProviderPrediction) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(prediction_to_dict(prediction), ensure_ascii=False) + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())
