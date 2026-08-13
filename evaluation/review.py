"""Deterministic label-consistency review for evaluation datasets."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .schema import EvaluationCase


@dataclass(frozen=True)
class LabelReviewIssue:
    case_id: str
    code: str
    detail: str


@dataclass(frozen=True)
class LabelReviewReport:
    case_count: int
    reviewer_status_counts: dict[str, int]
    issue_count: int
    human_review_pending_count: int
    issues: tuple[LabelReviewIssue, ...]

    def to_markdown(self, dataset_name: str) -> str:
        lines = [
            f"# Label review report: {dataset_name}",
            "",
            f"- Cases checked: {self.case_count}",
            f"- Deterministic consistency issues: {self.issue_count}",
            f"- Cases pending expert/domain review: {self.human_review_pending_count}",
            "- This report validates label consistency, not label truth.",
            "",
            "## Reviewer status",
            "",
            "| Status | Cases |",
            "|---|---:|",
        ]
        lines.extend(
            f"| {status} | {count} |"
            for status, count in sorted(self.reviewer_status_counts.items())
        )
        lines.extend(["", "## Consistency issues", ""])
        if self.issues:
            lines.extend(
                f"- `{issue.case_id}` · `{issue.code}` — {issue.detail}"
                for issue in self.issues
            )
        else:
            lines.append("No deterministic consistency issues found.")
        lines.extend(
            [
                "",
                "## Human review gate",
                "",
                "Before claiming expert validation, a qualified reviewer must assess "
                "scenario realism, expected route, emergency category, relevant evidence, "
                "required concepts, prohibited claims, and hard-negative quality. Update "
                "record-level provenance only after that review is documented.",
            ]
        )
        return "\n".join(lines) + "\n"

    def write(self, path: str | Path, dataset_name: str) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.to_markdown(dataset_name), encoding="utf-8")
        return destination


def review_labels(cases: tuple[EvaluationCase, ...]) -> LabelReviewReport:
    """Flag contradictions that can be reviewed without model or domain judgment."""
    issues: list[LabelReviewIssue] = []
    for case in cases:
        if case.expected_emergency != (case.expected_route == "emergency"):
            issues.append(
                LabelReviewIssue(
                    case.case_id,
                    "emergency_route_mismatch",
                    "expected.emergency and expected.route disagree",
                )
            )
        if case.relevant_document_ids and "retrieval" not in case.checks:
            issues.append(
                LabelReviewIssue(
                    case.case_id,
                    "retrieval_check_missing",
                    "relevant evidence is declared without a retrieval check",
                )
            )
        overlap = set(case.required_concepts).intersection(case.prohibited_claims)
        if overlap:
            issues.append(
                LabelReviewIssue(
                    case.case_id,
                    "concept_policy_overlap",
                    "the same literal is both required and prohibited: "
                    + ", ".join(sorted(overlap)),
                )
            )

    status_counts = Counter(case.reviewer_status for case in cases)
    return LabelReviewReport(
        case_count=len(cases),
        reviewer_status_counts=dict(sorted(status_counts.items())),
        issue_count=len(issues),
        human_review_pending_count=sum(
            case.reviewer_status != "expert_reviewed" for case in cases
        ),
        issues=tuple(issues),
    )
