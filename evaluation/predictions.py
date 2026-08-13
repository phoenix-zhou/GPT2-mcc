"""Provider-neutral prediction records for end-to-end agent evaluation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import ALLOWED_ROUTES


class EvaluationPredictionError(ValueError):
    """Raised when captured provider output violates the evaluation contract."""


@dataclass(frozen=True)
class ProviderPrediction:
    """One privacy-safe captured output, keyed to a versioned evaluation case."""

    case_id: str
    predicted_route: str | None
    answer: str
    source_ids: tuple[str, ...]
    model_calls: int
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: float | None
    estimated_cost: float | None
    error: str | None


@dataclass(frozen=True)
class PredictionRun:
    """Captured outputs plus provider/run provenance from the sidecar manifest."""

    run_id: str
    provider: str
    model: str
    dataset_id: str
    dataset_version: str
    predictions: tuple[ProviderPrediction, ...]

    @property
    def by_case_id(self) -> dict[str, ProviderPrediction]:
        return {prediction.case_id: prediction for prediction in self.predictions}


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationPredictionError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_non_negative_number(
    payload: dict[str, Any], key: str
) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise EvaluationPredictionError(f"{key} must be a non-negative number or null")
    return float(value)


def _optional_non_negative_integer(
    payload: dict[str, Any], key: str
) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvaluationPredictionError(f"{key} must be a non-negative integer or null")
    return value


def parse_prediction(payload: dict[str, Any]) -> ProviderPrediction:
    """Validate one captured output without accepting copied prompt text."""
    forbidden_fields = {"user_input", "conversation", "prompt"}.intersection(payload)
    if forbidden_fields:
        raise EvaluationPredictionError(
            "prediction records must not duplicate raw inputs: "
            + ", ".join(sorted(forbidden_fields))
        )

    answer = payload.get("answer", "")
    if not isinstance(answer, str):
        raise EvaluationPredictionError("answer must be a string")
    source_ids = payload.get("source_ids", [])
    if not isinstance(source_ids, list) or not all(
        isinstance(value, str) and value.strip() for value in source_ids
    ):
        raise EvaluationPredictionError("source_ids must be a list of strings")
    model_calls = _optional_non_negative_integer(payload, "model_calls")
    if model_calls is None:
        raise EvaluationPredictionError("model_calls is required")
    error = payload.get("error")
    if error is not None and (not isinstance(error, str) or not error.strip()):
        raise EvaluationPredictionError("error must be a non-empty string or null")
    route = payload.get("predicted_route")
    if route is None:
        if error is None:
            raise EvaluationPredictionError(
                "predicted_route is required when error is null"
            )
    elif not isinstance(route, str) or route not in ALLOWED_ROUTES:
        raise EvaluationPredictionError(f"unsupported predicted_route: {route}")

    return ProviderPrediction(
        case_id=_required_text(payload, "case_id"),
        predicted_route=route,
        answer=answer.strip(),
        source_ids=tuple(dict.fromkeys(value.strip() for value in source_ids)),
        model_calls=model_calls,
        input_tokens=_optional_non_negative_integer(payload, "input_tokens"),
        output_tokens=_optional_non_negative_integer(payload, "output_tokens"),
        latency_ms=_optional_non_negative_number(payload, "latency_ms"),
        estimated_cost=_optional_non_negative_number(payload, "estimated_cost"),
        error=error.strip() if error else None,
    )


def load_prediction_run(
    path: str | Path,
    *,
    expected_case_ids: set[str] | None = None,
) -> PredictionRun:
    """Load resumable JSONL predictions and validate their run manifest."""
    source = Path(path)
    predictions: list[ProviderPrediction] = []
    for line_number, line in enumerate(
        source.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise EvaluationPredictionError("record must be an object")
            predictions.append(parse_prediction(payload))
        except (json.JSONDecodeError, EvaluationPredictionError) as exc:
            raise EvaluationPredictionError(f"{source}:{line_number}: {exc}") from exc

    if not predictions:
        raise EvaluationPredictionError(f"prediction file is empty: {source}")
    case_ids = [prediction.case_id for prediction in predictions]
    duplicates = sorted(case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1)
    if duplicates:
        raise EvaluationPredictionError(
            f"duplicate prediction case_id values: {', '.join(duplicates)}"
        )
    if expected_case_ids is not None:
        unknown = sorted(set(case_ids) - expected_case_ids)
        if unknown:
            raise EvaluationPredictionError(
                f"predictions reference unknown case IDs: {', '.join(unknown)}"
            )

    manifest_path = source.with_suffix(".meta.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationPredictionError(
            f"invalid or missing prediction manifest: {manifest_path}"
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise EvaluationPredictionError("unsupported prediction schema_version")
    if manifest.get("prediction_count") != len(predictions):
        raise EvaluationPredictionError(
            "manifest prediction_count does not match loaded predictions"
        )
    if manifest.get("contains_personal_data") is not False:
        raise EvaluationPredictionError(
            "prediction manifest must declare contains_personal_data=false"
        )

    return PredictionRun(
        run_id=_required_text(manifest, "run_id"),
        provider=_required_text(manifest, "provider"),
        model=_required_text(manifest, "model"),
        dataset_id=_required_text(manifest, "dataset_id"),
        dataset_version=_required_text(manifest, "dataset_version"),
        predictions=tuple(predictions),
    )
