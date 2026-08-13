import json
import subprocess
import sys
from pathlib import Path

import pytest

from evaluation import (
    EvaluationDatasetError,
    EvaluationHarness,
    EvaluationPredictionError,
    load_dataset,
    load_prediction_run,
    review_labels,
    validate_dataset_manifest,
)
from evaluation.schema import parse_case
from evaluation.capture import (
    InstrumentedModel,
    append_prediction,
    capture_case,
    load_partial_predictions,
    write_prediction_manifest,
)
from knowledge import KnowledgeDocument
from safety import SafetyAssessment


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROJECT_ROOT / "evaluation" / "datasets" / "health_mvp_v1.jsonl"


def valid_payload(**overrides):
    payload = {
        "case_id": "case-001",
        "domain": "test-domain",
        "scenario": "retrieval",
        "user_input": "find the governed record",
        "checks": ["safety", "retrieval"],
        "expected": {
            "route": "search_evidence",
            "emergency": False,
            "relevant_document_ids": ["doc-1"],
        },
        "tags": ["smoke"],
        "provenance": {
            "authoring_method": "synthetic",
            "reviewer_status": "project_reviewed",
            "contains_personal_data": False,
        },
    }
    payload.update(overrides)
    return payload


def test_health_mvp_dataset_is_versioned_privacy_safe_and_has_80_cases():
    cases = load_dataset(DATASET)
    manifest = validate_dataset_manifest(DATASET, cases)

    assert len(cases) == 80
    assert len({case.case_id for case in cases}) == 80
    assert all(not case.contains_personal_data for case in cases)
    assert manifest["dataset_version"] == "1.0.0"
    assert manifest["expert_reviewed"] is False
    assert {case.scenario for case in cases} == {
        "emergency",
        "routine_health",
        "insufficient_context",
        "out_of_scope",
        "adversarial",
        "retrieval_citation",
    }


def test_dataset_rejects_records_marked_as_containing_personal_data():
    payload = valid_payload()
    payload["provenance"]["contains_personal_data"] = True

    with pytest.raises(EvaluationDatasetError, match="personal_data"):
        parse_case(payload)


def test_dataset_loader_reports_duplicate_case_ids(tmp_path):
    dataset = tmp_path / "duplicate.jsonl"
    line = json.dumps(valid_payload())
    dataset.write_text(f"{line}\n{line}\n", encoding="utf-8")

    with pytest.raises(EvaluationDatasetError, match="duplicate case_id"):
        load_dataset(dataset)


def test_harness_calculates_safety_and_retrieval_metrics():
    class Router:
        def assess(self, text):
            return SafetyAssessment(text == "urgent", "test" if text == "urgent" else None)

    document = KnowledgeDocument(
        document_id="doc-1",
        title="Test",
        content="Content",
        source_url="https://example.test",
        keywords=("find",),
    )

    class KnowledgeBase:
        documents = (document,)

        def search(self, query, limit=3):
            return [document] if "find" in query else []

    emergency = valid_payload(
        case_id="urgent",
        user_input="urgent",
        checks=["safety"],
        expected={
            "route": "emergency",
            "emergency": True,
            "emergency_category": "test",
            "relevant_document_ids": [],
        },
    )
    retrieval = valid_payload(case_id="retrieval")
    cases = (parse_case(emergency), parse_case(retrieval))

    report = EvaluationHarness(Router(), KnowledgeBase()).run(cases, "test")

    assert report.metrics["emergency_recall"] == 1.0
    assert report.metrics["retrieval_recall_at_k"] == 1.0
    assert report.metrics["retrieval_mrr"] == 1.0
    assert report.metrics["citation_id_validity"] == 1.0
    assert report.metrics["planner_route_accuracy"] is None
    assert "not measured" in report.to_markdown()


