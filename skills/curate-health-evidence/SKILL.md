---
name: curate-health-evidence
description: Curate, validate, and audit governed health-evidence corpora for ClearCare-style RAG projects. Use when adding or updating official health guidance, reviewing provenance and reuse metadata, checking content hashes or stale reviews, assessing source quality, or generating corpus coverage reports. Do not use for diagnosis, treatment selection, or patient-specific medical advice.
---

# Curate Health Evidence

Maintain a traceable health-information corpus without treating source authority as proof that a project-authored summary is clinically validated.

## Route the task

- For adding or updating a document, read `references/knowledge-schema.md`, then follow `references/review-workflow.md`.
- For approving a new source or auditing evidence quality, read `references/source-quality-rubric.md` and `references/review-workflow.md`.
- For integrity or freshness checks, run `scripts/validate_corpus.py`.
- For corpus inventory and gap analysis, run `scripts/coverage_report.py`.

## Work safely

1. Locate the project root containing `knowledge/medical_guidance.json` and `knowledge/source_manifest.json`.
2. Inspect the authoritative source page before changing data. Prefer primary issuing organizations and record uncertainty rather than guessing metadata.
3. Never mark content as clinician-reviewed, evidence-graded, licensed, or current without explicit supporting evidence.
4. Keep project-authored summaries distinguishable from source text. Do not paste large copyrighted passages.
5. Do not convert the corpus into patient-specific diagnosis, prescribing, or treatment instructions.
6. Preserve unrelated user changes and show the exact records affected.

## Add a governed document

1. Confirm that `source_id` exists in `knowledge/source_manifest.json`. If it does not, assess the source with `references/source-quality-rubric.md` and add a manifest entry before continuing.
2. Create a candidate JSON object following `references/knowledge-schema.md`. Omit `content_sha256`; the script calculates it.
3. Resolve the absolute directory containing this `SKILL.md`; use its scripts whether the skill is installed or checked out in the project.
4. Check without writing:

   ```bash
   python "<skill-directory>/scripts/add_evidence.py" \
     --project . --candidate /path/to/candidate.json
   ```

5. Review the normalized record printed by the script. Apply only when the user requested the change:

   ```bash
   python "<skill-directory>/scripts/add_evidence.py" \
     --project . --candidate /path/to/candidate.json --apply
   ```

6. Run corpus validation and the project test suite.

## Audit a corpus

Run:

```bash
python "<skill-directory>/scripts/validate_corpus.py" --project .
python "<skill-directory>/scripts/coverage_report.py" --project .
```

Use `--fail-on-stale` when CI should reject records whose review interval has elapsed. Treat coverage counts as inventory, not proof of clinical quality.

## Report results

State:

- records and sources checked;
- files or document IDs changed;
- validation errors and stale-review warnings;
- unsupported metadata left as `null`, `not_assessed`, or an explicit unverified status;
- whether tests passed;
- remaining coverage or review gaps.
