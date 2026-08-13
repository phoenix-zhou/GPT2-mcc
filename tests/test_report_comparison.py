import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _report(path: Path, strategy: str, success: float) -> None:
    path.write_text(
        json.dumps(
            {
                "dataset_name": "frozen-v1",
                "prediction_run": {"retrieval_strategy": strategy},
                "metrics": {
                    "task_success_rate": success,
                    "emergency_recall": 1.0,
                },
            }
        ),
        encoding="utf-8",
    )


def test_comparison_cli_reports_metric_delta_and_constraints(tmp_path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    output = tmp_path / "comparison"
    _report(baseline, "keyword", 0.7)
    _report(candidate, "bm25", 0.8)

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "compare_evaluation_reports.py"),
            str(baseline),
            str(candidate),
            "--output-dir",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads((output / "end_to_end_comparison.json").read_text())
    success = next(
        row for row in payload["metrics"] if row["metric"] == "task_success_rate"
    )
    markdown = (output / "end_to_end_comparison.md").read_text()
    assert success["delta"] == 0.1
    assert "provider generations were captured in separate runs" in payload["decision_reason"]
    assert "not a causal estimate" in markdown