def write_prediction_run(tmp_path, records, **manifest_overrides):
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "run_id": "test-run",
        "provider": "fake",
        "model": "fake-model",
        "dataset_id": "test-dataset",
        "dataset_version": "1.0.0",
        "prediction_count": len(records),
        "contains_personal_data": False,
    }
    manifest.update(manifest_overrides)
    predictions.with_suffix(".meta.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return predictions


def test_prediction_contract_rejects_copied_raw_input(tmp_path):
    path = write_prediction_run(
        tmp_path,
        [
            {
                "case_id": "case-001",
                "predicted_route": "search_evidence",
                "answer": "answer",
                "source_ids": [],
                "model_calls": 2,
                "user_input": "must not be copied",
            }
        ],
    )

    with pytest.raises(EvaluationPredictionError, match="raw inputs"):
        load_prediction_run(path)


def test_prediction_contract_preserves_provider_failures(tmp_path):
    path = write_prediction_run(
        tmp_path,
        [
            {
                "case_id": "case-001",
                "predicted_route": None,
                "answer": "",
                "source_ids": [],
                "model_calls": 1,
                "error": "provider timeout",
            }
        ],
    )

    run = load_prediction_run(path, expected_case_ids={"case-001"})

    assert run.predictions[0].predicted_route is None
    assert run.predictions[0].error == "provider timeout"


def test_harness_scores_provider_neutral_predictions(tmp_path):
    document = KnowledgeDocument(
        document_id="doc-1",
        title="Test",
        content="Content",
        source_url="https://example.test",
        keywords=("find",),
    )

    class Router:
        def assess(self, text):
            return SafetyAssessment(False, None)

    class KnowledgeBase:
        documents = (document,)

        def search(self, query, limit=3):
            return [document]

    case = parse_case(
        valid_payload(
            expected={
                "route": "search_evidence",
                "emergency": False,
                "relevant_document_ids": ["doc-1"],
                "required_concepts": ["governed"],
                "prohibited_claims": ["diagnosis"],
            }
        )
    )
    path = write_prediction_run(
        tmp_path,
        [
            {
                "case_id": case.case_id,
                "predicted_route": "search_evidence",
                "answer": "A governed answer",
                "source_ids": ["doc-1"],
                "model_calls": 2,
                "input_tokens": 100,
                "output_tokens": 20,
                "latency_ms": 250,
                "estimated_cost": 0.01,
                "error": None,
            }
        ],
    )
    prediction_run = load_prediction_run(path, expected_case_ids={case.case_id})

    report = EvaluationHarness(Router(), KnowledgeBase()).run(
        (case,), "test", prediction_run=prediction_run
    )

    assert report.metrics["prediction_coverage"] == 1.0
    assert report.metrics["planner_route_accuracy"] == 1.0
    assert report.metrics["prohibited_claim_pass_rate"] == 1.0
    assert report.metrics["required_concept_literal_coverage"] == 1.0
    assert report.metrics["prediction_source_recall"] == 1.0
    assert report.metrics["task_success_rate"] == 1.0
    assert report.metrics["model_call_count"] == 2
    assert report.metrics["estimated_cost_total"] == 0.01
    assert report.prediction_run["provider"] == "fake"
    assert report.failure_counts == {}
    markdown = report.to_markdown()
    assert "Provider route accuracy by scenario" in markdown
    assert "| retrieval | 1 | 1 | 1.0000 |" in markdown


def test_report_surfaces_route_mismatches_in_failure_taxonomy(tmp_path):
    class Router:
        def assess(self, text):
            return SafetyAssessment(False, None)

    class KnowledgeBase:
        documents = ()

        def search(self, query, limit=3):
            return []

    case = parse_case(
        valid_payload(
            scenario="out_of_scope",
            checks=["safety"],
            expected={
                "route": "refuse_out_of_scope",
                "emergency": False,
                "relevant_document_ids": [],
            },
        )
    )
    path = write_prediction_run(
        tmp_path,
        [
            {
                "case_id": case.case_id,
                "predicted_route": "respond_without_tool",
                "answer": "answered outside the boundary",
                "source_ids": [],
                "model_calls": 2,
                "error": None,
            }
        ],
    )
    report = EvaluationHarness(Router(), KnowledgeBase()).run(
        (case,),
        "test",
        prediction_run=load_prediction_run(path, expected_case_ids={case.case_id}),
    )

    assert report.failure_counts == {"scope_control_failure": 1}
    markdown = report.to_markdown()
    assert "expected route `refuse_out_of_scope`" in markdown
    assert "predicted route `respond_without_tool`" in markdown


def test_label_review_distinguishes_consistency_from_expert_validation():
    cases = load_dataset(DATASET)
    report = review_labels(cases)

    assert report.issue_count == 0
    assert report.human_review_pending_count == 80
    assert "not label truth" in report.to_markdown("health_mvp_v1")


def test_capture_case_uses_bounded_agent_and_counts_calls():
    outputs = iter(
        [
            '{"action":"search_evidence","query":"governed",'
            '"reason_code":"medical_evidence_needed"}',
            "A governed answer",
        ]
    )

    class Model:
        def generate(self, user_input):
            return next(outputs)

    document = KnowledgeDocument(
        document_id="doc-1",
        title="Test",
        content="Content",
        source_url="https://example.test",
        keywords=("governed",),
    )

    class Router:
        def assess(self, text):
            return SafetyAssessment(False, None)

    class KnowledgeBase:
        documents = (document,)

        def search(self, query, limit=3):
            return [document]

    prediction = capture_case(
        parse_case(valid_payload()),
        model=InstrumentedModel(Model()),
        safety_router=Router(),
        knowledge_base=KnowledgeBase(),
        estimated_cost=0.0,
    )

    assert prediction.predicted_route == "search_evidence"
    assert prediction.answer == "A governed answer"
    assert prediction.source_ids == ("doc-1",)
    assert prediction.model_calls == 2
    assert prediction.estimated_cost == 0.0


def test_prediction_capture_artifacts_are_resumable(tmp_path):
    prediction = {
        "case_id": "case-001",
        "predicted_route": "search_evidence",
        "answer": "answer",
        "source_ids": [],
        "model_calls": 2,
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": 1.0,
        "estimated_cost": 0.0,
        "error": None,
    }
    parsed = load_prediction_run(
        write_prediction_run(tmp_path, [prediction]),
        expected_case_ids={"case-001"},
    ).predictions[0]
    path = tmp_path / "nested" / "resumable.jsonl"
    append_prediction(path, parsed)
    partial = load_partial_predictions(path)
    write_prediction_manifest(
        path,
        run_id="run-1",
        provider="fake",
        model_name="fake-model",
        dataset_manifest={"dataset_id": "test", "dataset_version": "1.0.0"},
        prediction_count=len(partial),
    )

    assert partial == (parsed,)
    assert load_prediction_run(path).run_id == "run-1"


def test_evaluation_cli_writes_json_and_markdown_reports(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_evaluation.py"),
            "--dataset",
            str(DATASET),
            "--output-dir",
            str(tmp_path),
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads((tmp_path / "health_mvp_v1.json").read_text())
    markdown = (tmp_path / "health_mvp_v1.md").read_text()
    assert payload["case_count"] == 80
    assert "Evaluated 80 cases" in completed.stdout
    assert "deterministic component baseline" in markdown
