import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = PROJECT_ROOT / "skills" / "curate-health-evidence" / "scripts"


def run_script(name, *args):
    return subprocess.run(
        [sys.executable, str(SKILL_SCRIPTS / name), *map(str, args)],
        check=False,
        capture_output=True,
        text=True,
    )


def temporary_project(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT / "knowledge", project / "knowledge")
    return project


def candidate_record():
    return {
        "document_id": "cdc-test-topic-2026-08-review",
        "source_id": "cdc",
        "issuer": "U.S. Centers for Disease Control and Prevention",
        "jurisdiction": "US",
        "language": "zh-CN",
        "source_language": "en",
        "published_at": None,
        "last_reviewed_at": "2026-08-11",
        "version": "test-review-2026-08-11",
        "evidence_grade": "not_assessed",
        "source_type": "official_public_health_guidance",
        "topic_cluster": "neurological_warning_signs",
        "applicable_population": "general_public",
        "review_status": "project_summary_unverified_by_clinician",
        "license": "source-terms-apply",
        "title": "CDC：测试主题",
        "content": "这是用于验证 Skill 的项目摘要。",
        "source_url": "https://www.cdc.gov/test-topic/",
        "keywords": ["测试主题"],
    }


def test_skill_validator_and_coverage_report_run_on_project():
    validation = run_script("validate_corpus.py", "--project", PROJECT_ROOT)
    coverage = run_script("coverage_report.py", "--project", PROJECT_ROOT)

    assert validation.returncode == 0
    assert "Checked 9 documents from 3 approved sources" in validation.stdout
    assert coverage.returncode == 0
    assert "Corpus ID: health_corpus_v1" in coverage.stdout
    assert "Status: planning" in coverage.stdout
    assert "Documents: 9 / 24" in coverage.stdout
    assert "Remaining document gap: 15" in coverage.stdout
    assert "Clusters at document target: 2 / 8" in coverage.stdout
    assert "Clusters at source minimum: 2 / 8" in coverage.stdout
    assert "| gastrointestinal_symptoms | 3 | 3 | 0 | 3 |" in coverage.stdout
    assert "| respiratory_symptoms | 3 | 3 | 0 | 3 |" in coverage.stdout
    assert "project_summary_unverified_by_clinician" in coverage.stdout


def test_add_evidence_checks_without_writing_then_applies(tmp_path):
    project = temporary_project(tmp_path)
    records_path = project / "knowledge" / "medical_guidance.json"
    before = records_path.read_text(encoding="utf-8")
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps(candidate_record(), ensure_ascii=False), encoding="utf-8"
    )

    checked = run_script(
        "add_evidence.py", "--project", project, "--candidate", candidate
    )

    assert checked.returncode == 0
    assert "no files changed" in checked.stdout
    assert records_path.read_text(encoding="utf-8") == before

    applied = run_script(
        "add_evidence.py",
        "--project",
        project,
        "--candidate",
        candidate,
        "--apply",
    )
    records = json.loads(records_path.read_text(encoding="utf-8"))
    added = records[-1]

    assert applied.returncode == 0
    assert added["document_id"] == candidate_record()["document_id"]
    assert added["content_sha256"] == hashlib.sha256(
        added["content"].encode("utf-8")
    ).hexdigest()
    assert run_script("validate_corpus.py", "--project", project).returncode == 0


def test_add_evidence_rejects_unknown_source(tmp_path):
    project = temporary_project(tmp_path)
    record = candidate_record()
    record["source_id"] = "unapproved-source"
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "add_evidence.py", "--project", project, "--candidate", candidate
    )

    assert result.returncode == 1
    assert "unknown source_id" in result.stdout


def test_add_evidence_rejects_approved_id_with_unapproved_host(tmp_path):
    project = temporary_project(tmp_path)
    record = candidate_record()
    record["source_url"] = "https://www.cdc.gov.attacker.example/topic"
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "add_evidence.py", "--project", project, "--candidate", candidate
    )

    assert result.returncode == 1
    assert "source_url host is not approved" in result.stdout


def test_add_evidence_rejects_unknown_topic_cluster(tmp_path):
    project = temporary_project(tmp_path)
    record = candidate_record()
    record["topic_cluster"] = "invented_cluster"
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "add_evidence.py", "--project", project, "--candidate", candidate
    )

    assert result.returncode == 1
    assert "unknown topic_cluster" in result.stdout


def test_validator_rejects_coverage_target_mismatch(tmp_path):
    project = temporary_project(tmp_path)
    plan_path = project / "knowledge" / "coverage_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["target_document_count"] = 25
    plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    result = run_script("validate_corpus.py", "--project", project)

    assert result.returncode == 1
    assert "target_document_count does not match cluster targets" in result.stdout


def test_validator_rejects_premature_corpus_freeze(tmp_path):
    project = temporary_project(tmp_path)
    plan_path = project / "knowledge" / "coverage_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["status"] = "frozen"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    result = run_script("validate_corpus.py", "--project", project)

    assert result.returncode == 1
    assert "frozen corpus document count does not match target" in result.stdout
