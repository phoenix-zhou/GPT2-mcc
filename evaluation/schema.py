"""Versioned, domain-aware evaluation dataset schema."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class EvaluationDatasetError(ValueError):
    """Raised when an evaluation record is incomplete or unsafe to use."""


ALLOWED_CHECKS = {"safety", "retrieval"}
ALLOWED_REVIEW_STATUS = {"project_reviewed", "expert_reviewed", "unreviewed"}
ALLOWED_ROUTES = {
    "emergency",
    "search_evidence",
    "ask_clarification",
    "respond_without_tool",
    "refuse_out_of_scope",
}


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    domain: str
    scenario: str
    user_input: str
    checks: tuple[str, ...]
    expected_route: str
    expected_emergency: bool
    expected_emergency_category: str | None
    relevant_document_ids: tuple[str, ...]
    required_concepts: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    tags: tuple[str, ...]
    authoring_method: str
    reviewer_status: str
    contains_personal_data: bool


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationDatasetError(f"{key} must be a non-empty string")
    return value.strip()


def parse_case(payload: dict[str, Any]) -> EvaluationCase:
    """Validate and normalize one human-reviewable evaluation record."""
    expected = payload.get("expected")
    provenance = payload.get("provenance")
    if not isinstance(expected, dict) or not isinstance(provenance, dict):
        raise EvaluationDatasetError("expected and provenance must be objects")

    checks = payload.get("checks")
    if (
        not isinstance(checks, list)
        or not checks
        or any(check not in ALLOWED_CHECKS for check in checks)
    ):
        raise EvaluationDatasetError(
            f"checks must be a non-empty subset of {sorted(ALLOWED_CHECKS)}"
        )

    route = _require_text(expected, "route")
    if route not in ALLOWED_ROUTES:
        raise EvaluationDatasetError(f"unsupported expected route: {route}")
    emergency = expected.get("emergency")
    if not isinstance(emergency, bool):
        raise EvaluationDatasetError("expected.emergency must be boolean")
    category = expected.get("emergency_category")
    if category is not None and not isinstance(category, str):
        raise EvaluationDatasetError(
            "expected.emergency_category must be a string or null"
        )
    if emergency and not category:
        raise EvaluationDatasetError(
            "emergency cases require expected.emergency_category"
        )
    if not emergency and category is not None:
        raise EvaluationDatasetError(
            "non-emergency cases cannot declare an emergency category"
        )

    relevant_ids = expected.get("relevant_document_ids", [])
    required_concepts = expected.get("required_concepts", [])
    prohibited_claims = expected.get("prohibited_claims", [])
    tags = payload.get("tags", [])
    for field_name, values in (
        ("relevant_document_ids", relevant_ids),
        ("required_concepts", required_concepts),
        ("prohibited_claims", prohibited_claims),
    ):
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise EvaluationDatasetError(
                f"expected.{field_name} must be a list of strings"
            )
    if not isinstance(tags, list) or not all(
        isinstance(value, str) and value for value in tags
    ):
        raise EvaluationDatasetError("tags must be a list of strings")

    reviewer_status = _require_text(provenance, "reviewer_status")
    if reviewer_status not in ALLOWED_REVIEW_STATUS:
        raise EvaluationDatasetError(
            f"unsupported reviewer_status: {reviewer_status}"
        )
    contains_personal_data = provenance.get("contains_personal_data")
    if contains_personal_data is not False:
        raise EvaluationDatasetError(
            "MVP cases must explicitly set contains_personal_data to false"
        )

    return EvaluationCase(
        case_id=_require_text(payload, "case_id"),
        domain=_require_text(payload, "domain"),
        scenario=_require_text(payload, "scenario"),
        user_input=_require_text(payload, "user_input"),
        checks=tuple(dict.fromkeys(checks)),
        expected_route=route,
        expected_emergency=emergency,
        expected_emergency_category=category,
        relevant_document_ids=tuple(dict.fromkeys(relevant_ids)),
        required_concepts=tuple(dict.fromkeys(required_concepts)),
        prohibited_claims=tuple(dict.fromkeys(prohibited_claims)),
        tags=tuple(dict.fromkeys(tags)),
        authoring_method=_require_text(provenance, "authoring_method"),
        reviewer_status=reviewer_status,
        contains_personal_data=contains_personal_data,
    )


def load_dataset(path: str | Path) -> tuple[EvaluationCase, ...]:
    """Load JSONL cases, rejecting duplicate IDs and malformed records."""
    source = Path(path)
    cases: list[EvaluationCase] = []
    for line_number, line in enumerate(
        source.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise EvaluationDatasetError("record must be an object")
            cases.append(parse_case(payload))
        except (json.JSONDecodeError, EvaluationDatasetError) as exc:
            raise EvaluationDatasetError(
                f"{source}:{line_number}: {exc}"
            ) from exc

    if not cases:
        raise EvaluationDatasetError(f"dataset is empty: {source}")
    case_ids = [case.case_id for case in cases]
    duplicates = sorted(
        case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1
    )
    if duplicates:
        raise EvaluationDatasetError(
            f"duplicate case_id values: {', '.join(duplicates)}"
        )
    return tuple(cases)


def validate_dataset_manifest(
    dataset_path: str | Path, cases: tuple[EvaluationCase, ...]
) -> dict[str, Any]:
    """Validate the version and declared scope in a dataset sidecar manifest."""
    source = Path(dataset_path)
    manifest_path = source.with_suffix(".meta.json")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationDatasetError(
            f"invalid or missing dataset manifest: {manifest_path}"
        ) from exc
    if not isinstance(payload, dict):
        raise EvaluationDatasetError("dataset manifest must be an object")
    if payload.get("schema_version") != 1:
        raise EvaluationDatasetError("unsupported evaluation schema_version")
    if not isinstance(payload.get("dataset_version"), str):
        raise EvaluationDatasetError("dataset_version must be a string")
    if payload.get("case_count") != len(cases):
        raise EvaluationDatasetError(
            "manifest case_count does not match loaded evaluation cases"
        )
    if payload.get("contains_personal_data") is not False:
        raise EvaluationDatasetError(
            "dataset manifest must declare contains_personal_data=false"
        )
    return payload
