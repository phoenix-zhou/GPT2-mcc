# Evidence review workflow

## 1. Verify the source

- Open the canonical page and confirm the issuer.
- Prefer the current version and note superseded pages.
- Capture explicit publication and update dates; leave missing values unknown.
- Read the relevant section in context before drafting a summary.

## 2. Assess applicability

- Identify population, setting, jurisdiction, and intended audience.
- Separate emergency warning signs from routine self-care information.
- Flag translation or contextualization needs rather than silently generalizing.

## 3. Draft the project record

- Paraphrase concisely and avoid long source quotations.
- Preserve uncertainty and conditional language.
- Do not add diagnoses, doses, contraindications, or causal claims absent from the source.
- Choose retrieval keywords that users may actually use, including careful synonyms.

## 4. Record governance status

- Set `last_reviewed_at` to the actual review date.
- Use `project_summary_unverified_by_clinician` unless qualified review is documented.
- Use `not_assessed` unless evidence certainty was explicitly graded.
- Record reuse terms precisely or use `source-terms-apply`.

## 5. Validate and review the diff

Run the candidate in check mode, inspect normalized JSON, apply, then run:

```bash
python "<skill-directory>/scripts/validate_corpus.py" --project .
python "<skill-directory>/scripts/coverage_report.py" --project .
pytest
```

Do not treat a passing schema check as clinical approval. Report the difference between mechanical validation, source review, and clinician review.
