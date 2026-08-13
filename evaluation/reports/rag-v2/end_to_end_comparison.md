# RAG V2 end-to-end comparison

- Dataset: `health_mvp_v1`
- Decision: `candidate_gate_passed_production_default_unchanged`
- API cost: zero; both captures used local Qwen

| Metric | Keyword baseline | BM25 candidate | Delta |
|---|---:|---:|---:|
| task_success_rate | 0.7250 | 0.7875 | 0.0625 |
| planner_route_accuracy | 0.8125 | 0.8375 | 0.0250 |
| prediction_source_recall | 0.6250 | 0.7500 | 0.1250 |
| retrieval_recall_at_k | 0.6250 | 0.7083 | 0.0833 |
| retrieval_no_hit_accuracy | 1.0000 | 1.0000 | 0.0000 |
| citation_id_validity | 1.0000 | 1.0000 | 0.0000 |
| emergency_recall | 1.0000 | 1.0000 | 0.0000 |
| emergency_false_positive_rate | 0.0909 | 0.0909 | 0.0000 |
| prediction_error_count | 0 | 0 | 0 |
| prediction_p95_latency_ms | 13444.0128 | 17505.0925 | 4061.0798 |
| model_call_count | 95 | 94 | -1 |
| estimated_cost_total | 0.0000 | 0.0000 | 0.0000 |

## Decision

BM25 improved task-success and source-recall proxies without a measured safety, citation-validity, error-rate, or API-cost regression. Keyword remains the production default because BM25 threshold selection and this comparison use the same development set, and provider generations were captured in separate runs.

## Interpretation constraints

- These are synthetic, project-reviewed engineering cases, not clinical claims.
- BM25 threshold selection and evaluation share the same development set.
- The Qwen captures are separate runs, so planner variation is a confounder; the task-success delta is not a causal estimate of BM25 alone.
- `prediction_source_recall` measures sources returned by the captured agent; component retrieval metrics evaluate the configured retriever directly.
- Latency varies with local machine load and is reported as an operational observation, not a controlled benchmark.
