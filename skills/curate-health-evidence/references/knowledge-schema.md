# Governed knowledge schema

Use one JSON object per document in `knowledge/medical_guidance.json`.

## Required fields

| Field | Rule |
|---|---|
| `document_id` | Stable, unique lowercase identifier; include topic and review/version cue. |
| `source_id` | Must exist in `knowledge/source_manifest.json`. |
| `issuer` | Organization responsible for the source page. |
| `jurisdiction` | Use a documented code such as `CN`, `GB`, `US`, or `INTL`. |
| `language` | Language of the project record, normally `zh-CN`. |
| `source_language` | Language of the authoritative source. |
| `published_at` | ISO `YYYY-MM-DD` or `null`; never infer it. |
| `last_reviewed_at` | ISO date when the project checked the source and summary. |
| `version` | Source version, publication identifier, or explicit review snapshot label. |
| `evidence_grade` | Use the source's documented grade; otherwise `not_assessed`. |
| `source_type` | Controlled descriptive type such as `official_patient_guidance`. |
| `topic_cluster` | Controlled cluster ID declared in `knowledge/coverage_plan.json`. |
| `applicable_population` | Population explicitly covered by the source. |
| `review_status` | Default to `project_summary_unverified_by_clinician`; raise only with evidence. |
| `license` | Exact reuse license or `source-terms-apply`; do not guess. |
| `content_sha256` | SHA-256 of UTF-8 `content`; let `add_evidence.py` calculate it. |
| `title` | Concise project title naming the issuer and topic. |
| `content` | Project-authored summary for general health information. |
| `source_url` | Direct authoritative HTTPS page. |
| `keywords` | Non-empty list of retrieval terms and common synonyms. |

## Candidate example

```json
{
  "document_id": "issuer-topic-2026-08-review",
  "source_id": "approved-source-id",
  "issuer": "Issuing organization",
  "jurisdiction": "INTL",
  "language": "zh-CN",
  "source_language": "en",
  "published_at": null,
  "last_reviewed_at": "2026-08-11",
  "version": "web-current-2026-08-11",
  "evidence_grade": "not_assessed",
  "source_type": "official_patient_guidance",
  "topic_cluster": "gastrointestinal_symptoms",
  "applicable_population": "general_public",
  "review_status": "project_summary_unverified_by_clinician",
  "license": "source-terms-apply",
  "title": "机构：主题",
  "content": "项目自行撰写的简明中文摘要。",
  "source_url": "https://example.org/direct-source-page",
  "keywords": ["主题", "常用同义词"]
}
```

The cluster must identify a real coverage gap; do not create a new cluster only
to make a candidate fit. Paraphrases, no-hit prompts, and hard negatives belong
in evaluation data rather than evidence records.

Do not add extra fields casually. Update the project loader, validator,
coverage plan, references, and tests together when evolving the schema.
