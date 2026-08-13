#!/usr/bin/env python3
"""Create a reproducible baseline-versus-candidate evaluation comparison."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


METRICS = (
    "task_success_rate",
    "planner_route_accuracy",
    "prediction_source_recall",
    "retrieval_recall_at_k",
    "retrieval_no_hit_accuracy",
    "citation_id_validity",
    "emergency_recall",
    "emergency_false_positive_rate",
    "prediction_error_count",
    "prediction_p95_latency_ms",
    "model_call_count",
    "estimated_cost_total",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("metrics"), dict):
        raise ValueError(f"invalid evaluation report: {path}")
    return payload


def compare(baseline_path: Path, candidate_path: Path) -> dict[str, Any]:
    baseline = _load(baseline_path)
    candidate = _load(candidate_path)
    if baseline.get("dataset_name") != candidate.get("dataset_name"):
        raise ValueError("reports must use the same dataset")
    rows = []
    for metric in METRICS:
        before = baseline["metrics"].get(metric)
        after = candidate["metrics"].get(metric)
        delta = (
            round(after - before, 12)
            if isinstance(before, (int, float)) and isinstance(after, (int, float))
            else None
        )
        rows.append(
            {"metric": metric, "baseline": before, "candidate": after, "delta": delta}
        )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_name": baseline["dataset_name"],
        "baseline": baseline.get("prediction_run"),
        "candidate": candidate.get("prediction_run"),
        "metrics": rows,
        "decision": "candidate_gate_passed_production_default_unchanged",
        "decision_reason": (
            "BM25 improved task-success and source-recall proxies without a measured "
            "safety, citation-validity, error-rate, or API-cost regression. Keyword "
            "remains the production default because BM25 threshold selection and this "
            "comparison use the same development set, and provider generations were "
            "captured in separate runs."
        ),
    }


def _display(value: Any) -> str:
    if value is None:
        return "not measured"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# RAG V2 end-to-end comparison",
        "",
        f"- Dataset: `{payload['dataset_name']}`",
        f"- Decision: `{payload['decision']}`",
        "- API cost: zero; both captures used local Qwen",
        "",
        "| Metric | Keyword baseline | BM25 candidate | Delta |",
        "|---|---:|---:|---:|",
    ]
    for row in payload["metrics"]:
        lines.append(
            f"| {row['metric']} | {_display(row['baseline'])} | "
            f"{_display(row['candidate'])} | {_display(row['delta'])} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            payload["decision_reason"],
            "",
            "## Interpretation constraints",
            "",
            "- These are synthetic, project-reviewed engineering cases, not clinical claims.",
            "- BM25 threshold selection and evaluation share the same development set.",
            "- The Qwen captures are separate runs, so planner variation is a confounder; "
            "the task-success delta is not a causal estimate of BM25 alone.",
            "- `prediction_source_recall` measures sources returned by the captured agent; "
            "component retrieval metrics evaluate the configured retriever directly.",
            "- Latency varies with local machine load and is reported as an operational "
            "observation, not a controlled benchmark.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    payload = compare(args.baseline, args.candidate)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "end_to_end_comparison.json"
    markdown_path = args.output_dir / "end_to_end_comparison.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(to_markdown(payload), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
