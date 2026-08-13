#!/usr/bin/env python3
"""Capture resumable provider predictions for a frozen evaluation dataset."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chat_models import create_chat_model
from evaluation import load_dataset, validate_dataset_manifest
from evaluation.capture import (
    InstrumentedModel,
    append_prediction,
    capture_case,
    load_partial_predictions,
    write_prediction_manifest,
)
from evaluation.predictions import load_prediction_run
from knowledge import LocalKnowledgeBase
from safety import EmergencyRiskRouter
from settings import get_setting


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture independent, resumable provider predictions."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "evaluation" / "datasets" / "health_mvp_v1.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "evaluation"
        / "predictions"
        / "qwen-local-health-mvp-v1.jsonl",
    )
    parser.add_argument("--provider", default="qwen-local")
    parser.add_argument(
        "--model",
        help="Runtime model name or local path; defaults depend on the provider.",
    )
    parser.add_argument(
        "--model-label",
        help="Portable model identifier for the manifest when --model is a local path.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        help="Capture only a selected case ID; may be repeated.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Capture at most this many still-pending cases.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    if args.provider in {"qwen", "qwen-local"}:
        model_runtime = args.model or get_setting(
            "QWEN_MODEL", "mlx-community/Qwen3-4B-Instruct-2507-4bit"
        )
        cost_basis = "local inference; API cost recorded as 0.0"
        estimated_cost = 0.0
    elif args.provider == "openai":
        model_runtime = args.model or get_setting("OPENAI_MODEL", "gpt-5.6-luna")
        cost_basis = "not reported by capture adapter"
        estimated_cost = None
    else:
        model_runtime = args.model or args.provider
        cost_basis = "not reported by capture adapter"
        estimated_cost = None

    cases = load_dataset(args.dataset)
    dataset_manifest = validate_dataset_manifest(args.dataset, cases)
    by_id = {case.case_id: case for case in cases}
    requested_ids = set(args.case_id or by_id)
    unknown = sorted(requested_ids - by_id.keys())
    if unknown:
        raise SystemExit(f"unknown --case-id values: {', '.join(unknown)}")

    existing = load_partial_predictions(args.output)
    existing_ids = {prediction.case_id for prediction in existing}
    pending = [
        case for case in cases
        if case.case_id in requested_ids and case.case_id not in existing_ids
    ]
    if args.limit is not None:
        pending = pending[: args.limit]

    run_id = f"{args.provider}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    model_label = args.model_label or model_runtime
    manifest_path = args.output.with_suffix(".meta.json")
    if manifest_path.exists():
        import json

        run_id = json.loads(manifest_path.read_text(encoding="utf-8"))["run_id"]
    write_prediction_manifest(
        args.output,
        run_id=run_id,
        provider=args.provider,
        model_name=model_label,
        dataset_manifest=dataset_manifest,
        prediction_count=len(existing),
        cost_basis=cost_basis,
    )

    if not pending:
        print(f"No pending cases. Captured predictions: {len(existing)}")
        return 0

    print(
        f"Loading {args.provider}/{model_runtime} for {len(pending)} pending cases..."
    )
    if args.provider in {"qwen", "qwen-local"}:
        os.environ["GOVERNED_AGENT_QWEN_MODEL"] = model_runtime
    elif args.provider == "openai":
        os.environ["GOVERNED_AGENT_OPENAI_MODEL"] = model_runtime
    instrumented = InstrumentedModel(create_chat_model(args.provider))
    router = EmergencyRiskRouter()
    knowledge_base = LocalKnowledgeBase()
    completed = len(existing)
    for index, case in enumerate(pending, start=1):
        prediction = capture_case(
            case,
            model=instrumented,
            safety_router=router,
            knowledge_base=knowledge_base,
            estimated_cost=estimated_cost,
        )
        append_prediction(args.output, prediction)
        completed += 1
        write_prediction_manifest(
            args.output,
            run_id=run_id,
            provider=args.provider,
            model_name=model_label,
            dataset_manifest=dataset_manifest,
            prediction_count=completed,
            cost_basis=cost_basis,
        )
        state = "error" if prediction.error else prediction.predicted_route
        print(
            f"[{index}/{len(pending)}] {case.case_id}: {state}; "
            f"calls={prediction.model_calls}; latency={prediction.latency_ms:.0f} ms",
            flush=True,
        )

    run = load_prediction_run(
        args.output,
        expected_case_ids=set(by_id),
    )
    print(f"Captured predictions: {len(run.predictions)}")
    print(f"JSONL: {args.output}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
