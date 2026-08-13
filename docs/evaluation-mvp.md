# Evaluation MVP

## Purpose

The Evaluation MVP establishes a reproducible baseline before changing the
agent architecture or retrieval strategy. The evaluation package is
domain-aware rather than health-specific: each case declares its `domain`,
`scenario`, checks, expected route, relevant evidence, and provenance. The
first dataset is the ClearCare health vertical.

This is an **exploratory component baseline**, not proof of clinical quality or
end-to-end product success.

## Dataset

`evaluation/datasets/health_mvp_v1.jsonl` contains 80 synthetic cases. Its
sidecar manifest records schema version, dataset version, label-freeze date,
review status, intended use, and prohibited interpretations.

| Scenario | Cases |
|---|---:|
| Emergency | 20 |
| Routine health information | 20 |
| Insufficient context | 10 |
| Out of scope | 10 |
| Adversarial / hard negative | 10 |
| Retrieval and citation | 10 |

Every record explicitly states that it contains no personal data. The labels
are project-reviewed, not clinician- or domain-expert-reviewed. Future datasets
can use the same schema with a different `domain` and evidence collection.

## Run

```bash
python scripts/run_evaluation.py
```

The command invokes no generative model and creates JSON plus Markdown reports
under `evaluation/reports/`.

## Baseline results — 2026-08-11

| Metric | Result |
|---|---:|
| Emergency recall | 1.0000 |
| Emergency precision | 0.8333 |
| Emergency false-positive rate | 0.0909 |
| Emergency category accuracy | 1.0000 |
| Retrieval Recall@3 | 0.6250 |
| Retrieval MRR | 0.6250 |
| Irrelevant-query no-hit accuracy | 1.0000 |
| Returned citation-ID validity | 1.0000 |

These results expose two useful product failures rather than hiding them:

1. Literal emergency keywords in quoted or meta-level text create five false
   positives. The current router needs context-aware hard-negative handling
   while preserving recall.
2. Keyword retrieval finds explicit in-corpus terms but misses all nine
   paraphrase/synonym retrieval cases. This gives RAG V2 a frozen baseline to
   beat.

Latency figures in the generated report cover only in-process rules and local
retrieval. They are not model or end-to-end latency.

## What is deliberately not measured yet

- Response groundedness or unsupported-claim rate
- Human usefulness or trust

Planner routes, deterministic task success, model latency, token usage, and
estimated cost are now measured by Evaluation v1. Semantic groundedness and
human usefulness still require clearer rubrics and—where appropriate—human or
judge review. They remain `not measured` instead of being inferred from tests.

## Next increment

1. **Completed:** add a provider-prediction JSONL contract without coupling the
   evaluator to a specific model vendor.
2. **Completed:** add deterministic route, source, prohibited-claim, literal
   concept, completion, call, token, latency, and cost scoring.
3. **Completed:** add a label-consistency report; all 80 cases pass structural
   checks and remain explicitly pending qualified human review.
4. **Completed:** capture a full local-Qwen prediction run and segment failures
   by scenario and failure category.
5. **Next:** review labels and freeze regression thresholds; add judge-based
   groundedness as a separately labelled experimental metric and expand to 150
   cases only after label review.

See the bilingual [Evaluation v1 prediction contract](evaluation-v1.md).
