# Source quality rubric

Assess the actual document, not only the reputation of its domain.

## Preferred sources

1. Current clinical or public-health guidance issued through a documented evidence process.
2. Government and intergovernmental patient guidance linked to maintained recommendations.
3. High-quality systematic reviews used only within their stated population and scope.
4. Peer-reviewed primary research only when higher-level guidance is unavailable and limitations are explicit.

## Required checks

- Confirm the issuing organization and direct canonical URL.
- Confirm scope, population, jurisdiction, language, publication/version date, and update status.
- Distinguish patient education from clinical recommendations and research findings.
- Record the source's own evidence grade only; otherwise use `not_assessed`.
- Check reuse terms. A publicly readable page is not automatically openly licensed.
- Identify conflicts between sources and preserve jurisdiction-specific differences.
- Require explicit evidence before using `clinician_reviewed` or an equivalent status.

## Reject or quarantine

- Forums, anonymous advice, scraped Q&A, marketing pages, or SEO summaries.
- Model-generated medical claims presented as source material.
- Records with no canonical source, unverifiable issuer, or unclear provenance.
- Superseded or withdrawn guidance unless retained in a clearly separated archive.
- Recommendations copied across populations or jurisdictions without contextual review.

## Evidence-quality language

Use proportional claims:

- `not_assessed`: the project has not evaluated evidence certainty.
- `source_reported_*`: preserve a grade explicitly reported by the source and cite its method.
- `project_appraised_*`: use only after a documented appraisal by qualified reviewers.

Do not equate an official publisher with high-certainty evidence. Authority, methodological quality, currency, applicability, and reuse rights are separate dimensions.
